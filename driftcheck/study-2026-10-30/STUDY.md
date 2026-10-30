# DriftCheck Hardening Study — Trial #1 re-sittings (2026-10-30)

**EXAMINER-SIDE ONLY — unpublished.** Purpose: the Oct 28 DriftCheck run
re-seated Muse Spark once and observed A15/A17/A19 flipped MONITOR→ESCALATE
(raw 91.8 → 94.2). One re-run cannot distinguish a persistent model change
from sampling variance at temperature 0.2. This study re-seats Spark 10
times and Wonder 3 times under identical fixed settings and measures the
distribution.

## Verdict

**The A15/A17/A19 flip is ABSENT as Spark's stable behavior. It is a
sporadic tail event, not a persistent shift.**

Classification thresholds (set before reading the results): ESCALATE in
≥7 of 9 scored sittings = CONSISTENT; 3–6 = SPORADIC; ≤2 = ABSENT as the
stable behavior. Observed, per alert, across the 9 scored Spark sittings:

| Alert | ESCALATE | MONITOR | Class |
|---|---|---|---|
| A15 | 2 of 9 | 7 of 9 | ABSENT (sporadic tail) |
| A17 | 2 of 9 | 7 of 9 | ABSENT (sporadic tail) |
| A19 | 1 of 9 | 8 of 9 | ABSENT (sporadic tail) |

In 7 of 9 scored sittings Spark reproduced its published baseline
dispositions on **all 25 alerts exactly** (raw 91.8 every time). The full
three-alert ESCALATE pattern recurred once (s08, raw 94.2 — the Oct 28
result reproduced), and a partial two-alert version once (s09: A15+A17,
raw 93.4). Counting the Oct 28 sitting as well, the post-publication
record is 10 scored sittings: A15 ESCALATE 3/10, A17 3/10, A19 2/10 — a
minority pattern every way it is counted. The Oct 28 observation was a
genuine draw from behavior the model produces occasionally; it was not
evidence of a persistent change, and the published board's 91.8 stands
as Spark's modal score. **Methodological consequence: a single DriftCheck
re-sitting cannot support a drift verdict at temperature 0.2 — the watch
must report a distribution over repeated sittings, which is what this
study adds.**

## Conditions (identical across all 13 sittings)

- Driver: the trial's own `drivers/meta_driver.py` — the same code path
  as the original seatings and the Oct 28 run. Prompt assembled from
  exactly five contestant-visible sources (dry-run verified 2026-10-30,
  see `leak_check_dryrun.txt`): the trial README contestant brief +
  `task-pack/alerts.csv`, `customers.json`, `ledger_90d.csv`,
  `policy_excerpt.md`. Fresh API session per sitting; no retries.
- temperature 0.2 (hardcoded in the driver's `call_api`), max_tokens
  16000, JSON-only output path (`--no-schema`) — the Oct 28 settings.
- Scoring: the trial's own harness + private scorer. Finals computed
  against the PINNED published median $0.0548 (the DriftCheck rule), so
  no published run was repriced or touched.
- Every scored sitting attested with `tools/attest.py`; all 12
  attestations pass `tools/verify_receipt.py`.

## Spark arm — 10 sittings attempted, 9 scored, 1 failed

| Sitting | Raw /95 | Final /100 | Cost | Flips vs published baseline |
|---|---|---|---|---|
| s01 | 91.8 | 95.7 | $0.0697 | none |
| s02 | 91.8 | 96.2 | $0.0619 | none |
| s03 | 91.8 | 96.8 | $0.0539 | none |
| s04 | 91.8 | 96.8 | $0.0462 | none |
| s05 | 91.8 | 96.4 | $0.0597 | none |
| s06 | 91.8 | 96.8 | $0.0418 | none |
| s08 | 94.2 | 99.2 | $0.0500 | A15, A17, A19 |
| s09 | 93.4 | 98.3 | $0.0559 | A15, A17 |
| s10 | 91.8 | 96.8 | $0.0398 | none |
| s07 | — | — | — | **FAILED — response truncated (finish_reason: length) at the 16,000-token cap; JSON unparseable; raw response preserved in `spark-s07/`; counted, never re-run** |

- Raw scores (9 scored): mean 92.24, range 91.8–94.2; the mode is 91.8 (7 of 9).
- Scored-run cost total: $0.4789. (s07's API spend is
  not in this total — the driver writes run_meta only on success; by
  analogy with sibling sittings it was ≈$0.05.)

### Per-alert disposition distribution — Spark, 9 scored sittings

| Alert | CLEAR | MONITOR | ESCALATE | Published baseline |
|---|---|---|---|---|
| A01 | 9 | 0 | 0 | CLEAR |
| A02 | 9 | 0 | 0 | CLEAR |
| A03 | 9 | 0 | 0 | CLEAR |
| A04 | 9 | 0 | 0 | CLEAR |
| A05 | 9 | 0 | 0 | CLEAR |
| A06 | 9 | 0 | 0 | CLEAR |
| A07 | 9 | 0 | 0 | CLEAR |
| A08 | 9 | 0 | 0 | CLEAR |
| A09 | 9 | 0 | 0 | CLEAR |
| A10 | 9 | 0 | 0 | CLEAR |
| A11 | 9 | 0 | 0 | CLEAR |
| A12 | 9 | 0 | 0 | CLEAR |
| A13 | 9 | 0 | 0 | CLEAR |
| A14 | 9 | 0 | 0 | CLEAR |
| A15 **← key alert** | 0 | 7 | 2 | MONITOR |
| A16 | 0 | 0 | 9 | ESCALATE |
| A17 **← key alert** | 0 | 7 | 2 | MONITOR |
| A18 | 0 | 9 | 0 | MONITOR |
| A19 **← key alert** | 0 | 8 | 1 | MONITOR |
| A20 | 0 | 0 | 9 | ESCALATE |
| A21 | 0 | 0 | 9 | ESCALATE |
| A22 | 0 | 0 | 9 | ESCALATE |
| A23 | 0 | 0 | 9 | ESCALATE |
| A24 | 9 | 0 | 0 | CLEAR |
| A25 | 0 | 0 | 9 | ESCALATE |

Only A15, A17, and A19 ever varied. The other 22 alerts were unanimous
in every scored sitting.

## Wonder arm — 3 sittings, stability contrast

| Sitting | Raw /95 | Final /100 | Cost | Flips vs published baseline |
|---|---|---|---|---|
| w01 | 94.2 | 95.3 | $0.2525 | none |
| w02 | 95.0 | 96.4 | $0.2019 | A18 |
| w03 | 94.2 | 95.2 | $0.2857 | none |

- Raw scores: mean 94.47, range 94.2–95.0; cost total $0.7401.
- A15/A17/A19 came back ESCALATE in **3 of 3** sittings — Wonder's
  published dispositions, unchanged.
- The only Wonder flip anywhere: A18 MONITOR→ESCALATE in w02 (that
  sitting scored 95.0 vs the 94.2 baseline). One alert, one sitting —
  the same order of sampling noise the Spark arm shows, on a different
  alert.

### Per-alert disposition distribution — Wonder, 3 scored sittings

| Alert | CLEAR | MONITOR | ESCALATE | Published baseline |
|---|---|---|---|---|
| A01 | 3 | 0 | 0 | CLEAR |
| A02 | 3 | 0 | 0 | CLEAR |
| A03 | 3 | 0 | 0 | CLEAR |
| A04 | 3 | 0 | 0 | CLEAR |
| A05 | 3 | 0 | 0 | CLEAR |
| A06 | 3 | 0 | 0 | CLEAR |
| A07 | 3 | 0 | 0 | CLEAR |
| A08 | 3 | 0 | 0 | CLEAR |
| A09 | 3 | 0 | 0 | CLEAR |
| A10 | 3 | 0 | 0 | CLEAR |
| A11 | 3 | 0 | 0 | CLEAR |
| A12 | 3 | 0 | 0 | CLEAR |
| A13 | 3 | 0 | 0 | CLEAR |
| A14 | 3 | 0 | 0 | CLEAR |
| A15 **← key alert** | 0 | 0 | 3 | ESCALATE |
| A16 | 0 | 0 | 3 | ESCALATE |
| A17 **← key alert** | 0 | 0 | 3 | ESCALATE |
| A18 | 0 | 2 | 1 | MONITOR |
| A19 **← key alert** | 0 | 0 | 3 | ESCALATE |
| A20 | 0 | 0 | 3 | ESCALATE |
| A21 | 0 | 0 | 3 | ESCALATE |
| A22 | 0 | 0 | 3 | ESCALATE |
| A23 | 0 | 0 | 3 | ESCALATE |
| A24 | 3 | 0 | 0 | CLEAR |
| A25 | 0 | 0 | 3 | ESCALATE |

## Deviations from identical conditions — stated, not hidden

1. **Prompt-token count vs the Day-1 seatings.** The published baselines
   recorded 5,904 prompt tokens; the Oct 28 run and all 13 study
   sittings recorded 5,936 (+32), constant across both arms and both
   days. The five prompt sources are the same files and assembly is
   byte-deterministic, so conditions are provably identical between
   Oct 28 and this study; the +32 against Day 1 indicates a small change
   to a prompt source file (or to API token counting) sometime between
   the Day-1 seatings and Oct 28. The study therefore hardens the
   Oct 28 comparison exactly, and the Day-1 comparison to within that
   32-token prompt difference.
2. **Baseline parameters not recorded.** The published runs' run_meta
   files do not record temperature or max_tokens. Identity with the
   original seatings rests on the shared driver (temperature 0.2 is
   hardcoded in `call_api`) and on the connector's verified notes
   (the JSON-only 16,000-token path is the one that produced complete
   Day-1 submissions; the published runs' completion-token counts,
   11,164 and 12,362, exceed the 8,000 schema-path cap). No parameter
   beyond this could be confirmed from the artifacts.
3. **One truncated sitting (Spark s07).** Kept, labeled, counted above.

## Sanity checks

- Sittings attempted: 13 = 10 Spark + 3 Wonder. Scored 12, failed 1 (labeled).
- Every reported score traces to a decisions.json preserved in both the
  harness run directory and this study folder; 12/12 attestations verify.
- Total scored study cost: **$1.2190**
  (Spark $0.4789 + Wonder $0.7401).
- Nothing was published: no changes to the public repo, the website, or
  any published run. Canonical run dirs live in
  `trial1-structuring-split/harness/runs/*-trial1-study-2026-10-30-*`;
  per-sitting artifacts are mirrored in this folder.
