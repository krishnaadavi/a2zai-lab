#!/usr/bin/env python3
"""A2ZAI Lab cost/time scoring — the pinned rule (ratified by Krish, Oct 26, 2026).

    cost/time points = 5 x min(1, median run cost / this run's cost)

- A run's cost is its estimated USD cost from published per-token rates,
  as recorded in the run's run_meta.json (est_cost_usd).
- The median is taken across all REAL model runs of the same trial that
  have a recorded cost. Deterministic reference runs never enter the median.
- Points are rounded to 1 decimal. The result is written as final_score.json
  beside the run's score.json; score.json itself is never modified — the
  harness record stands, this is the ratified addendum on top of it.
- "Time" is in the column's name and recorded in run_meta.json, but the
  ratified rule scores cost only: API wall time varies with load, cost does
  not lie.

Usage: python3 cost_time.py <trial_dir>   (the folder containing harness/runs/)
"""
import json, pathlib, statistics, sys

RULE = "5 x min(1, median run cost / run cost), costs from published per-token rates"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    runs_dir = pathlib.Path(sys.argv[1]).resolve() / "harness" / "runs"
    runs = []
    for run_dir in sorted(runs_dir.iterdir()):
        meta_f, score_f = run_dir / "run_meta.json", run_dir / "score.json"
        if not (meta_f.exists() and score_f.exists()):
            continue
        meta = json.loads(meta_f.read_text())
        cost = meta.get("est_cost_usd")
        if not isinstance(cost, (int, float)):
            continue
        score = json.loads(score_f.read_text())
        runs.append((run_dir, meta, score, float(cost)))
    if not runs:
        print("No costed runs found.")
        return 1
    median = statistics.median(c for _, _, _, c in runs)
    print(f"Median run cost across {len(runs)} real runs: ${median:.4f}")
    for run_dir, meta, score, cost in runs:
        pts = round(5 * min(1.0, median / cost), 1) if cost > 0 else 5.0
        total = round(float(score["subtotal_of_95"]) + pts, 1)
        final = {
            "run": run_dir.name,
            "model": meta.get("model"),
            "subtotal_of_95": score["subtotal_of_95"],
            "cost_time_points": pts,
            "total_of_100": total,
            "run_cost_usd": cost,
            "median_cost_usd": round(median, 4),
            "rule": RULE,
            "ratified": "Krish, 2026-10-26",
        }
        (run_dir / "final_score.json").write_text(json.dumps(final, indent=2))
        print(f"  {run_dir.name}: cost ${cost:.4f} -> {pts} pts -> total {total}/100")
    return 0


if __name__ == "__main__":
    sys.exit(main())
