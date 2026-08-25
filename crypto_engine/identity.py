"""
identity.py

Generates the Identity Fragment (Fid)
using PBKDF2-HMAC-SHA256.
"""

import os
import hashlib


KEY_LENGTH = 32          # 256 bits
ITERATIONS = 100000


def generate_identity_fragment(identity: str):
    """
    Generates a random salt and derives
    a 256-bit identity fragment.

    Returns:
        salt
        Fid
    """

    salt = os.urandom(16)

    fid = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=identity.encode(),
        salt=salt,
        iterations=ITERATIONS,
        dklen=KEY_LENGTH
    )

    return salt, fid


def regenerate_identity_fragment(identity: str, salt: bytes):
    """
    Regenerates Fid using
    the same identity and salt.
    """

    return hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=identity.encode(),
        salt=salt,
        iterations=ITERATIONS,
        dklen=KEY_LENGTH
    )


def verify_identity_fragment(identity, salt, expected_fid):

    new_fid = regenerate_identity_fragment(
        identity,
        salt
    )

    return new_fid == expected_fid


if __name__ == "__main__":

    identity = "Sanjay@123"

    salt, fid = generate_identity_fragment(identity)

    print("Salt :", salt.hex())

    print("Fid  :", fid.hex())

    print(
        "Verified:",
        verify_identity_fragment(identity, salt, fid)
    )