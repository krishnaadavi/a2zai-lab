# Population Trials — Receipt (v2-spark-100-tx-2025-26)

- **Run:** v2-spark-100-tx-2025-26 · 100 agents · model: spark (Muse Spark 1.3, batched cohort planner)
- **Data:** CDC ILINet via Delphi epidata, season file data/ilinet_tx_2025-26.csv (verified live pull, Oct 27 2026)
- **Design (v2):** the pool saw the first 4 observed weeks
  (epiweeks 202540–202543, wILI [2.07906, 2.06636, 2.06582, 1.77178]) and nothing after.
  It forecast the next 13 weeks — window rule: through 4 weeks past the real peak
  (wILI 8.32 @ 202552) — scored against reality by engine/calibrate.py.
- **What was fit, and on what data:** ONLY the kernel's base_transmission. Grid of
  59 values (0.002–0.060) run through the kernel with rule-based mock
  behavior, seeded from the first observed week; the winner minimized squared error
  against the remaining seed-window observations (sim [1.2, 1.5, 2.7]
  vs real [2.06636, 2.06582, 1.77178], SSE 1.9323). The holdout was never read by
  the fit. **Fitted base_transmission: 0.025** (v0/v1 used the a priori 0.055),
  frozen for the forecast. Reporting fraction, cohort table, and every other kernel
  parameter are unchanged from v0/v1.
- **Calibration score: 17.2 / 100**
  - curve shape 0.0/40 (Pearson r = -0.635)
  - peak timing 0.0/30 (peak off by 5 week(s))
  - magnitude 17.2/30 (sim/real mass ratio 0.374)
  - gate: peak timing off by 5 weeks (>=3) — capped at 49
- **May publish what-ifs:** False (threshold 70)
- **Dynamics:** import_rate 1.0/wk, waning 8 wks (same as v1, for comparability)
- **Cost:** $0.3158 — Spark usage: {'prompt_tokens': 12077, 'completion_tokens': 70746, 'calls': 52, 'fallbacks': 0}
- **Honest label:** v2: seed-window-fitted kernel + Spark behavior. The fit used seed weeks only; the score is whatever the untouched holdout gave.
  The flagship calibration key (Dallas County DCHHS absence series) is still to be wired.
