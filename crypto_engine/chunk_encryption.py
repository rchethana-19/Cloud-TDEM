"""
TDEM Week 3
Per-Chunk Key Derivation and AES-256-GCM Encryption
"""

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ============================================================
# CHUNK KEY DERIVATION
# ============================================================

def derive_chunk_key(master_key, chunk_index):
    """
    Derive a unique 256-bit key for a specific chunk.

    Master Key + Chunk Index
              ↓
             HKDF
              ↓
        Chunk-specific key
    """

    info = (
        b"TDEM-WEEK3-CHUNK-KEY-"
        + str(chunk_index).encode()
    )

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info
    )

    return hkdf.derive(master_key)


# ============================================================
# ENCRYPT CHUNK
# ============================================================

def encrypt_chunk(chunk, master_key, chunk_index):
    """
    Encrypt one chunk using its derived key.

    Returns:
        dictionary containing:
        ciphertext
        nonce
        chunk_index
    """

    chunk_key = derive_chunk_key(
        master_key,
        chunk_index
    )

    nonce = os.urandom(12)

    aes = AESGCM(chunk_key)

    encrypted = aes.encrypt(
        nonce,
        chunk,
        None
    )

    # AES-GCM contains the authentication tag
    # in the final 16 bytes.
    ciphertext = encrypted[:-16]
    auth_tag = encrypted[-16:]

    return {
        "chunk_index": chunk_index,
        "ciphertext": ciphertext,
        "nonce": nonce,
        "auth_tag": auth_tag
    }


# ============================================================
# DECRYPT CHUNK
# ============================================================

def decrypt_chunk(
    ciphertext,
    nonce,
    auth_tag,
    master_key,
    chunk_index
):
    """
    Decrypt one chunk using its derived key.
    """

    chunk_key = derive_chunk_key(
        master_key,
        chunk_index
    )

    aes = AESGCM(chunk_key)

    encrypted = ciphertext + auth_tag

    return aes.decrypt(
        nonce,
        encrypted,
        None
    )