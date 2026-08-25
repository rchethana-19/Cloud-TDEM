
import os
import time
import math
import random

KEY_LEN = 32
INTERVAL = 1          # seconds
TOTAL_TIME = 30       # seconds
LAMBDA = 0.10         # decay rate

GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
RESET="\033[0m"

orig = os.urandom(KEY_LEN)

def fmt(b):
    return " ".join(f"{x:02X}" for x in b)

print("="*70)
print("      DIGITAL MEMORY DECAY (Concept Visualization)")
print("="*70)
print("\nNOTE:")
print("This is ONLY a visualization of the idea.")
print("Your real TDEM reconstructs correctly until expiry, then fails.")
print("="*70)

for t in range(TOTAL_TIME+1):
    recover = math.exp(-LAMBDA*t)
    corrupted = min(KEY_LEN, int((1-recover)*KEY_LEN))

    idx = list(range(KEY_LEN))
    random.seed(42)           # deterministic corruption order
    random.shuffle(idx)

    recon = bytearray(orig)
    for i in idx[:corrupted]:
        recon[i] = random.randint(0,255)

    if recover > 0.7:
        color=GREEN
        status="HEALTHY"
    elif recover > 0.3:
        color=YELLOW
        status="DECAYING"
    else:
        color=RED
        status="FAILED"

    print("\n"+"-"*70)
    print(f"Time Elapsed        : {t:2d} sec")
    print(f"Recoverability      : {recover*100:6.2f}%")
    print(f"Entropy Score       : {recover:.4f}")
    print(f"Corrupted Bytes     : {corrupted}/{KEY_LEN}")
    print(f"Status              : {color}{status}{RESET}")

    print("\nOriginal Key")
    print(fmt(orig))

    print("\nReconstructed Key")
    print(fmt(recon))

    if corrupted == KEY_LEN:
        print(f"\n{RED}>>> Key reconstruction impossible.")
        print(">>> AES Decryption FAILED.{RESET}")
        break

    time.sleep(INTERVAL)

print("\nSimulation Complete.")
