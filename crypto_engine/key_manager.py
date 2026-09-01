"""
key_manager.py

This module coordinates the complete cryptographic workflow
of the Time-Dependent Encryption Model (TDEM).

Workflow:

User Identity
      │
      ▼
Generate Identity Fragment (Fid)
      │
      ▼
Generate Temporal Fragment (Ftime)
      │
      ▼
Generate Master Key (Km)
      │
      ▼
Generate Database Fragment (Fdb)
      │
      ▼
Encrypt Plaintext
      │
      ▼
Reconstruct Master Key
      │
      ▼
Decrypt Ciphertext

Author : Sanjay
"""

import os

# ---------- Import Cryptographic Modules ----------

from crypto import generate_master_key

from identity import (
    generate_identity_fragment,
    regenerate_identity_fragment
)

from temporal import generate_temporal_fragment

from fragmentation import (
    generate_database_fragment,
    reconstruct_master_key
)

from encryption import (
    encrypt,
    decrypt
)


# ============================================================
#               KEY MANAGER CLASS
# ============================================================

class KeyManager:
    """
    Handles the complete key lifecycle.

    Responsibilities:
    -----------------
    1. Generate all cryptographic fragments.
    2. Encrypt data.
    3. Reconstruct the master key.
    4. Decrypt data.
    """

    def __init__(self):

        # Secret key used for generating the temporal fragment.
        # In production this should be securely stored.
        self.kseed = os.urandom(32)

    # ========================================================

    def encrypt_workflow(self,
                         identity: str,
                         plaintext: bytes):
        """
        Complete Encryption Workflow

        Parameters
        ----------
        identity : User password / authentication token

        plaintext : Data to encrypt

        Returns
        -------
        Dictionary containing every cryptographic component.
        """

        # ---------------------------------------------
        # Step 1
        # Generate random Master Key (Km)
        # ---------------------------------------------

        km = generate_master_key()

        # ---------------------------------------------
        # Step 2
        # Generate Identity Fragment (Fid)
        # ---------------------------------------------

        salt, fid = generate_identity_fragment(identity)

        # ---------------------------------------------
        # Step 3
        # Generate Temporal Fragment (Ftime)
        # ---------------------------------------------

        ftime = generate_temporal_fragment(self.kseed)

        # ---------------------------------------------
        # Step 4
        # Compute Database Fragment
        #
        # Fdb = Km XOR Fid XOR Ftime
        # ---------------------------------------------

        fdb = generate_database_fragment(
            km,
            fid,
            ftime
        )

        # ---------------------------------------------
        # Step 5
        # Encrypt plaintext using AES-256-GCM
        # ---------------------------------------------

        ciphertext, nonce, tag = encrypt(
            plaintext,
            km
        )

        # ---------------------------------------------
        # Step 6
        # Return every required value.
        #
        # These values would normally be stored in
        # different locations by the backend.
        # ---------------------------------------------

        return {

            "ciphertext": ciphertext,

            "nonce": nonce,

            "tag": tag,

            "salt": salt,

            "database_fragment": fdb,

            "master_key": km,      # Demo only (don't store in production)

            "kseed": self.kseed    # Demo only

        }

    # ========================================================

    def decrypt_workflow(self,
                         identity,
                         encrypted_data):
        """
        Complete Decryption Workflow.

        Steps:

        1. Regenerate Fid

        2. Generate current Ftime

        3. Reconstruct Master Key

        4. Decrypt ciphertext
        """

        # ---------------------------------------------
        # Step 1
        # Regenerate Identity Fragment
        #
        # Using same identity + salt
        # ---------------------------------------------

        fid = regenerate_identity_fragment(

            identity,

            encrypted_data["salt"]

        )

        # ---------------------------------------------
        # Step 2
        # Generate Temporal Fragment
        # ---------------------------------------------

        ftime = generate_temporal_fragment(

            encrypted_data["kseed"]

        )

        # ---------------------------------------------
        # Step 3
        # Reconstruct Master Key
        #
        # Km = Fdb XOR Fid XOR Ftime
        # ---------------------------------------------

        reconstructed_key = reconstruct_master_key(

            encrypted_data["database_fragment"],

            fid,

            ftime

        )

        # ---------------------------------------------
        # Step 4
        # AES-GCM Decryption
        # ---------------------------------------------

        plaintext = decrypt(

            encrypted_data["ciphertext"],

            encrypted_data["nonce"],

            encrypted_data["tag"],

            reconstructed_key

        )

        return plaintext


# ============================================================
#               DEMONSTRATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("Time-Dependent Encryption Model (TDEM)")
    print("=" * 60)

    manager = KeyManager()

    identity = "Sanjay@123"

    message = b"This is a confidential document."

    print("\nOriginal Message:")
    print(message.decode())

    print("\nEncrypting...\n")

    encrypted = manager.encrypt_workflow(
        identity,
        message
    )

    print("Encryption Successful")

    print("\nDatabase Fragment:")
    print(encrypted["database_fragment"].hex())

    print("\nCiphertext:")
    print(encrypted["ciphertext"].hex())

    print("\nDecrypting...\n")

    recovered = manager.decrypt_workflow(
        identity,
        encrypted
    )

    print("Recovered Plaintext:")

    print(recovered.decode())

    print("\nVerification:")

    print(message == recovered)