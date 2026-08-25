"""
TDEM Week 3
SHA-256 Integrity Verification
"""

import hashlib


def calculate_hash(data):
    """
    Calculate SHA-256 hash of data.
    """

    return hashlib.sha256(data).hexdigest()


def verify_integrity(data, expected_hash):
    """
    Verify SHA-256 integrity.
    """

    actual_hash = calculate_hash(data)

    return actual_hash == expected_hash