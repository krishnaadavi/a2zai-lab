#!/usr/bin/env python3
"""Population Trials — v3 runner: multi-season shape-teaching fit.

THE V3 QUESTION (posed in the v2 write-up, Oct 28): v2 fitted the kernel's
base_transmission on a FLAT 4-week seed window of the target season. A flat
window cannot tell the kernel the season accelerates later — v2's pool
peaked 5 weeks early and burned out while the real season climbed.

V3 DESIGN (decided before any v3 score existed):
  1. The flagship key: DCHHS Dallas County student-absence ILI % (the
     series the v0–v2 receipts flagged as "still to be wired"). Target
     season 2024–25 is the temporal HOLDOUT.
  2. Information set = (a) the first 4 observed weeks of 2024–25 (the v2
     seed-window convention, unchanged) PLUS (b) the COMPLETE curves of
     the three past DCHHS seasons (2018–19, 2022–23, 2023–24). The
     2024–25 holdout is read by nobody: not the fit, not the planner.
  3. base_transmission — and ONLY that parameter — is estimated from
     HISTORY: for each past season, the v2 grid search is run against
     that season's FULL curve (seeded from its first observed week, SSE
     over every remaining week — history is fully visible, so the
     acceleration phase informs the fit; that is the change under test).
     beta_v3 = the MEDIAN of the three per-season winners, per pool size
     (the fit is pool-size-specific, as in v2). Frozen for the forecast.
  4. The Spark planner is told the history too (past seasons' peak weeks
     and magnitudes, in its prompt — the past is public record) and the
     correct series definition (student absences, Dallas County). Its
     per-week card still contains only the forecast's own state.
  5. Flagged points: the six `suspected_no_report_plotted_as_zero` points
     in the DCHHS extraction are NOT observations — they are no-report
     weeks the chart drew at zero. They are dropped from every curve
     (fit, seed, holdout, scoring), i.e. treated as the gaps they are.
     Gaps are never filled; each season's curve is its reported weeks
     in order, and one sim step = one reported week.
  6. Scored by engine/calibrate.py, UNCHANGED (shape 40 / peak timing 30
     / magnitude 30; peak miss >= 3 weeks caps at 49; >= 70 unlocks
     what-ifs). Whatever it earns is published, gate included.

Usage:
  python3 run_v3.py --agents 100 --model spark \
      --run-name v3-spark-100-dchhs-2024-25
"""
import argparse
import csv
import json
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "engine"))
from sim import run_sim, mock_model, COHORTS          # noqa: E402
from calibrate import score                          # noqa: E402

FIT_GRID = [round(0.002 + 0.001 * i, 3) for i in range(59)]   # 0.002 .. 0.060
PAST_SEASONS = ["2018-19", "2022-23", "2023-24"]
TARGET_SEASON = "2024-25"
SEED_WEEKS = 4

HISTORY_TEXT = (
    "Historical Dallas County school-absence ILI seasons (DCHHS, public record): "
    "2018-19 peaked at 1.01% in CDC week 6; 2022-23 peaked early at 0.23% in CDC "
    "week 46; 2023-24 peaked at 0.30% in CDC week 4. Fall weeks (CDC 40-47) "
    "typically run 0.00-0.15%; in two of the three seasons the main rise began "
    "around the New Year, in one it came in November."
)


def load_dchhs(stem: str) -> dict:
    """Load one DCHHS season on its observed grid.

    Flagged suspected-no-report zeros are dropped (treated as gaps);
    no-report weeks are absent from the file already. Nothing is filled.
    """
    path = HERE / "data" / f"dchhs_dallas_student_absence_ili_{stem}.csv"
    epiweeks, cdc_weeks, values, dropped = [], [], [], []
    for r in csv.DictReader(path.open()):
        if r["quality_flag"] == "suspected_no_report_plotted_as_zero":
            dropped.append({"epiweek": int(r["epiweek"]),
                            "cdc_week": int(r["cdc_week"]),
                            "plotted_pct": float(r["student_absence_ili_pct"])})
            continue
        epiweeks.append(int(r["epiweek"]))
        cdc_weeks.append(int(r["cdc_week"]))
        values.append(float(r["student_absence_ili_pct"]))
    return {"season": stem, "epiweeks": epiweeks, "cdc_weeks": cdc_weeks,
            "values": values, "dropped_flagged": dropped}


class SparkPlannerV3:
    """Spark batch planner, v3: same transport/contract/pricing as
    engine/spark_model.py, with the prompt corrected to the DCHHS series
    and the past-season history the v3 design entitles the pool to know.
    Fallbacks are recorded, never silent (same rule as v1/v2)."""

    def __init__(self, forecast_cdc_weeks: list[int]):
        from spark_model import MODEL_ID, PRICE_IN, PRICE_OUT, DEFAULTS
        self._model_id, self._pin, self._pout = MODEL_ID, PRICE_IN, PRICE_OUT
        self._defaults = DEFAULTS
        self.forecast_cdc_weeks = forecast_cdc_weeks
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0,
                      "calls": 0, "fallbacks": 0}

    def est_cost(self) -> float:
        return (self.usage["prompt_tokens"] * self._pin
                + self.usage["completion_tokens"] * self._pout)

    def plan_week(self, week: int, cohort: str, card: dict) -> dict:
        import meta_driver
        spec = COHORTS[cohort]
        cdc_week = self.forecast_cdc_weeks[week]
        prompt = (
            "You are setting weekly behavior parameters for one population cohort in a "
            "flu-season simulation of Dallas County, Texas. The series being forecast is "
            "the weekly percentage of student absences due to influenza-like illness "
            "(DCHHS). The cohort never sees future data.\n\n"
            f"{HISTORY_TEXT}\n\n"
            f"Cohort: {cohort} — baseline {spec['contacts']} contacts/week, "
            f"baseline care-seeking propensity {spec['care_seek']}.\n"
            f"It is now CDC week {cdc_week} (forecast week {week}). Last week's local "
            f"level: {card['local_ili_pct']:.3f}% of student absences due to ILI. "
            f"Current prevalence in the pool: {card['prevalence_pct']}%. "
            f"Schools open: {card['school_open']}.\n\n"
            "Decide how this cohort behaves THIS week as illness circulates: how much they "
            "cut contacts relative to baseline (contact_factor_mean 0.1-1.2, with spread "
            "contact_factor_sd 0-0.4 across individuals), for school households the "
            "probability a family keeps kids home is reflected in attend_prob (probability "
            "of attending, 0-1), and care_seek (0-1) if symptomatic.\n"
            "Respond with ONLY a JSON object, no other text:\n"
            '{"contact_factor_mean": <float>, "contact_factor_sd": <float>, '
            '"attend_prob": <float>, "care_seek": <float>, "rationale": "<one sentence>"}'
        )
        resp, err = meta_driver.call_api(
            None, self._model_id, [{"role": "user", "content": prompt}],
            max_tokens=4000, use_schema=False, schema=None)
        self.usage["calls"] += 1
        if err is not None or resp is None:
            self.usage["fallbacks"] += 1
            return {**self._defaults,
                    "rationale": f"FALLBACK (API error {err})", "fallback": True}
        u = resp.get("usage") or {}
        self.usage["prompt_tokens"] += u.get("prompt_tokens", 0)
        self.usage["completion_tokens"] += u.get("completion_tokens", 0)
        text = resp["choices"][0]["message"]["content"]
        try:
            t = text.strip().strip("`")
            if t.lower().startswith("json"):
                t = t[4:].strip()
            obj = json.loads(t[t.find("{"):t.rfind("}") + 1])
            out = {"contact_factor_mean": float(obj["contact_factor_mean"]),
                   "contact_factor_sd": float(obj["contact_factor_sd"]),
                   "attend_prob": float(obj.get("attend_prob", 0.95)),
                   "care_seek": float(obj["care_seek"]),
                   "rationale": str(obj.get("rationale", ""))[:240]}
            out["contact_factor_mean"] = min(1.2, max(0.1, out["contact_factor_mean"]))
            out["contact_factor_sd"] = min(0.4, max(0.0, out["contact_factor_sd"]))
            out["attend_prob"] = min(1.0, max(0.0, out["attend_prob"]))
            out["care_seek"] = min(1.0, max(0.0, out["care_seek"]))
            return out
        except Exception as e:  # parse failure — recorded, never silent
            self.usage["fallbacks"] += 1
            return {**self._defaults,
                    "rationale": f"FALLBACK (parse: {e})", "fallback": True}


def fit_on_season(n_agents: int, curve: list[float],
                  import_rate: float, waning_weeks, rng_seed: int = 42) -> dict:
    """v2 grid fit, but the objective is the season's FULL remaining curve:
    history is fully visible, so the acceleration phase informs beta."""
    trials = []
    for beta in FIT_GRID:
        r = run_sim(n_agents, seed_weeks_ili=curve[0],
                    n_weeks=len(curve) - 1, model=mock_model, seed=rng_seed,
                    import_rate=import_rate, waning_weeks=waning_weeks,
                    base_transmission=beta)
        sse = sum((s - o) ** 2 for s, o in zip(r.weekly_ili_pct, curve[1:]))
        trials.append({"base_transmission": beta, "sse": round(sse, 6)})
    trials.sort(key=lambda t: (t["sse"], t["base_transmission"]))
    return {"best": trials[0], "grid_size": len(trials), "top5": trials[:5]}


def fit_history(n_agents: int, past: dict, import_rate: float, waning) -> dict:
    per_season = {}
    for stem, curve in past.items():
        f = fit_on_season(n_agents, curve["values"], import_rate, waning)
        per_season[stem] = {"best_base_transmission": f["best"]["base_transmission"],
                            "sse": f["best"]["sse"], "top5": f["top5"],
                            "grid_size": f["grid_size"],
                            "season_weeks_fit": len(curve["values"]) - 1}
    betas = [v["best_base_transmission"] for v in per_season.values()]
    return {"per_season": per_season,
            "beta_v3_median": statistics.median(betas),
            "objective": "per past season: SSE of kernel sim vs the season's full "
                         "remaining curve (mock behavior as fitting instrument, "
                         "seeded from the season's first observed week); "
                         "beta_v3 = median of the per-season winners",
            "fit_data": "past seasons only (2018-19, 2022-23, 2023-24) — the "
                        "2024-25 holdout was not read by the fit"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, default=100)
    ap.add_argument("--model", default="spark", choices=["mock", "spark"])
    ap.add_argument("--import-rate", type=float, default=1.0,
                    help="v1/v2 dynamics, kept identical for comparability")
    ap.add_argument("--waning", type=int, default=8,
                    help="v1/v2 dynamics, kept identical for comparability")
    ap.add_argument("--run-name", default=None)
    a = ap.parse_args()

    past = {stem: load_dchhs(stem) for stem in PAST_SEASONS}
    target = load_dchhs(TARGET_SEASON)
    curve, epi = target["values"], target["epiweeks"]
    seed_window = curve[:SEED_WEEKS]
    seed_epi = epi[:SEED_WEEKS]
    peak_idx = curve.index(max(curve))
    sim_weeks = peak_idx - SEED_WEEKS + 5       # v2 window rule: 4 past the peak
    holdout = curve[SEED_WEEKS:SEED_WEEKS + sim_weeks]
    holdout_epi = epi[SEED_WEEKS:SEED_WEEKS + sim_weeks]
    holdout_cdc = target["cdc_weeks"][SEED_WEEKS:SEED_WEEKS + sim_weeks]

    fit = fit_history(a.agents, past, a.import_rate, a.waning)
    beta = fit["beta_v3_median"]

    if a.model == "mock":
        model = mock_model
    else:
        model = SparkPlannerV3(holdout_cdc)
    result = run_sim(a.agents, seed_weeks_ili=seed_window[-1], n_weeks=sim_weeks,
                     model=model, import_rate=a.import_rate,
                     waning_weeks=a.waning, base_transmission=beta)
    s = score(result.weekly_ili_pct, holdout)
    usage = getattr(model, "usage", None)
    cost = model.est_cost() if hasattr(model, "est_cost") else 0.0

    name = a.run_name or f"v3-{a.model}-{a.agents}-dchhs-{TARGET_SEASON}"
    out = HERE / "runs" / name
    out.mkdir(parents=True, exist_ok=True)
    dropped_all = {stem: past[stem]["dropped_flagged"] for stem in PAST_SEASONS}
    dropped_all[TARGET_SEASON] = target["dropped_flagged"]
    design = {
        "information_set": {
            "target_seed_window_epiweeks": seed_epi,
            "target_seed_window_values": seed_window,
            "past_seasons_full_curves": PAST_SEASONS,
            "holdout": "2024-25 observed weeks after the seed window — read by "
                       "nobody (not the fit, not the planner); used only to score",
        },
        "flagged_points_dropped_as_gaps": dropped_all,
        "grid_convention": "one sim step = one reported week, in file order; "
                           "no-report gaps are never filled",
    }
    (out / "trace.json").write_text(json.dumps(
        {"params": result.params, "design": design, "fit": fit,
         "weeks": result.trace, "planner_trace": result.planner_trace}, indent=1))
    fit_summary = {"beta_v3_median": beta,
                   "per_season_best": {k: v["best_base_transmission"]
                                       for k, v in fit["per_season"].items()},
                   "per_season_sse": {k: v["sse"]
                                      for k, v in fit["per_season"].items()}}
    (out / "result.json").write_text(json.dumps(
        {"season": f"dchhs_dallas_{TARGET_SEASON}", "epiweeks": holdout_epi,
         "real_student_absence_ili_pct": holdout,
         "sim_ili_pct": result.weekly_ili_pct, "score": s,
         "fit": fit_summary}, indent=1))
    cohorts = []
    for c, spec in COHORTS.items():
        cohorts += [c] * round(result.params["n_agents"] * spec["share"])
    (out / "replay.json").write_text(json.dumps(
        {"run": name, "model": a.model, "n_agents": result.params["n_agents"],
         "epiweeks": holdout_epi, "real_student_absence_ili_pct": holdout,
         "sim_ili_pct": result.weekly_ili_pct, "score": s,
         "agent_cohorts": cohorts, "weekly_states": result.weekly_states,
         "sample_decisions": [w["sample_decisions"] for w in result.trace],
         "planner_trace": result.planner_trace}))
    # Trace bundle: the data-pull receipt rides along (DATASETS.md rule).
    (out / "data_pull_receipt.json").write_text(
        (HERE / "data" / "dchhs_pull_receipt.json").read_text())

    peak_real_epi = holdout_epi[holdout.index(max(holdout))]
    ps = fit["per_season"]
    model_label = ("rule-based stand-in" if a.model == "mock"
                   else "Muse Spark 1.3, batched cohort planner (v3 prompt: "
                        "DCHHS series + past-season history)")
    receipt = f"""# Population Trials — Receipt ({name})

- **Run:** {name} · {result.params['n_agents']} agents · model: {a.model} ({model_label})
- **Data:** DCHHS Dallas County student-absence ILI %, Figure 4 of the DCHHS
  Influenza Surveillance Reports (dallascounty.org) — primary source, vector
  extraction, pulled Oct 29 2026; pull receipt rides in this bundle
  (data_pull_receipt.json) and at data/dchhs_pull_receipt.json.
- **Design (v3):** multi-season shape-teaching. The pool's information set:
  the first {SEED_WEEKS} observed weeks of 2024–25 (epiweeks {seed_epi[0]}–{seed_epi[-1]},
  values {seed_window}) plus the COMPLETE curves of 2018–19, 2022–23, 2023–24.
  It forecast the next {sim_weeks} reported weeks — window rule: through 4 weeks
  past the real peak ({max(holdout):.3f}% @ epiweek {peak_real_epi}) — scored
  against the untouched 2024–25 holdout by engine/calibrate.py, unchanged.
- **Flagged points:** six `suspected_no_report_plotted_as_zero` points are
  no-report weeks the chart drew at zero — dropped from every curve as the
  gaps they are (2022–23 wks 5, 11; 2023–24 wks 47, 52, 11; 2024–25 wk 11).
  Gaps are never filled; one sim step = one reported week.
- **What was fit, and on what data:** ONLY the kernel's base_transmission.
  Per past season, the v2 grid ({fit['per_season'][PAST_SEASONS[0]]['grid_size']} values,
  0.002–0.060, mock behavior as the fitting instrument, seeded from that
  season's first observed week) minimized SSE against that season's FULL
  remaining curve — the acceleration phase is inside the fit objective;
  that is the v3 change. Winners: 2018–19 β={ps['2018-19']['best_base_transmission']}
  (SSE {ps['2018-19']['sse']}), 2022–23 β={ps['2022-23']['best_base_transmission']}
  (SSE {ps['2022-23']['sse']}), 2023–24 β={ps['2023-24']['best_base_transmission']}
  (SSE {ps['2023-24']['sse']}). **beta_v3 = median = {beta}**, frozen for the
  forecast (v0/v1 a priori: 0.055; v2 seed-window fit: 0.022–0.025). Reporting
  fraction, cohort table, and every other kernel parameter are unchanged.
- **Calibration score: {s['calibration_score']} / 100**
  - curve shape {s['components']['curve_shape_40']}/40 (Pearson r = {s['pearson_r']})
  - peak timing {s['components']['peak_timing_30']}/30 (peak off by {s['peak_week_error']} week(s))
  - magnitude {s['components']['magnitude_30']}/30 (sim/real mass ratio {s['magnitude_ratio_sim_over_real']})
  - gate: {s['gate_applied'] or 'none'}
- **May publish what-ifs:** {s['may_publish_whatifs']} (threshold {s['publication_threshold']})
- **Dynamics:** import_rate {a.import_rate}/wk, waning {a.waning} wks (same as v1/v2, for comparability)
- **Cost:** ${cost:.4f}{f" — Spark usage: {usage}" if usage else " (mock model — no API spend)"}
- **Honest label:** {'v3 pipeline check with stand-in behavior; the history fit is the artifact under test' if a.model == 'mock' else 'v3: history-fitted kernel + Spark behavior with past-season context. The fit and the planner saw past seasons and the seed window only; the score is whatever the untouched 2024–25 holdout gave'}.
"""
    (out / "receipt.md").write_text(receipt)
    print(json.dumps({"run": name, "agents": result.params["n_agents"],
                      "beta_v3_median": beta,
                      "per_season_best": fit_summary["per_season_best"],
                      "score": s, "sim": result.weekly_ili_pct, "real": holdout,
                      "holdout_epiweeks": holdout_epi,
                      "cost": cost, "usage": usage}, indent=1))


if __name__ == "__main__":
    main()
