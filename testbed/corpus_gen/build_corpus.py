#!/usr/bin/env python3
import os
import random
from pathlib import Path

ROOT_DIR = Path("./testbed/corpus_root")

def generate_corpus(seed=42, total_files=2000):
    random.seed(seed)
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    
    subdirs = [
        "Documents/Finances", 
        "Documents/Projects", 
        "Desktop/Work", 
        "Downloads", 
        "Pictures/Archive"
    ]
    for s in subdirs:
        (ROOT_DIR / s).mkdir(parents=True, exist_ok=True)

    print(f"[*] Generating {total_files}-file multi-class synthetic corpus in {ROOT_DIR}...")

    # 1. Plain Text / Source Code (40%): Low Entropy (3.5 - 4.8 bits)
    words = "system kernel memory buffer socket pointer struct return function trace probe dev ino".split()
    text_count = int(total_files * 0.40)
    for i in range(text_count):
        folder = ROOT_DIR / random.choice(subdirs)
        size = random.randint(1024, 16384)
        content = (" ".join(random.choices(words, k=size // 6))).encode("utf-8")
        (folder / f"source_{i}.txt").write_bytes(content)

    # 2. Compressed Office XML (20%): Medium-High Entropy (6.8 - 7.5 bits)
    doc_count = int(total_files * 0.20)
    for i in range(doc_count):
        folder = ROOT_DIR / random.choice(subdirs)
        size = random.randint(4096, 32768)
        content = b"PK\x03\x04\x14\x00" + os.urandom(size - 6)
        (folder / f"report_{i}.docx").write_bytes(content)

    # 3. High-Entropy Media / Photos (20%): High Entropy (7.8 - 7.95 bits)
    media_count = int(total_files * 0.20)
    for i in range(media_count):
        folder = ROOT_DIR / random.choice(subdirs)
        size = random.randint(8192, 65536)
        content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + os.urandom(size - 10)
        (folder / f"photo_{i}.jpg").write_bytes(content)

    # 4. Structured Data / Logs (20%): Repetitive Low/Med Entropy
    log_count = total_files - (text_count + doc_count + media_count)
    for i in range(log_count):
        folder = ROOT_DIR / random.choice(subdirs)
        lines = [f"{idx},user_{idx},status_ok,{random.random()}\n" for idx in range(50)]
        (folder / f"log_{i}.csv").write_text("".join(lines))

    print(f"[+] Corpus successfully generated: {total_files} files ready for evaluation.")

if __name__ == "__main__":
    generate_corpus()
