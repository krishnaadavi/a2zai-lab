# Population Trials — Problem Statement & Cost Model

Written Tue Oct 27, 2026, at Krish's ask. Companion to population-trials-vision-2026-10-27.md;
dataset facts per population-trials-dataset-verification-2026-10-27.md (where they differ,
the verification wins). Cost anchors are the Lab's own verified Trial #1 numbers.

## The problem

Every flu season, every county health department and school district in America answers the
same questions — when will it peak, do we close schools, where do we put the clinics — and
every city answers the same questions about crime — where will hotspots move, do we shift
patrols. The answers come from models: epidemiological models, forecasting tools, consultant
studies. Almost none of them can be checked.

- The model's assumptions are buried in a PDF appendix, if they exist at all.
- Nobody publishes how well the model reproduced last season before trusting it with this one.
- When the decision is wrong, there is no receipt — no record of what the model saw, what it
  assumed, or what it predicted, scored against what actually happened.

We built A2ZAI Lab to fix exactly this for AI agents doing professional work: a real job, a
checked answer key, public traces, a score. **Population Trials is the same fix for
population decisions**: the answer key is the future the model never saw, and the score —
how faithfully the simulation reproduced reality — is printed on every conclusion the
simulation is allowed to draw.

## The large use case (lead): county public health — the school flu season

- **The decision-makers:** ~3,000 county health departments and every school district that
  has ever had to decide, mid-season, whether a closure week helps or just moves the peak.
- **The data (verified):** Dallas County Health and Human Services publishes weekly
  syndromic flu visits from 18 Dallas County emergency departments AND "Percentage of
  Student Absences Due to ILI by Week" for Dallas County schools — a school-specific,
  county-level answer key in our home county. CDC ILINet provides the national weekly
  context, including the 5–24 age band. No Hugging Face mirror of ILINet was found; the
  pull is CDC FluView + DCHHS directly.
- **The trial:** 1,000 agents (households, schools, clinics) live a flu season week by week.
  Calibration first: seeded through week N, the pool must reproduce the real absence and
  ED curves for the weeks it never saw — scored. Only then: what does a one-week closure at
  the peak do? The delta is published next to the calibration score, or not published at all.
- **Why it's large:** this exact decision recurs every winter, in every county, and the
  current state of the art available to a mid-size district is a state PDF and a guess.

## The second use case: crime — the moving hotspot map

- **The data (verified):** Chicago Crimes 2001–present, 7.7M+ incident records, block-level
  (victim privacy preserved), updated continuously via the city data portal.
- **The trial:** agents model neighborhood rhythms and patrol allocation across a city grid.
  Scored on a number anyone can compute: what fraction of next month's actual incidents
  landed inside the predicted hotspots. Calibration discipline identical to flu — predict
  a month the pool never saw before advising on the month ahead.
- **Why it's large:** every mid-size city runs some version of this planning, and the
  outputs shape where police presence goes. An auditable forecast — assumptions, score,
  and receipts public — is a civic good, not just a product.

Third in line (same machinery): cancer screening allocation across counties, scored on
State Cancer Profiles incidence (11,048,853 county-level rows, NCI / Zenodo-archived) —
planning only, never patient advice.

## What does a 1,000-agent simulation actually cost? (documented, with assumptions)

Krish's worry, answered with our own numbers instead of vibes.

**Anchors (verified, Trial #1, Oct 26):** a full professional-judgment run — 25 items,
~18,000 tokens — cost $0.2709 on Muse Wonder and $0.0548 on Muse Spark. Published rates:
Spark $1.25 / $4.25 per 1M tokens (in/out); Wonder $4 / $20.

**Assumptions (printed, per Lab practice):** a population agent's weekly decision is a
small call — a compact persona + state card in, a short decision out: ~600 input + ~150
output tokens. A flu season = 20 weekly steps. A scenario suite = 1 calibration run +
4 what-if runs.

| Item | Math | Cost |
|---|---|---|
| One agent-week (Spark-tier) | 600×$1.25/1M + 150×$4.25/1M | ≈ $0.0014 |
| One 1,000-agent season run | 20,000 agent-weeks | **≈ $28** |
| Full scenario suite (calibration + 4 what-ifs) | 5 runs | **≈ $140** |
| Analyst layer (Wonder-tier synthesis, per run) | ~20k tokens | ≈ $0.16 |
| Reasoning-token headroom (our Day 1 lesson: reasoning eats budget — budget ×3) | suite × 3 | **≈ $450 worst case** |
| 100-agent prototype suite (the actual first build) | 2,000 agent-weeks × 5 | **≈ $14 (≈ $45 with headroom)** |
| Crime variant (1,000 agents × 30 daily steps) | 30,000 calls | ≈ $42/run, ~$210/suite |

**The self-hosted route (Glimmer on Modal):** one A10G-class GPU (~$1/hr class on Modal)
serving the 30B model with batched inference turns a 20,000-call run into roughly 1–3
GPU-hours — **single-digit dollars per run**. The API route is zero-setup; the Glimmer
route is 10–50× cheaper per run once serving is up. Both are small money.

**Conclusion:** the simulation does not cost a lot. A full county flu suite ≈ the $150 of
Meta credits already claimed; the prototype ≈ a rounding error on the $30 Modal free tier.
**The real cost is calibration design** — building a pool whose behavior deserves to be
scored against reality. That is a craft problem, not a compute bill, and it is the same
craft Trial #1 already exercises.

**Still to learn by doing (the point of documenting):** the real per-call token
distribution once agents carry memory, retry/failure rates at 1,000-agent concurrency,
wall-clock per run (parallelism limits on the API), and Glimmer throughput on Modal.
Each is measured on the 100-agent prototype before any 1,000-agent claim is made publicly.

## Placement

Unchanged: the Nov 4 hackathon submission is the Lab (Trial #1, Trial #2, Glimmer).
Population Trials is the demo's closing beat and the first post-window build, prototype
gated on Trial #2 publishing Sat Oct 31. This document is the problem statement for that
build — and, lightly edited, for the demo script and the roadmap page.
