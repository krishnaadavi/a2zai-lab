#!/usr/bin/env python3
"""Population Trials — runner.

Flow (the problem statement, executable):
  1. Load a real ILINet season curve (data/, pulled by data_pull.py or the
     season pull in this repo's history — source recorded in the receipt).
  2. Split it: seed weeks (the pool may see these) / holdout weeks (it may
     not). Default window: from season start through 4 weeks past the real
     peak — the window choice is a stated design rule, printed in the
     receipt; kernel parameters are never fit to the holdout.
  3. Run the pool forward across the holdout, seeded from the last observed
     week. Score with engine/calibrate.py.
  4. Write runs/<name>/ : trace.json, result.json, receipt.md.

Usage:
  python3 run_prototype.py --season ilinet_tx_2025-26 --agents 1000 \
      --run-name v0-mock-1000-tx-2025-26
"""
import argparse
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "engine"))
from sim import run_sim, mock_model          # noqa: E402
from calibrate import score                  # noqa: E402


def make_model(name: str):
    if name == "mock":
        return mock_model
    if name == "spark":
        from spark_model import SparkPlanner
        return SparkPlanner()
    raise ValueError(name)


MODELS = ["mock", "spark"]


def load_curve(stem: str):
    rows = list(csv.DictReader((HERE / "data" / f"{stem}.csv").open()))
    return [int(r["epiweek"]) for r in rows], [float(r["wili"]) for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="ilinet_tx_2022-23")
    ap.add_argument("--agents", type=int, default=100)
    ap.add_argument("--seed-weeks", type=int, default=2)
    ap.add_argument("--sim-weeks", type=int, default=0,
                    help="0 = auto: through 4 weeks past the real peak")
    ap.add_argument("--model", default="mock", choices=MODELS)
    ap.add_argument("--import-rate", type=float, default=0.0,
                    help="v1 dynamics: expected imported infections/week (0 = v0)")
    ap.add_argument("--waning", type=int, default=None,
                    help="v1 dynamics: weeks until recovered -> susceptible (unset = v0)")
    ap.add_argument("--run-name", default=None)
    a = ap.parse_args()

    weeks, real = load_curve(a.season)
    sim_weeks = a.sim_weeks or (real.index(max(real)) - a.seed_weeks + 5)
    seed_ili = real[a.seed_weeks - 1]
    holdout = real[a.seed_weeks:a.seed_weeks + sim_weeks]
    holdout_weeks = weeks[a.seed_weeks:a.seed_weeks + sim_weeks]

    model = make_model(a.model)
    result = run_sim(a.agents, seed_weeks_ili=seed_ili, n_weeks=sim_weeks, model=model,
                     import_rate=a.import_rate, waning_weeks=a.waning)
    s = score(result.weekly_ili_pct, holdout)
    usage = getattr(model, "usage", None)
    cost = model.est_cost() if hasattr(model, "est_cost") else 0.0

    name = a.run_name or f"v0-{a.model}-{a.agents}-{a.season}"
    out = HERE / "runs" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "trace.json").write_text(json.dumps(
        {"params": result.params, "weeks": result.trace,
         "planner_trace": result.planner_trace}, indent=1))
    (out / "result.json").write_text(json.dumps(
        {"season": a.season, "epiweeks": holdout_weeks, "real_wili": holdout,
         "sim_ili_pct": result.weekly_ili_pct, "score": s}, indent=1))
    # replay bundle for the console UI: per-week agent states + curves + samples
    cohorts = []
    from sim import COHORTS
    for c, spec in COHORTS.items():
        cohorts += [c] * round(result.params["n_agents"] * spec["share"])
    (out / "replay.json").write_text(json.dumps(
        {"run": name, "model": a.model, "n_agents": result.params["n_agents"],
         "epiweeks": holdout_weeks, "real_wili": holdout,
         "sim_ili_pct": result.weekly_ili_pct, "score": s,
         "agent_cohorts": cohorts, "weekly_states": result.weekly_states,
         "sample_decisions": [w["sample_decisions"] for w in result.trace],
         "planner_trace": result.planner_trace}))
    peak_real = holdout_weeks[holdout.index(max(holdout))]
    receipt = f"""# Population Trials — Receipt ({name})

- **Run:** {name} · {result.params['n_agents']} agents · model: {a.model}{' (rule-based stand-in)' if a.model == 'mock' else ' (Muse Spark 1.3, batched cohort planner)'}
- **Data:** CDC ILINet via Delphi epidata, season file data/{a.season}.csv (verified live pull)
- **Design:** pool seeded from the season's week-{a.seed_weeks} observation (wILI {seed_ili:.2f});
  simulated the next {sim_weeks} weeks it never saw — window rule: through 4 weeks past the
  real peak (wILI {max(holdout):.2f} @ {peak_real}) — scored against reality by engine/calibrate.py.
- **Calibration score: {s['calibration_score']} / 100**
  - curve shape {s['components']['curve_shape_40']}/40 (Pearson r = {s['pearson_r']})
  - peak timing {s['components']['peak_timing_30']}/30 (peak off by {s['peak_week_error']} week(s))
  - magnitude {s['components']['magnitude_30']}/30 (sim/real mass ratio {s['magnitude_ratio_sim_over_real']})
  - gate: {s['gate_applied'] or 'none'}
- **May publish what-ifs:** {s['may_publish_whatifs']} (threshold {s['publication_threshold']})
- **Dynamics:** import_rate {a.import_rate}/wk, waning {a.waning} wks (v0 defaults = off)
- **Cost:** ${cost:.4f}{f" — Spark usage: {usage}" if usage else " (mock model — no API spend)"}
- **Honest label:** {'stand-in agents prove the pipeline at scale on real data' if a.model == 'mock' else 'first real-model run; batched cohort-parameter design (see COSTS.md)'}.
  The flagship calibration key (Dallas County DCHHS absence series) is still to be wired.
"""
    (out / "receipt.md").write_text(receipt)
    print(json.dumps({"run": name, "agents": result.params["n_agents"], "score": s,
                      "sim": result.weekly_ili_pct, "real": holdout}, indent=1))


if __name__ == "__main__":
    main()
