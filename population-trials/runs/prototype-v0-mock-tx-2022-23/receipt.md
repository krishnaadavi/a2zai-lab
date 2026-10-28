# Population Trials — Receipt (prototype v0)

- **Run:** prototype-v0-mock-tx-2022-23 · 100 agents · model: mock (rule-based stand-in)
- **Data:** CDC ILINet, Texas, 2022-23 season, via Delphi epidata (verified pull, data/ilinet_tx_2022-23.csv)
- **Design:** pool seeded from the season's week-2 observation (wILI 5.41); simulated the next
  12 weeks it never saw — the window containing the real peak (wILI 9.88 @ 202245) —
  scored against reality by engine/calibrate.py. (v0's first cut seeded the season's tail
  by mistake; the window was corrected on methodology, kernel parameters untouched.)
- **Calibration score: 24.5 / 100**
  - curve shape 0.0/40 (Pearson r = -0.08)
  - peak timing 10.0/30 (peak off by 2 week(s))
  - magnitude 14.5/30 (sim/real mass ratio 0.303)
  - gate: none
- **May publish what-ifs:** False (threshold 70)
- **Cost:** $0.00 (mock model — plumbing proof, not a scientific result)
- **Honest label:** v0 exists to prove the pipeline end-to-end — data in, pool runs,
  holdout scored, receipt out. The science claim waits for the Spark-tier caller
  and the Dallas County DCHHS absence series as the calibration key.
