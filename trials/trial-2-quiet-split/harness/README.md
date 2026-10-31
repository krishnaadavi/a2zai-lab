# Trial #2 v2 harness (built Mon 2026-10-26, patterned on Trial #1/#2 v1 runners)

Infrastructure, not a model run — no LLM has run this trial yet.

## What's here
- `runner.py` — validates any agent decision file (exactly I01–I30, disposition
  in AUTO_APPROVE/MANAGER_APPROVAL/FINANCE_ESCALATE/HOLD_VERIFY/REJECT,
  rule_cited in Q-1..Q-7 only, evidence_fields a list), scores it with
  `../private/scorer.py`, and writes a replay-ready trace:
  `runs/<run>/trace.json` (30 invoice-card steps in order, `trap_rewinds`
  events — one per case the run linked, with invoice lists and $ totals —
  plus `score_reveal`) and `runs/<run>/score.json`. Model-agnostic: a real
  run only has to emit the same decision-file shape.
- `baseline_naive.json` / `runs/verify-2026-10-26/naive/` — deterministic
  per-invoice baseline: judges each invoice alone, manager-approves the
  four split invoices and the genuine pair individually under Q-2.
  Verified score: **59/95, hard gate "split link missed entirely"** (raw 68.0 capped).
- `baseline_linkaware.json` / `runs/verify-2026-10-26/linkaware/` — deterministic
  reference baseline: links the split I02/I08/I11/I15 as CASE-SPLIT-1 under
  Q-3 ($17,888), links the genuine pair I03/I09 as CASE-HALF-1 under Q-3
  (aggregate $11,800 counting the paid part 1), holds I10 under Q-4,
  rejects the I22 duplicate under Q-5, works the DataCore cluster
  (I16/I24/I29) and the rhyme pair (I05/I12) as individual manager
  approvals, and leaves the legitimate Apex invoices (I04/I13) unlinked.
  Verified score: **95.0/95, no gates**, trap_rewinds total $17,888 + $9,650.
- Also verified in `runs/verify-2026-10-26/`: linking all four NorthPeak
  invoices into the pair's case scores **90.17** (over-linking costs 4.83);
  wrongly linking the DataCore cluster as a Q-3 case scores **88.0** (the
  wrong link costs 7.0); missing the genuine pair entirely scores **83.67**
  (costs 11.33); approving the I10 bank-detail change caps at **39**
  (raw 92.17).
- Validation verified: a file missing I30 and citing invented rule Q-99 is
  rejected with both errors named (exit 2), before any scoring.

## Honest limits
- Both baselines are hand-built deterministic decision files, NOT agent runs.
  They prove the pipeline end-to-end and set the floor (59) and ceiling (95)
  a real model run will be read against — they are not leaderboard entries.
- Cost/time (5 pts) is scored under the pinned rule (5 × min(1, median run
  cost ÷ run cost), ratified Oct 26, 2026) by `drivers/cost_time.py` once
  real runs exist to median against; the scorer itself reports it UNSCORED.
- Citation scoring checks per-invoice rule governance against the answer
  key's expected-rules map (stricter than Trial #1's validity-only check):
  a real rule cited on the wrong invoice earns no citation credit for that
  invoice, and an invented rule counts toward the >2 citation-zeroing rule.
- The evidence point for a manager-routed invoice requires the approving
  manager's name in the evidence fields (stated in the contestant README);
  the scorer checks for the surname from the answer key's managers map.
