# Population Trials + Lab — cost ledger

Krish's ask (Oct 27): document the costs. Two parts: the **model** (what a
run should cost, assumptions printed) and the **ledger** (what runs actually
cost, from receipts). Estimates never wear the clothes of actuals.

## Rates (verified Oct 26, Meta Model API)
- Muse Wonder 1.0: $4 / $20 per 1M tokens (in/out)
- Muse Spark 1.3: $1.25 / $4.25 per 1M tokens (in/out)
- Muse Glimmer: open weights — Modal GPU time instead of tokens
  (A100-40GB ≈ low single-digit $/run; measure at first deploy)

## The model (from the problem statement; assumptions stated)
- Agent-week decision, per-agent design: ~600 in / ~150 out tokens
  → ≈ $0.0014 on Spark-tier → 1,000 agents × 20 wks ≈ **$28/run**,
  5-run suite ≈ **$140** (≈ $450 worst case with ×3 reasoning headroom).
- **Batched design (v1, as built):** one Spark call per cohort per week
  returns that cohort's behavior parameters (4 cohorts × 15 wks = 60 calls,
  ~3–4k tokens each) → **≈ $0.50–1.50 per full season run**, any pool size.
  The trade: per-agent texture comes from traced sampling around cohort
  parameters, not 20,000 individual calls. Both designs stay documented;
  the ledger shows which one a run used.

## Credits inventory
- Meta Model API: **$150 hackathon credits claimed Oct 26**
- Modal: **$30/mo free tier** live; $100 hackathon-credit application pending

## Ledger — actuals
| Date | Run | Design | Cost | Notes |
|---|---|---|---|---|
| Oct 26 | Trial #1 — Wonder | per-run API | **$0.2709** | 18,266 tokens; scored 94.2/95 |
| Oct 26 | Trial #1 — Spark | per-run API | **$0.0548** | 17,068 tokens; scored 91.8/95 |
| Oct 26 | Trial #2 v2 — Wonder | per-run API | **$0.2144** | examiner-side; 95.0/95 |
| Oct 26 | Trial #2 v2 — Spark | per-run API | **$0.0380** | examiner-side; 95.0/95 |
| Oct 27 | Population v0 — 100 agents, mock | local kernel | **$0.00** | calibration 24.5/100 |
| Oct 27 | Population v0 — 1,000 agents, mock, TX fall 2025 | local kernel | **$0.00** | calibration 19.5/100; kernel wall time 0.19s |
| Oct 27 | Population v1 — Spark, batched, 100 agents, TX fall 2025 | cohort-week calls | **$0.3404** | 60 calls, 0 fallbacks; 13,935 in / 75,996 out tokens (reasoning dominates); calibration 21.1/100 |

## What we still don't know (measure, don't guess)
Per-call token distribution once agents carry memory; API wall-clock at
1,000-agent concurrency (per-agent design); Glimmer throughput on Modal.
Each gets measured on its first real run and lands in this ledger.
