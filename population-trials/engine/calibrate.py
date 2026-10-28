#!/usr/bin/env python3
"""Population Trials — calibration scorer.

Scores a simulated weekly curve against the REAL holdout weeks the pool
never saw. Three components, Lab-style (points + a hard gate):

  curve shape   40  Pearson correlation, mapped (r<=0 -> 0, r=1 -> 40)
  peak timing   30  exact peak week = 30, -10 per week of error
  magnitude     30  total simulated vs real ILI mass: 30 * (1 - |log10 ratio|),
                    floored at 0 (a 10x miss scores 0)

  GATE: peak off by >= 3 weeks caps the total at 49 — a simulation that
  misses WHEN it happens has not earned the right to advise, whatever its
  shape. (Same gate philosophy as Trial #1: miss the trap, cap the score.)

PUBLICATION RULE (prototype threshold, to be ratified): what-if deltas may
be published from a pool only when its calibration score >= 70. Below that,
the Lab publishes the failure, not conclusions.
"""
import math

PUBLICATION_THRESHOLD = 70


def _pearson(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, b_ in zip(a, b) for y in [b_])
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else 0.0


def score(sim: list[float], real: list[float]) -> dict:
    assert len(sim) == len(real) and len(sim) >= 4, "need >=4 aligned weeks"
    r = _pearson(sim, real)
    shape = max(0.0, r) * 40.0
    peak_err = abs(sim.index(max(sim)) - real.index(max(real)))
    peak = max(0.0, 30.0 - 10.0 * peak_err)
    ratio = (sum(sim) + 1e-9) / (sum(real) + 1e-9)
    magnitude = max(0.0, 30.0 * (1.0 - abs(math.log10(ratio))))
    total = shape + peak + magnitude
    gate = None
    if peak_err >= 3:
        gate = f"peak timing off by {peak_err} weeks (>=3) — capped at 49"
        total = min(total, 49.0)
    total = round(total, 1)
    return {
        "calibration_score": total,
        "components": {"curve_shape_40": round(shape, 1), "peak_timing_30": round(peak, 1),
                       "magnitude_30": round(magnitude, 1)},
        "pearson_r": round(r, 3), "peak_week_error": peak_err,
        "magnitude_ratio_sim_over_real": round(ratio, 3),
        "gate_applied": gate,
        "may_publish_whatifs": total >= PUBLICATION_THRESHOLD and gate is None,
        "publication_threshold": PUBLICATION_THRESHOLD,
    }
