from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
    InvalidHashError
)

from app import storage

password_hasher = PasswordHasher()

def register_user(username, password):
    username = username.strip()

    if not username or len(username) > 64 or len(password) < 8:
        return False

    password_hash = password_hasher.hash(password)

    return storage.add_user(username, password_hash)

def authenticate_user(username, password):
    stored_hash = storage.get_user(username)

    if stored_hash is None:
        return False

    try:
        password_hasher.verify(stored_hash, password)

        if password_hasher.check_needs_rehash(stored_hash):
            new_hash = password_hasher.hash(password)
            storage.update_password_hash(username, new_hash)

        return True

    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError
    ):
        return False
