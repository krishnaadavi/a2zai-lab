#!/usr/bin/env python3
"""Population Trials — simulation engine (prototype v0).

Architecture (as stated in the problem statement, printed on every receipt):
  - AGENTS set behavior. Each agent is a cohort persona (school household,
    working adult, elder, essential worker) with a weekly state card. A model
    (mock rules today; Spark-tier via the Lab transport next) returns a small
    JSON decision: contact level, school attendance, care-seeking.
  - A transparent KERNEL does the infection math. No model is asked to "be"
    epidemiology; the kernel is published code with published parameters.
  - The run is scored ONLY against weeks the pool never saw (temporal
    holdout), by calibrate.py. What-if deltas may attach to a run only when
    its calibration score clears the publication threshold.

Deterministic given a seed: same seed + same model = same trace.
"""
import json
import math
import random
from dataclasses import dataclass, field

COHORTS = {
    # share of population, baseline weekly contacts, care-seek propensity
    "school_household": {"share": 0.34, "contacts": 22, "care_seek": 0.55},
    "working_adult":    {"share": 0.38, "contacts": 14, "care_seek": 0.40},
    "elder":            {"share": 0.16, "contacts": 6,  "care_seek": 0.75},
    "essential_worker": {"share": 0.12, "contacts": 18, "care_seek": 0.35},
}


@dataclass
class Agent:
    idx: int
    cohort: str
    susceptibility: float          # 0.7 .. 1.3, fixed per agent
    state: str = "S"               # S / I / R
    weeks_infected: int = 0
    weeks_recovered: int = 0
    decisions: list = field(default_factory=list)


def mock_model(agent: Agent, card: dict) -> dict:
    """Rule-based stand-in for an LLM caller — same I/O contract, zero spend.
    Behavior: contacts scale down as local ILI rises; school households pull
    kids at high ILI; care-seeking rises with perceived severity."""
    ili = card["local_ili_pct"]
    caution = max(0.45, 1.0 - 0.055 * ili)          # at 10% ILI -> ~0.45
    contacts = COHORTS[agent.cohort]["contacts"] * caution
    attend = not (agent.cohort == "school_household" and ili > 7.0)
    if not attend:
        contacts *= 0.4
    seek = COHORTS[agent.cohort]["care_seek"] * (1.0 + 0.04 * ili)
    return {"contact_factor": round(contacts / COHORTS[agent.cohort]["contacts"], 3),
            "attend_school": attend, "care_seek": round(min(seek, 0.95), 3)}


REPORTING_FRACTION = 0.30


@dataclass
class SimResult:
    weekly_ili_pct: list           # simulated %ILI-like incidence per week
    trace: list                    # per-week aggregates + sampled agent decisions
    params: dict
    weekly_states: list = field(default_factory=list)   # per-week "SIR" string per agent (animation)
    planner_trace: list = field(default_factory=list)   # batched-model rationales, when used


def run_sim(n_agents: int, seed_weeks_ili: float, n_weeks: int,
            model=mock_model, seed: int = 42,
            intervention: dict | None = None,
            import_rate: float = 0.0, waning_weeks: int | None = None) -> SimResult:
    """Seed: initial infected share = last observed real %ILI / 100.
    Intervention (optional): {"close_schools_week": k} — forces
    attend_school=False for school households that week (the what-if lever).

    v1 dynamics (a priori, documented — defaults reproduce v0 exactly):
    - import_rate: expected imported infections per week from outside the
      pool (real seasons are reseeded; naive pools burn out without this).
    - waning_weeks: recovered agents return to susceptible after this many
      weeks (immunity is not a one-way door across a season).

    Model contract: either a per-agent callable model(agent, card)->decision,
    or a batch planner with plan_week(week, cohort, card)->cohort params,
    from which per-agent decisions are sampled with the run RNG (traced).
    """
    rng = random.Random(seed)
    agents = []
    idx = 0
    for cohort, spec in COHORTS.items():
        for _ in range(round(n_agents * spec["share"])):
            agents.append(Agent(idx, cohort, susceptibility=rng.uniform(0.7, 1.3)))
            idx += 1
    # seed infections
    n_seed = max(1, round(len(agents) * seed_weeks_ili / 100.0))
    for a in rng.sample(agents, n_seed):
        a.state, a.weeks_infected = "I", 1

    base_transmission = 0.055      # per-contact weekly infection pressure (kernel param)
    weekly, trace, weekly_states, planner_trace = [], [], [], []
    prev_ili = seed_weeks_ili
    planner = getattr(model, "plan_week", None)
    for wk in range(n_weeks):
        infected = [a for a in agents if a.state == "I"]
        prevalence = len(infected) / len(agents)
        decisions = {}
        sample = []
        cohort_params = {}
        if planner is not None:
            for cohort in COHORTS:
                card = {"week": wk, "local_ili_pct": prev_ili, "prevalence_pct": round(100 * prevalence, 2),
                        "school_open": not (intervention and intervention.get("close_schools_week") == wk)}
                p = planner(wk, cohort, card)
                cohort_params[cohort] = p
                planner_trace.append({"week": wk, "cohort": cohort, "card": card, "params": p})
        for a in agents:
            card = {"week": wk, "local_ili_pct": prev_ili,
                    "school_open": not (intervention and intervention.get("close_schools_week") == wk)}
            if planner is not None:
                p = cohort_params[a.cohort]
                cf = min(1.2, max(0.1, rng.gauss(p["contact_factor_mean"], p["contact_factor_sd"])))
                d = {"contact_factor": round(cf, 3),
                     "attend_school": rng.random() < p.get("attend_prob", 1.0),
                     "care_seek": p["care_seek"]}
                if not d["attend_school"] and a.cohort == "school_household":
                    d["contact_factor"] = round(d["contact_factor"] * 0.4, 3)
            else:
                d = model(a, card)
            if intervention and intervention.get("close_schools_week") == wk and a.cohort == "school_household":
                d = {**d, "attend_school": False, "contact_factor": d["contact_factor"] * 0.4}
            decisions[a.idx] = d
            if a.idx % max(1, len(agents) // 8) == 0:
                sample.append({"agent": a.idx, "cohort": a.cohort, "card": card, "decision": d})
        # kernel: new infections among susceptibles
        new_cases = 0
        for a in agents:
            if a.state != "S":
                continue
            pressure = base_transmission * prevalence * 100 * decisions[a.idx]["contact_factor"] * a.susceptibility
            if rng.random() < min(pressure, 0.9):
                a.state, a.weeks_infected, new_cases = "I", 0, new_cases + 1
        # imported cases (v1 dynamics; skipped entirely at rate 0 = v0)
        if import_rate > 0:
            n_import = int(import_rate) + (1 if rng.random() < import_rate % 1 else 0)
            sus = [a for a in agents if a.state == "S"]
            for a in rng.sample(sus, min(n_import, len(sus))):
                a.state, a.weeks_infected = "I", 1
                new_cases += 1
        # progress / recover (infectious ~1 week at this granularity)
        for a in agents:
            if a.state == "I":
                a.weeks_infected += 1
                if a.weeks_infected >= 2:
                    a.state, a.weeks_recovered = "R", 0
            elif a.state == "R" and waning_weeks is not None:
                a.weeks_recovered += 1
                if a.weeks_recovered >= waning_weeks:
                    a.state = "S"
        # Reporting: wILI is % of outpatient visits, not population incidence.
        # A priori assumption (documented, not fit): ~30% of infections
        # present as an ILI visit. REPORTING_FRACTION lives in params.
        ili_pct = 100.0 * new_cases / len(agents) * REPORTING_FRACTION
        weekly.append(round(ili_pct, 3))
        trace.append({"week": wk, "new_cases": new_cases, "prevalence": round(prevalence, 4),
                      "sim_ili_pct": ili_pct, "sample_decisions": sample})
        weekly_states.append("".join(a.state for a in agents))
        prev_ili = ili_pct
    params = {"n_agents": len(agents), "seed_ili_pct": seed_weeks_ili, "n_weeks": n_weeks,
              "base_transmission": base_transmission, "reporting_fraction": REPORTING_FRACTION,
              "seed": seed, "import_rate": import_rate, "waning_weeks": waning_weeks,
              "intervention": intervention, "model": getattr(model, "__name__", str(model))}
    return SimResult(weekly, trace, params, weekly_states, planner_trace)
