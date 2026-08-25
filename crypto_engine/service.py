"""
TDEM Week 2 - Cryptographic Service

Provides:

1. encrypt_data()
2. retrieve_data()
3. refresh_key()
4. generate_identity_fragment()
5. generate_temporal_fragment()

Workflow:

Identity
   ↓
Fid

Current Time Window
   ↓
Ftime

Random Master Key
   ↓
Km

Fdb = Km XOR Fid XOR Ftime

AES-256-GCM
   ↓
Encrypted Data
"""


import os
import time
import hmac
import hashlib

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ============================================================
# CONFIGURATION
# ============================================================

# 5 seconds is used for testing.
#
# For the actual project you can later change this to:
#
# 300  -> 5 minutes
# 600  -> 10 minutes
# 3600 -> 1 hour
#
TIME_WINDOW = 5


# ============================================================
# HELPER: GET CURRENT TIME WINDOW
# ============================================================

def get_current_time_window():
    """
    Converts the current Unix timestamp into a discrete
    temporal window.

    Example with TIME_WINDOW = 5:

        0-4 sec   -> window 0
        5-9 sec   -> window 1
        10-14 sec -> window 2

    Returns:
        int: Current time-window number
    """

    return int(time.time()) // TIME_WINDOW


# ============================================================
# 1. IDENTITY FRAGMENT
# ============================================================

def generate_identity_fragment(identity, salt):
    """
    Generates the 256-bit Identity Fragment (Fid).

    PBKDF2-HMAC-SHA256 is used to derive a 32-byte value.

    Same identity + same salt
    -------------------------
    produces
    -------------------------
    same Fid

    Args:
        identity: User identity/password/token
        salt: Random 16-byte salt

    Returns:
        bytes: 32-byte Identity Fragment
    """

    if isinstance(identity, str):
        identity = identity.encode("utf-8")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000
    )

    return kdf.derive(identity)


# ============================================================
# 2. TEMPORAL FRAGMENT
# ============================================================

def generate_temporal_fragment(kseed, time_window=None):
    """
    Generates Ftime using HMAC-SHA256.

    Ftime = HMAC-SHA256(Kseed, CurrentTimeWindow)

    Args:
        kseed: 32-byte secret seed
        time_window: Optional explicit time window

    Returns:
        bytes: 32-byte Temporal Fragment
    """

    if time_window is None:
        time_window = get_current_time_window()

    message = str(time_window).encode("utf-8")

    return hmac.new(
        kseed,
        message,
        hashlib.sha256
    ).digest()


# ============================================================
# 3. XOR HELPER
# ============================================================

def xor_bytes(a, b, c=None):
    """
    Performs XOR between byte strings.

    If only a and b are provided:

        a XOR b

    If a, b and c are provided:

        a XOR b XOR c
    """

    if len(a) != len(b):
        raise ValueError("Byte strings must have the same length.")

    result = bytes(
        x ^ y
        for x, y in zip(a, b)
    )

    if c is not None:

        if len(result) != len(c):
            raise ValueError("Byte strings must have the same length.")

        result = bytes(
            x ^ y
            for x, y in zip(result, c)
        )

    return result


# ============================================================
# 4. ENCRYPTION WORKFLOW
# ============================================================

def encrypt_data(identity, plaintext, kseed):
    """
    Complete TDEM encryption workflow.

    Steps:

    1. Generate random salt.
    2. Generate Fid.
    3. Generate current Ftime.
    4. Generate random 256-bit Master Key.
    5. Generate Fdb.
    6. Encrypt plaintext using AES-256-GCM.
    7. Return encrypted package.

    Args:
        identity: User identity
        plaintext: Data to encrypt
        kseed: Secret temporal seed

    Returns:
        dict containing all information required for retrieval.
    """

    # --------------------------------------------------------
    # Validate plaintext
    # --------------------------------------------------------

    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")

    # --------------------------------------------------------
    # Generate random salt
    # --------------------------------------------------------

    salt = os.urandom(16)

    # --------------------------------------------------------
    # Generate Identity Fragment
    # --------------------------------------------------------

    fid = generate_identity_fragment(
        identity,
        salt
    )

    # --------------------------------------------------------
    # Get current time window
    # --------------------------------------------------------

    encryption_window = get_current_time_window()

    # --------------------------------------------------------
    # Generate Temporal Fragment
    # --------------------------------------------------------

    ftime = generate_temporal_fragment(
        kseed,
        encryption_window
    )

    # --------------------------------------------------------
    # Generate random 256-bit Master Key
    # --------------------------------------------------------

    km = os.urandom(32)

    # --------------------------------------------------------
    # Generate Database Fragment
    #
    # Fdb = Km XOR Fid XOR Ftime
    # --------------------------------------------------------

    fdb = xor_bytes(
        km,
        fid,
        ftime
    )

    # --------------------------------------------------------
    # AES-256-GCM encryption
    # --------------------------------------------------------

    nonce = os.urandom(12)

    aes = AESGCM(km)

    encrypted = aes.encrypt(
        nonce,
        plaintext,
        None
    )

    # AESGCM returns:
    #
    # ciphertext + authentication tag
    #
    # GCM tag is the last 16 bytes.

    ciphertext = encrypted[:-16]
    auth_tag = encrypted[-16:]

    # --------------------------------------------------------
    # Remove reference to Master Key
    #
    # Python cannot guarantee true memory zeroization.
    # This removes our reference to the key.
    # --------------------------------------------------------

    del km

    # --------------------------------------------------------
    # Return package
    # --------------------------------------------------------

    return {
        "ciphertext": ciphertext,
        "nonce": nonce,
        "auth_tag": auth_tag,
        "salt": salt,
        "database_fragment": fdb,
        "encryption_window": encryption_window
    }


# ============================================================
# 5. RETRIEVAL WORKFLOW
# ============================================================

def retrieve_data(identity, encrypted_data, kseed):
    """
    Complete TDEM retrieval workflow.

    Steps:

    1. Check temporal window.
    2. Regenerate Fid.
    3. Regenerate Ftime.
    4. Reconstruct Km.
    5. Decrypt using AES-256-GCM.

    Raises:
        ValueError if temporal window has expired.
        Exception if authentication/decryption fails.

    Returns:
        bytes: Original plaintext
    """

    # --------------------------------------------------------
    # Read stored encryption window
    # --------------------------------------------------------

    stored_window = encrypted_data["encryption_window"]

    # --------------------------------------------------------
    # Read current time window
    # --------------------------------------------------------

    current_window = get_current_time_window()

    # --------------------------------------------------------
    # TIME VALIDATION
    #
    # If current window != stored window,
    # the old temporal fragment is invalid.
    # --------------------------------------------------------

    if current_window != stored_window:

        raise ValueError(
            "Temporal window expired. "
            "Key reconstruction denied."
        )

    # --------------------------------------------------------
    # Regenerate Fid
    # --------------------------------------------------------

    fid = generate_identity_fragment(
        identity,
        encrypted_data["salt"]
    )

    # --------------------------------------------------------
    # Regenerate Ftime
    # --------------------------------------------------------

    ftime = generate_temporal_fragment(
        kseed,
        current_window
    )

    # --------------------------------------------------------
    # Reconstruct Master Key
    #
    # Km = Fdb XOR Fid XOR Ftime
    # --------------------------------------------------------

    km = xor_bytes(
        encrypted_data["database_fragment"],
        fid,
        ftime
    )

    # --------------------------------------------------------
    # AES-256-GCM decryption
    # --------------------------------------------------------

    aes = AESGCM(km)

    encrypted_payload = (
        encrypted_data["ciphertext"]
        +
        encrypted_data["auth_tag"]
    )

    plaintext = aes.decrypt(
        encrypted_data["nonce"],
        encrypted_payload,
        None
    )

    # --------------------------------------------------------
    # Remove reference to Master Key
    # --------------------------------------------------------

    del km

    return plaintext


# ============================================================
# 6. REFRESH MECHANISM
# ============================================================

def refresh_key(identity, encrypted_data, kseed):
    """
    Refreshes the temporal component.

    The Master Key is NOT exposed outside this function.

    If the current temporal window is different from the
    original encryption window, a new Ftime is generated.

    The Master Key is reconstructed internally and then used
    to calculate a new Fdb.

    New:

        Fdb = Km XOR Fid XOR NewFtime

    Returns:
        Updated encrypted_data dictionary.
    """

    # --------------------------------------------------------
    # Current time window
    # --------------------------------------------------------

    current_window = get_current_time_window()

    # --------------------------------------------------------
    # If already in the same window, nothing needs updating.
    # --------------------------------------------------------

    if current_window == encrypted_data["encryption_window"]:

        return encrypted_data

    # --------------------------------------------------------
    # Regenerate Fid
    # --------------------------------------------------------

    fid = generate_identity_fragment(
        identity,
        encrypted_data["salt"]
    )

    # --------------------------------------------------------
    # Generate OLD temporal fragment
    # --------------------------------------------------------

    old_ftime = generate_temporal_fragment(
        kseed,
        encrypted_data["encryption_window"]
    )

    # --------------------------------------------------------
    # Reconstruct Master Key internally
    #
    # Km = Fdb XOR Fid XOR OldFtime
    # --------------------------------------------------------

    km = xor_bytes(
        encrypted_data["database_fragment"],
        fid,
        old_ftime
    )

    # --------------------------------------------------------
    # Generate NEW temporal fragment
    # --------------------------------------------------------

    new_ftime = generate_temporal_fragment(
        kseed,
        current_window
    )

    # --------------------------------------------------------
    # Generate NEW Database Fragment
    #
    # Fdb_new = Km XOR Fid XOR NewFtime
    # --------------------------------------------------------

    new_fdb = xor_bytes(
        km,
        fid,
        new_ftime
    )

    # --------------------------------------------------------
    # Remove Master Key reference
    # --------------------------------------------------------

    del km

    # --------------------------------------------------------
    # Update metadata
    # --------------------------------------------------------

    encrypted_data["database_fragment"] = new_fdb

    encrypted_data["encryption_window"] = current_window

    return encrypted_data