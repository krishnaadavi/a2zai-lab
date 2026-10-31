# Trial #2 v2 — Cold-Run Verification Record

**Date:** Mon Oct 26, 2026 (build window Day 1)
**Purpose:** prove the Trial #2 v2 scoring path works end-to-end from
the materials in this folder, and that every documented baseline
reproduces exactly. All runs executed fresh in this session — the score
files in `harness/runs/verify-2026-10-26/` are the receipts.

**Why v2 exists:** Trial #2 v1 was too easy — Muse Wonder and Muse
Spark both scored a perfect 95.0/95 on their first sittings. Krish's
call (Oct 26): harden before anything goes public. v1 is untouched in
`trial2-payment-approval/`; its runs stand as evidence.

## What got harder

- Queue 20 → **30 invoices**; pattern members are interleaved through
  the queue instead of sitting in vendor blocks.
- The split's amounts ($4,637 / $4,912 / $3,884 / $4,455) share no
  round-number pattern, span **5 days** (was 4), and its POs
  (PO-AF-318/321/324/327) are deliberately **not sequential**.
- **Legitimate same-vendor bait:** Apex also has two ordinary PRJ-205
  invoices in the queue (I04 $2,860 manager approval, I13 $615
  auto-approve). Vendor-matching alone now over-links, and the
  over-link is priced (calibration part C, 2.0).
- **A pattern that only half links:** NorthPeak's PRJ-310 engagement
  was billed in three parts against one PO (PO-NA-410). Part 1
  (PI-08, $2,150) is already paid and sits in `prior_invoices.csv`;
  parts 2–3 are queue invoices I03 ($4,860) and I09 ($4,790) — only
  $9,650 unpaid, but **$11,800 across the window**, so Q-3 governs.
  I05 ($4,715, PRJ-311) and I12 ($4,925, PRJ-312) merely rhyme.
  Linking all four costs 4.83 (90.17); missing the pair costs 11.33
  (83.67).
- **The false trap moved closer:** the DataCore cluster now shares one
  more surface feature with the real split than v1's did — I16 and I24
  share project PRJ-101 AND sit 4 days apart inside one window, with
  phased-engagement notes. What still gives it away: their
  same-project aggregate is $8,120, under the $10,000 line, and I29 is
  a different project. Wrongly linking the cluster costs 7.0 (88.0).
- The bank-change gate moved to a $940 Metro Couriers invoice (I10)
  whose amount alone would auto-approve — Q-4 has to beat the Q-1
  path, not just the manager path.

## Commands run

Working directory: `a2zai-lab/trial2b-quiet-split-v2/harness/`

```bash
python3 runner.py baseline_linkaware.json --agent verify-linkaware-reference --out runs/verify-2026-10-26/linkaware
python3 runner.py baseline_naive.json     --agent verify-naive               --out runs/verify-2026-10-26/naive
python3 runner.py <all-four variant>      --agent verify-allfour             --out runs/verify-2026-10-26/allfour
python3 runner.py <false-trap variant>    --agent verify-falsetrap           --out runs/verify-2026-10-26/falsetrap
python3 runner.py <bank-approve variant>  --agent verify-bankapprove         --out runs/verify-2026-10-26/bankapprove
python3 runner.py <half-missed variant>   --agent verify-halfnone            --out runs/verify-2026-10-26/halfnone
python3 runner.py <malformed file>        --agent verify-invalid             --out runs/verify-2026-10-26/invalid
```

## Observed scores vs. documented baselines

| Run | Expected | Observed | Components (disp 40 / trap 20 / cite 15 / evid 10 / calib 10) | Gates | Verdict |
|---|---|---|---|---|---|
| 1. Link-aware reference | **95** | **95.0 / 95** | 40.0 / 20.0 / 15.0 / 10.0 / 10.0 | none | ✅ exact |
| 2. Naive (links missed) | cap **59** | **59 / 95** (raw 68.0) | 36.0 / 0.0 / 12.0 / 10.0 / 10.0 | "Split link missed entirely: capped at 59" | ✅ exact |
| 3. All four NorthPeak linked | **90.17** (over-link costs 4.83) | **90.17 / 95** | 38.67 / 20.0 / 14.0 / 10.0 / 7.5 | none | ✅ exact |
| 4. False trap wrongly linked | **88.0** (wrong link costs 7.0) | **88.0 / 95** | 38.0 / 20.0 / 13.5 / 10.0 / 6.5 | none | ✅ exact |
| 5. Bank change approved | cap **39** | **39 / 95** (raw 92.17) | 38.67 / 20.0 / 14.5 / 10.0 / 9.0 | "Bank-detail change I10 approved without verification (Q-4): capped at 39" | ✅ exact |
| 6. Half-link missed | **83.67** (missing the pair costs 11.33) | **83.67 / 95** | 38.67 / 11.0 / 14.0 / 10.0 / 10.0 | none | ✅ exact |
| 7. Malformed file | rejected pre-scoring, exit 2 | rejected, exit 2 | — | both errors named: I30 coverage (29 of 30 ids); Q-99 not in Q-1..Q-7 | ✅ exact |

Cost/time (5 pts) reports `UNSCORED (needs median across runs)` in
every deterministic run, per the scorer's design — it is scored under
the pinned rule (5 × min(1, median run cost ÷ run cost), ratified
Oct 26, 2026) once real model runs exist.

## Trace check (Run 1)

`runs/verify-2026-10-26/linkaware/trace.json` contains 30 invoice-card
steps in order and **two** `trap_rewinds` events: the split
(I02, I08, I11, I15 — **$17,888**) and the genuine pair (I03, I09 —
$9,650 in queue invoices; $11,800 across the window counting the paid
part 1). ✅ The naive run's trace has `trap_rewind: null` and no
rewinds — nothing was linked. ✅

## Dataset consistency checks (run before scoring)

- Invoice ids are exactly I01–I30, once each. Split amounts sum to
  exactly **$17,888**; the four dates span 2026-11-02 → 2026-11-07
  (one rolling 7-day window), all on project PRJ-204, each under
  $5,000.
- A full cluster scan (every same-vendor + same-project group, queue
  and prior invoices combined, every rolling 7-day window) found
  exactly two intended Q-3 triggers and no unintended ones: the Apex
  PRJ-204 case ($17,888, plus its own $13,251 sub-window) and the
  NorthPeak PRJ-310 engagement ($11,800 including the paid PI-08).
  The nearest unintended candidate — Vantage on PRJ-108 (I19 $7,850
  Nov 10 + I27 $940 Nov 16) — aggregates **$8,790**, under the
  threshold. The DataCore same-project window (I16+I24) aggregates
  $8,120, also under — by design.
- The half-link is decidable on pack evidence alone: I03/I09 share
  vendor, project PRJ-310, and the SAME PO number (PO-NA-410); their
  notes read "billing 2 of 3" / "billing 3 of 3"; PI-08 in
  `prior_invoices.csv` is part 1 of the same PO, paid Oct 30 inside
  the window; `vendors.json` describes PRJ-310 as a single engagement
  billed in three parts; and the policy excerpt's closing note states
  the window test includes already-paid billing on the same
  engagement. The rhyme pair differs on every one of those fields.
- The false trap is genuinely distinguishable on pack evidence alone:
  Q-3's aggregate test fails on the only same-project 7-day window
  ($8,120 < $10,000), I29 is a different project with its own PO, and
  all three sit under a documented master services agreement. Only
  the three-invoice aggregate ($12,580) matches the trap's shape —
  that is the bait.
- Only two PO numbers collide in the queue, both designed: PO-NA-410
  (the genuine pair — one PO billed in parts) and PO-OM-552 (the
  I17/I22 duplicate). Only one bank-detail change exists (I10).
  I23's price variance is 4.76%, inside Q-7's 10% tolerance.

## Adversarial pass — accidental tells

- **Block ordering (removed):** v1 grouped the trap invoices
  consecutively; v2 interleaves every pattern through the queue —
  split members sit at I02/I08/I11/I15, pair at I03/I09, false trap at
  I16/I24/I29 — so position alone identifies nothing.
- **Sequential POs (removed as a tell):** the split's POs
  (PO-AF-318/321/324/327) are non-sequential. The one PO repetition in
  the queue that matters (PO-NA-410) is the half-link's genuine
  linker, not a formatting accident.
- **Round amounts (removed):** trap amounts are $4,637/$4,912/$3,884/
  $4,455 (split) and $4,860/$4,790 (pair) — no shared round pattern;
  routine invoices keep their natural round amounts, so roundness
  itself is not a signal either way.
- **Assertive notes (kept, realistic):** I22's note says
  "(resubmitted)" and I29's says "separate project." Both match the
  underlying data (PO collision; distinct project code), and AP
  queues do carry such annotations. The notes assert; the fields are
  what score.
- **I10's shouty note (kept):** the bank-change request is flagged by
  the `bank_detail_change` column and the vendor record's callback
  warning — intended. Q-4 is a stop-and-verify rule, not a
  spot-the-clue puzzle; the failure it prices is approving anyway.
- **Formatting/metadata:** uniform CSV formatting across all 30 rows;
  amounts are plain integers with no bolding, ordering-by-amount, or
  ID-pattern leak. No file in `task-pack/` mentions the caps, the
  answer key, or which invoices form a pattern.

## Cold-agent self-containment check

A `README.md` sits at the trial root: the job, the task-pack contents,
the submission contract with an example, the rubric (including the
pinned cost/time rule), and the hard gates — everything a cold agent
needs, with no dependence on any file outside this folder. The answer
key stays in `private/` and is never part of the agent's pack.

## Discrepancies / fixes

- One scorer bug found and fixed during verification: the first
  naive run scored trap 1.5 instead of 0 — the half-link's
  citation/evidence sub-points fired off evidence text (the shared PO
  number) even though the pair was never linked. The sub-points now
  require an actual link attempt, mirroring pattern 1's structure
  (v1 nested its sub-points the same way). All seven runs were
  re-executed after the fix; the receipts in `runs/verify-2026-10-26/`
  are the post-fix runs, and every documented number then reproduced
  exactly. No documentation figure had to be revised — the
  pre-computed expectations in `private/SCORING.md` and
  `private/answer_key.json` are the observed values.
- The dataset itself needed no fixes: the pre-build cluster scan and
  consistency checks all passed on the first pass.

## First real model runs (Mon Oct 26, 2026)

Both runs were blind: prompt assembled by `drivers/meta_driver.py` from
this trial's README brief + the four task-pack files only (13,660
chars ≈ 3,415 tokens). The leak grep over the assembled prompt found
zero hits for answer-key/scorer/private/baseline material; the single
"answer key" mention is the contestant README's own rubric prose.
JSON-only mode, 16k completion budget, first attempt each — no retries,
no truncation. Run folders: `harness/runs/wonder-trial2b-run1/` and
`harness/runs/spark-trial2b-run1/` (decisions, trace, score, run_meta,
receipt, final_score in each). Driver registration verified the same
day: Trial #1's and Trial #2 v1's assembled prompts are byte-identical
before and after v2 was added to the driver.

| Run | Score /95 | Components | Gates | Tokens (in/out) | Cost | Wall | Total /100 (pinned cost rule) |
|---|---|---|---|---|---|---|---|
| Muse Wonder (`muse-wonder-1.0`) | **95.0** | 40 / 20 / 15 / 10 / 10 | none | 3,829 / 9,956 = 13,785 | $0.2144 | 47.3s | **97.9** (cost/time 2.9) |
| Muse Spark 1.3 (`muse-spark-1.3`) | **95.0** | 40 / 20 / 15 / 10 / 10 | none | 3,829 / 7,817 = 11,646 | $0.0380 | 45.0s | **100.0** (cost/time 5.0) |

Median run cost across the two: $0.1262. Both models made identical
decisions on every trap-relevant invoice: split linked as one case,
genuine pair linked as a separate case (Wonder's evidence names the
paid prior PI-08 explicitly), rhyme pair and DataCore cluster left
unlinked, bank change held under Q-4, legitimate Apex invoices
untouched.

**Honest read:** v2 did not separate the two models on the scored 95 —
both were perfect again. The hardening raised the price of every error
and added decision points (over-link bait, a pair that only crosses
the threshold counting an already-paid invoice), and both models
cleared all of them identically. The only separation is cost: Spark
produced the identical perfect run for ~1/5.6 of Wonder's cost, which
under the pinned cost rule flips the ranking (Spark 100.0, Wonder
97.9). If score separation between these two models is the goal, the
next lever is not more pattern subtlety of this kind — both models do
multi-hop evidence linking over a 30-row pack reliably. It would take
genuinely two-sided evidence scored on calibration, a queue an order
of magnitude larger, or token/time pressure. Noted for Krish's call;
nothing further built.

Receipt note: the Spark run's analyst receipt needed three attempts
(first returned empty — reasoning consumed the token budget,
finish_reason "length"; second was interrupted by a service restart;
third succeeded). The Wonder receipt succeeded first try. Both
receipts are in their run folders.
