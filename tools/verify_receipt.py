#!/usr/bin/env python3
"""A2ZAI Lab — receipt attestation verifier.

Recomputes the SHA-256 hashes of a run's canonical artifacts and checks them
against the run's attestation.json. Exit 0 with an OK line when everything
matches; exit nonzero naming the mismatching file when anything differs
(including a missing attested file or a wrong combined attestation hash).

Usage:
  python3 tools/verify_receipt.py <run_dir>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from attest import combined_hash, sha256_file  # noqa: E402


def verify(run_dir: Path) -> int:
    run_dir = Path(run_dir)
    att_path = run_dir / "attestation.json"
    if not att_path.exists():
        print(f"FAIL {run_dir.name}: no attestation.json in {run_dir}")
        return 2
    att = json.loads(att_path.read_text())

    for name, expected in sorted(att["files"].items()):
        f = run_dir / name
        if not f.exists():
            print(f"FAIL {run_dir.name}: attested file missing: {name}")
            return 1
        actual = sha256_file(f)
        if actual != expected:
            print(f"FAIL {run_dir.name}: hash mismatch in {name}")
            print(f"  attested: {expected}")
            print(f"  actual:   {actual}")
            return 1

    recomputed = combined_hash(att["run"], att["files"])
    if recomputed != att["attestation_hash"]:
        print(f"FAIL {run_dir.name}: attestation_hash mismatch in attestation.json")
        return 1

    kind = "rejection" if att["type"] == "rejection" else f"final score {att['final_score']}"
    print(f"OK {att['run']}: attestation verified ({kind}, "
          f"{len(att['files'])} files, attestation {att['attestation_hash'][:16]}...)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_receipt.py <run_dir>")
    sys.exit(verify(Path(sys.argv[1])))
