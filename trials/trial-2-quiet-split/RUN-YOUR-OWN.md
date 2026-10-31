# Run your own model on Trial #2 — "The Quiet Split" (v2)

This file is the operator's guide for running **your** agent against
this trial and getting a score you can trust. The contestant brief is
`README.md` at this folder's root — that, plus `task-pack/`, is the
exam. This file is everything around the exam.

## Step 1 — Seat your agent blind

Give your agent **only**:

- the contestant brief (the root `README.md` of this folder), and
- the four files in `task-pack/`: `invoices.csv`, `vendors.json`,
  `prior_invoices.csv`, `policy_excerpt.md`.

Nothing else in this folder may reach the agent — not this file, not
`VERIFICATION.md`, not `RESULTS.md`, not anything under `harness/`.
The Lab's own reference runs were produced exactly this way (prompt
assembled from the brief + task pack only), which is what makes the
scores comparable.

## Step 2 — Collect one decisions file

Your agent returns **one JSON file**: a list of exactly 30 decision
objects, one per invoice (I01–I30), in the shape specified in the
brief's "Your submission" section. The two files
`harness/baseline_linkaware.json` and `harness/baseline_naive.json`
are worked examples in exactly this format — use them to check your
file's *shape* (they are reference decision files, and reading their
contents before your run would, of course, spoil the exam for your
agent; keep them away from the agent itself).

## Step 3 — Check the file before you submit it

A malformed submission is rejected **before scoring** (the harness
exits with code 2 and names every error). Your file must satisfy:

- exactly I01–I30, each once;
- every `disposition` one of `AUTO_APPROVE`, `MANAGER_APPROVAL`,
  `FINANCE_ESCALATE`, `HOLD_VERIFY`, `REJECT`;
- every `rule_cited` one of `Q-1` … `Q-7` — a rule that is not in the
  policy excerpt is a compliance finding, not a style error;
- `evidence_fields` a list on every decision;
- `linked_case_id` either `null` or the same id shared by every
  invoice you intend as one case.

## Step 4 — Scoring is examiner-side, by design

The scorer and the answer key are **not in this package** — the same
arrangement as Trial #1, and the point of the Lab's integrity model:
contestants never see the key, and every published run ships its full
trace and score breakdown so results are auditable without it.

Concretely: `harness/runner.py` is the Lab's own harness, published so
you can read exactly how validation and trace generation work. It
imports the examiner-side scorer (`private/scorer.py`), so if you run
it from this package it stops with
`FileNotFoundError: ... private/scorer.py`. **That is expected — your
download is not broken, and no file is missing that should be here.**

To get an official score and a published trace for your run, send your
decisions file to the Lab via [a2zai.ai](https://a2zai.ai). Runs the
Lab scores are published in this folder's `harness/runs/` with the
full artifact set (decisions, trace, score, run meta, receipt).

## What you can verify yourself, right now

- `RESULTS.md` — the Lab's two examiner-side reference runs
  (Wonder 95.0/95 → 97.9/100; Spark 95.0/95 → 100.0/100) and the
  deterministic baselines that price specific errors.
- `harness/runs/` — complete artifacts for both reference runs and
  all six verification runs: the exact decisions each run made, the
  step-by-step trace, and the component-by-component score.
- `VERIFICATION.md` — the Lab's cold-run verification record: every
  documented baseline was reproduced exactly from these materials
  before any model ran.

## About `harness/drivers/`

These are the Lab's own run tools, published for audit — they are how
the reference runs were produced (`meta_driver.py` assembles the blind
prompt from the brief + task pack and calls the model;
`cost_time.py` applies the pinned cost/time rule; `meta_analyst.py`
writes the run receipts). Two honest caveats: the Meta driver expects
the examiner-side folder layout (it addresses this trial by its
examiner slug, `trial2b-quiet-split-v2`) and it hands scoring to the
same examiner-side harness above — so treat the drivers as a readable
record of method, not a turnkey runner. `replay.py` is Trial #1's
replay generator and does not render this trial's dispositions;
Trial #2 runs ship their `trace.json` as the replay source instead.

## Reporting your run's cost

If you publish your own run, report token counts and estimate cost
from published per-token rates, as the reference runs do. The final
/100 total uses the pinned rule — 5 × min(1, median run cost ÷ your
run's cost), median across the trial's real runs — so a cheaper run at
the same quality scores *higher*, which is the honest economics of
the thing.
