#!/usr/bin/env python3
"""Trial #2 v2 run harness (built 2026-10-26, patterned on Trial #1/#2 v1 runners).

Takes ANY agent decision file in the spec's output contract, validates it,
scores it with the deterministic scorer, and emits a replay-ready trace JSON
(invoice cards in order, trap-rewind events for every case the run linked,
score reveal) that the replay template consumes. Model-agnostic: a real LLM
run just has to produce the same decision-file shape.

Usage: runner.py <decisions.json> --agent <name> [--model <id>] [--tokens N] --out <dir>
Output contract per decision: {"invoice_id","disposition","rule_cited",
"evidence_fields":[...], "linked_case_id": optional}
"""
import argparse, importlib.util, json, sys, time, csv, pathlib
BASE = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("scorer", BASE/"private"/"scorer.py")
scorer = importlib.util.module_from_spec(spec); spec.loader.exec_module(scorer)
VALID_DISP = {"AUTO_APPROVE","MANAGER_APPROVAL","FINANCE_ESCALATE","HOLD_VERIFY","REJECT"}
VALID_RULES = {"Q-1","Q-2","Q-3","Q-4","Q-5","Q-6","Q-7"}

def validate(decisions):
    errs = []
    if not isinstance(decisions, list): return ["top level must be a list of decisions"]
    ids = [d.get("invoice_id") for d in decisions]
    want = [f"I{i:02d}" for i in range(1,31)]
    if sorted(ids) != want: errs.append(f"must cover exactly I01-I30 once; got {sorted(set(ids))} (n={len(ids)})")
    for d in decisions:
        if str(d.get("disposition","")).upper() not in VALID_DISP: errs.append(f"{d.get('invoice_id')}: bad disposition {d.get('disposition')!r}")
        r = (d.get("rule_cited") or "").strip().upper()
        if r and r not in VALID_RULES: errs.append(f"{d.get('invoice_id')}: rule_cited {r!r} not in Q-1..Q-7 (invented rules zero the citation component)")
        if not isinstance(d.get("evidence_fields", []), list): errs.append(f"{d.get('invoice_id')}: evidence_fields must be a list")
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
    invoices = {r["invoice_id"]: r for r in csv.DictReader(open(BASE/"task-pack"/"invoices.csv"))}
    t0 = time.time(); result = scorer.score(decisions); elapsed = round(time.time()-t0, 4)
    by_id = {d["invoice_id"]: d for d in decisions}
    steps = []
    for iid in sorted(by_id):
        d, inv = by_id[iid], invoices[iid]
        steps.append({"invoice_id": iid, "card": {"date": inv["date"], "vendor": inv["vendor"],
            "amount": int(inv["amount"]), "project_code": inv["project_code"], "po_number": inv["po_number"]},
            "disposition": d["disposition"].upper(), "rule_cited": (d.get("rule_cited") or "").upper() or None,
            "evidence_fields": d.get("evidence_fields", []), "linked_case_id": d.get("linked_case_id")})
    # Trap rewinds: one event per case the run actually linked (grouped by
    # case id), largest first. In a correct run these are the two patterns.
    groups = {}
    for s in steps:
        if s["linked_case_id"]:
            groups.setdefault(s["linked_case_id"], []).append(s["invoice_id"])
    rewinds = []
    for cid, members in groups.items():
        if len(members) < 2: continue
        rewinds.append({"case_id": cid, "linked_invoices": members,
                        "total_amount": sum(int(invoices[i]["amount"]) for i in members),
                        "note": "replay moment: the linked cards merge into one case"})
    rewinds.sort(key=lambda g: -g["total_amount"])
    trace = {"trial": "trial2b-quiet-split-v2", "run": {"agent": a.agent, "model": a.model,
             "tokens": a.tokens, "scorer_elapsed_s": elapsed},
             "steps": steps,
             "trap_rewind": ({"linked_invoices": rewinds[0]["linked_invoices"],
                              "total_amount": rewinds[0]["total_amount"],
                              "note": rewinds[0]["note"]} if rewinds else None),
             "trap_rewinds": rewinds,
             "score_reveal": result}
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out/"trace.json").write_text(json.dumps(trace, indent=2))
    (out/"score.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"ok": True, "agent": a.agent, "score": result, "trace": str(out/"trace.json")}, indent=2))
if __name__ == "__main__": main()
