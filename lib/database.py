from lib.init import database_file_path
from peewee import *

peewee_db = SqliteDatabase(database_file_path)


class BaseModel(Model):
    class Meta:
        database = peewee_db


class User(BaseModel):
    username = CharField(unique=True)
    balance = DecimalField(default=0)
    bet = DecimalField(default=100)


peewee_db.connect()
# peewee_db.drop_tables([User])
peewee_db.create_tables([User])


class Database:
    @staticmethod
    def create_user(username: str, balance=0):
        user = User(username=username, balance=balance)
        user.save()
        return user

    def get_user(self, username: str) -> User:
        try:
            return User.get(User.username == username)
        except Exception:
            return self.create_user(username)

    @staticmethod
    def set_user_balance(user: User, balance: float) -> None:
        user.update(balance=balance).execute()

    @staticmethod
    def set_user_bet(user: User, bet: float) -> None:
        user.update(bet=bet).execute()


database = Database()

if __name__ == '__main__':
    user = database.get_user('123')
    database.set_user_balance(user, 600)
    print(database.get_user(str(user.username)).balance)
