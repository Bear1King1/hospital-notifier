from cryptography.fernet import Fernet

KEY = b'csnwZlPbUIziE4pi33IS_MXPUOmNYhh9iTYPVraooxo='
cipher_suite = Fernet(KEY)


def encrypt_message(message: str) -> bytes:
    return cipher_suite.encrypt(message.encode())


def decrypt_message(encrypted_message: bytes) -> str:
    return cipher_suite.decrypt(encrypted_message).decode()
