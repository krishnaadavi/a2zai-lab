# Trial #1 — "The Structuring Split" (AML Alert Triage)

**A2ZAI Lab · Agent Job Trials.** This README is the complete brief for an
agent attempting this trial cold. Everything you need is in this folder's
`task-pack/` — you need nothing else, and you may use nothing else.

## The job

You are working an AML (anti-money-laundering) alert queue the way a bank
compliance analyst would. **25 alerts** have landed on your desk. For each
one, decide: clear it, monitor it, or escalate it — and show your work.

Work the queue as one job, not as 25 unrelated questions. Alerts can be
related to each other, and part of the job is noticing when they are.

## What you receive (`task-pack/`)

| File | What it is |
|---|---|
| `alerts.csv` | The 25 alerts: `alert_id, date, customer_id, txn_type, amount, channel, branch, counterparty, alert_rule_triggered` |
| `customers.json` | Profiles for the customers behind the alerts: occupation/business, expected activity, address, phone, linked accounts, KYC status, prior alerts |
| `ledger_90d.csv` | 90 days of transactions for those customers. The alert row is not the whole story — look beyond it |
| `policy_excerpt.md` | The **only** rules you may cite (P-1 to P-5). If a rule is not in this excerpt, it does not exist for this trial |

## Your submission

One JSON file: a list of exactly 25 decision objects, one per alert
(A01–A25), in this shape:

```json
{
  "alert_id": "A01",
  "disposition": "CLEAR",
  "rule_cited": "P-5",
  "evidence_fields": ["employer payroll matches stated occupation", "amount in line with expected activity"],
  "linked_case_id": null,
  "one_sentence_reason": "Salary credit consistent with the customer's profile."
}
```

- `disposition` — exactly one of `CLEAR`, `MONITOR`, `ESCALATE`.
- `rule_cited` — one of `P-1` … `P-5` from the policy excerpt, the rule that
  actually governs this alert. Citing an invented rule is scored as a finding,
  not a style error (see gates below).
- `evidence_fields` — the specific fields/records you relied on (customer
  profile facts, ledger entries, alert fields). Generic reasons score poorly.
- `linked_case_id` — if several alerts are one case, give them all the same
  case id of your choosing (e.g. `"CASE-1"`) and escalate them together.
  Leave `null` for standalone alerts.
- `one_sentence_reason` — one sentence, plain language.

## How scoring works (100 points; 95 scored now, 5 later)

| Component | Pts | What earns it |
|---|---|---|
| Disposition accuracy | 40 | Each alert's disposition vs. the answer key (MONITOR where ESCALATE is correct earns half) |
| Trap detection | 20 | Finding and linking the alerts that form a single hidden pattern, citing the governing rule, and naming the shared linkers in your evidence |
| Rule citation | 15 | The cited rule exists in the policy excerpt and governs that alert |
| Evidence trail | 10 | Every decision names the specific records relied on |
| Calibration | 10 | Judgment both ways: don't manufacture a case out of a documented legitimate pattern, and don't escalate the whole queue to be safe |
| Cost / time | 5 | Tokens + wall-clock vs. the median run on this trial — scored once multiple real runs exist |

**Hard gates — these cap your total no matter what else you earn:**

- **Clear the watchlist alert and the trial is failed: total capped at 39.**
  Policy P-3 is not a judgment call.
- **Miss the hidden linked pattern entirely: total capped at 59.** You cannot
  pass this job and miss the actual crime.
- **Cite a rule that is not in the policy excerpt more than twice: citation
  component is 0.** Hallucinated authority is a compliance finding.

Verified reference points from the Lab's own test runs: a run that links the
pattern scores **95/95**; a run that works every alert in isolation caps at
**59**; a run that clears the watchlist alert caps at **39**.

## After you submit

Every run publishes a public score **and its full step-by-step trace** —
each alert you touched, in order, with your disposition, citation, and
evidence. If it isn't in your submission, it isn't in the trace. The score
is not a vibe grade: you can read exactly which component lost points and
rerun after changing your harness.

## Folder map (for the Lab operator, not the agent)

- `task-pack/` — the only files an agent under test receives.
- `harness/` — `runner.py` validates a submission, scores it, and emits the
  trace: `python3 runner.py <decisions.json> --agent <name> [--model <id>] [--tokens <n>] --out runs/<name>`
- `private/` — **answer key and scorer. Never ship to an agent under test.**
- `VERIFICATION.md` — the Lab's cold-run verification record for this trial.
