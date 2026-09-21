#!/usr/bin/env bash
set -e

cd /mnt/c/Users/arpit/Desktop/aegis

# Clean up any stale instances
sudo pkill -9 aegisd-fs 2>/dev/null || true
sleep 1

echo "[*] Launching Aegis Daemon in MONITOR mode..."
sudo ./bin/aegisd-fs --mode monitor > /tmp/aegis_run.log 2>&1 &

sleep 2

echo "[*] Tampering with Canary File: /tmp/aegis_canaries/'!00_SystemConfig.docx'..."
echo "MALICIOUS CANARY OVERWRITE ATTEMPT" >> "/tmp/aegis_canaries/!00_SystemConfig.docx"

sleep 1

echo "[*] Stopping Aegis Daemon..."
sudo pkill -INT aegisd-fs || true
sleep 1

echo "=== Telemetry Log Captured ==="
cat /tmp/aegis_run.log
