from decimal import Decimal
from lib.logger import peewee_logger
from lib.init import database_file_path
from peewee import *

db = SqliteDatabase(database_file_path)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True, primary_key=True)
    bet = DecimalField(default=100, decimal_places=10)


class Transaction(BaseModel):
    height = IntegerField(unique=True, primary_key=True)  # 0 = genesis, 1, 2, ...
    timestamp = DateTimeField()
    from_user = ForeignKeyField(User, null=True, backref='sent')
    to_user = ForeignKeyField(User, null=True, backref='received')
    amount = DecimalField(decimal_places=8, constraints=[Check('amount > 0')])
    description = TextField(null=True)
    prev_hash = CharField(max_length=64)
    tx_hash = CharField(max_length=64, unique=True)

    def __str__(self):
        return f'{self.height} - {self.timestamp}'

    class Meta:
        indexes = (
            (('height',), True),
            (('from_user', 'to_user'), False),
        )


db.connect()
# db.drop_tables([User, Transaction])
db.create_tables([User, Transaction])

peewee_logger.info("Connected to database.")
peewee_logger.disabled = True


def get_user_bet(username: str) -> Decimal:
    user = User.get_or_create(username=username)[0]
    return user.bet


def set_user_bet(username: str, bet: Decimal | str | float) -> None:
    user = User.get_or_create(username=username)[0]
    user.bet = Decimal(bet)
    user.save()
