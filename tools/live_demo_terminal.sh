#!/usr/bin/env bash
# Project Aegis — Live Interactive Backend Monitor & Real-Time Demo
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

clear
echo -e "\033[1;36m======================================================================\033[0m"
echo -e "\033[1;32m    PROJECT AEGIS — REAL-TIME KERNEL BACKEND & DEMO MONITOR         \033[0m"
echo -e "\033[1;36m======================================================================\033[0m"
echo -e "\033[0;37mKernel: $(uname -r) | Arch: $(uname -m) | Architecture: eBPF CO-RE LSM\033[0m\n"

# Step 1: Run the full 5-stage automated harness to prove everything is passing
echo -e "\033[1;33m[*] STEP 1: Running Full 5-Stage Verification & Parity Harness...\033[0m"
sudo ./tools/run_full_evaluation.sh

echo -e "\n\033[1;32m======================================================================\033[0m"
echo -e "\033[1;32m[+] HARNESS COMPLETE: All 5 stages passed! Launching Live Daemon...  \033[0m"
echo -e "\033[1;32m======================================================================\033[0m"
echo -e "\033[1;37mThe Aegis Daemon is now attached to Linux Kernel VFS and LSM hooks.\033[0m"
echo -e "\033[1;37mWeb Operations Dashboard: \033[1;34mhttp://localhost:8000\033[0m"
echo -e "\033[0;37mClick 'Kill Encryptor', 'Tripwire Canary', or 'Entropy Write' in your browser\033[0m"
echo -e "\033[0;37mand watch this terminal intercept and neutralize the threat in real time!\033[0m"
echo -e "\033[1;30m(Press Ctrl+C to stop the daemon)\033[0m\n"

# Cleanup any stale instances
sudo pkill -INT aegisd-fs 2>/dev/null || true
sleep 0.5
sudo pkill -9 aegisd-fs 2>/dev/null || true

# Launch live daemon in ENFORCE mode directly in the terminal
exec sudo ./bin/aegisd-fs --mode enforce
