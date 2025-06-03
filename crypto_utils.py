from cryptography.fernet import Fernet

from dotenv import load_dotenv
import os

# Load variables from .env into the environment
load_dotenv()
KEY = os.getenv('MY_SECRET_KEY')
cipher_suite = Fernet(KEY.encode())


def encrypt_message(message: str) -> bytes:
    return cipher_suite.encrypt(message.encode())


def decrypt_message(encrypted_message: bytes) -> str:
    return cipher_suite.decrypt(encrypted_message).decode()
