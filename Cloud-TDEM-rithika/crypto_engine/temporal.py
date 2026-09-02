"""
temporal.py

Generates the Temporal Fragment.

Ftime = HMAC(Kseed, CurrentTimeWindow)
"""

import time
import hmac
import hashlib


DEFAULT_WINDOW = 300      # 5 minutes


def current_time_window(window=DEFAULT_WINDOW):

    unix_time = int(time.time())

    return unix_time // window

# import hmac
# import hashlib


def generate_temporal_fragment(kseed, time_window):

    message = str(time_window).encode()

    return hmac.new(
        kseed,
        message,
        hashlib.sha256
    ).digest()


if __name__ == "__main__":

    seed = b"MySecretSeed"

    fragment = generate_temporal_fragment(seed)

    print("Current Window :", current_time_window())

    print("Ftime :", fragment.hex())