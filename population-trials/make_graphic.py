#!/usr/bin/env python3
"""Render a run's poster card: sim vs real curves + score + the value line.

The Lab's standing rule (Krish, Oct 27): value must be visible ON the
artifact — problem, score, and what it means travel inside the image, so a
screenshot alone carries the argument. Palette: navy/orange on cream.

Usage: python3 make_graphic.py runs/<run-name> <out.png> [title] [subtitle]
"""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
NAVY, ORANGE, CREAM, INK = "#1B2A4A", "#E8762D", "#FBF6EA", "#232323"


def main():
    run = HERE / sys.argv[1]
    out = pathlib.Path(sys.argv[2])
    title = sys.argv[3] if len(sys.argv) > 3 else "1,000 AGENTS vs. A REAL FLU SEASON"
    subtitle = sys.argv[4] if len(sys.argv) > 4 else (
        "Population Trials · A2ZAI Lab — Texas flu, fall 2025 (CDC ILINet)\n"
        "the pool never saw these weeks")
    d = json.loads((run / "result.json").read_text())
    real, sim, s = d["real_wili"], d["sim_ili_pct"], d["score"]
    wk = list(range(1, len(real) + 1))

    fig, ax = plt.subplots(figsize=(12, 8.6), dpi=110)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)
    ax.plot(wk, real, color=NAVY, lw=3.4, marker="o", ms=5,
            label="REALITY — the season as it happened")
    ax.fill_between(wk, real, color=NAVY, alpha=0.10)
    ax.plot(wk, sim, color=ORANGE, lw=3.0, ls="--", marker="s", ms=5,
            label="THE POOL — 1,000 agents, stand-in behavior (v0)")
    rp, sp = real.index(max(real)), sim.index(max(sim))
    ax.annotate(f"real peak {max(real):.1f}\nweek {rp + 1}", (rp + 1, max(real)),
                textcoords="offset points", xytext=(-64, 14), fontsize=11, color=NAVY, weight="bold")
    ax.annotate(f"pool peak {max(sim):.1f}\nweek {sp + 1} — then burnout", (sp + 1, max(sim)),
                textcoords="offset points", xytext=(16, 6), fontsize=11, color=ORANGE, weight="bold")
    ax.set_xlabel("weeks into the holdout (the part of the season the pool never saw)", fontsize=11.5)
    ax.set_ylabel("influenza-like illness (%)", fontsize=11.5)
    ax.set_title(f"{title}\n{subtitle}", fontsize=16.5, weight="bold", color=INK, loc="left", pad=14)
    ax.legend(fontsize=11.5, frameon=False, loc="upper right")
    ax.grid(axis="y", color="#D8CFBB", lw=0.7)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    fig.text(0.065, 0.155,
             f"CALIBRATION SCORE:  {s['calibration_score']} / 100   —   peak missed by "
             f"{s['peak_week_error']} weeks",
             fontsize=14.5, weight="bold", color=NAVY)
    fig.text(0.065, 0.118, "→ what-if conclusions NOT published (the Lab gate)",
             fontsize=13, weight="bold", color=ORANGE)
    fig.text(0.065, 0.072,
             "A demo shows you agents moving. A test tells you whether to believe them.\n"
             "This pool failed — so the Lab publishes the failure, fixes the mechanism, and runs it again.",
             fontsize=12.5, color=INK)
    fig.text(0.065, 0.018, "A2ZAI Lab · a2zai.ai/lab · AI Systems Brief — Krish Adavi",
             fontsize=11, color="#6B6250")
    fig.tight_layout(rect=(0, 0.21, 1, 1))
    fig.savefig(out, facecolor=CREAM)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
