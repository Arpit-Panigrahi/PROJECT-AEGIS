#!/usr/bin/env bash
set -e

cd /mnt/c/Users/arpit/Desktop/aegis

# Clean up any stale instances
sudo pkill -9 aegisd-fs 2>/dev/null || true
sleep 1

echo "[*] Launching Aegis Daemon in ENFORCE mode..."
sudo ./bin/aegisd-fs --mode enforce > /tmp/aegis_enforce.log 2>&1 &

sleep 2

echo "[*] Launching simulated encryptor attack script..."
cat << 'EOF' > /tmp/victim_attack.sh
#!/usr/bin/env bash
echo "[ATTACK] Attack process PID: $$ started..."
# 1. Touch first canary (+40 risk)
echo "ENCRYPT_HEADER" >> "/tmp/aegis_canaries/!00_SystemConfig.docx"
sleep 0.1
# 2. Touch second canary (+40 risk -> Risk reaches 80.0, Tier 3 Quarantine!)
echo "ENCRYPT_HEADER" >> "/tmp/aegis_canaries/00_TaxReturn_2026.pdf"
sleep 0.1
# 3. Attempt further writes
for i in {1..20}; do
    echo "This should be blocked" >> "/tmp/test_lost_$i.bin"
    sleep 0.05
done
echo "[ATTACK] Failed to be stopped! This line should NOT be reached."
EOF

chmod +x /tmp/victim_attack.sh

# Run victim and capture its exit status
set +e
/tmp/victim_attack.sh
EXIT_CODE=$?
set -e

echo "[*] Victim attack process terminated with exit code: $EXIT_CODE (137 = SIGKILL)"

sleep 1
sudo pkill -INT aegisd-fs || true
sleep 1

echo "=== Telemetry Log Captured ==="
cat /tmp/aegis_enforce.log
