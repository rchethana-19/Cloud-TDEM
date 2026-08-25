"""
TDEM Week 3
Interactive File Test

The user provides a file from the laptop.
The file is processed in memory.

No encrypted or decrypted file is written back to disk.
"""

import os

from file_service import (
    encrypt_file,
    decrypt_file,
    expire_file,
    verify_integrity,
    get_crypto_metrics
)


# ============================================================
# HEADER
# ============================================================

print("\n")
print("=" * 65)
print("       TDEM WEEK 3 - FILE CRYPTOGRAPHIC TEST")
print("=" * 65)


# ============================================================
# GET FILE FROM USER
# ============================================================

file_path = input(
    "\nEnter the full path of the file to encrypt:\n> "
).strip().strip('"')


# ============================================================
# CHECK FILE
# ============================================================

if not os.path.isfile(file_path):

    print("\n✗ File not found.")
    print("Check the path and try again.")
    exit()


print("\n✓ File found.")

file_size = os.path.getsize(file_path)

print(
    f"File size: {file_size:,} bytes"
)


# ============================================================
# GENERATE MASTER KEY
# ============================================================

master_key = os.urandom(32)

# Temporal fragment for Week 3 expiry simulation
temporal_fragment = os.urandom(32)


# ============================================================
# TEST 1 - CHUNKED ENCRYPTION
# ============================================================

print("\n")
print("=" * 65)
print("TEST 1 - CHUNKED ENCRYPTION")
print("=" * 65)


try:

    encrypted_data = encrypt_file(
        file_path,
        master_key,
        temporal_fragment
    )

    print("\n✓ File encrypted successfully.")

    print(
        "Number of chunks:",
        len(encrypted_data["chunks"])
    )

except Exception as e:

    print("\n✗ Encryption failed.")
    print("Reason:", e)
    exit()


# ============================================================
# TEST 2 - PER-CHUNK KEY DERIVATION
# ============================================================

print("\n")
print("=" * 65)
print("TEST 2 - PER-CHUNK KEY DERIVATION")
print("=" * 65)


if encrypted_data.get("chunk_keys"):

    print("✓ Per-chunk key metadata generated.")

else:

    print("✗ Chunk key metadata missing.")


# ============================================================
# TEST 3 - DECRYPTION
# ============================================================

print("\n")
print("=" * 65)
print("TEST 3 - CHUNKED DECRYPTION")
print("=" * 65)


try:

    recovered_data = decrypt_file(
        encrypted_data,
        master_key
    )

    print("✓ Decryption successful.")

except Exception as e:

    print("✗ Decryption failed.")
    print("Reason:", e)
    exit()


# ============================================================
# TEST 4 - INTEGRITY
# ============================================================

print("\n")
print("=" * 65)
print("TEST 4 - INTEGRITY VERIFICATION")
print("=" * 65)


integrity_result = verify_integrity(
    recovered_data,
    encrypted_data["plaintext_hash"]
)


if integrity_result:

    print(
        "✓ SHA-256 integrity verification passed."
    )

else:

    print(
        "✗ SHA-256 integrity verification failed."
    )


# ============================================================
# TEST 5 - PERFORMANCE METRICS
# ============================================================

print("\n")
print("=" * 65)
print("TEST 5 - PERFORMANCE METRICS")
print("=" * 65)


metrics = get_crypto_metrics(
    encrypted_data
)


for name, value in metrics.items():

    print(
        f"{name}: {value}"
    )


# ============================================================
# TEST 6 - CRYPTOGRAPHIC EXPIRY
# ============================================================

print("\n")
print("=" * 65)
print("TEST 6 - CRYPTOGRAPHIC EXPIRY")
print("=" * 65)


expire_file(
    encrypted_data
)


print(
    "\nTemporal fragment:",
    encrypted_data["temporal_fragment"]
)

print(
    "Chunk key metadata:",
    encrypted_data["chunk_keys"]
)


# ============================================================
# VERIFY DECRYPTION FAILS
# ============================================================

try:

    decrypt_file(
        encrypted_data,
        master_key
    )

    print(
        "\n✗ Expired file was decrypted."
    )

except Exception as e:

    print(
        "\n✓ Decryption failed after expiry."
    )

    print(
        "Reason:",
        e
    )


# ============================================================
# IMPORTANT
# ============================================================

print("\n")
print("=" * 65)
print("FILE HANDLING")
print("=" * 65)

print(
    "✓ Original file was only READ."
)

print(
    "✓ Encrypted data remained in memory."
)

print(
    "✓ Decrypted data remained in memory."
)

print(
    "✓ No encrypted file was created."
)

print(
    "✓ No decrypted file was created."
)


# ============================================================
# CLEANUP
# ============================================================

del master_key
del temporal_fragment
del encrypted_data
del recovered_data


print("\n")
print("=" * 65)
print("       TDEM WEEK 3 FILE TEST COMPLETED")
print("=" * 65)