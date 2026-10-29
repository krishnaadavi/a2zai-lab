#!/usr/bin/env python3
"""A2ZAI Lab — receipt attestation stamper.

Computes a SHA-256 attestation over a run's canonical artifacts and writes
attestation.json into the run directory. The attestation binds the published
decisions and score to the exact bytes the harness produced: change any
attested file by one byte and verification fails, naming the file.

Canonical artifact sets (chosen from the harness run layout):
  scored run    : decisions.json, score.json, final_score.json, run_meta.json
  rejected run  : raw_response.txt, rejection.json
receipt.md is deliberately NOT attested (it is human prose that receives
dated correction appends); trace.json / replay.html are derived views of
decisions.json, so attesting decisions.json covers their source.

Usage:
  python3 tools/attest.py <run_dir> [<run_dir> ...]
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCORED_FILES = ["decisions.json", "score.json", "final_score.json", "run_meta.json"]
REJECTION_FILES = ["raw_response.txt", "rejection.json"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def combined_hash(run_name: str, file_hashes: dict) -> str:
    """Hash of the per-file hashes (sorted-filename order) + the run name."""
    concat = "".join(file_hashes[name] for name in sorted(file_hashes))
    return hashlib.sha256((concat + run_name).encode("utf-8")).hexdigest()


def build_attestation(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    rejection_path = run_dir / "rejection.json"
    is_rejection = rejection_path.exists() and not (run_dir / "final_score.json").exists()
    files = REJECTION_FILES if is_rejection else SCORED_FILES

    missing = [name for name in files if not (run_dir / name).exists()]
    if missing:
        raise SystemExit(f"{run_dir}: missing canonical artifacts: {', '.join(missing)}")

    file_hashes = {name: sha256_file(run_dir / name) for name in files}

    model = None
    final_score = None
    status = "SCORED"
    if is_rejection:
        meta = json.loads(rejection_path.read_text())
        model = meta.get("model")
        status = meta.get("status", "REJECTED_PRE_SCORING")
    else:
        fs = json.loads((run_dir / "final_score.json").read_text())
        model = fs.get("model")
        final_score = fs.get("total_of_100")
        if model is None and (run_dir / "run_meta.json").exists():
            model = json.loads((run_dir / "run_meta.json").read_text()).get("model")

    record = {
        "attestation_version": 1,
        "type": "rejection" if is_rejection else "scored",
        "run": run_dir.name,
        "model": model,
        "status": status,
        "final_score": final_score,
        "files": file_hashes,
        "attestation_hash": combined_hash(run_dir.name, file_hashes),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return record


def stamp(run_dir: Path) -> dict:
    record = build_attestation(run_dir)
    out = Path(run_dir) / "attestation.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    return record


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: attest.py <run_dir> [<run_dir> ...]")
    for arg in sys.argv[1:]:
        rec = stamp(Path(arg))
        kind = "REJECTION" if rec["type"] == "rejection" else f"final {rec['final_score']}"
        print(f"{rec['run']}: {kind}  attestation {rec['attestation_hash']}")
