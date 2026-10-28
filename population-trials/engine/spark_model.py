#!/usr/bin/env python3
"""Population Trials — Spark-tier batch planner (v1 model).

Implements the engine's batch-planner contract: ONE Muse Spark call per
cohort per week returns that cohort's behavior parameters + a one-sentence
rationale (traced in the run's planner_trace). Per-agent decisions are then
sampled around those parameters by the engine's RNG — the design trade is
documented in COSTS.md (a full season at any pool size for ~$0.50–1.50,
vs ~$28 for 20,000 individual calls).

Transport: the Lab's own meta_driver.call_api (Secure Vault surrogate to
api.meta.ai) — the key never appears here. JSON-only instruction (the
proven Day 1 route; no response_format schema).

Failure honesty: a failed/unparseable call falls back to documented
defaults and the fallback is RECORDED in the params (never silent).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "drivers"))
import meta_driver  # noqa: E402

from sim import COHORTS  # noqa: E402

MODEL_ID = "muse-spark-1.3"
PRICE_IN, PRICE_OUT = 1.25 / 1e6, 4.25 / 1e6   # $ per token (verified Oct 26)
DEFAULTS = {"contact_factor_mean": 0.9, "contact_factor_sd": 0.15,
            "attend_prob": 0.95, "care_seek": 0.45}


class SparkPlanner:
    def __init__(self):
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "fallbacks": 0}

    def est_cost(self) -> float:
        return (self.usage["prompt_tokens"] * PRICE_IN
                + self.usage["completion_tokens"] * PRICE_OUT)

    def plan_week(self, week: int, cohort: str, card: dict) -> dict:
        spec = COHORTS[cohort]
        prompt = (
            "You are setting weekly behavior parameters for one population cohort in a "
            "flu-season simulation. The cohort never sees future data.\n\n"
            f"Cohort: {cohort} — baseline {spec['contacts']} contacts/week, "
            f"baseline care-seeking propensity {spec['care_seek']}.\n"
            f"Week {week} of the season. Last week's local influenza-like-illness level: "
            f"{card['local_ili_pct']:.2f}% of outpatient visits. Current prevalence in the "
            f"pool: {card['prevalence_pct']}%. Schools open: {card['school_open']}.\n\n"
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
            None, MODEL_ID, [{"role": "user", "content": prompt}],
            max_tokens=4000, use_schema=False, schema=None)
        self.usage["calls"] += 1
        if err is not None or resp is None:
            self.usage["fallbacks"] += 1
            return {**DEFAULTS, "rationale": f"FALLBACK (API error {err})", "fallback": True}
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
            return {**DEFAULTS, "rationale": f"FALLBACK (parse: {e})", "fallback": True}
