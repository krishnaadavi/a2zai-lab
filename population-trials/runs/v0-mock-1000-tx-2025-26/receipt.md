# Population Trials — Receipt (v0-mock-1000-tx-2025-26)

- **Run:** v0-mock-1000-tx-2025-26 · 1000 agents · model: mock (rule-based stand-in)
- **Data:** CDC ILINet via Delphi epidata, season file data/ilinet_tx_2025-26.csv (verified live pull)
- **Design:** pool seeded from the season's week-2 observation (wILI 2.07);
  simulated the next 15 weeks it never saw — window rule: through 4 weeks past the
  real peak (wILI 8.32 @ 202552) — scored against reality by engine/calibrate.py.
- **Calibration score: 19.5 / 100**
  - curve shape 0.0/40 (Pearson r = -0.563)
  - peak timing 0.0/30 (peak off by 9 week(s))
  - magnitude 19.5/30 (sim/real mass ratio 0.448)
  - gate: peak timing off by 9 weeks (>=3) — capped at 49
- **May publish what-ifs:** False (threshold 70)
- **Dynamics:** import_rate 0.0/wk, waning None wks (v0 defaults = off)
- **Cost:** $0.0000 (mock model — no API spend)
- **Honest label:** stand-in agents prove the pipeline at scale on real data.
  The flagship calibration key (Dallas County DCHHS absence series) is still to be wired.
