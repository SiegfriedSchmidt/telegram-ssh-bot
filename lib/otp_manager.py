import pyotp
from datetime import datetime, timedelta
from pydantic import SecretStr

from lib.config_reader import config

OTP_ACCESS_GRANTED_HOURS = 24


class OTPUser:
    def __init__(self):
        self.authenticated = False
        self.attempts = 0
        self.last_attempt_time = datetime.min

    def update_attempts(self):
        self.attempts += 1
        self.last_attempt_time = datetime.now()

    def authenticate(self):
        self.authenticated = True
        self.attempts = 0
        self.last_attempt_time = datetime.now()

    def deauthenticate(self):
        self.authenticated = False

    def attempt_timedelta(self):
        return datetime.now() - self.last_attempt_time


class OTPManager:
    def __init__(self, otp_secret: SecretStr):
        self.users: dict[int, OTPUser] = dict()
        self.totp = pyotp.TOTP(otp_secret.get_secret_value())

    def authenticate(self, chat_id: int, code: str) -> str:
        user = self.users.get(chat_id)
        if user:
            if user.authenticated:
                delta = (timedelta(hours=OTP_ACCESS_GRANTED_HOURS) - user.attempt_timedelta()) / timedelta(hours=1)
                return f'You are already authenticated, remaining access time is {round(delta)} hours.'

            delta = int((timedelta(seconds=2 ** user.attempts) - user.attempt_timedelta()).total_seconds())
            if delta > 0:
                return f'For the next attempt you should wait for {delta} seconds.'
        else:
            user = OTPUser()
            self.users[chat_id] = user

        if self.totp.verify(code):
            user.authenticate()
            return ''
        else:
            user.update_attempts()
            return f'Invalid OTP, for the next attempt you should wait for {2 ** user.attempts} seconds.'

    def is_authenticated(self, chat_id: int) -> bool:
        user = self.users.get(chat_id)
        if user and user.authenticated:
            delta = user.attempt_timedelta()
            if delta < timedelta(hours=OTP_ACCESS_GRANTED_HOURS):
                return True

            user.deauthenticate()
        return False


otp_manager = OTPManager(config.otp_secret)
