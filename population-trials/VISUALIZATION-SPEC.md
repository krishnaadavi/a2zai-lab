# Population Trials — the surface: run it, watch it, audit it

Krish approved the picture Oct 27: a 1,000-agent season run, trace recorded
as an animation video. This spec is what gets built; the engine + scorer
already exist (`engine/`, `run_prototype.py`).

## Three panes (one Lab page, `/lab/population-trials`)

**1. Run a simulation**
Pick dataset + season + place (ILINet TX flu 2022-23 first), pick the
question template (peak-week school closure; clinic surge), pool size
100 → 1,000, model tier. **The price prints before the run starts** — the
cost model's estimate ($-per-run) sits next to the button. No run happens
without its estimate shown; that's Lab manners.

**2. View a simulation (the animation — this is the video)**
A county grid: school catchments as cells, 1,000 agent dots colored by
state (susceptible / infected / recovered; for crime: heat building on
the map week over week). Playback unrolls the holdout: the simulated curve
draws itself while the real curve draws next to it, and the calibration
score assembles live as the gap between them resolves. End frame: final
score + gate verdict. Recorded at 1,000 agents, this animation IS the
demo asset and the shareable clip — a scored simulation you can watch
pass or fail in 60 seconds.

**3. View the trace**
Click a week → the pool's aggregate state + sampled agent decisions with
their state cards (what the pool "saw" and did that week). Click an agent
dot → its season story, decision by decision. Same receipt discipline as
Trial #1 traces, at population scale.

## What it proves (in order)
1. A cheap agent pool can **reproduce a real season it never saw** —
   scored against reality, not asserted.
2. Only then do its what-if deltas deserve a hearing — and the
   calibration score travels printed on every delta.
3. The whole chain is auditable: data-pull receipt (source, query,
   timestamp, row count) → run trace → score → published conclusion.

## Build order from here
1. v1 engine: Spark-tier caller on the existing model contract (batched
   per cohort-week; per-agent decisions for the traced sample) + the
   a priori dynamics v0's failure diagnosed (imported-case reseeding,
   non-permanent immunity) — decided before scores, printed in params.
2. The 1,000-agent season run (est. ~$28 API; wall-clock measured, not
   promised).
3. Replay renderer for population traces (extends the Lab's replay
   concept) → record the animation.
4. DCHHS school-absence loader → the flagship calibration key.
