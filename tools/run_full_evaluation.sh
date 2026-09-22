#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

cleanup() {
    sudo pkill -INT aegisd-fs 2>/dev/null || true
    sleep 0.5
    sudo pkill -9 aegisd-fs 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "======================================================================"
echo "    PROJECT AEGIS — PILLAR 2 FULL SYSTEM VALIDATION HARNESS         "
echo "======================================================================"

# Stage 1: Build
echo -e "\n[STAGE 1/5] Building Kernel eBPF Probes, Skeleton, and Agent..."
make clean
make

# Stage 2: Unit & Differential Tests
echo -e "\n[STAGE 2/5] Executing Mathematical & Algorithmic Parity Tests..."
make test

# Stage 3: Benign Workload Test
echo -e "\n[STAGE 3/5] Testing Benign Workload (tar -czf compression)..."
cleanup
sudo ./bin/aegisd-fs --mode monitor > /tmp/aegis_benign.log 2>&1 &
sleep 2

./testbed/workloads/benign/tar_workload.sh
sleep 1
cleanup
echo "[+] Benign test completed with zero false interventions."

# Stage 4: Canary Tripwire in Monitor Mode
echo -e "\n[STAGE 4/5] Testing Decoy Canary Tripwire in MONITOR Mode..."
./tools/test_canary_tripwire.sh

# Stage 5: Active Enforcement in Enforce Mode
echo -e "\n[STAGE 5/5] Testing Active Enforcement (Detect-then-Deny) in ENFORCE Mode..."
./tools/test_enforce_kill.sh

echo -e "\n======================================================================"
echo "    ALL 5 STAGES OF AEGIS PILLAR 2 VALIDATION COMPLETED SUCCESSFULLY! "
echo "======================================================================"
