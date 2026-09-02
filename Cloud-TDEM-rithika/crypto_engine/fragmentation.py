"""
fragmentation.py

Implements XOR-based key fragmentation.

Fdb = Km XOR Fid XOR Ftime

Km = Fdb XOR Fid XOR Ftime
"""

from crypto_engine.crypto import generate_master_key, xor_three
from crypto_engine.identity import generate_identity_fragment
from crypto_engine.temporal import generate_temporal_fragment

import os


def generate_database_fragment(
        km: bytes,
        fid: bytes,
        ftime: bytes):
    """
    Computes:

    Fdb = Km XOR Fid XOR Ftime
    """

    return xor_three(
        km,
        fid,
        ftime
    )


def reconstruct_master_key(
        fdb: bytes,
        fid: bytes,
        ftime: bytes):
    """
    Computes:

    Km = Fdb XOR Fid XOR Ftime
    """

    return xor_three(
        fdb,
        fid,
        ftime
    )


if __name__ == "__main__":

    # --------------------------
    # Generate components
    # --------------------------

    km = generate_master_key()

    salt, fid = generate_identity_fragment(
        "Sanjay@123"
    )

    kseed = os.urandom(32)

    ftime = generate_temporal_fragment(
        kseed
    )

    # --------------------------
    # Fragmentation
    # --------------------------

    fdb = generate_database_fragment(
        km,
        fid,
        ftime
    )

    # --------------------------
    # Reconstruction
    # --------------------------

    reconstructed = reconstruct_master_key(
        fdb,
        fid,
        ftime
    )

    print("Original Km :")

    print(km.hex())

    print("\nDatabase Fragment (Fdb):")

    print(fdb.hex())

    print("\nReconstructed Km:")

    print(reconstructed.hex())

    print("\nMatch:")

    print(km == reconstructed)