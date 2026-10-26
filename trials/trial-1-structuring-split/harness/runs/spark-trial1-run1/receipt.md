# Receipt — Muse Spark (Meta Model API) on Trial #1 (model: muse-spark-1.3)
## The score — the total and the component breakdown, as numbers.
- subtotal_of_95: 91.8
- disposition_40: 36.8
- trap_20: 20.0
- citation_15: 15.0
- evidence_10: 10.0
- calibration_10: 10
- cost_time_5pts: UNSCORED (needs median across runs)
- hard_gates_triggered: []
## What the agent did — how it worked the queue, in a few sentences.
It worked through alerts from A01 to A25, giving each a disposition (its final decision of CLEAR meaning close as normal, MONITOR meaning keep watching, or ESCALATE meaning send for urgent human review). For routine salary and small-business receipts from A01 to A14 and for A24 it chose CLEAR with rule P-5 (the policy it says applies) and listed evidence (the customer and transaction records it used to justify the decision). For riskier activity it chose MONITOR for A15, A17, A18, A19 and ESCALATE for A16, A20, A21, A22, A23, A25, grouping A20, A21, A22, A23 together under CASE-1 (a shared investigation file).
## What it caught — correct escalations, links it made (use the trace's trap_rewind data if present), rules cited well.
It recorded ESCALATE for A16 with rule P-3, for A20, A21, A22, A23 with rule P-2 under CASE-1, and for A25 with rule P-4, with each rule citation (the policy it says applies) reflected in the score. For the link, the trace's trap_rewind (replay showing linked alerts belong together) lists linked_alerts A20, A21, A22, A23 with total_amount 38200 and the note replay moment: the linked cards merge into one case. The score records trap_20: 20.0, citation_15: 15.0, evidence_10: 10.0 and calibration_10: 10, where calibration means how well its confidence matches results and evidence means the records it used to justify each decision.
## What it missed — dispositions or links the score shows it lost points on; if it lost none, say so.
The score records disposition_40: 36.8, below the top implied by its name, so it lost points on dispositions (its CLEAR, MONITOR or ESCALATE decisions). It lost no points on links, citations, evidence or calibration according to trap_20: 20.0, citation_15: 15.0, evidence_10: 10.0 and calibration_10: 10. The documents provided do not name which alert or alerts caused the disposition loss, so no specific missed alert can be named from them.
## Gates — hard gate outcomes, per the rules above.
The run hit no hard gates (automatic fail rules that cap the score), as hard_gates_triggered is empty.
## The one-line verdict — a single sentence a reader could quote.
It cleared the routine work, connected the related cash alerts, and lost only a little on decision points.
