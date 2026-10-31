# Population Trials — Receipt (v3-spark-100-dchhs-2024-25)

- **Run:** v3-spark-100-dchhs-2024-25 · 100 agents · model: spark (Muse Spark 1.3, batched cohort planner (v3 prompt: DCHHS series + past-season history))
- **Data:** DCHHS Dallas County student-absence ILI %, Figure 4 of the DCHHS
  Influenza Surveillance Reports (dallascounty.org) — primary source, vector
  extraction, pulled Oct 29 2026; pull receipt rides in this bundle
  (data_pull_receipt.json) and at data/dchhs_pull_receipt.json.
- **Design (v3):** multi-season shape-teaching. The pool's information set:
  the first 4 observed weeks of 2024–25 (epiweeks 202440–202443,
  values [0.035, 0.038, 0.082, 0.028]) plus the COMPLETE curves of 2018–19, 2022–23, 2023–24.
  It forecast the next 15 reported weeks — window rule: through 4 weeks
  past the real peak (0.512% @ epiweek 202505) — scored
  against the untouched 2024–25 holdout by engine/calibrate.py, unchanged.
- **Flagged points:** six `suspected_no_report_plotted_as_zero` points are
  no-report weeks the chart drew at zero — dropped from every curve as the
  gaps they are (2022–23 wks 5, 11; 2023–24 wks 47, 52, 11; 2024–25 wk 11).
  Gaps are never filled; one sim step = one reported week.
- **What was fit, and on what data:** ONLY the kernel's base_transmission.
  Per past season, the v2 grid (59 values,
  0.002–0.060, mock behavior as the fitting instrument, seeded from that
  season's first observed week) minimized SSE against that season's FULL
  remaining curve — the acceleration phase is inside the fit objective;
  that is the v3 change. Winners: 2018–19 β=0.002
  (SSE 1.658959), 2022–23 β=0.002
  (SSE 1.480643), 2023–24 β=0.002
  (SSE 1.479875). **beta_v3 = median = 0.002**, frozen for the
  forecast (v0/v1 a priori: 0.055; v2 seed-window fit: 0.022–0.025). Reporting
  fraction, cohort table, and every other kernel parameter are unchanged.
- **Calibration score: 20.6 / 100**
  - curve shape 0.0/40 (Pearson r = 0.0)
  - peak timing 0.0/30 (peak off by 10 week(s))
  - magnitude 20.6/30 (sim/real mass ratio 2.057)
  - gate: peak timing off by 10 weeks (>=3) — capped at 49
- **May publish what-ifs:** False (threshold 70)
- **Dynamics:** import_rate 1.0/wk, waning 8 wks (same as v1/v2, for comparability)
- **Cost:** $0.6345 — Spark usage: {'prompt_tokens': 22755, 'completion_tokens': 142603, 'calls': 60, 'fallbacks': 0}
- **Honest label:** v3: history-fitted kernel + Spark behavior with past-season context. The fit and the planner saw past seasons and the seed window only; the score is whatever the untouched 2024–25 holdout gave.
