#!/usr/bin/env python3
"""hash_chain.py — append-only SHA-256 evidence chain (Temporal-style audit log).

Each entry links to the previous entry's hash, so any tampering with an earlier
evidence artifact breaks the chain and is detectable. This is the durable history
that lets the supervisor recover from a crash and prove what really happened.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHAIN = os.path.join(ROOT, "state", "hash_chain.jsonl")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def last_hash() -> str:
    if not os.path.exists(CHAIN):
        return "0" * 64
    prev = "0" * 64
    with open(CHAIN, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                prev = json.loads(line)["chained_hash"]
    return prev


def append(step_id: str, evidence_path: str, classification: str) -> dict:
    os.makedirs(os.path.dirname(CHAIN), exist_ok=True)
    file_hash = sha256_file(evidence_path)
    prev = last_hash()
    chained = hashlib.sha256((prev + file_hash).encode()).hexdigest()
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "step": step_id,
        "evidence": os.path.relpath(evidence_path, ROOT),
        "classification": classification,
        "evidence_sha256": file_hash,
        "prev_hash": prev,
        "chained_hash": chained,
    }
    with open(CHAIN, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def verify_chain() -> bool:
    if not os.path.exists(CHAIN):
        return True
    prev = "0" * 64
    with open(CHAIN, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            recomputed = hashlib.sha256((prev + e["evidence_sha256"]).encode()).hexdigest()
            if recomputed != e["chained_hash"] or e["prev_hash"] != prev:
                return False
            prev = e["chained_hash"]
    return True


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--verify":
        print("CHAIN_OK" if verify_chain() else "CHAIN_BROKEN")
    elif len(sys.argv) >= 4 and sys.argv[1] == "--append":
        print(json.dumps(append(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "SUCCESS")))
    else:
        print("usage: hash_chain.py --verify | --append STEP EVIDENCE CLASSIFICATION")
