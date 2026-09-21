#!/usr/bin/env bash
set -eo pipefail

CORPUS_DIR="${1:-./testbed/corpus_root}"
PASS="AegisSafeBenchmarkKey2026"

echo "[*] Starting Safe Encryptor Simulation on $CORPUS_DIR (PID: $$)..."
MODIFIED=0
START_NS=$(date +%s%N)

find "$CORPUS_DIR" -type f ! -name "*.locked" | shuf | while read -r f; do
    # 1. Encrypt in-place to .locked using OpenSSL AES-256-CBC
    if ! openssl enc -aes-256-cbc -salt -pbkdf2 -pass "pass:$PASS" -in "$f" -out "${f}.locked" 2>/dev/null; then
        echo -e "\n\033[1;31m[-] ENCRYPTION BLOCKED! Write denied by kernel LSM (-EPERM) on ${f}.locked\033[0m"
        break
    fi

    # 2. Delete original
    rm -f "$f"
    MODIFIED=$((MODIFIED + 1))

    if [ $((MODIFIED % 10)) -eq 0 ]; then
        echo -n "."
    fi
done

END_NS=$(date +%s%N)
ELAPSED_MS=$(( (END_NS - START_NS) / 1000000 ))
echo -e "\n[+] Encryptor run completed or halted. Files modified: $MODIFIED in ${ELAPSED_MS}ms."
