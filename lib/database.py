from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from lib.config_reader import config
from lib.logger import peewee_logger
from lib.init import database_file_path
from lib.storage import storage
from lib.utils.utils import used_today
from peewee import *

db = SqliteDatabase(database_file_path)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True, primary_key=True)
    bet = DecimalField(default=100, decimal_places=64)
    daily_prize_time = DateTimeField(default=datetime(1980, 1, 1))
    mine_attempt_time = DateTimeField(default=datetime(1980, 1, 1))


class Block(BaseModel):
    height = IntegerField(unique=True, primary_key=True)
    timestamp = DateTimeField()
    miner = ForeignKeyField(User, backref='blocks')
    merkle_root = CharField(max_length=64)
    nonce = IntegerField()
    prev_hash = CharField(max_length=64)
    block_hash = CharField(max_length=64, unique=True)

    class Meta:
        indexes = (
            (('height',), True),
        )


class Transaction(BaseModel):
    number = AutoField()
    block = ForeignKeyField(Block, null=True, backref='transactions')  # None = pending
    timestamp = DateTimeField()
    from_user = ForeignKeyField(User, null=True, backref='sent')
    to_user = ForeignKeyField(User, backref='received')
    amount = DecimalField(decimal_places=64, constraints=[Check('amount > 0')])
    description = TextField(null=True)
    tx_hash = CharField(max_length=64, unique=True)

    def __str__(self):
        return f'{"pending" if self.block is None else self.block} - {self.timestamp}'

    class Meta:
        indexes = (
            (('block', 'timestamp'), False),
        )


db.connect()
# db.drop_tables([User, Block, Transaction])
db.create_tables([User, Block, Transaction])

peewee_logger.info("Connected to database.")
peewee_logger.disabled = True


def is_user_exists(username: str) -> bool:
    return User.get_or_none(username=username) is not None


def get_user_bet(username: str) -> Decimal:
    user = User.get_or_create(username=username)[0]
    return user.bet


def set_user_bet(username: str, bet: Decimal | str | float) -> None:
    user = User.get_or_create(username=username)[0]
    user.bet = Decimal(bet)
    user.save()


def available_daily_prize(username: str) -> bool:
    user = User.get_or_create(username=username)[0]
    if not used_today(user.daily_prize_time, config.day_start_time):
        user.daily_prize_time = datetime.now()
        user.save()
        return True
    return False


def available_mine_attempt(username: str) -> bool:
    user = User.get_or_create(username=username)[0]
    now = datetime.now()
    delta = timedelta(seconds=storage.mine_block_interval_seconds) - (now - user.mine_attempt_time)
    if delta.total_seconds() < 0:
        user.mine_attempt_time = now
        user.save()
        return True
    return False


def get_user_transactions(username: str, limit: Optional[int] = None) -> list[Transaction]:
    return list(
        Transaction
        .select()
        .where((Transaction.from_user.username == username) | (Transaction.to_user.username == username))
        .order_by(Transaction.number.desc())
        .limit(limit)
    )


def get_transactions(limit: Optional[int] = None, ascending=False) -> list[Transaction]:
    transactions = (
        Transaction
        .select()
        .order_by(Transaction.number.asc() if ascending else Transaction.number.desc())
        .limit(limit)
    )
    users = User.select()
    return prefetch(transactions, users)


def get_pending_transactions(limit: Optional[int] = None, ascending=False) -> list[Transaction]:
    return list(
        Transaction
        .select()
        .where(Transaction.block.is_null())
        .order_by(Transaction.number.asc() if ascending else Transaction.number.desc())
        .limit(limit)
    )


def delete_pending_transactions() -> int:
    return Transaction.delete().where(Transaction.block.is_null()).execute()


def get_block_transactions(block: Block, limit: Optional[int] = None, ascending=False) -> list[Transaction]:
    return list(
        block.transactions.
        order_by(Transaction.number.asc() if ascending else Transaction.number.desc()).
        limit(limit)
    )


def get_block(height: int) -> Block | None:
    return Block.get_or_none(height=height)


def get_transactions_count() -> int:
    return Transaction.select().count()


def get_blocks(limit: Optional[int] = None, ascending=False) -> list[Block]:
    return list(
        Block
        .select()
        .order_by(Block.height.asc() if ascending else Block.height.desc())
        .limit(limit)
    )


def get_blocks_count() -> int:
    return Block.select().count()
