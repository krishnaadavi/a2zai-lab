# Receipt — Muse Spark (Meta Model API) on Trial #2 v2 (model: muse-spark-1.3)
## The score — the total and the component breakdown, as numbers.
subtotal_of_95 (total before time bonus — overall points): 95.0
- disposition_40 (handling choices — the final decision on each invoice): 40.0
- trap_20 (spotting split bills — linked invoices that together evade a limit): 20.0
- citation_15 (naming the correct rule — the Q-label for each decision): 15.0
- evidence_10 (listing supporting facts — the details backing each decision): 10.0
- calibration_10 (confidence matching correctness — how well certainty fits results): 10.0
- cost_time_5pts: UNSCORED (needs median across runs)
## What the agent did — how it worked the queue, in a few sentences.
It worked the queue from I01 through I30, giving each invoice a disposition (final handling choice) with a rule cited (Q-label — the policy tag for the decision) and evidence fields (supporting facts — the details backing the choice). It used AUTO_APPROVE (automatic approval) for trusted small buys such as I01, I06 and I07, MANAGER_APPROVAL (manager sign-off) for mid-size buys such as I04, I05 and I12, and FINANCE_ESCALATE (senior finance review) for high-risk buys such as I19. It also paused I10 with HOLD_VERIFY (temporary hold to check details) for a bank-detail change and turned down I22 with REJECT (refusal as duplicate) as a repeat of I17.
## What it caught — correct escalations, links it made (use the trace's trap_rewind data if present), rules cited well.
It sent for FINANCE_ESCALATE (senior finance review) the split-bill pattern (breaking a large need into smaller invoices to stay under a limit) in CASE-1 (linked case — invoices grouped as one review) linking I02, I08, I11 and I15 with total_amount 17888, and in CASE-2 linking I03 and I09 with total_amount 9650, both carrying the trace note that the linked cards merge into one case. It also caught the bank-detail change on I10 with rule cited Q-4, the duplicate on I22 with rule cited Q-5 where PO PO-OM-552 matches I17, and the high-risk buy on I19, while citing Q-1 for small approvals, Q-2 for manager approvals, Q-3 for split-bill escalations, and Q-6 and Q-7 where those rules applied, consistent with citation_15: 15.0 and evidence_10: 10.0.
## What it missed — dispositions or links the score shows it lost points on; if it lost none, say so.
It lost no points on dispositions or links, as shown by disposition_40: 40.0 and trap_20: 20.0, with no missed handling choices or grouped cases left unlinked.
## Gates — hard gate outcomes, per the rules above.
The run hit no hard gates (automatic fail-safes — rules that cap the score when triggered), with hard_gates_triggered empty.
## The one-line verdict — a single sentence a reader could quote.
A clean run that linked the split bills, protected the bank-change and duplicate checks, and cited every rule correctly.
