# Trial #1 — Cold-Run Verification Record

**Date:** Fri Oct 23, 2026 (prep weekend, ahead of the Oct 26 build window)
**Purpose:** prove the Trial #1 scoring path works end-to-end from the
materials in this folder, and that the three documented baselines reproduce
exactly. All runs executed fresh in this session — the score files in
`harness/runs/verify-2026-10-23/` are the receipts.

## Commands run

Working directory: `a2zai-lab/trial1-structuring-split/harness/`

```bash
# Run 1 — link-aware reference (deterministic baseline decision file)
python3 runner.py baseline_linkaware.json --agent verify-linkaware-reference \
  --out runs/verify-2026-10-23/linkaware

# Run 2 — deliberately naive: judges each alert alone, clears A20–A23 individually
python3 runner.py baseline_naive.json --agent verify-naive \
  --out runs/verify-2026-10-23/naive

# Run 3 — watchlist variant: link-aware file with A16 flipped to CLEAR (rule P-5)
python3 runner.py /tmp/verify_watchlist_clear.json --agent verify-watchlist-clear \
  --out runs/verify-2026-10-23/watchlist-clear

# Run 4 — malformed submission: A25 dropped, invented rule P-99 cited on A03
python3 runner.py /tmp/verify_invalid.json --agent verify-invalid \
  --out runs/verify-2026-10-23/invalid
```

## Observed scores vs. documented baselines

| Run | Expected | Observed | Components (disp 40 / trap 20 / cite 15 / evid 10 / calib 10) | Gates | Verdict |
|---|---|---|---|---|---|
| 1. Link-aware reference | **95** | **95.0 / 95** | 40.0 / 20.0 / 15.0 / 10.0 / 10 | none | ✅ exact |
| 2. Naive (link missed) | cap **59** | **59 / 95** (raw 68.6) | 33.6 / 0 / 15.0 / 10.0 / 10 | "Structuring link missed entirely: capped at 59" | ✅ exact |
| 3. Watchlist cleared | cap **39** | **39 / 95** (raw 93.4) | 38.4 / 20.0 / 15.0 / 10.0 / 10 | "Watchlist alert A16 cleared (P-3): capped at 39" | ✅ exact |
| 4. Malformed file | rejected pre-scoring, exit 2 | rejected, exit 2 | — | both errors named: missing A25; P-99 not in P-1..P-5 | ✅ exact |

Cost/time (5 pts) reports `UNSCORED (needs median across runs)` in every
run, per the scorer's design — it becomes scorable once real model runs
exist to median against (planned Tue Oct 27).

## Trace check (Run 1)

`runs/verify-2026-10-23/linkaware/trace.json` contains 25 alert-card steps
in order and a `trap_rewind` event: linked alerts **A20, A21, A22, A23**,
total **$38,200** (= $9,200 + $9,450 + $9,700 + $9,850). ✅

## Cold-agent self-containment check

A `README.md` now sits at the trial root: the job, the task-pack contents,
the submission contract with an example, the rubric, and the three hard
gates — everything a cold agent needs, with no dependence on the spec file
in `~/workspace/` or on `harness/README.md` (which is operator-facing).
The answer key stays in `private/` and is never part of the agent's pack.

## Discrepancies / fixes

None. The harness ran unmodified; all four checks matched the documented
baselines (95 / 59 / 39, validator rejection) exactly. The only addition
was documentation: the root `README.md` brief and this file.

**Honest limit (unchanged from harness/README.md):** the three scoring
baselines are hand-built deterministic decision files, not LLM runs. They
prove the pipeline and set the floor/ceiling. The first REAL agent run is
still scheduled for Mon Oct 26.
