#!/usr/bin/env python3
"""Population Trials — v2 runner: seed-window transmission fit.

What changed from v0/v1, and why (Day 3 diagnosis): the v0/v1 kernel's
base_transmission (0.055) was an a priori constant, and at the seed week's
~2% prevalence it ignites instantly — v1's pool hit 13.5%ILI in simulated
week 2 and burned out while the real season was still at ~2%. The kernel,
not the planner's behavior, was the binding constraint.

V2 DESIGN (decided before any v2 score existed):
  1. The pool may see the first --seed-weeks observations (default 4).
  2. The kernel's base_transmission — and ONLY that parameter — is ESTIMATED
     from those seed weeks: grid search minimizing squared error between
     the kernel's simulated wILI and the observed seed-window wILI.
     The fit simulation uses the rule-based mock behavior (the fitting
     instrument is the deterministic kernel, not the planner) and the
     run's own pool size and RNG seed. The holdout is never touched.
  3. The fitted value is FROZEN. The forecast then runs the untouched
     holdout with the chosen planner (Spark by default), seeded from the
     last observed seed week — exactly the v1 seeding convention.
  4. Scored by engine/calibrate.py, unchanged. Whatever it earns is
     published, gate included.

Usage:
  python3 run_v2.py --season ilinet_tx_2025-26 --agents 100 \
      --run-name v2-spark-100-tx-2025-26
"""
import argparse
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "engine"))
from sim import run_sim, mock_model, COHORTS          # noqa: E402
from calibrate import score                          # noqa: E402

FIT_GRID = [round(0.002 + 0.001 * i, 3) for i in range(59)]   # 0.002 .. 0.060


def make_model(name: str):
    if name == "mock":
        return mock_model
    if name == "spark":
        from spark_model import SparkPlanner
        return SparkPlanner()
    raise ValueError(name)


def load_curve(stem: str):
    rows = list(csv.DictReader((HERE / "data" / f"{stem}.csv").open()))
    return [int(r["epiweek"]) for r in rows], [float(r["wili"]) for r in rows]


def fit_transmission(n_agents: int, seed_window: list[float],
                     import_rate: float, waning_weeks, rng_seed: int = 42) -> dict:
    """Grid-search base_transmission on the seed window ONLY.

    The fit sim is seeded from the FIRST observed week (same convention as
    the forecast: initial infected = observed wILI) and simulated across
    the remaining seed weeks; SSE is against those observed weeks.
    """
    trials = []
    for beta in FIT_GRID:
        r = run_sim(n_agents, seed_weeks_ili=seed_window[0],
                    n_weeks=len(seed_window) - 1, model=mock_model, seed=rng_seed,
                    import_rate=import_rate, waning_weeks=waning_weeks,
                    base_transmission=beta)
        sse = sum((s - o) ** 2 for s, o in zip(r.weekly_ili_pct, seed_window[1:]))
        trials.append({"base_transmission": beta, "sse": round(sse, 4),
                       "sim_seed_window": r.weekly_ili_pct})
    trials.sort(key=lambda t: (t["sse"], t["base_transmission"]))
    return {"best": trials[0], "grid_size": len(trials),
            "top5": trials[:5],
            "objective": "sum of squared errors, simulated vs observed wILI, seed-window weeks 2..N",
            "fit_behavior": "rule-based mock_model (kernel is the fitting instrument)",
            "fit_data": "seed window only — the holdout was not read by the fit"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", default="ilinet_tx_2025-26")
    ap.add_argument("--agents", type=int, default=100)
    ap.add_argument("--seed-weeks", type=int, default=4,
                    help="observed weeks the pool may see (v2 design: ~4)")
    ap.add_argument("--sim-weeks", type=int, default=0,
                    help="0 = auto: through 4 weeks past the real peak")
    ap.add_argument("--model", default="spark", choices=["mock", "spark"])
    ap.add_argument("--import-rate", type=float, default=1.0,
                    help="v1 dynamics, kept identical to the v1 run for comparability")
    ap.add_argument("--waning", type=int, default=8,
                    help="v1 dynamics, kept identical to the v1 run for comparability")
    ap.add_argument("--run-name", default=None)
    a = ap.parse_args()

    weeks, real = load_curve(a.season)
    seed_window = real[:a.seed_weeks]
    seed_weeks_epi = weeks[:a.seed_weeks]
    sim_weeks = a.sim_weeks or (real.index(max(real)) - a.seed_weeks + 5)
    seed_ili = real[a.seed_weeks - 1]
    holdout = real[a.seed_weeks:a.seed_weeks + sim_weeks]
    holdout_weeks = weeks[a.seed_weeks:a.seed_weeks + sim_weeks]

    fit = fit_transmission(a.agents, seed_window, a.import_rate, a.waning)
    beta = fit["best"]["base_transmission"]

    model = make_model(a.model)
    result = run_sim(a.agents, seed_weeks_ili=seed_ili, n_weeks=sim_weeks, model=model,
                     import_rate=a.import_rate, waning_weeks=a.waning,
                     base_transmission=beta)
    s = score(result.weekly_ili_pct, holdout)
    usage = getattr(model, "usage", None)
    cost = model.est_cost() if hasattr(model, "est_cost") else 0.0

    name = a.run_name or f"v2-{a.model}-{a.agents}-{a.season}"
    out = HERE / "runs" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "trace.json").write_text(json.dumps(
        {"params": result.params, "fit": fit, "weeks": result.trace,
         "planner_trace": result.planner_trace}, indent=1))
    (out / "result.json").write_text(json.dumps(
        {"season": a.season, "epiweeks": holdout_weeks, "real_wili": holdout,
         "sim_ili_pct": result.weekly_ili_pct, "score": s,
         "fit": {"base_transmission": beta, "sse": fit["best"]["sse"],
                 "seed_window_epiweeks": seed_weeks_epi,
                 "seed_window_wili": seed_window,
                 "sim_seed_window": fit["best"]["sim_seed_window"]}}, indent=1))
    cohorts = []
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
    model_label = ("rule-based stand-in" if a.model == "mock"
                   else "Muse Spark 1.3, batched cohort planner")
    receipt = f"""# Population Trials — Receipt ({name})

- **Run:** {name} · {result.params['n_agents']} agents · model: {a.model} ({model_label})
- **Data:** CDC ILINet via Delphi epidata, season file data/{a.season}.csv (verified live pull, Oct 27 2026)
- **Design (v2):** the pool saw the first {a.seed_weeks} observed weeks
  (epiweeks {seed_weeks_epi[0]}–{seed_weeks_epi[-1]}, wILI {seed_window}) and nothing after.
  It forecast the next {sim_weeks} weeks — window rule: through 4 weeks past the real peak
  (wILI {max(holdout):.2f} @ {peak_real}) — scored against reality by engine/calibrate.py.
- **What was fit, and on what data:** ONLY the kernel's base_transmission. Grid of
  {fit['grid_size']} values (0.002–0.060) run through the kernel with rule-based mock
  behavior, seeded from the first observed week; the winner minimized squared error
  against the remaining seed-window observations (sim {fit['best']['sim_seed_window']}
  vs real {seed_window[1:]}, SSE {fit['best']['sse']}). The holdout was never read by
  the fit. **Fitted base_transmission: {beta}** (v0/v1 used the a priori 0.055),
  frozen for the forecast. Reporting fraction, cohort table, and every other kernel
  parameter are unchanged from v0/v1.
- **Calibration score: {s['calibration_score']} / 100**
  - curve shape {s['components']['curve_shape_40']}/40 (Pearson r = {s['pearson_r']})
  - peak timing {s['components']['peak_timing_30']}/30 (peak off by {s['peak_week_error']} week(s))
  - magnitude {s['components']['magnitude_30']}/30 (sim/real mass ratio {s['magnitude_ratio_sim_over_real']})
  - gate: {s['gate_applied'] or 'none'}
- **May publish what-ifs:** {s['may_publish_whatifs']} (threshold {s['publication_threshold']})
- **Dynamics:** import_rate {a.import_rate}/wk, waning {a.waning} wks (same as v1, for comparability)
- **Cost:** ${cost:.4f}{f" — Spark usage: {usage}" if usage else " (mock model — no API spend)"}
- **Honest label:** {'v2 pipeline check with stand-in behavior; the transmission fit is the artifact under test' if a.model == 'mock' else 'v2: seed-window-fitted kernel + Spark behavior. The fit used seed weeks only; the score is whatever the untouched holdout gave'}.
  The flagship calibration key (Dallas County DCHHS absence series) is still to be wired.
"""
    (out / "receipt.md").write_text(receipt)
    print(json.dumps({"run": name, "agents": result.params["n_agents"],
                      "fitted_base_transmission": beta, "fit_sse": fit["best"]["sse"],
                      "score": s, "sim": result.weekly_ili_pct, "real": holdout,
                      "cost": cost, "usage": usage}, indent=1))


if __name__ == "__main__":
    main()
