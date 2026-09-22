#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

CANARY_DIR="/tmp/aegis_canaries"
LOG_FILE="/tmp/aegis_run.log"

cleanup() {
    echo "[*] Cleaning up Aegis daemon..."
    sudo pkill -INT aegisd-fs 2>/dev/null || true
    sleep 0.5
    sudo pkill -9 aegisd-fs 2>/dev/null || true
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

echo "[*] Launching Aegis Daemon in MONITOR mode..."
sudo ./bin/aegisd-fs --mode monitor > "$LOG_FILE" 2>&1 &
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

CANARY_FILE="$CANARY_DIR/!00_SystemConfig.docx"
if [ ! -f "$CANARY_FILE" ]; then
    echo "[-] ERROR: Canary file $CANARY_FILE was not created by daemon!"
    cat "$LOG_FILE" 2>/dev/null || true
    exit 1
fi

echo "[*] Tampering with Canary File: $CANARY_FILE..."
echo "MALICIOUS CANARY OVERWRITE ATTEMPT" >> "$CANARY_FILE"

# Wait briefly for ringbuffer event processing
sleep 1

echo "=== Telemetry Log Captured ==="
cat "$LOG_FILE"

# Verification assertion
if grep -q "CANARY_HIT" "$LOG_FILE"; then
    echo "[+] SUCCESS: Decoy canary breach successfully detected by in-kernel hook!"
else
    echo "[-] FAILED: CANARY_HIT event was not detected in telemetry log!"
    exit 1
fi
