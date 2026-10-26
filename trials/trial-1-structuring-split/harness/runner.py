#!/usr/bin/env python3
"""Trial #1 run harness (Week 2 pull-forward, built 2026-10-18).

Takes ANY agent decision file in the spec's output contract, validates it,
scores it with the deterministic scorer, and emits a replay-ready trace JSON
(alert cards in order, trap-link event, score reveal) that the Week 2/3 replay
template consumes. Model-agnostic: a real LLM run just has to produce the
same decision-file shape.

Usage: runner.py <decisions.json> --agent <name> [--model <id>] [--tokens N] --out <dir>
Output contract per decision: {"alert_id","disposition","rule_cited",
"evidence_fields":[...], "linked_case_id": optional}
"""
import argparse, importlib.util, json, sys, time, csv, pathlib
BASE = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("scorer", BASE/"private"/"scorer.py")
scorer = importlib.util.module_from_spec(spec); spec.loader.exec_module(scorer)
VALID_DISP = {"CLEAR","ESCALATE","MONITOR"}
VALID_RULES = {"P-1","P-2","P-3","P-4","P-5"}

def validate(decisions):
    errs = []
    if not isinstance(decisions, list): return ["top level must be a list of decisions"]
    ids = [d.get("alert_id") for d in decisions]
    want = [f"A{i:02d}" for i in range(1,26)]
    if sorted(ids) != want: errs.append(f"must cover exactly A01-A25 once; got {sorted(set(ids))} (n={len(ids)})")
    for d in decisions:
        if str(d.get("disposition","")).upper() not in VALID_DISP: errs.append(f"{d.get('alert_id')}: bad disposition {d.get('disposition')!r}")
        r = (d.get("rule_cited") or "").strip().upper()
        if r and r not in VALID_RULES: errs.append(f"{d.get('alert_id')}: rule_cited {r!r} not in P-1..P-5 (invented rules zero the citation component)")
        if not isinstance(d.get("evidence_fields", []), list): errs.append(f"{d.get('alert_id')}: evidence_fields must be a list")
    return errs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decisions"); ap.add_argument("--agent", required=True)
    ap.add_argument("--model", default=None); ap.add_argument("--tokens", type=int, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    decisions = json.load(open(a.decisions))
    errs = validate(decisions)
    if errs:
        print(json.dumps({"ok": False, "validation_errors": errs}, indent=2)); sys.exit(2)
    alerts = {r["alert_id"]: r for r in csv.DictReader(open(BASE/"task-pack"/"alerts.csv"))}
    t0 = time.time(); result = scorer.score(decisions); elapsed = round(time.time()-t0, 4)
    by_id = {d["alert_id"]: d for d in decisions}
    steps = []
    for aid in sorted(by_id):
        d, al = by_id[aid], alerts[aid]
        steps.append({"alert_id": aid, "card": {"date": al["date"], "amount": int(al["amount"]),
            "txn_type": al["txn_type"], "branch": al["branch"], "trigger": al["alert_rule_triggered"]},
            "disposition": d["disposition"].upper(), "rule_cited": (d.get("rule_cited") or "").upper() or None,
            "evidence_fields": d.get("evidence_fields", []), "linked_case_id": d.get("linked_case_id")})
    linked = [s["alert_id"] for s in steps if s["linked_case_id"]]
    trace = {"trial": "trial1-structuring-split", "run": {"agent": a.agent, "model": a.model,
             "tokens": a.tokens, "scorer_elapsed_s": elapsed},
             "steps": steps,
             "trap_rewind": ({"linked_alerts": linked,
                              "total_amount": sum(alerts[i]["amount"] and int(alerts[i]["amount"]) for i in linked),
                              "note": "replay moment: the linked cards merge into one case"} if linked else None),
             "score_reveal": result}
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out/"trace.json").write_text(json.dumps(trace, indent=2))
    (out/"score.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"ok": True, "agent": a.agent, "score": result, "trace": str(out/"trace.json")}, indent=2))
if __name__ == "__main__": main()
