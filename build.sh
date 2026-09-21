#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "======================================================================"
echo "   PROJECT AEGIS — BUILDING SUBSYSTEM (NATIVE WSL)"
echo "======================================================================"
make clean && make
echo ""
echo "======================================================================"
echo "[+] BUILD SUCCESSFUL!"
echo "[+] In-kernel eBPF object: bpf/p2_fs.bpf.o"
echo "[+] Skeleton generated:   agent/p2_fs.skel.h"
echo "[+] Userspace daemon:     bin/aegisd-fs"
echo "[+] Test binaries:        bin/test_risk, bin/entropy_test_runner"
echo "======================================================================"
