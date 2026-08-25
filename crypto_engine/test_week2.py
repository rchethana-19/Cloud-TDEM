"""
TDEM Week 2 Test Suite

Tests:

1. Correct identity / wrong identity
2. Temporal expiry
3. Temporal key refresh
"""

import time
import os

import service

from service import (
    encrypt_data,
    retrieve_data,
    refresh_key
)


# ============================================================
# TEST CONFIGURATION
# ============================================================

IDENTITY = "Sanjay"

WRONG_IDENTITY = "WrongUser"

PLAINTEXT = b"TDEM Week 2 Testing"

# Random 256-bit temporal seed
KSEED = os.urandom(32)


# ============================================================
# TEST 1
# CORRECT IDENTITY / WRONG IDENTITY
# ============================================================

def test_identity():

    print("\n" + "=" * 60)
    print("TEST 1 - IDENTITY VALIDATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Encrypt data
    # --------------------------------------------------------

    encrypted_data = encrypt_data(
        IDENTITY,
        PLAINTEXT,
        KSEED
    )

    print("\nEncryption successful.")

    # --------------------------------------------------------
    # Correct identity
    # --------------------------------------------------------

    try:

        recovered = retrieve_data(
            IDENTITY,
            encrypted_data,
            KSEED
        )

        if recovered == PLAINTEXT:

            print(
                "✓ Correct identity → "
                "DECRYPTION SUCCESS"
            )

        else:

            print(
                "✗ Correct identity → "
                "WRONG PLAINTEXT"
            )

    except Exception as e:

        print(
            "✗ Correct identity → FAILED"
        )

        print("Error:", e)

    # --------------------------------------------------------
    # Wrong identity
    # --------------------------------------------------------

    try:

        retrieve_data(
            WRONG_IDENTITY,
            encrypted_data,
            KSEED
        )

        # If this line is reached, something is wrong.

        print(
            "✗ Wrong identity → "
            "DECRYPTION SUCCEEDED"
        )

        print(
            "  SECURITY TEST FAILED"
        )

    except Exception:

        print(
            "✓ Wrong identity → REJECTED"
        )


# ============================================================
# TEST 2
# TEMPORAL EXPIRY
# ============================================================

def test_expiry():

    print("\n" + "=" * 60)
    print("TEST 2 - TEMPORAL EXPIRY")
    print("=" * 60)

    # --------------------------------------------------------
    # The service uses:
    #
    # TIME_WINDOW = 5
    #
    # Therefore this test also uses:
    #
    # service.TIME_WINDOW
    #
    # This prevents mismatch between the test and service.
    # --------------------------------------------------------

    print(
        f"\nConfigured time window: "
        f"{service.TIME_WINDOW} seconds"
    )

    # --------------------------------------------------------
    # Encrypt
    # --------------------------------------------------------

    encrypted_data = encrypt_data(
        IDENTITY,
        PLAINTEXT,
        KSEED
    )

    print("\nData encrypted.")

    print(
        "Original time window:",
        encrypted_data["encryption_window"]
    )

    print(
        "Waiting for temporal window to expire..."
    )

    # --------------------------------------------------------
    # Wait until the actual service time window changes.
    # --------------------------------------------------------

    while True:

        current_window = (
            int(time.time())
            // service.TIME_WINDOW
        )

        if (
            current_window
            != encrypted_data["encryption_window"]
        ):

            break

        time.sleep(0.25)

    print("Temporal window changed.")

    print(
        "New time window:",
        current_window
    )

    # --------------------------------------------------------
    # Attempt retrieval
    # --------------------------------------------------------

    try:

        retrieve_data(
            IDENTITY,
            encrypted_data,
            KSEED
        )

        print(
            "✗ EXPIRED DATA WAS DECRYPTED"
        )

        print(
            "  TEMPORAL SECURITY TEST FAILED"
        )

    except ValueError as e:

        print(
            "✓ Temporal expiry → "
            "RECONSTRUCTION REJECTED"
        )

        print(
            "  Reason:",
            e
        )

    except Exception as e:

        print(
            "✓ Retrieval failed after expiry"
        )

        print(
            "  Reason:",
            e
        )


# ============================================================
# TEST 3
# TEMPORAL KEY REFRESH
# ============================================================

def test_refresh():

    print("\n" + "=" * 60)
    print("TEST 3 - TEMPORAL KEY REFRESH")
    print("=" * 60)

    # --------------------------------------------------------
    # Encrypt
    # --------------------------------------------------------

    encrypted_data = encrypt_data(
        IDENTITY,
        PLAINTEXT,
        KSEED
    )

    old_fdb = encrypted_data[
        "database_fragment"
    ]

    old_window = encrypted_data[
        "encryption_window"
    ]

    print("\nOriginal encryption successful.")

    print(
        "Original time window:",
        old_window
    )

    # --------------------------------------------------------
    # Retrieve before refresh
    # --------------------------------------------------------

    try:

        recovered = retrieve_data(
            IDENTITY,
            encrypted_data,
            KSEED
        )

        if recovered == PLAINTEXT:

            print(
                "✓ Before refresh → "
                "DECRYPTION SUCCESS"
            )

        else:

            print(
                "✗ Before refresh → "
                "WRONG PLAINTEXT"
            )

    except Exception as e:

        print(
            "✗ Before refresh → FAILED"
        )

        print("Error:", e)

    # --------------------------------------------------------
    # Wait until a NEW temporal window begins.
    #
    # This is important because if refresh happens in the
    # same window, Ftime does not change.
    # --------------------------------------------------------

    print(
        "\nWaiting for next temporal window..."
    )

    while True:

        current_window = (
            int(time.time())
            // service.TIME_WINDOW
        )

        if current_window != old_window:

            break

        time.sleep(0.25)

    print(
        "New temporal window:",
        current_window
    )

    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------

    print(
        "\nRefreshing temporal fragment..."
    )

    try:

        encrypted_data = refresh_key(
            IDENTITY,
            encrypted_data,
            KSEED
        )

        print(
            "✓ Refresh completed."
        )

    except Exception as e:

        print(
            "✗ Refresh failed."
        )

        print(
            "Error:",
            e
        )

        return

    # --------------------------------------------------------
    # Check Fdb
    # --------------------------------------------------------

    new_fdb = encrypted_data[
        "database_fragment"
    ]

    if old_fdb != new_fdb:

        print(
            "✓ Database Fragment updated"
        )

    else:

        print(
            "✗ Database Fragment did not change"
        )

        print(
            "  REFRESH TEST FAILED"
        )

    # --------------------------------------------------------
    # Check time window
    # --------------------------------------------------------

    if (
        encrypted_data["encryption_window"]
        != old_window
    ):

        print(
            "✓ Encryption window updated"
        )

    else:

        print(
            "✗ Encryption window "
            "was not updated"
        )

    # --------------------------------------------------------
    # Retrieve after refresh
    # --------------------------------------------------------

    try:

        recovered = retrieve_data(
            IDENTITY,
            encrypted_data,
            KSEED
        )

        if recovered == PLAINTEXT:

            print(
                "✓ After refresh → "
                "DECRYPTION SUCCESS"
            )

        else:

            print(
                "✗ After refresh → "
                "WRONG PLAINTEXT"
            )

    except Exception as e:

        print(
            "✗ After refresh → FAILED"
        )

        print(
            "Error:",
            e
        )


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":

    print("\n")

    print("=" * 60)

    print(
        "       TDEM WEEK 2 TEST SUITE"
    )

    print("=" * 60)

    # Test 1
    test_identity()

    # Test 2
    test_expiry()

    # Test 3
    test_refresh()

    print("\n")

    print("=" * 60)

    print(
        "       WEEK 2 TESTS COMPLETED"
    )

    print("=" * 60)