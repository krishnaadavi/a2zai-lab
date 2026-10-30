# DriftCheck Ledger

The Lab re-seats published entrants on the same exams, under the same
conditions, and records what changes. A single re-sitting is an
observation, not a verdict: since the 2026-10-30 hardening study, drift
verdicts are issued only from a distribution over repeated sittings,
against thresholds set before the runs begin.

## 2026-10-28 — Observation (single sitting, no verdict issued)

Spark re-seated once on Trial #1 flipped MONITOR→ESCALATE on A15, A17,
A19 vs its published baseline (raw 91.8 → 94.2, cost $0.0627). Recorded
at the time as an examiner-side observation pending methodology.

## 2026-10-30 — Hardening study: verdict NO PERSISTENT DRIFT

Spark ×10 sittings (9 scored, 1 truncated — kept and labeled) + Wonder
×3 as a control, identical fixed settings, total scored cost $1.2190.

- 7 of 9 scored Spark sittings reproduced the published baseline
  dispositions on all 25 alerts exactly (raw 91.8, the mode).
- ESCALATE counts: A15 2/9, A17 2/9, A19 1/9. The full three-alert flip
  recurred once; a partial flip once. Only A15/A17/A19 ever varied.
- Wonder held its published dispositions in 3 of 3 sittings (one
  unrelated single-alert flip, A18, in one sitting).
- Verdict: the Oct 28 observation was a draw from minority behavior the
  model produces occasionally. The published board's 91.8 stands as
  Spark's modal score. Thresholds (CONSISTENT ≥7/9, SPORADIC 3–6/9,
  ABSENT ≤2/9 per alert) were set before the results were read.
- Full report, per-sitting artifacts, and attestations:
  driftcheck/study-2026-10-30/ in this repo (STUDY.md).
- Stated deviations: prompt-token count +32 vs the Day-1 seatings
  (constant across Oct 28 and the study; the study hardens the Oct 28
  comparison exactly); the Day-1 run_metas do not record temperature, so
  parameter identity with Day 1 rests on the shared driver.
