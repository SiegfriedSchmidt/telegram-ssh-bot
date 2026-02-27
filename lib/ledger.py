import csv
import hashlib
import json
from threading import Lock
from decimal import Decimal
from datetime import datetime
from io import StringIO
from typing import Optional, BinaryIO
from peewee import prefetch
from lib.database import db, Block, Transaction, User
from lib.logger import ledger_logger

GENESIS_BLOCK_REWARD = Decimal(1_000_000)
EMPTY_HASH = "0" * 64
mining_lock = Lock()


def compute_hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def compute_merkle_root(tx_hashes: list[str]) -> str:
    if len(tx_hashes) == 0:
        return EMPTY_HASH

    level = [bytes.fromhex(h) for h in tx_hashes]

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        next_level = []
        for i in range(0, len(level), 2):
            combined = level[i] + level[i + 1]
            hash1 = hashlib.sha256(combined).digest()
            hash2 = hashlib.sha256(hash1).digest()
            next_level.append(hash2)

        level = next_level

    return level[0].hex()


class Ledger:
    def __init__(self, block_reward=Decimal(1000), difficulty=2):
        self.block_reward = block_reward
        self.difficulty = "0" * difficulty
        self.__genesis_username = ""
        self.__balances: dict[str, Decimal] = dict()

    @property
    def genesis_username(self) -> str:
        return self.__genesis_username

    @genesis_username.setter
    def genesis_username(self, username: str):
        self.__genesis_username = username

    def init_genesis(self):
        if self.get_blocks_count() == 0:
            self.__mine_block(self.__genesis_username, GENESIS_BLOCK_REWARD, "Genesis block reward")
            ledger_logger.info("Genesis block created!")

    def __update_balance(self, from_username: str | None, to_username: str, amount: Decimal) -> None:
        if from_username:
            if from_username not in self.__balances or self.__balances[from_username] < amount:
                raise ValueError("Negative balance detected!")
            self.__balances[from_username] -= amount

        if to_username not in self.__balances:
            self.__balances[to_username] = amount
        else:
            self.__balances[to_username] += amount

    def __update_balance_transactions(self, txs: list[Transaction]) -> None:
        for tx in txs:
            self.__update_balance(
                tx.from_user.username if tx.from_user else None,
                tx.to_user.username,
                tx.amount
            )

    def load_and_verify_chain(self):
        self.__balances.clear()

        with db.atomic():
            blocks = self.get_blocks(ascending=True)
            if not blocks:
                self.init_genesis()
                return

            if blocks[0].miner != self.genesis_username:
                raise ValueError(
                    f"BLOCKCHAIN BROKEN! Genesis username mismatch! '{blocks[0].miner}' != '{self.genesis_username}'"
                )

            prev_hash = EMPTY_HASH
            for block in blocks:
                txs: list[Transaction] = list(block.transactions.order_by(Transaction.number.asc()))
                miner_tx = txs[-1]  # The last transaction in block is miner reward transaction

                merkle_root = compute_merkle_root([tx.tx_hash for tx in txs])
                if merkle_root != block.merkle_root:
                    raise ValueError(
                        f"BLOCKCHAIN BROKEN at height {block.height}! Transactions merkle root: {merkle_root}, block merkle root: {block.merkle_root}"
                    )

                miner_username = miner_tx.to_user.username
                if miner_username != block.miner.username:
                    raise ValueError(
                        f"BLOCKCHAIN BROKEN at height {block.height}! Transaction miner username: {miner_username}, block miner username: {block.miner.username}"
                    )

                miner_reward = miner_tx.amount
                if block.height != 0 and miner_reward != self.block_reward:
                    raise ValueError(
                        f"BLOCKCHAIN BROKEN at height {block.height}! Transaction miner reward: {miner_reward}, block miner reward: {self.block_reward}"
                    )

                block_data = {
                    "height": block.height,
                    "timestamp": block.timestamp,
                    "miner": miner_username,
                    "merkle_root": merkle_root,
                    "nonce": block.nonce,
                    "prev_hash": prev_hash,
                }
                computed_hash = compute_hash(block_data)

                if computed_hash != block.block_hash:
                    raise ValueError(
                        f"BLOCKCHAIN BROKEN at height {block.height}! Block hash: {block.block_hash}, computed hash: {computed_hash}"
                    )

                if not computed_hash.startswith(self.difficulty):
                    raise ValueError(
                        f"BLOCKCHAIN BROKEN at height {block.height}! Computed hash: {computed_hash}, difficulty: {self.difficulty}"
                    )

                self.__update_balance_transactions(txs)
                prev_hash = computed_hash

        ledger_logger.info(
            f"Blockchain verified! {self.get_blocks_count()} blocks loaded. {self.get_transactions_count()} transactions loaded. Users with balance: {len(self.__balances)}"
        )
        self.__update_balance_transactions(self.get_pending_transactions(ascending=True))
        self.mine_block()

    def mine_block(self, miner_username: str = None) -> Block | None:
        if miner_username is None:
            miner_username = self.__genesis_username

        with mining_lock:
            pending_txs = self.get_pending_transactions(ascending=True)

            if not pending_txs:
                return None

            return self.__mine_block(miner_username, pending_txs=pending_txs)

    def __mine_block(self, miner_username: str, reward: Decimal = None, tx_description="Block reward",
                     pending_txs: list[Transaction] = None) -> Block:
        if reward is None:
            reward = self.block_reward
        if pending_txs is None:
            pending_txs = []

        with db.atomic():
            pending_txs += [self.__record_transaction(None, miner_username, reward, tx_description)]  # add miner tx
            merkle_root = compute_merkle_root([tx.tx_hash for tx in pending_txs])
            block = self.__create_block(miner_username, merkle_root)

            for tx in pending_txs:
                tx.block = block
                tx.save()

            ledger_logger.info(
                f"Block {block.height} with {len(pending_txs)} transactions mined by {block.miner}! Nonce: {block.nonce}, Block hash: {block.block_hash}"
            )
            return block

    def __create_block(self, miner_username: str, merkle_root: str) -> Block:
        last_block = Block.select(Block.height, Block.block_hash).order_by(Block.height.desc()).first()
        if last_block is None:
            height = 0
            prev_hash = EMPTY_HASH
        else:
            height = last_block.height + 1
            prev_hash = last_block.block_hash

        block_data = dict()
        block_data.update({
            "height": height,
            "timestamp": datetime.now().isoformat(),
            "miner": miner_username,
            "merkle_root": merkle_root,
            "prev_hash": prev_hash
        })
        block_data["nonce"] = self.__mine_nonce(block_data)
        block_data["block_hash"] = compute_hash(block_data)
        block_data["miner"] = User.get_or_create(username=miner_username)[0]
        block = Block.create(**block_data)
        return block

    def __mine_nonce(self, block_data: dict) -> int:
        nonce = 0
        while True:
            block_data["nonce"] = nonce
            block_hash = compute_hash(block_data)
            if block_hash.startswith(self.difficulty):
                break
            nonce += 1
        return nonce

    def __record_transaction(self, from_username: str | None, to_username: str, amount: Decimal | str | float,
                             description: str = None, timestamp: str = None) -> Transaction:
        amount = Decimal(int(amount))

        if amount <= 0:
            raise ValueError("Amount must be positive")

        if from_username and self.__balances.get(from_username, Decimal("0")) < amount:
            raise ValueError("Insufficient balance")

        with db.atomic():
            tx_data = dict()
            tx_data.update({
                "timestamp": datetime.now().isoformat() if timestamp is None else timestamp,
                "from_user": from_username,
                "to_user": to_username,
                "amount": str(amount),
                "description": description,
            })

            tx_data["tx_hash"] = compute_hash(tx_data)
            tx_data["from_user"] = User.get_or_create(username=from_username)[0] if from_username else None
            tx_data["to_user"] = User.get_or_create(username=to_username)[0]
            tx = Transaction.create(**tx_data)

            self.__update_balance(from_username, to_username, amount)

            ledger_logger.info(f"Transaction recorded {from_username} -> {to_username}: {amount}, {description}")
            return tx

    def record_transaction(self, from_username: str, to_username: str, amount: Decimal | str | float,
                           description: str = None) -> Transaction:
        return self.__record_transaction(from_username, to_username, amount, description)

    def record_deposit(self, from_username: str, amount: Decimal | str | float, description: str = None):
        self.record_transaction(from_username, self.__genesis_username, amount, description)

    def record_gain(self, to_username: str, amount: Decimal | str | float, description: str = None):
        self.record_transaction(self.__genesis_username, to_username, amount, description)

    def get_user_balance(self, username: str) -> Decimal:
        return self.__balances.get(username, 0)

    def get_all_balances(self):
        return sorted(list(self.__balances.items()), key=lambda item: item[1], reverse=True)

    def import_transactions_csv(self, file: BinaryIO) -> int:
        reader = csv.reader(StringIO(file.read().decode("utf-8")), delimiter=' ', quotechar='"')
        next(reader)
        count = 0
        for row in reader:
            if all(row):
                count += 1
                self.__record_transaction(*row)

        return count

    def export_transactions_csv(self) -> str:
        file = StringIO()
        writer = csv.writer(file, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["from_user", "to_user", "amount", "description", "timestamp"])
        for tx in self.get_transactions(ascending=True):
            writer.writerow([
                tx.from_user.username if tx.from_user else None,
                tx.to_user.username,
                tx.amount,
                tx.description,
                tx.timestamp
            ])
        file.name = "transactions.csv"
        return file.getvalue()

    @staticmethod
    def get_user_transactions(username: str, limit: Optional[int] = None) -> list[Transaction]:
        return list(
            Transaction
            .select()
            .where((Transaction.from_user.username == username) | (Transaction.to_user.username == username))
            .order_by(Transaction.number.desc())
            .limit(limit)
        )

    @staticmethod
    def get_transactions(limit: Optional[int] = None, ascending=False) -> list[Transaction]:
        transactions = (
            Transaction
            .select()
            .order_by(Transaction.number.asc() if ascending else Transaction.number.desc())
            .limit(limit)
        )
        users = User.select()
        return prefetch(transactions, users)

    @staticmethod
    def get_pending_transactions(limit: Optional[int] = None, ascending=False) -> list[Transaction]:
        return list(
            Transaction
            .select()
            .where(Transaction.block.is_null())
            .order_by(Transaction.number.asc() if ascending else Transaction.number.desc())
            .limit(limit)
        )

    @staticmethod
    def get_transactions_count() -> int:
        return Transaction.select().count()

    @staticmethod
    def get_blocks(limit: Optional[int] = None, ascending=False) -> list[Block]:
        return list(
            Block
            .select()
            .order_by(Block.height.asc() if ascending else Block.height.desc())
            .limit(limit)
        )

    @staticmethod
    def get_blocks_count() -> int:
        return Block.select().count()
