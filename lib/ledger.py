import hashlib
import json
from decimal import Decimal
from datetime import datetime
from typing import Optional

from peewee import prefetch

from lib.database import db, Transaction, User
from lib.logger import ledger_logger

GENESIS_USER = "admin"
GENESIS = {
    "height": 0,
    "from_user": None,
    "to_user": GENESIS_USER,
    "amount": Decimal(1e12),
    "prev_hash": "0" * 64,
    "description": "GENESIS BLOCK"
}


def compute_hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


class Ledger:
    def __init__(self):
        self.__balances: dict[str, Decimal] = dict()
        self.load_and_verify_chain()

    def init_genesis(self):
        genesis_user = User.get_or_create(username=GENESIS_USER)[0]
        if self.get_transactions_count() == 0:
            genesis_data = GENESIS.copy()
            genesis_data["timestamp"] = datetime.now().isoformat()
            genesis_hash = compute_hash(genesis_data)

            genesis_data["to_user"] = genesis_user
            Transaction.create(**genesis_data, tx_hash=genesis_hash)
            ledger_logger.info("Genesis transaction created!")

    def __update_balance(self, from_username: str, to_username: str, amount: Decimal) -> None:
        if from_username:
            if from_username not in self.__balances:
                raise ValueError("Negative balance detected!")
            self.__balances[from_username] -= amount
        if to_username:
            if to_username not in self.__balances:
                self.__balances[to_username] = amount
            else:
                self.__balances[to_username] += amount

    def load_and_verify_chain(self):
        self.__balances.clear()
        self.__balances[GENESIS_USER] = GENESIS["amount"]

        txs = self.__get_all_transactions()
        if not txs:
            self.init_genesis()
            return

        prev_hash = GENESIS["prev_hash"]
        for tx in txs:
            # Recompute hash exactly as it was created
            tx_data = {
                "height": tx.height,
                "timestamp": tx.timestamp,
                "from_user": tx.from_user.username if tx.from_user else None,
                "to_user": tx.to_user.username if tx.to_user else None,
                "amount": tx.amount,
                "prev_hash": prev_hash,
                "description": tx.description
            }
            computed_hash = compute_hash(tx_data)

            if computed_hash != tx.tx_hash:
                raise ValueError(f"CHAIN BROKEN at height {tx.height}! Tampering detected!")

            # Apply to state
            if tx.from_user and tx.to_user:
                self.__update_balance(tx.from_user.username, tx.to_user.username, tx.amount)

            prev_hash = tx.tx_hash

        ledger_logger.info(
            f"Blockchain verified! {len(txs)} transactions loaded. Users with balance: {len(self.__balances)}"
        )

    def record_transaction(self, from_username: str, to_username: str, amount: Decimal | str | float,
                           description: str = None):
        amount = Decimal(int(amount))

        if amount <= 0:
            raise ValueError("Amount must be positive")

        if from_username and self.__balances.get(from_username, Decimal("0")) < amount:
            raise ValueError("Insufficient balance")

        with db.atomic():
            last_tx = Transaction.select().order_by(Transaction.height.desc()).first()

            from_user = User.get_or_create(username=from_username)[0]
            to_user = User.get_or_create(username=to_username)[0]

            tx_data = {
                "height": last_tx.height + 1,
                "timestamp": datetime.now().isoformat(),
                "from_user": from_user.username if from_user else None,
                "to_user": to_user.username if to_user else None,
                "amount": str(amount),
                "prev_hash": last_tx.tx_hash,
                "description": description,
            }

            new_hash = compute_hash(tx_data)
            tx_data["from_user"] = from_user
            tx_data["to_user"] = to_user
            tx = Transaction.create(**tx_data, tx_hash=new_hash)

            self.__update_balance(from_username, to_username, amount)

            ledger_logger.info(
                f"Transaction {tx_data['height']} recorded {from_username} -> {to_username}: {amount}, {description}"
            )
            return tx

    def record_deposit(self, from_username: str, amount: Decimal | str | float, description: str = None):
        self.record_transaction(from_username, GENESIS_USER, amount, description)

    def record_gain(self, to_username: str, amount: Decimal | str | float, description: str = None):
        self.record_transaction(GENESIS_USER, to_username, amount, description)

    def get_user_balance(self, username: str) -> Decimal:
        return self.__balances.get(username, 0)

    @staticmethod
    def get_user_transactions(username: str, limit: Optional[int] = None) -> list[Transaction]:
        return list(
            Transaction
            .select()
            .where((Transaction.from_user.username == username) | (Transaction.to_user.username == username))
            .order_by(Transaction.height.desc())
            .limit(limit)
        )

    @staticmethod
    def get_recent_transactions(limit: Optional[int] = None) -> list[Transaction]:
        transactions = (
            Transaction
            .select()
            .order_by(Transaction.height.desc())
            .limit(limit)
        )
        users = User.select()
        return prefetch(transactions, users)

    @staticmethod
    def get_transactions_count() -> int:
        return Transaction.select().count()

    @staticmethod
    def __get_all_transactions() -> list[Transaction]:
        transactions = (
            Transaction
            .select()
            .order_by(Transaction.height.asc())
        )
        users = User.select()
        return prefetch(transactions, users)


ledger = Ledger()
