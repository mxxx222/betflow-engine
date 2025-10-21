#!/usr/bin/env python3
import hashlib
import json
import sys


def verify_sha_chain(logfile):
    prev_sha = None
    with open(logfile, 'r') as f:
        for i, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
            except Exception as e:
                print(f"Line {i}: Invalid JSON: {e}")
                return False
            chain_input = (prev_sha or "") + json.dumps(entry, sort_keys=True, separators=(',', ':'))
            chain_sha = hashlib.sha256(chain_input.encode()).hexdigest()
            if entry.get('sha_chain') != chain_sha:
                print(f"Line {i}: SHA chain mismatch! Expected {chain_sha}, found {entry.get('sha_chain')}")
                return False
            prev_sha = chain_sha
    print("SHA chain verified: OK")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <audit-log-file>")
        sys.exit(1)
    logfile = sys.argv[1]
    if not verify_sha_chain(logfile):
        sys.exit(2)
