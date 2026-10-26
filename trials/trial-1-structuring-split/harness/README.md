# Trial #1 harness — Week 2 pulled forward (built Sun 2026-10-18)

Week 1 (task pack + scorer) finished early on Oct 18, so the first half of
Week 2 in the no-hackathon roadmap is now built too. This is infrastructure,
not a model run — no LLM has run the trial yet.

## What's here
- `runner.py` — validates any agent decision file (exactly A01–A25, disposition
  in CLEAR/ESCALATE/MONITOR, rule_cited in P-1..P-5 only, evidence_fields a list),
  scores it with `../private/scorer.py`, and writes a replay-ready trace:
  `runs/<run>/trace.json` (25 alert-card steps in order, a `trap_rewind` event
  naming the linked alerts + $ total when a run links them, and `score_reveal`)
  plus `runs/<run>/score.json`. Model-agnostic: a real run only has to emit the
  same decision-file shape.
- `baseline_naive.json` / `runs/baseline-naive/` — deterministic per-alert
  baseline: judges each alert alone, clears A20–A23 individually.
  Verified score: **59/95, hard gate "structuring link missed"** (raw 68.6 capped).
- `baseline_linkaware.json` / `runs/baseline-linkaware/` — deterministic
  reference baseline: links A20–A23 as CASE-STRUCTURING-1 under P-2 with the
  phone/address/account linkers, MONITORs the A24 false trap.
  Verified score: **95.0/95, no gates**, trap_rewind total $38,200.
- Validation verified: a file missing an alert and citing invented rule P-99 is
  rejected with both errors named (exit 2), before any scoring.

## Honest limits
- Both baselines are hand-built deterministic decision files, NOT agent runs.
  They prove the pipeline end-to-end and set the floor (59) and ceiling (95)
  a real model run will be read against — they are not leaderboard entries.
- Cost/time (5 pts) stays UNSCORED until there are multiple real runs to take
  a median from, per the scorer's design.
- Citation scoring in scorer v1 checks rule validity (P-1..P-5), not
  per-alert rule correctness — the link-aware baseline's P-5 cites on
  A15/A19 mean "inconsistent with stated profile."

## What remains for Week 2 (Oct 26–Nov 1, unchanged)
1. Plug in one real model config, then a second, each emitting a decision file;
   run: `python3 runner.py <decisions.json> --agent <name> --model <id> --tokens <n> --out runs/<name>`
2. Build the replay template against `trace.json` (the trap_rewind event is
   the ~4:30 merge moment in the episode storyboard).
3. Krish: two short face takes (30-sec intro, verdict) once the first REAL
   scored run exists — not before, and not on the baselines.
