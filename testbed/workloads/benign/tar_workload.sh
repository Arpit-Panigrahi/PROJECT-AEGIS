#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CORPUS_DIR="${1:-$SCRIPT_DIR/testbed/corpus_root}"
DEST_TAR="/tmp/aegis_benign_backup.tar.gz"

# Auto-generate synthetic corpus if missing or empty
if [ ! -d "$CORPUS_DIR" ] || [ -z "$(ls -A "$CORPUS_DIR" 2>/dev/null)" ]; then
    echo "[*] Synthetic corpus not found at $CORPUS_DIR. Generating..."
    python3 "$SCRIPT_DIR/testbed/corpus_gen/build_corpus.py"
fi

echo "[*] Running Benign Compression Workload (tar -czf on $CORPUS_DIR)..."
tar -czf "$DEST_TAR" -C "$CORPUS_DIR" .
rm -f "$DEST_TAR"
echo "[+] Benign compression workload completed successfully without interruption."
