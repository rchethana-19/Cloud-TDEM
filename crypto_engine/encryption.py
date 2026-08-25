"""
encryption.py

AES-256-GCM Encryption/Decryption
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os


NONCE_SIZE = 12  # Recommended size for AES-GCM


def encrypt(plaintext: bytes, key: bytes):
    """
    Encrypts plaintext using AES-256-GCM.

    Returns:
        ciphertext,
        nonce,
        authentication tag
    """

    aes = AESGCM(key)

    nonce = os.urandom(NONCE_SIZE)

    encrypted = aes.encrypt(
        nonce,
        plaintext,
        None
    )

    # Last 16 bytes are authentication tag
    ciphertext = encrypted[:-16]
    tag = encrypted[-16:]

    return ciphertext, nonce, tag


def decrypt(ciphertext: bytes,
            nonce: bytes,
            tag: bytes,
            key: bytes):
    """
    Decrypts AES-GCM ciphertext.
    """

    aes = AESGCM(key)

    encrypted = ciphertext + tag

    plaintext = aes.decrypt(
        nonce,
        encrypted,
        None
    )

    return plaintext


if __name__ == "__main__":

    key = AESGCM.generate_key(bit_length=256)

    message = b"Time-Dependent Encryption Model"

    ciphertext, nonce, tag = encrypt(
        message,
        key
    )

    recovered = decrypt(
        ciphertext,
        nonce,
        tag,
        key
    )

    print("Original :", message)

    print("Ciphertext :", ciphertext.hex())

    print("Nonce :", nonce.hex())

    print("Tag :", tag.hex())

    print("Recovered :", recovered)