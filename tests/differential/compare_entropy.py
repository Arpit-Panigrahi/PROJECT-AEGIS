#!/usr/bin/env python3
import os
import random
import subprocess
import sys
from entropy_ref import miller_madow

def main():
    print("[*] Running Differential Entropy Parity Tests (Python float vs C Q16.16)...")
    runner_path = "./tests/unit/entropy_test_runner"
    if not os.path.exists(runner_path):
        runner_path = "./bin/entropy_test_runner"

    if not os.path.exists(runner_path):
        print(f"[-] Error: {runner_path} not found. Please compile it first.")
        sys.exit(1)

    sample_sizes = [512, 1024, 2048, 4096]
    max_divergence = 0.0
    total_tests = 0

    for n in sample_sizes:
        for trial in range(50):
            # Test different entropy profiles
            profile = trial % 5
            if profile == 0:
                payload = os.urandom(n) # Ciphertext / Random
            elif profile == 1:
                payload = bytes([random.choice([0x00, 0x20, 0x41, 0x61]) for _ in range(n)]) # Low entropy
            elif profile == 2:
                payload = ("Project Aegis Kernel Security Invariant " * (n // 38 + 1)).encode()[:n] # Plain ASCII text
            elif profile == 3:
                payload = bytes([trial & 0xFF] * n) # Constant (H = 0)
            else:
                payload = bytes([i % 256 for i in range(n)]) # Uniform ramp

            py_val = miller_madow(payload)

            proc = subprocess.run(
                [runner_path, str(n)],
                input=payload,
                capture_output=True,
                check=True
            )
            c_raw = int(proc.stdout.strip())
            c_val = c_raw / 65536.0

            diff = abs(py_val - c_val)
            if diff > max_divergence:
                max_divergence = diff

            # Bound tolerance to 0.02 bits
            if diff > 0.02:
                print(f"[-] Divergence exceeded! n={n}, Py={py_val:.4f}, C={c_val:.4f}, Diff={diff:.4f}")
                sys.exit(1)

            total_tests += 1

    print(f"[+] All {total_tests} differential tests PASSED!")
    print(f"[+] Maximum fixed-point divergence: {max_divergence:.5f} bits (Tolerance limit: 0.02000 bits)")

if __name__ == "__main__":
    main()
