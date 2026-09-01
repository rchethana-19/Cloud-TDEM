"""
TDEM Week 3
Cryptographic Expiry Simulation
"""


def expire_file(file_data):
    """
    Simulate cryptographic expiry.

    Deletes:
    1. Temporal fragment
    2. Chunk key metadata
    """

    # Delete temporal fragment
    file_data["temporal_fragment"] = None

    # Delete chunk key metadata
    file_data["chunk_keys"] = None

    file_data["expired"] = True

    return file_data


def is_expired(file_data):
    """
    Check whether cryptographic material has expired.
    """

    return file_data.get("expired", False)