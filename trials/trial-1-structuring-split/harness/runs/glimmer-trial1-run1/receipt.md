# Receipt — Muse Glimmer 30B (open weights, via Together AI) on Trial #1 (model: meta-models/Muse-Glimmer-30B)
## The score — the total and the component breakdown, as numbers.
- status: REJECTED PRE-SCORING — no score was awarded
- subtotal_of_95: not scored
- disposition_40: not scored
- trap_20: not scored
- citation_15: not scored
- evidence_10: not scored
- calibration_10: not scored
- cost_time_5pts: not scored
- hard_gates_triggered: none evaluated (gates apply to scored submissions)
## What the agent did — how it worked the queue, in a few sentences.
It began working the queue in order and produced complete, well-formed decisions for A01 through A08 — all CLEAR under rule P-5, each with evidence fields and a one-sentence reason — and started A09. The response then stopped mid-sentence inside A09's evidence list. The full raw output is preserved in raw_response.txt (3,481 characters). Alerts A10–A25 never appear in the response at all.
## What it caught — correct escalations, links it made, rules cited well.
Nothing can be credited: the submission was never scored, so no catches, links or citations were evaluated. The eight completed decisions (A01–A08) are visible in the raw response for anyone to read, but the Lab does not grade partial, unparseable submissions — that is the point of the harness.
## What it missed — dispositions or links the score shows it lost points on.
The submission itself. Together AI returned HTTP 200 with max_tokens set to 16,000, but the response body ended abruptly at 3,481 characters ("...counterparty Register sales", "ledger 202 — cut off). The harness's parser failed with a JSON error (Expecting ',' delimiter at char 3198), no decisions file was written, and the run ended there. Its answers were not hand-fixed and no second attempt was made: under Lab rules a retry is for transport failures, and this was not one — the model/API returned an incomplete answer.
## Gates — hard gate outcomes, per the rules above.
No gates were triggered or evaluated. The score caps (59 for a missed structuring link, 39 for clearing a watchlist alert) apply to scored submissions; this run never reached the scorer.
## The one-line verdict — a single sentence a reader could quote.
The Lab's first open-weights entrant never finished the exam — its answer sheet tore off a third of the way through, and the harness published the tear instead of a grade.


---
**Correction (Oct 28, 2026):** the run's finish_reason was `length` — the 16,000-token completion budget ran out with only ~870 visible tokens emitted, most plausibly spent on reasoning tokens before the JSON finished (the Day 1 Meta API pitfall, on Together's serving). The rejection stands as recorded; this note only sharpens the cause.
