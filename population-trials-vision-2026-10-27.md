# Population Trials — the 1,000-agent test bed (vision fleshed out Tue Oct 27, 2026)

The floor above the Lab. The Lab grades ONE agent on ONE job. Population Trials grade MANY
agents inside ONE simulated world, against what actually happened.

## The product in one line

Pick a real dataset, ask a real question, watch a pool of 1,000 agents live it out, and get
an analysis whose every claim carries a receipt — including the receipt for how well the
simulation reproduced reality in the first place.

## The design move that makes it a Lab, not a toy

A simulation that can't be checked is just an animated opinion. So the Lab rule carries over,
in a form built for time series: **temporal holdout scoring.**

1. **Calibration run first, scored.** The pool sees data up to week N only. It must reproduce
   the real season/curve/map for the weeks it never saw. That reproduction gets a published
   calibration score — how close the simulated curve lands to the real one.
2. **What-ifs only off a validated baseline.** Interventions (close schools a week, move a
   patrol beat, add a screening unit) are computed as deltas from the calibrated baseline.
   Every conclusion prints its calibration score next to it. No calibration, no analysis.

That's the same integrity pattern as Trial #1 — contestants see the task pack, never the
private key — with the key being *the future*, which nobody can peek at.

## The scenario catalog

### Population Trial #1 — The School Flu Season (flagship)
- **Data:** Dallas County Health and Human Services publishes the ideal calibration key:
  weekly syndromic flu visits from 18 Dallas County EDs AND student absences due to ILI by
  week for Dallas County schools (verified Oct 27 — see the verification addendum). CDC
  ILINet adds national weekly context (age bands including 5–24). Pulled from CDC FluView +
  DCHHS directly; no HF mirror of ILINet was found.
- **Agents:** households and schools in one county — kids, parents, teachers, each with a
  weekly decision loop (attend, stay home, vaccinate, seek care).
- **The question:** "What does a one-week school closure at peak do to pediatric ER load?"
- **Scored on:** the pool's curve vs. the real season's curve (calibration), then the
  closure deltas. Why it's the flagship: parents, superintendents, and newsrooms all
  instantly understand it — and a kids'-season sim is inherently shareable content.

### Population Trial #2 — The Crime Map
- **Data:** Chicago Crimes 2001–present (7.7M+ incident records, block-level for victim
  privacy, FBI Type I violent categories), also available in event-sequence form for
  temporal models. (Corrected Oct 27: an earlier draft's "2.7M" was an old subset.)
- **Agents:** patrol beats and neighborhood rhythms across a city grid.
- **The question:** "Where do hotspots move next month — and does moving a beat change it?"
- **Scored on:** spatial hit-rate of predicted hotspots vs. the actual next month's
  incidents. A real, computable, non-hand-wavy score. Every city reporter understands a
  hotspot map.

### Population Trial #3 — The Screening Gap (planning only, never patient advice)
- **Data:** State Cancer Profiles county-level incidence (11,048,853 incidence rows,
  verified exactly; cite statecancerprofiles.cancer.gov + the Zenodo archive — a Hugging
  Face mirror under that name could not be confirmed by opening it, Oct 27) —
  county-level, not patient-level, which is exactly why it fits.
- **Agents:** counties and health systems allocating scarce screening capacity.
- **The question:** "Where does one mobile screening unit a month close the most late-stage
  gap?" Framing discipline is designed in: population planning, never advice to any person.

### A fourth, in Krish's own domain (one line)
A bank-run simulation: depositors, rumor spread, and a liquidity line — the same
calibration-then-what-if machinery on financial panic. His Goldman/compliance moat, as a
Population Trial.

## How a visitor uses it

1. Pick a dataset and a question template (no code, no prompt engineering).
2. Watch the pool run — the replay view from Trial #1, scaled: a curve animating live as
   1,000 agents decide, week by week.
3. Get the analysis: headline numbers, the calibration score, the what-if deltas, and the
   trace bundle behind every number.
4. Share the receipt link. The analysis is only as good as its published calibration —
   which is also why it's shareable: anyone can check it.

## Why it's appealing (the cool factor, honestly stated)

- **It's a wind tunnel for decisions.** Choices that today take a consultancy six months
  and produce a PDF nobody can audit become a 20-minute public run with receipts.
- **Every run is content.** "Watch 1,000 agents live a flu season in 4 minutes" is a video
  people actually open — the flywheel feeds itself.
- **The moat carries over.** Datasets are commodity; HF hosts them for anyone. The craft
  is the same as Trial #1: scenario design by practitioners, calibration discipline, and
  attestation receipts. That's not copyable by downloading a CSV.

## Honest risks (designed in, not hand-waved)

- **Calibration is genuinely hard.** An uncalibrated sim that speaks confidently is worse
  than no sim. Mitigation: the calibration score is printed on every output, and below a
  threshold the Lab refuses to publish conclusions — it publishes the failure instead.
- **Dataset vetting per dataset.** License, freshness, suppression rules (cancer data
  suppresses small counts), and privacy level each get a dataset card before a trial ships.
- **Medical framing discipline.** Population planning only; any scenario that drifts toward
  individual advice is refused at the template level.
- **Compute economics.** The crowd runs on Spark-tier models; the analyst layer (the
  agents that interpret and write the report) runs on Wonder-tier. Same split the Lab
  already runs — the pool is cheap, the judgment is premium.

## Hackathon placement (unchanged)

Nov 4 submission stays the Lab (Trials #1 + #2, Glimmer, receipts). Population Trials is
the demo's closing beat and the post-window roadmap; the bounded prototype (flu school
season, 100 agents first — 1,000 is a config change once the harness holds) starts only
if Trial #2 publishes on schedule Sat Oct 31.
