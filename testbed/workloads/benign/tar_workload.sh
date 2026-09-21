#!/usr/bin/env bash
set -eo pipefail

CORPUS_DIR="${1:-./testbed/corpus_root}"
DEST_TAR="/tmp/aegis_benign_backup.tar.gz"

echo "[*] Running Benign Compression Workload (tar -czf on $CORPUS_DIR)..."
tar -czf "$DEST_TAR" -C "$CORPUS_DIR" .
rm -f "$DEST_TAR"
echo "[+] Benign compression workload completed successfully without interruption."
