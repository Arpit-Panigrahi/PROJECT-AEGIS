#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "======================================================================"
echo "   PROJECT AEGIS — LAUNCHING OPERATIONS DASHBOARD"
echo "======================================================================"
echo "[*] Dashboard server listening at: http://localhost:8080"
python3 dashboard/server.py 8080
