import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITERATIONS = 100_000

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Generates a PBKDF2HMAC sha256 derivation key with given salt key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode())

def encrypt_data(data: bytes, password: str) -> bytes:
    """
    Encrypts given data and master_password with random salt key, nonce and aesgcm encryption.
    """
    salt = os.urandom(16)
    key = derive_key(password, salt)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    # Store salt and nonce with the ciphertext
    return salt + nonce + ciphertext

def decrypt_data(encrypted_blob: bytes, password: str) -> bytes:
    """
    Dencrypts given data using master_password and aesgcm decryption.
    """
    salt = encrypted_blob[:16]
    nonce = encrypted_blob[16:28]
    ciphertext = encrypted_blob[28:]
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)