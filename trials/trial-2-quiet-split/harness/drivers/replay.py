#!/usr/bin/env python3
"""A2ZAI Lab replay generator.

Reads a completed run (trace.json + score.json + run_meta.json) and emits a
single self-contained replay.html: the 25 alert cards in the order the agent
worked them, disposition counters, the trap-rewind moment (linked cards
merging into one case), and the score reveal. No external assets — the file
opens anywhere, which is the point: it is the demo surface and the seed of
the replay video.

Usage: python3 replay.py <run_dir> [--out replay.html]
"""
import argparse, html, json, pathlib, sys

DISP_STYLE = {
    "CLEAR": ("#34d399", "CLEAR"),
    "MONITOR": ("#fbbf24", "MONITOR"),
    "ESCALATE": ("#f87171", "ESCALATE"),
}

CSS = """
body{background:#030712;color:#e5e7eb;font-family:ui-sans-serif,system-ui,sans-serif;margin:0}
.wrap{max-width:880px;margin:0 auto;padding:32px 20px 64px}
.kicker{color:#22d3ee;font-size:12px;font-weight:700;letter-spacing:.2em}
h1{color:#fff;font-size:32px;margin:8px 0 4px}
.sub{color:#9ca3af;margin:0 0 24px}
.counters{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 28px}
.counter{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:10px 16px}
.counter b{color:#fff;font-size:20px;display:block}
.counter span{color:#9ca3af;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.card{background:#111827;border:1px solid #1f2937;border-radius:14px;padding:14px 16px;transition:outline-color .3s}
.card.trap{border-color:#7c3aed}
.card.lit{outline:2px solid #22d3ee}
.card .top{display:flex;justify-content:space-between;align-items:baseline}
.card .amt{color:#fff;font-weight:700;font-size:18px}
.chip{font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;border:1px solid}
.meta{color:#9ca3af;font-size:12px;margin:6px 0}
.ev{color:#6b7280;font-size:11px;margin:6px 0 0;padding-left:14px}
.rule{color:#d1d5db;font-size:12px}
.trapbox{background:#1e1b4b;border:1px solid #7c3aed;border-radius:16px;padding:20px;margin:32px 0}
.trapbox h2{color:#fff;margin:0 0 8px}
.scorebox{background:#111827;border:1px solid #1f2937;border-radius:16px;padding:20px;margin:32px 0}
.bar{height:8px;background:#1f2937;border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;background:#22d3ee}
.srow{display:flex;justify-content:space-between;color:#d1d5db;font-size:14px;margin:10px 0 4px}
.total{color:#22d3ee;font-size:40px;font-weight:900}
button{background:#164e63;color:#fff;border:1px solid #22d3ee;border-radius:10px;padding:8px 18px;font-size:14px;cursor:pointer}
.foot{color:#6b7280;font-size:12px;margin-top:24px}
a{color:#22d3ee}
"""

JS = """
let idx=-1,timer=null;
const cards=[...document.querySelectorAll('.card')];
function step(){ if(idx>=0&&cards[idx])cards[idx].classList.remove('lit');
  idx++; if(idx>=cards.length){stop();return;}
  cards[idx].classList.add('lit'); cards[idx].scrollIntoView({block:'center',behavior:'smooth'}); }
function play(){ if(timer)return; timer=setInterval(step,900); step(); }
function stop(){ clearInterval(timer); timer=null; }
document.getElementById('play').addEventListener('click',()=>{idx=-1;play();});
"""


def money(n):
    return f"${n:,.0f}" if isinstance(n, (int, float)) else str(n)


def main():
    ap = argparse.ArgumentParser(description="A2ZAI Lab replay generator")
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    run_dir = pathlib.Path(a.run_dir).resolve()
    trace = json.loads((run_dir / "trace.json").read_text())
    score = json.loads((run_dir / "score.json").read_text())
    meta = {}
    if (run_dir / "run_meta.json").exists():
        meta = json.loads((run_dir / "run_meta.json").read_text())
    run = trace.get("run", {})
    agent = html.escape(str(run.get("agent") or meta.get("agent") or "agent"))
    model = html.escape(str(run.get("model") or meta.get("model") or ""))
    steps = trace.get("steps", [])
    trap = trace.get("trap_rewind") or {}
    linked = set(trap.get("linked_alerts") or [])

    counts = {"CLEAR": 0, "MONITOR": 0, "ESCALATE": 0}
    for s in steps:
        if s.get("disposition") in counts:
            counts[s["disposition"]] += 1

    cards = []
    for s in steps:
        c = s.get("card", {})
        color, label = DISP_STYLE.get(s.get("disposition"), ("#9ca3af", "?"))
        trap_cls = " trap" if s.get("alert_id") in linked else ""
        ev = "".join(f"<li>{html.escape(str(e))}</li>" for e in (s.get("evidence_fields") or []))
        cards.append(f"""
<div class="card{trap_cls}" id="card-{html.escape(str(s.get('alert_id')))}">
  <div class="top"><span style="color:#fff;font-weight:700">{html.escape(str(s.get('alert_id')))}</span>
  <span class="chip" style="color:{color};border-color:{color}">{label}</span></div>
  <div class="amt">{money(c.get('amount'))}</div>
  <div class="meta">{html.escape(str(c.get('txn_type','')))} · {html.escape(str(c.get('date','')))} · {html.escape(str(c.get('branch','')))}<br>Trigger: {html.escape(str(c.get('trigger','')))}</div>
  <div class="rule">Rule cited: {html.escape(str(s.get('rule_cited','')))}{(' · Case: ' + html.escape(str(s.get('linked_case_id')))) if s.get('linked_case_id') else ''}</div>
  <ul class="ev">{ev}</ul>
</div>""")

    comp = score.get("components", {})
    comp_rows = ""
    labels = {"disposition_40": ("Disposition accuracy", 40), "trap_20": ("Trap detection", 20),
              "citation_15": ("Rule citation", 15), "evidence_10": ("Evidence trail", 10),
              "calibration_10": ("Calibration", 10)}
    for key, (label, mx) in labels.items():
        v = comp.get(key)
        if v is None:
            continue
        pct = round(100 * float(v) / mx)
        comp_rows += (f'<div class="srow"><span>{label}</span><span>{v} / {mx}</span></div>'
                      f'<div class="bar"><i style="width:{pct}%"></i></div>')

    gates = score.get("hard_gates_triggered") or []
    gates_txt = "No hard gates hit." if not gates else "Gates hit: " + "; ".join(map(str, gates))
    trap_cards = ", ".join(sorted(linked))
    cost = meta.get("est_cost_usd")
    cost_txt = f" · est. cost ${cost:.2f}" if isinstance(cost, (int, float)) else ""
    tokens = run.get("tokens") or meta.get("total_tokens")

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Replay — {agent} on Trial #1</title><style>{CSS}</style></head>
<body><div class="wrap">
<p class="kicker">A2ZAI LAB — RUN REPLAY</p>
<h1>{agent}</h1>
<p class="sub">Trial #1 — The Structuring Split · model {model} · every card below is from the run's published trace, in the order the agent worked them.</p>
<div class="counters">
  <div class="counter"><b>{len(steps)}</b><span>alerts worked</span></div>
  <div class="counter"><b>{counts['ESCALATE']}</b><span>escalated</span></div>
  <div class="counter"><b>{counts['MONITOR']}</b><span>monitored</span></div>
  <div class="counter"><b>{counts['CLEAR']}</b><span>cleared</span></div>
  <div class="counter"><b>{tokens if tokens is not None else '—'}</b><span>tokens{cost_txt}</span></div>
</div>
<p><button id="play">▶ Play the run</button></p>
<div class="grid">{''.join(cards)}</div>
<div class="trapbox"><h2>The trap rewind</h2>
<p style="color:#c4b5fd;margin:0">Four deposits, each harmless alone: {html.escape(trap_cards)} — together {money(trap.get('total_amount'))}. {html.escape(str(trap.get('note','')))} Purple cards above are the linked set.</p></div>
<div class="scorebox"><div class="srow"><span style="color:#fff;font-weight:700">Score</span><span class="total">{score.get('subtotal_of_95')} / 95</span></div>
{comp_rows}
<p style="color:#9ca3af">{gates_txt} Cost/time (5 pts): {html.escape(str(score.get('cost_time_5pts')))}</p></div>
<p class="foot">Generated from trace.json + score.json by the Lab's replay template. Full artifacts: github.com/krishnaadavi/a2zai-lab</p>
</div><script>{JS}</script></body></html>"""

    out = pathlib.Path(a.out) if a.out else run_dir / "replay.html"
    out.write_text(doc)
    print(f"Replay written: {out} ({len(doc)} bytes, {len(steps)} cards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
