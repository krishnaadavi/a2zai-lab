# Population Trials — prototype

The executable companion to `../population-trials-problem-statement-2026-10-27.md`.

**Design in one line:** agents set behavior, a transparent kernel does the
infection math, and the pool is scored only against real weeks it never saw
(temporal holdout). Below the publication threshold (70), the Lab publishes
the failure — never conclusions.

## Layout
- `data_pull.py` — CDC ILINet via Delphi epidata (verified live Oct 27, 2026) → `data/*.csv`
- `engine/sim.py` — agent pool + kernel. Model is a pluggable callable:
  `mock_model` (rule-based, $0) today; a Spark-tier caller on the same
  contract next. Interventions are explicit dicts (e.g. school closure week).
- `engine/calibrate.py` — the scorer: curve shape 40 + peak timing 30 +
  magnitude 30; peak off by ≥3 weeks caps at 49; `may_publish_whatifs` ≥ 70.
- `run_prototype.py` — seeds from the real season, runs the holdout, writes
  `runs/<name>/{trace.json, result.json, receipt.md}`.
- `runs/prototype-v0-mock-tx-2022-23/` — the first run. **Calibration 24.5/100.**
  The mock pool flashes and burns out by week 6 (permanent immunity, no
  reseeding) while reality plateaus — a legible, published failure, and the
  v1 diagnosis: sustained-transmission dynamics + real model behavior in the
  loop. Nothing was tuned to the holdout; kernel parameters are a priori
  and printed in every trace.

## V2 (Day 3, Oct 28) — seed-window transmission fit

`run_v2.py`: the pool sees 4 seed weeks; the kernel's base_transmission —
and only that parameter — is grid-fit on those seed weeks (mock behavior as
the fitting instrument), frozen, and the untouched holdout is forecast with
the Spark planner. Fitted β: 0.025 (100 agents) / 0.022 (1,000), vs the
a priori 0.055. The instant-explosion pathology is gone (v1 hit 13.5%ILI in
week 2; v2 peaks at a plausible ~5) and the peak miss narrowed 9 → 5 weeks,
but the pool still peaks early and burns out while the real season climbs:
**Spark 100 → 17.2/100, Spark 1,000 → 17.3/100, mock 100 → 18.5/100** — gate
applied, `may_publish_whatifs: false`, receipts in `runs/v2-*`. A flat seed
window cannot tell the kernel the season accelerates later; that is the v3
question, and it will be answered with seed-window information only.

## Next (v1)
1. Spark-tier caller behind the same model contract (~$14/suite at prototype
   scale per the cost model in the problem statement).
2. DCHHS Dallas County loader (student absences due to ILI by week) — the
   flagship calibration key; ILINet TX is the stand-in until it lands.
3. A priori dynamics: imported-case reseeding + immunity that isn't a
   one-way door. Decided before seeing scores, documented in the run params.
