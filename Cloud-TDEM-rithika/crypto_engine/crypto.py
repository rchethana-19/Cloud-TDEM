"""
crypto.py

Common cryptographic utilities.
"""

import os


KEY_SIZE = 32


def generate_master_key():
    """
    Generates a secure
    256-bit Master Key.
    """

    return os.urandom(KEY_SIZE)


def xor_bytes(a: bytes, b: bytes):

    return bytes(

        x ^ y

        for x, y in zip(a, b)

    )


def xor_three(a: bytes,
              b: bytes,
              c: bytes):

    return bytes(

        x ^ y ^ z

        for x, y, z in zip(a, b, c)

    )


if __name__ == "__main__":

    key = generate_master_key()

    print("Master Key:")

    print(key.hex())