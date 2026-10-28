# Population Trials — Receipt (v1-spark-100-tx-2025-26)

- **Run:** v1-spark-100-tx-2025-26 · 100 agents · model: spark (rule-based stand-in)
- **Data:** CDC ILINet via Delphi epidata, season file data/ilinet_tx_2025-26.csv (verified live pull)
- **Design:** pool seeded from the season's week-2 observation (wILI 2.07);
  simulated the next 15 weeks it never saw — window rule: through 4 weeks past the
  real peak (wILI 8.32 @ 202552) — scored against reality by engine/calibrate.py.
- **Calibration score: 21.1 / 100**
  - curve shape 0.0/40 (Pearson r = -0.529)
  - peak timing 0.0/30 (peak off by 9 week(s))
  - magnitude 21.1/30 (sim/real mass ratio 0.506)
  - gate: peak timing off by 9 weeks (>=3) — capped at 49
- **May publish what-ifs:** False (threshold 70)
- **Dynamics:** import_rate 1.0/wk, waning 8 wks (v0 defaults = off)
- **Cost:** $0.3404 — Spark usage: {'prompt_tokens': 13935, 'completion_tokens': 75996, 'calls': 60, 'fallbacks': 0}
- **Honest label:** first real-model run; batched cohort-parameter design (see COSTS.md).
  The flagship calibration key (Dallas County DCHHS absence series) is still to be wired.
- **Correction (Oct 27, same evening):** the Run line above mislabels the model as
  "(rule-based stand-in)" — a template leftover from v0. The model was Muse Spark 1.3
  (60/60 planner calls answered, 0 fallbacks; usage and cost above are its real ones).
  Template fixed; the original line stands unedited, per Lab practice.
