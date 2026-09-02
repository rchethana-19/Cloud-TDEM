"""
TDEM Week 3
File-Level Cryptographic Service

Exposes:

encrypt_file()
decrypt_file()
expire_file()
verify_integrity()
get_crypto_metrics()
"""

import os

from crypto_engine.chunking import split_file
from crypto_engine.chunk_encryption import encrypt_chunk, decrypt_chunk, derive_chunk_key
from crypto_engine.integrity import calculate_hash
from crypto_engine.expiry import expire_file as apply_expiry
from crypto_engine.metrics import start_metrics, stop_metrics


# ============================================================
# ENCRYPT FILE
# ============================================================

def encrypt_file(
    file_path,
    master_key,
    temporal_fragment
):
    """
    Encrypt a complete file chunk-by-chunk.

    Each chunk receives a separate key derived using HKDF.
    """

    total_start = start_metrics()

    # --------------------------------------------------------
    # Read and split file
    # --------------------------------------------------------

    chunks = split_file(file_path)

    # --------------------------------------------------------
    # Calculate plaintext integrity hash
    # --------------------------------------------------------

    with open(file_path, "rb") as file:

        plaintext = file.read()

    plaintext_hash = calculate_hash(
        plaintext
    )

    encrypted_chunks = []

    chunk_times = []

    # --------------------------------------------------------
    # Encrypt each chunk
    # --------------------------------------------------------

    for index, chunk in enumerate(chunks):

        chunk_start = start_metrics()

        encrypted = encrypt_chunk(
            chunk,
            master_key,
            index
        )

        chunk_result = stop_metrics(
            chunk_start
        )

        chunk_times.append(
            chunk_result["time_seconds"]
        )

        encrypted_chunks.append(
            encrypted
        )

    # --------------------------------------------------------
    # Store chunk key metadata
    #
    # We store indexes rather than exposing actual keys.
    # --------------------------------------------------------

    chunk_keys = [
        index
        for index in range(
            len(encrypted_chunks)
        )
    ]

    total_metrics = stop_metrics(
        total_start
    )

    return {

        "chunks": encrypted_chunks,

        "temporal_fragment": temporal_fragment,

        "chunk_keys": chunk_keys,

        "plaintext_hash": plaintext_hash,

        "metrics": {
            "encryption_time": (
                total_metrics["time_seconds"]
            ),

            "chunk_processing_time": (
                sum(chunk_times)
            ),

            "memory_usage": (
                total_metrics[
                    "memory_peak_bytes"
                ]
            )
        },

        "expired": False
    }


# ============================================================
# DECRYPT FILE
# ============================================================

def decrypt_file(
    encrypted_data,
    master_key
):
    """
    Decrypt all chunks and reconstruct the original file.
    """

    if encrypted_data.get("expired"):

        raise ValueError(
            "File has expired. "
            "Cryptographic material deleted."
        )

    if (
        encrypted_data.get("temporal_fragment")
        is None
    ):

        raise ValueError(
            "Temporal fragment is unavailable."
        )

    if (
        encrypted_data.get("chunk_keys")
        is None
    ):

        raise ValueError(
            "Chunk key metadata is unavailable."
        )

    start = start_metrics()

    decrypted_chunks = []

    for chunk in encrypted_data["chunks"]:

        plaintext_chunk = decrypt_chunk(
            chunk["ciphertext"],
            chunk["nonce"],
            chunk["auth_tag"],
            master_key,
            chunk["chunk_index"]
        )

        decrypted_chunks.append(
            plaintext_chunk
        )

    plaintext = b"".join(
        decrypted_chunks
    )

    metrics = stop_metrics(start)

    encrypted_data["metrics"][
        "decryption_time"
    ] = metrics["time_seconds"]

    encrypted_data["metrics"][
        "decryption_memory_usage"
    ] = metrics["memory_peak_bytes"]

    return plaintext


# ============================================================
# EXPIRE FILE
# ============================================================

def expire_file(encrypted_data):
    """
    Apply cryptographic expiry.
    """

    return apply_expiry(
        encrypted_data
    )


# ============================================================
# VERIFY INTEGRITY
# ============================================================

def verify_integrity(
    decrypted_data,
    expected_hash
):
    """
    Verify SHA-256 integrity of decrypted data.
    """

    actual_hash = calculate_hash(
        decrypted_data
    )

    return actual_hash == expected_hash


# ============================================================
# GET METRICS
# ============================================================

def get_crypto_metrics(encrypted_data):
    """
    Return collected cryptographic performance metrics.
    """

    return encrypted_data.get(
        "metrics",
        {}
    )