# A2ZAI Lab — a driving test for AI agents

**The problem:** AI agents now do real work everywhere, but nobody can verify
an agent did the job well. Demos are staged, benchmarks get gamed, receipts
don't exist.

**A2ZAI Lab is the trust layer.** Agents take exams built from real work,
graded against a checked answer key, with scores and full evidence published.
A driving test for AI agents.

Built by [Krish Adavi](https://www.linkedin.com/in/krishadavi) —
previously an engineering manager at AWS Security and Goldman Sachs
(security applications, banking compliance and risk), and a real-money
trader. These exams come from work he knows firsthand.

🌐 [a2zai.ai](https://a2zai.ai) · 📰 [AI Systems Brief](https://www.linkedin.com/newsletters/ai-systems-brief-7461477781760294912/) — a weekly newsletter on AI systems

## Trial #1 — "The Structuring Split" (AML alert triage)

An agent works a bank's AML alert queue: **25 alerts**, and for each one a
decision — CLEAR, MONITOR, or ESCALATE — with a cited rule (P-1…P-5) and an
evidence trail. Hidden in the queue: one money-laundering pattern split
across four deposits, engineered so that judging each alert alone misses it.

- **The exam:** [`trials/trial-1-structuring-split/`](trials/trial-1-structuring-split/) — brief, task pack, harness
- **Scoring (of 100):** disposition 40 · trap detection 20 · rule citation 15 ·
  evidence trail 10 · calibration 10 · cost/time 5
- **Hard gates:** miss the linked pattern and the score caps at **59/95**;
  clear a watchlist alert and it caps at **39/95**. (Cost/time's 5 points stay
  unscored until multiple real runs set a median.)
- **Verified reference baselines** (deterministic decision files, *not* model
  runs — they prove the pipeline and set the floor and ceiling real runs are
  read against): link-aware **95.0/95**, per-alert naive **59/95**. Receipts in
  `trials/trial-1-structuring-split/harness/runs/` and `VERIFICATION.md`.

## Run an agent on it

Contestants receive **only** `task-pack/` (alerts, customer profiles, a
90-day ledger, the policy excerpt) and return one JSON file of 25 decisions.

```sh
cd trials/trial-1-structuring-split/harness
python3 runner.py <decisions.json> --agent <name> --model <id> --tokens <n> --out runs/<name>
```

The runner validates the submission (malformed files are rejected before
scoring) and writes a replay-ready `trace.json` plus a `score.json`.

## Integrity

- The scorer and answer key stay **examiner-side** and are not in this repo.
  Contestants never see them; every published run ships its full trace and
  score breakdown, so results are auditable without the key.
- Scores in posts and on the leaderboard come only from runs executed
  through this harness.

## Verify a receipt

Every published run carries an `attestation.json` — SHA-256 fingerprints of
the run's canonical artifacts (`decisions.json`, `score.json`,
`final_score.json`, `run_meta.json`; a rejected run attests its
`raw_response.txt` + `rejection.json` instead). Check that the published
decisions and score are the harness's original bytes:

```bash
python3 tools/verify_receipt.py trials/trial-1-structuring-split/harness/runs/glimmer-trial1-run2
# OK glimmer-trial1-run2: attestation verified (final score 98.4, 4 files, attestation 7dc5f65dc6...)
```

Exit code 0 means every attested file matches; a mismatch fails and names
the file. How the scheme works — and what it does and doesn't prove — is in
[ATTESTATION.md](ATTESTATION.md).

## DriftCheck

The Lab re-seats published entrants on the same exams, under the same
conditions, and records what changes — a model can change after its score
is published. A single re-sitting is an observation, not a verdict: on
Oct 28 one Spark re-run flipped three alerts against its published
baseline, so on Oct 30 the watch ran a hardening study — Spark ×10
sittings, Wonder ×3 as a control, $1.2190 in total. Verdict: **no
persistent drift**. Seven of nine scored Spark sittings reproduced the
published board exactly, and the flip is a sporadic draw (ESCALATE counts:
A15 2/9, A17 2/9, A19 1/9). Drift verdicts now come only from
distributions over repeated sittings, against thresholds set before the
runs. The full record is in [driftcheck/LEDGER.md](driftcheck/LEDGER.md);
the study report and per-sitting artifacts are in
`driftcheck/study-2026-10-30/` and verify with the same receipt tool
above.

## Results — Trial #1

| Run | Model | Score | Notes |
|---|---|---|---|
| Reference (link-aware) | deterministic | 95.0/95 | ceiling — hand-built, not a model run |
| Reference (naive) | deterministic | 59/95 | floor — judges each alert alone, link missed |
| **wonder-trial1-run1** (Oct 26, 2026) | **Muse Wonder** (`muse-wonder-1.0`, Meta Model API) | **95.2/100** (94.2/95 + 1.0 cost/time) | first real model run — trap linked, no gates hit; final recomputed Oct 28 under the pinned rule when a third run joined the board (see cost/time note) |
| **spark-trial1-run1** (Oct 26, 2026) | **Muse Spark** (`muse-spark-1.3`, Meta Model API) | **96.8/100** (91.8/95 + 5.0 cost/time) | trap linked, no gates hit — at ~1/5 of Wonder's cost |
| **glimmer-trial1-run1** (Oct 28, 2026) | **Muse Glimmer 30B** (open weights, via Together AI) | **rejected pre-scoring** | response truncated mid-JSON at A09 (3,481 chars of a 25-alert answer); harness published the rejection, not a grade — raw output + receipt in the run folder |
| **glimmer-trial1-run2** (Oct 28, 2026) | **Muse Glimmer 30B** (open weights, via Together AI) | **98.4/100** (93.4/95 + 5.0 cost/time) | budget-fix rerun, 64k cap — Run 1's 16k budget was consumed by reasoning tokens; at 64k the answer finished: trap linked 20/20, no gates, $0.0289/run — cheapest seat on the board |

Head-to-head, same exam, same conditions: Wonder 94.2 (disposition 39.2/40)
vs Spark 91.8 (disposition 36.8/40) on the 95 scorable points. Both linked
the structuring trap for 20/20 and maxed citation, evidence and calibration.
The whole quality gap is disposition judgment on routine alerts. Spark's run
cost ~$0.05 against Wonder's ~$0.27 — the workhorse is nearly as accurate
for a fifth of the price. Glimmer's budget-fix rerun landed between them on
the 95 — 93.4 (disposition 38.4/40), trap linked 20/20, everything else
maxed — and at $0.0289 it is the cheapest run on the board.

**Cost/time rule — pinned Oct 26, 2026, before any points were awarded:**
points = 5 × min(1, median run cost ÷ this run's cost), with cost estimated
from published per-token rates and the median taken across real model runs
of the trial. The median is defined over the runs on the board, so it moves
as runs join: across the first two runs it was $0.1628 (Wonder 3.0 →
97.2/100, Spark 5.0 → 96.8/100); when Glimmer's scored rerun joined on
Oct 28 the median across the three real runs became $0.0548 and every
final was recomputed by the same pinned rule — Glimmer earns the full 5.0
(**98.4/100**), Spark the full 5.0 (**96.8/100**), Wonder 1.0
(**95.2/100**). The 95-point quality ranking never moved (Wonder 94.2 >
Glimmer 93.4 > Spark 91.8); the cost column is what reorders the board,
which is the honest economics of the thing. Each run's `final_score.json`
shows its own arithmetic. Full artifacts —
decisions, trace, score, run meta, and the Spark-written receipt — in
[`trials/trial-1-structuring-split/harness/runs/`](trials/trial-1-structuring-split/harness/runs/).

## Results — Trial #3 (held-out)

Trial #3 is the Lab's first **held-out** exam — a trade-surveillance alert
queue, in a domain neither prior trial touched. Its task pack and answer
key **never publish**: a held-out score is one a contestant could not
prepare for, which is exactly what makes it the paid tier of the Lab.
What publishes is the score record — run meta, final score, and a redacted
receipt per entrant in
[`trials/trial-3-held-out/`](trials/trial-3-held-out/) — with no alert
identifiers, instruments, accounts, queue amounts, or rule-by-rule mapping.

Same rubric and gates as every Lab trial (disposition 40 · trap 20 ·
citation 15 · evidence 10 · calibration 10 · cost/time 5; miss the linked
pattern → cap 59; clear the never-clear alert → cap 39). Examiner-side
reference points, verified before any model ran: link-aware **95.0/95**,
per-alert naive **capped at 59**, restricted-clear variant **capped at 39**.

| Run | Model | Score | Notes |
|---|---|---|---|
| **glimmer-trial3-run1** (Oct 28, 2026) | **Muse Glimmer 30B** (open weights, via Together AI) | **100.0/100** (95.0/95 + 5.0 cost/time) | trap linked 20/20, no gates — cheapest run of the three at $0.0170 |
| **spark-trial3-run1** (Oct 28, 2026) | **Muse Spark** (`muse-spark-1.3`, Meta Model API) | **100.0/100** (95.0/95 + 5.0 cost/time) | trap linked 20/20, no gates — $0.0381, the three-run median |
| **wonder-trial3-run1** (Oct 28, 2026) | **Muse Wonder** (`muse-wonder-1.0`, Meta Model API) | **95.9/100** (95.0/95 + 0.9 cost/time) | trap linked 20/20, no gates — same perfect rubric, priced at $0.2184 |

The honest read: all three entrants maxed the 95 — every disposition,
the link, citations, evidence, calibration. On a held-out queue none of
them had seen, quality did not separate them; cost did, and the pinned
cost/time rule (median $0.0381) is the whole difference between 95.9 and
100.0. A rubric that three model classes all max is a rubric due for a
harder revision — that is a finding about the exam, published the same
way as the scores.

## Entrants this week

- **Claude** — frontier reference run
- **Muse Wonder** (Meta Model API) — Meta's frontier model sits the exam
  as an entrant, blind, under the same contract as everyone else
- **Muse Spark 1.3** (Meta Model API) — a Meta model inside the machine:
  the Lab's trace analyst, turning raw runs into published failure
  receipts. Its driver and the Wonder contestant driver live in
  [`trials/trial-1-structuring-split/harness/drivers/`](trials/trial-1-structuring-split/harness/drivers/)
- **Muse Glimmer 30B** — open-weights entrant, served by Together AI
  (serverless FP8). Sat Trial #1 on Oct 28, 2026: its first submission was
  rejected pre-scoring (truncated response) — the rejection receipt is
  published with the other runs, because a lab that only publishes passes
  is a demo. Its budget-fix rerun the same day (64k cap, labeled as the
  fix) finished the exam at 93.4/95 and tops the board at 98.4/100 on the
  cost rule
- Trial #2 — "The Quiet Split" (payment-approval fraud) — in build

## Built for the Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026)

**Built during the event:** the public Lab (this repo's runs, traces,
leaderboard, and the `/lab` page — source in [`web/`](web/)), the Meta Model
API driver, the trace-analyst loop, Trial #2, and every model run.

**Pre-existing, stated plainly:** the [a2zai.ai](https://a2zai.ai) platform,
and Trial #1's task pack, scorer, and harness — built Oct 18–23, 2026 as
preparation, before the event window. Only in-window work is claimed as the
hackathon build.
