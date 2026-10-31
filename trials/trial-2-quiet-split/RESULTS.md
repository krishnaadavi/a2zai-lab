# Trial #2 — "The Quiet Split" (v2) — Examiner-Side Reference Runs

**Read this label first:** the model runs below are **examiner-side
reference runs**, executed by the Lab operator — Wonder and Spark on
Mon Oct 26, 2026, Glimmer on Wed Oct 28, 2026 — blind, under the same
conditions any contestant gets (the prompt was assembled from this
trial's README brief + the four `task-pack/` files only; no answer
key, scorer, or baseline material entered it). They are
published so anyone can audit what a scored run looks like and what the
ceiling costs. They are not contestant submissions, and the answer key
they were scored against stays examiner-side (see the repo's Integrity
section).

## Model runs (first attempt each)

| Run | Model | Score /95 | Components (disp 40 / trap 20 / cite 15 / evid 10 / calib 10) | Gates | Tokens (in/out) | Cost | Wall | Final /100 |
|---|---|---|---|---|---|---|---|---|
| `wonder-trial2b-run1` | Muse Wonder (`muse-wonder-1.0`, Meta Model API) | **95.0** | 40.0 / 20.0 / 15.0 / 10.0 / 10.0 | none | 3,829 / 9,956 | $0.2144 | 47.3s | **95.9** (cost/time 0.9) |
| `spark-trial2b-run1` | Muse Spark 1.3 (`muse-spark-1.3`, Meta Model API) | **95.0** | 40.0 / 20.0 / 15.0 / 10.0 / 10.0 | none | 3,829 / 7,817 | $0.0380 | 45.0s | **100.0** (cost/time 5.0) |
| `glimmer-trial2b-run1` | Muse Glimmer 30B (`meta-models/Muse-Glimmer-30B`, open weights, via Together AI) | **95.0** | 40.0 / 20.0 / 15.0 / 10.0 / 10.0 | none | 3,844 / 12,681 | $0.0204 | 175.4s | **100.0** (cost/time 5.0) |

Final totals use the pinned cost/time rule (ratified Oct 26, 2026,
before points were awarded): **5 × min(1, median run cost ÷ run cost)**,
costs from published per-token rates, median across this trial's real
runs. The median is defined over the runs on the board, so it moved
when Glimmer's run joined: across the first two runs it was $0.1262
(Wonder 97.9, Spark 100.0); across the three it is **$0.0380**, and
every final was recomputed by the same pinned rule — Spark 100.0,
Glimmer 100.0, Wonder 95.9. Each run's `final_score.json` shows its
own arithmetic. Full artifacts (decisions, trace, score, run meta,
receipt) are in `harness/runs/wonder-trial2b-run1/` and
`harness/runs/spark-trial2b-run1/`; Glimmer's run folder
(`harness/runs/glimmer-trial2b-run1/`) is examiner-side until this
trial's publication. Glimmer sat with the 64,000-token completion
budget set by the Trial #1 budget-fix precedent; its token counts are
Together AI's tokenizer (3,844 in vs 3,829 on Meta's counter — same
assembled prompt).

**Honest read:** v2 did not separate the models on the 95 scored
points — all three were perfect. All three linked the split invoices
as one case, linked the genuine pair as a separate case, left the
look-alike invoices unlinked, held the bank-detail change for
verification, and left the legitimate same-vendor invoices untouched.
The only separation is cost: Glimmer produced the identical perfect
run for $0.0204 — ~1/10.5 of Wonder's cost and ~half of Spark's —
which under the pinned rule ties Glimmer with Spark at 100.0 and
moves Wonder to third. Trial #2 v1 (20 invoices) scored the same way
— 95.0/95 for both Meta models — which is why this hardened v2 (30
invoices) is the public version and v1 stays examiner-side as
evidence.

## Deterministic reference baselines (not model runs)

Hand-built decision files that prove the scoring pipeline and price
specific errors — receipts in `harness/runs/verify-2026-10-26/`,
full record in `VERIFICATION.md`:

| Baseline | Score /95 | What it proves |
|---|---|---|
| Link-aware reference | **95.0** | The ceiling: patterns linked, queue worked clean |
| Naive (each invoice alone) | **59** (raw 68.0) | Hard gate: missing a linked pattern caps the total at 59 |
| All four look-alikes linked into the pair's case | **90.17** | Over-linking costs 4.83 |
| False-trap cluster wrongly linked | **88.0** | A wrong link costs 7.0 |
| Genuine pair missed entirely | **83.67** | Missing the half-link costs 11.33 |
| Bank-detail change approved | **39** (raw 92.17) | Hard gate: approving a bank change without verification caps at 39 |
