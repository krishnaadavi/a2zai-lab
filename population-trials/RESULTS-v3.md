# Population Trials v3 — Results: the Dallas County calibration run
### Run Sat Oct 31, 2026 · Status: mock pipeline check COMPLETE · Spark runs BLOCKED on an environment policy (see §5)

**Dataset:** DCHHS Dallas County student-absence ILI % (primary source:
DCHHS Influenza Surveillance Reports, Figure 4 vector extraction; pull
receipt in every run bundle). **Target:** 2024–25, held out. **History:**
2018–19, 2022–23, 2023–24, shown to the pool in full.

---

## 1. The design (locked before any score)

Same seed-fit lineage as v2, one change under test: **where the fit
learns from.** v2 grid-fit the kernel's `base_transmission` — the only
fitted parameter, as in v2 — on a flat 4-week seed window of the target
season. v3 fits it on **history**: per past season, the same grid
(0.002–0.060, mock behavior as the fitting instrument) minimizes SSE
against that season's **full remaining curve**, so the acceleration
phase is inside the fit objective. β_v3 = median of the three winners,
per pool size, frozen. The 2024–25 information set stays v2-disciplined:
the pool sees only its first 4 observed weeks (epiweeks 40–43:
0.035 / 0.038 / 0.082 / 0.028) plus the past seasons. The holdout — the
15 reported weeks after the seed window, through 4 weeks past the real
peak (0.512% @ epiweek 202505) — was read by nobody until scoring.
Scorer: `engine/calibrate.py`, unchanged. Gate: peak miss ≥3 weeks caps
at 49; ≥70 unlocks what-ifs.

**Flagged points:** the six `suspected_no_report_plotted_as_zero`
points (2022–23 wks 5, 11 · 2023–24 wks 47, 52, 11 · 2024–25 wk 11) are
no-report weeks the chart drew at zero. They were **dropped from every
curve — fit, seed, holdout, scoring — treated as the gaps they are**.
Gaps were never filled; one sim step = one reported week. (The 2024–25
wk-11 point sits after the peak, so the drop cannot flatter the peak
timing score either way.)

## 2. What the history fit actually did — the run's real finding

Per-season winners, both pool sizes:

| Past season | Real peak | β winner (100 agents) | β winner (1,000 agents) |
|---|---|---|---|
| 2018–19 | 1.005% @ wk 6 | 0.002 | 0.002 |
| 2022–23 | 0.227% @ wk 46 | 0.002 | 0.002 |
| 2023–24 | 0.297% @ wk 4 | 0.002 | 0.002 |
| **β_v3 (median)** | | **0.002** | **0.002** |

Every season, every pool size: **the grid floor.** Not a fit failure —
a measurement. Diagnostics (recorded in the working notes, reproducible
from `run_v3.py`): at DCHHS scale this kernel has exactly two regimes.
Seeded at ~0.03% prevalence with the v1/v2 import floor (1.0/wk) and
reporting fraction (0.30), it either **never ignites** (flat at the
import floor, 0.03%/wk at 1,000 agents) or **ignites and overshoots by
an order of magnitude** — β=0.022 from a 0.027% seed produces a ~4.3%
peak against a real-world maximum of 1.005%. Full-curve SSE, shown the
whole season including its peak, therefore prefers no ignition at all:
any β that reaches the real peak's *timing* blows through its
*magnitude* ten times over.

## 3. Scores

| Run | Score | Shape /40 | Peak timing /30 | Magnitude /30 | Peak miss | Gate | What-ifs |
|---|---|---|---|---|---|---|---|
| v3 mock, 100 agents (pipeline check) | **20.6** | 0.0 (r = 0.0 — constant curve) | 0.0 | 20.6 (mass ratio 2.06) | 10 wks | capped at 49 | **LOCKED** |
| v3 Spark, 100 agents | — pending, §5 — | | | | | | |
| v3 Spark, 1,000 agents | — pending, §5 — | | | | | | |

Mock detail: with β at the floor and rule-based behavior, the pool sits
at its quantization floor (0.300%/wk at 100 agents — one imported case
per week × the reporting fraction) for all 15 holdout weeks while
reality climbs 0.028 → 0.512 → 0.092. Receipt: `runs/v3-mock-100-dchhs-2024-25/`.

## 4. The v3 question, answered

*Did multi-season shape-teaching fix v2's flaw — a flat seed window that
can't see later acceleration?*

**The flaw is real, but on this dataset it is not the binding
constraint — so no, teaching the shape could not fix the score, and the
fit itself proves why.** v2's problem statement assumed the information
was the bottleneck: give the kernel the season's shape and the right β
would follow. v3 gave the fit *perfect* shape information — three
complete seasons, acceleration phases included — and the best β in the
grid was still "don't ignite." The bottleneck moved: **the kernel's
scale constants, carried unchanged from the ILINet design (peaks
2–8%), cannot express a sub-1% season at any β.** A parameter that only
controls *whether* the epidemic explodes cannot fit a season whose
whole story is *how gently* it rises.

That is a sharper result than a score bump would have been, and it
names the v4 question precisely: re-derive the kernel's scale for the
absence series (reporting fraction and import floor are the suspects),
or fit a scale parameter alongside β. Stated here as a question —
**not** tuned in v3, because a design changed after seeing the fit is
a design fitted to the answer.

**Gate verdict (unchanged by any of this): calibration < 70 →
what-ifs stay LOCKED.** The Lab publishes this failure, not
conclusions — same as 24.5, 21.1, 17.2, and 17.3 before it.

## 5. Execution status — read this before citing §3

- **Mock pipeline check: complete** (cost $0.00), bundle published.
- **Spark runs: NOT YET EXECUTED.** The subagent session that ran v3
  hit an environment policy block — `POST /v1/chat/completions` to
  api.meta.ai returned `403 policy_denied
  (proactivity_read_only_preparation)` — a restriction on that
  session, not on the code, the credentials, or the design (the same
  transport carried every v1/v2 run). The Spark planner calls could
  not be made from that session, and no Spark numbers exist. §3 will
  be completed — and this file amended with a dated note, never
  silently rewritten — when the runs execute from an unrestricted
  session:
  - `python3 run_v3.py --agents 100 --model spark --run-name v3-spark-100-dchhs-2024-25`
  - `python3 run_v3.py --agents 1000 --model spark --run-name v3-spark-1000-dchhs-2024-25`
  Expected cost ≈ $0.33/run at v2's token profile. β is already frozen
  (0.002 at both pool sizes) and the holdout is untouched, so the
  design's integrity does not depend on when the calls are made.
- **Cost so far: $0.00.**
