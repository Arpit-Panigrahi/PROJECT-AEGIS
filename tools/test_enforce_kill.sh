#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

CANARY_DIR="/tmp/aegis_canaries"
LOG_FILE="/tmp/aegis_enforce.log"
ATTACK_SCRIPT="/tmp/victim_attack.sh"

cleanup() {
    echo "[*] Cleaning up Aegis daemon and temporary files..."
    sudo pkill -INT aegisd-fs 2>/dev/null || true
    sleep 0.5
    sudo pkill -9 aegisd-fs 2>/dev/null || true
    rm -f "$ATTACK_SCRIPT" /tmp/test_lost_*.bin
}
trap cleanup EXIT INT TERM

# Ensure binary is compiled
if [ ! -f "bin/aegisd-fs" ]; then
    echo "[*] Compiling Aegis daemon..."
    make bin/aegisd-fs
fi

# Clean up any stale instances
cleanup
rm -f "$LOG_FILE"

echo "[*] Launching Aegis Daemon in ENFORCE mode..."
sudo ./bin/aegisd-fs --mode enforce > "$LOG_FILE" 2>&1 &
AEGIS_PID=$!

# Wait for daemon to initialize and register canaries (up to 5 seconds)
READY=0
for i in {1..25}; do
    if grep -q "Ring buffer consumer listening" "$LOG_FILE" 2>/dev/null; then
        READY=1
        break
    fi
    sleep 0.2
done

if [ "$READY" -ne 1 ]; then
    echo "[-] ERROR: Aegis daemon failed to initialize within timeout!"
    cat "$LOG_FILE" 2>/dev/null || true
    exit 1
fi

echo "[*] Creating simulated encryptor attack script..."
cat << 'EOF' > "$ATTACK_SCRIPT"
#!/usr/bin/env bash
echo "[ATTACK] Attack process PID: $$ started..."
# 1. Touch first canary (+40 risk)
echo "ENCRYPT_HEADER" >> "/tmp/aegis_canaries/!00_SystemConfig.docx"
sleep 0.08
# 2. Touch second canary (+40 risk -> Risk reaches 80.0, Tier 3 Quarantine!)
echo "ENCRYPT_HEADER" >> "/tmp/aegis_canaries/00_TaxReturn_2026.pdf"
sleep 0.08
# 3. Attempt further writes (should be killed immediately)
for i in {1..20}; do
    echo "This should be blocked" >> "/tmp/test_lost_$i.bin"
    sleep 0.04
done
echo "[ATTACK] Failed to be stopped! This line should NOT be reached."
exit 0
EOF

chmod +x "$ATTACK_SCRIPT"

# Run victim and capture its exit status
set +e
"$ATTACK_SCRIPT"
EXIT_CODE=$?
set -e

echo "[*] Victim attack process terminated with exit code: $EXIT_CODE (137 = SIGKILL)"

# Wait briefly for ringbuffer to flush
sleep 1

echo "=== Telemetry Log Captured ==="
cat "$LOG_FILE"

# Comprehensive verification assertions
TEST_PASSED=1

if [ "$EXIT_CODE" -ne 137 ]; then
    echo "[-] FAILED: Expected exit code 137 (SIGKILL), but got: $EXIT_CODE"
    TEST_PASSED=0
fi

if ! grep -q "KILL_DECISION" "$LOG_FILE"; then
    echo "[-] FAILED: KILL_DECISION event was not logged by Aegis agent!"
    TEST_PASSED=0
fi

if [ "$TEST_PASSED" -eq 1 ]; then
    echo "[+] SUCCESS: In-kernel active enforcement verified! Attack stopped with SIGKILL (Exit code 137)."
    exit 0
else
    echo "[-] FAILED: Active enforcement verification failed!"
    exit 1
fi
