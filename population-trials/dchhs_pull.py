#!/usr/bin/env python3
"""Pull Dallas County (DCHHS) student-absence ILI data — the flagship
calibration key for Population Trials.

Source: DCHHS weekly Influenza Surveillance Reports (PDFs, dallascounty.org).
Finding (verified Oct 28, 2026): the reports publish NO data table for the
two county series. The numbers live in Figure 4, "Percentage of Student
Absences Due to ILI by Week, Dallas County" (page 3). Crucially, Figure 4
is a *native vector chart* — each season is a stroked polyline path in the
PDF, so the plotted coordinates can be recovered exactly (to the chart's
own rendering quantization, ~0.003 percentage points) instead of guessed
from pixels. The axis labels are real text, so each PDF calibrates itself:
a linear fit of label value vs. label position, per PDF, no hardcoding.

Figure 3 (syndromic ED ILI visits, 18 Dallas County EDs) is NOT vector:
it is a single raster image (1519x637 px in the 2024-25 report) of ~960
*daily* ESSENCE points. There is no ED data table and no ED number in the
report prose, so a weekly ED series cannot be extracted to scored-run
standard from the public reports — it would need a DCHHS/ESSENCE data
export. This loader therefore covers the student-absence series only and
says so in the receipt.

Method, honestly stated: this is vector-coordinate extraction from the
published chart, not a republished data table. It is cross-validated two
independent ways before anything is written (see the receipt):
  1. Prose check — every report's Epidemiologic Summary states that
     week's absence % in words; it must match the extracted point for
     the report's own season/week (prose is rounded to 2 decimals).
  2. Overlap check — seasons 2022-23 and 2023-24 are charted in BOTH the
     2023-24 and the 2024-25 season-final reports; the two independent
     extractions must agree point-by-point.

Weeks with no polyline segment are no-report weeks (the chart breaks the
line, mostly school holidays — the HOLIDAY bands in Figure 4). They are
recorded as gaps, never interpolated. Isolated points at ~0.00% sitting
far below both neighbours are flagged `suspected_no_report_plotted_as_zero`
(Excel plots a missing value as zero; a real 0.00% between two 0.03%+
weeks, mid-season, is not credible) — the value is kept, the flag is the
honesty, and calibration code should mask flagged points as missing.

Requires: pdftocairo + pdftotext (poppler) on PATH. Stdlib otherwise,
same conventions as data_pull.py. Outputs, in data/:
  dchhs_dallas_student_absence_ili.csv            (all seasons, tidy)
  dchhs_dallas_student_absence_ili_<season>.csv   (per season)
  dchhs_pull_receipt.json                         (the pull receipt)
"""
import csv
import json
import math
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).parent
UA = {"User-Agent": "a2zai-lab-prototype/0.1"}

# Season-final reports (Surveillance Week 16) — Figure 4 of the later
# report re-charts the earlier seasons, which is what makes the overlap
# cross-check possible. Extraction prefers the LATEST report per season.
EXTRACTION_REPORTS = [
    {
        "report_season": "2024-2025",
        "url": "https://www.dallascounty.org/Assets/uploads/docs/hhs/influenza-surveillance/2025/Influenza-Weekly-Report-Week-16-Ending-4.19.2025.pdf",
        "figure_page": 3,
    },
    {
        "report_season": "2023-2024",
        "url": "https://www.dallasCounty.org/Assets/uploads/docs/hhs/influenza-surveillance/2024/Influenza%20Weekly%20Report%20Week%20Ending%204-20-2024-1.pdf",
        "figure_page": 3,
    },
]
# Mid-season report used for prose validation only (its Figure 4 is a
# partial-season chart; its summary sentence is an independent check of
# the 2023-24 week-49 point extracted from the season-final reports).
PROSE_ONLY_REPORTS = [
    {
        "report_season": "2023-2024",
        "url": "https://www.dallascounty.org/Assets/uploads/docs/hhs/influenza-surveillance/2023/Influenza%20Weekly%20Report%20Week%20ending%2012-9-2023.pdf",
    },
]
SERIES_ID = "dchhs_student_absence_ili_pct"
SOURCE_ID = "DCHHS Influenza Surveillance Report, Figure 4 (dallascounty.org)"


# ---------------------------------------------------------------- download
def fetch_pdf(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if data[:4] != b"%PDF":
        raise RuntimeError(f"Not a PDF: {url}")
    return data


def run_tool(args: list[str]) -> None:
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{args[0]} failed: {p.stderr.strip()[:300]}")


# ---------------------------------------------------------------- pdf text
WORD_RE = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]+)</word>'
)


def pdf_words(pdf: pathlib.Path, page: int) -> list[dict]:
    out = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-bbox", str(pdf), "-"],
        capture_output=True, text=True, check=True,
    ).stdout
    words = []
    for xmin, ymin, xmax, ymax, text in WORD_RE.findall(out):
        xmin, ymin, xmax, ymax = float(xmin), float(ymin), float(xmax), float(ymax)
        words.append({
            "text": text, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
            "cx": (xmin + xmax) / 2, "cy": (ymin + ymax) / 2,
        })
    return words


def pdf_text(pdf: pathlib.Path) -> str:
    out = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True, text=True, check=True,
    ).stdout
    return re.sub(r"\s+", " ", out)


def prose_absence_value(text: str) -> tuple[float, int] | None:
    """The Epidemiologic Summary sentence, e.g. '...0.09% was attributed to
    influenza-like illness during week 49 of the schools reporting...' or
    the 2024-25 phrasing 'out of the total enrollment, 0.05% of absences
    were attributed to influenza-like illness during week 16...'."""
    m = re.search(
        r"(\d+\.\d+)%[^.]{0,120}?attributed to influenza-like illness during week\s+(\d+)",
        text,
    )
    if not m:
        return None
    return float(m.group(1)), int(m.group(2))


# ---------------------------------------------------------------- svg paths
def parse_matrix(t: str):
    m = re.match(r"matrix\(([^)]+)\)", t.strip())
    if not m:
        return None
    vals = [float(v) for v in re.split(r"[,\s]+", m.group(1).strip())]
    return vals if len(vals) == 6 else None


def compose(m1, m2):
    """Affine composition m1 after m2 (column-vector convention)."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return [
        a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1,
    ]


IDENT = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]


def svg_paths(svg_file: pathlib.Path):
    """Yield (stroke, stroke_width, segments) in absolute page coordinates.
    segments = list of polylines; each polyline = [(x, y), ...]. A new
    polyline starts at each M command — in Figure 4, a break in the line
    is a no-report week, so segment structure is data."""
    tree = ET.parse(svg_file)
    results = []

    def walk(elem, mat):
        t = elem.get("transform")
        if t:
            m = parse_matrix(t)
            if m:
                mat = compose(m, mat) if mat is not IDENT else m
        if elem.tag.endswith("path"):
            d = elem.get("d") or ""
            pts = re.findall(r"([ML])\s+(-?[\d.]+)\s+(-?[\d.]+)", d)
            if pts:
                segs, cur = [], None
                a, b, c, dd, e, f = mat
                for cmd, xs, ys in pts:
                    x, y = float(xs), float(ys)
                    ax, ay = a * x + c * y + e, b * x + dd * y + f
                    if cmd == "M":
                        cur = []
                        segs.append(cur)
                    if cur is not None:
                        cur.append((ax, ay))
                results.append({
                    "stroke": elem.get("stroke") or "",
                    "width": float(elem.get("stroke-width") or 0),
                    "segments": segs,
                    "n_points": sum(len(s) for s in segs),
                })
        for child in elem:
            walk(child, mat)

    walk(tree.getroot(), IDENT)
    return results


# ---------------------------------------------------------------- fitting
def linfit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Least squares y = a*x + b; returns (a, b, max_abs_residual)."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    a = sxy / sxx
    b = my - a * mx
    resid = max(abs(a * x + b - y) for x, y in zip(xs, ys))
    return a, b, resid


SEASON_WORD_RE = re.compile(r"^(\d{4})[–—-](\d{4})$")
PCT_WORD_RE = re.compile(r"^(\d+\.\d+)%$")


def extract_figure4(pdf: pathlib.Path, page: int, tmp: pathlib.Path) -> dict:
    words = pdf_words(pdf, page)
    svg_file = tmp / f"fig{page}.svg"
    run_tool(["pdftocairo", "-svg", "-f", str(page), "-l", str(page),
              str(pdf), str(svg_file)])
    paths = svg_paths(svg_file)

    # --- y calibration: "%" axis labels are real text on the left margin
    y_labels = []
    for w in words:
        m = PCT_WORD_RE.match(w["text"])
        if m and w["xmax"] < 125:
            y_labels.append((w["cy"], float(m.group(1))))
    if len(y_labels) < 4:
        raise RuntimeError(f"Only {len(y_labels)} y-axis % labels found — chart layout changed?")
    ya, yb, y_resid = linfit([c for c, _ in y_labels], [v for _, v in y_labels])
    zero_label_cy = max(c for c, v in y_labels if v == 0.0)

    # --- x calibration: CDC-week labels sit just under the x-axis
    week_labels = []
    for w in words:
        if w["text"].isdigit() and 1 <= int(w["text"]) <= 53:
            if zero_label_cy < w["cy"] < zero_label_cy + 22 and w["xmin"] > 120:
                week_labels.append((w["cx"], int(w["text"])))
    week_labels.sort()
    if len(week_labels) < 6:
        raise RuntimeError(f"Only {len(week_labels)} week labels found — chart layout changed?")
    start_week = week_labels[0][1]
    # Wrapped season sequence: start_week..52, 1, 2, ...
    seq = list(range(start_week, 53)) + list(range(1, 54))
    label_ord = [(cx, seq.index(wk)) for cx, wk in week_labels]
    xa, xb, x_resid = linfit([c for c, _ in label_ord], [o for _, o in label_ord])

    def week_of_x(x: float) -> int:
        ordinal = int(round(xa * x + xb))
        if ordinal < 0 or ordinal >= len(seq):
            raise RuntimeError(f"Point x={x} maps outside the week sequence")
        return seq[ordinal]

    # --- legend: season words (right side) matched to swatch lines by y
    legend_words = []
    for w in words:
        m = SEASON_WORD_RE.match(w["text"])
        if m and w["xmin"] > 400:
            legend_words.append({
                "season": f"{m.group(1)}-{m.group(2)}", "cy": w["cy"],
            })
    swatches = [p for p in paths if p["width"] >= 2 and p["n_points"] == 2]
    season_by_color = {}
    for sw in swatches:
        y = sw["segments"][0][0][1]
        nearest = min(legend_words, key=lambda lw: abs(lw["cy"] - y))
        if abs(nearest["cy"] - y) > 4:
            raise RuntimeError("Legend swatch does not line up with any season label")
        season_by_color[sw["stroke"]] = nearest["season"]
    if len(season_by_color) < 2:
        raise RuntimeError(f"Legend mapping failed: {season_by_color}")

    # --- series: thick paths with many points
    series = {}
    for p in paths:
        if p["width"] < 2 or p["n_points"] < 5:
            continue
        season = season_by_color.get(p["stroke"])
        if season is None:
            raise RuntimeError(f"Series path with unmapped color {p['stroke']}")
        rows = []
        for seg in p["segments"]:
            for x, y in seg:
                pct = ya * y + yb
                # Points plotted at exactly 0.00% can render up to ~1 chart
                # quantization step (~0.007 pct points) below the label-fit
                # zero line; clip those, but fail loudly beyond that.
                if pct < -0.01:
                    raise RuntimeError(f"Calibrated value {pct:.4f} < 0 — calibration is wrong")
                rows.append({
                    "week": week_of_x(x),
                    "pct": round(max(pct, 0.0), 3),
                    "segment_break_before": False,
                })
            rows[-len(seg)]["segment_break_before"] = True
        rows.sort(key=lambda r: seq.index(r["week"]))
        series[season] = rows

    return {
        "series": series,
        "calibration": {
            "y_fit": {"slope_pct_per_pt": ya, "intercept": yb,
                      "max_residual_pct_points": y_resid, "n_labels": len(y_labels)},
            "x_fit": {"slope_ordinal_per_pt": xa, "intercept": xb,
                      "max_residual_ordinal": x_resid, "n_labels": len(week_labels)},
            "week_sequence_start": start_week,
        },
    }


def flag_suspect_zeros(rows: list[dict], full_seq: list[int]) -> None:
    """In-place: flag isolated ~zero points that look like Excel's
    missing-plotted-as-zero (both neighbours >= 0.02, or a gap next door),
    plus exact zeros inside the chart's HOLIDAY bands (weeks 47-48,
    52-1, 11 — schools closed; the band weeks vary by season, so the
    neighbour/gap tests do the real work and this is only a supplement)."""
    by_week = {r["week"]: r for r in rows}
    idx = {wk: i for i, wk in enumerate(full_seq)}
    holiday_weeks = {47, 48, 52, 1, 11}
    for r in rows:
        r["quality_flag"] = ""
        if r["pct"] > 0.0035:
            continue
        i = idx[r["week"]]
        prev_wk = full_seq[i - 1] if i > 0 else None
        next_wk = full_seq[i + 1] if i + 1 < len(full_seq) else None
        prev_r = by_week.get(prev_wk) if prev_wk is not None else None
        next_r = by_week.get(next_wk) if next_wk is not None else None
        neighbours_high = (
            prev_r is not None and next_r is not None
            and prev_r["pct"] >= 0.02 and next_r["pct"] >= 0.02
        )
        beside_gap = (prev_wk is not None and prev_r is None) or \
                     (next_wk is not None and next_r is None)
        if neighbours_high or beside_gap or r["week"] in holiday_weeks:
            r["quality_flag"] = "suspected_no_report_plotted_as_zero"


def epiweek_for(season: str, week: int) -> int:
    start_year = int(season.split("-")[0])
    year = start_year if week >= 40 else start_year + 1
    return year * 100 + week


# ---------------------------------------------------------------- main
def main() -> int:
    data_dir = HERE / "data"
    data_dir.mkdir(exist_ok=True)
    pulled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    extracted = {}   # (report_season) -> {season: rows, calibration}
    prose_checks = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        jobs = [(r, True) for r in EXTRACTION_REPORTS] + \
               [(r, False) for r in PROSE_ONLY_REPORTS]
        for report, do_extract in jobs:
            pdf_bytes = fetch_pdf(report["url"])
            pdf_file = tmp / "report.pdf"
            pdf_file.write_bytes(pdf_bytes)
            # prose check for this report's own season/week
            pv = prose_absence_value(pdf_text(pdf_file))
            if pv is not None:
                prose_checks.append({
                    "report_season": report["report_season"],
                    "prose_pct": pv[0], "week": pv[1], "url": report["url"],
                    "_extract_from": report["report_season"],
                })
            if do_extract:
                got = extract_figure4(pdf_file, report["figure_page"], tmp)
                extracted[report["report_season"]] = got

    # ---- merge seasons, latest report wins; keep the overlap for the check
    by_season: dict[str, list[dict]] = {}
    by_season_source: dict[str, str] = {}
    overlap_checks = []
    report_order = [r["report_season"] for r in EXTRACTION_REPORTS]  # newest first
    for season in sorted({s for g in extracted.values() for s in g["series"]}):
        holders = [rs for rs in report_order if season in extracted[rs]["series"]]
        winner = holders[0]
        by_season[season] = extracted[winner]["series"][season]
        by_season_source[season] = winner
        if len(holders) > 1:
            other = extracted[holders[1]]["series"][season]
            a = {r["week"]: r["pct"] for r in by_season[season]}
            b = {r["week"]: r["pct"] for r in other}
            common = sorted(set(a) & set(b))
            diffs = [abs(a[w] - b[w]) for w in common]
            overlap_checks.append({
                "season": season,
                "reports_compared": holders,
                "common_weeks": len(common),
                "weeks_only_in_newer": sorted(set(a) - set(b)),
                "weeks_only_in_older": sorted(set(b) - set(a)),
                "max_abs_diff_pct_points": round(max(diffs), 4) if diffs else None,
                "mean_abs_diff_pct_points": round(sum(diffs) / len(diffs), 4) if diffs else None,
            })

    # ---- finish prose checks against extracted values
    for chk in prose_checks:
        season = chk.pop("_extract_from")
        rows = by_season.get(season, [])
        match = next((r for r in rows if r["week"] == chk["week"]), None)
        chk["extracted_pct"] = match["pct"] if match else None
        chk["abs_diff"] = (round(abs(match["pct"] - chk["prose_pct"]), 4)
                           if match else None)
        # prose is rounded to 2dp (tolerance 0.005) + chart quantization ~0.004
        chk["within_tolerance_0.01"] = (chk["abs_diff"] is not None
                                        and chk["abs_diff"] <= 0.01)

    # ---- flags, gaps, sanity
    full_seq_cache = {}
    sanity = {}
    all_rows = []
    for season, rows in sorted(by_season.items()):
        start_week = extracted[by_season_source[season]]["calibration"]["week_sequence_start"]
        seq = list(range(start_week, 53)) + list(range(1, 54))
        present = [r["week"] for r in rows]
        span = seq[seq.index(present[0]): seq.index(present[-1]) + 1]
        full_seq_cache[season] = span
        flag_suspect_zeros(rows, span)
        gaps = [wk for wk in span if wk not in set(present)]
        peak = max(rows, key=lambda r: r["pct"])
        plausible_peak = peak["week"] >= 44 or peak["week"] <= 10
        sanity[season] = {
            "rows": len(rows),
            "weeks_present": present,
            "gap_weeks_no_report": gaps,
            "min_pct": min(r["pct"] for r in rows),
            "max_pct": peak["pct"],
            "peak_week": peak["week"],
            "peak_in_plausible_flu_window_wk44_to_wk10": plausible_peak,
            "flagged_points": [
                {"week": r["week"], "pct": r["pct"], "flag": r["quality_flag"]}
                for r in rows if r["quality_flag"]
            ],
            "all_values_within_0_to_1_3_pct": all(0.0 <= r["pct"] <= 1.3 for r in rows),
        }
        for r in rows:
            all_rows.append({
                "epiweek": epiweek_for(season, r["week"]),
                "cdc_week": r["week"],
                "season": season,
                "student_absence_ili_pct": f"{r['pct']:.3f}",
                "series": SERIES_ID,
                "source": SOURCE_ID,
                "quality_flag": r["quality_flag"],
            })
    all_rows.sort(key=lambda r: (r["season"], r["epiweek"]))

    # ---- write CSVs
    fields = ["epiweek", "cdc_week", "season", "student_absence_ili_pct",
              "series", "source", "quality_flag"]
    combined = data_dir / "dchhs_dallas_student_absence_ili.csv"
    with combined.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)
    per_season_files = {}
    for season in sorted(by_season):
        short = f"{season[:4]}-{season[-2:]}"
        path = data_dir / f"dchhs_dallas_student_absence_ili_{short}.csv"
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows([r for r in all_rows if r["season"] == season])
        per_season_files[season] = path.name

    # ---- receipt
    receipt = {
        "dataset": "dchhs_dallas_student_absence_ili",
        "source": "Dallas County Health and Human Services (DCHHS), Influenza Surveillance Reports",
        "endpoint": "dallascounty.org/Assets/uploads/docs/hhs/influenza-surveillance/",
        "query": "Figure 4 (Percentage of Student Absences Due to ILI by Week), page 3, "
                 "of the season-final (Week 16) reports for 2023-2024 and 2024-2025; "
                 "2023-2024 Week 49 report used for prose validation only",
        "report_urls": [r["url"] for r in EXTRACTION_REPORTS + PROSE_ONLY_REPORTS],
        "pulled_at": pulled_at,
        "rows": len(all_rows),
        "file": f"data/{combined.name}",
        "per_season_files": per_season_files,
        "extraction_method": "Vector-coordinate extraction: Figure 4 is a native vector "
                             "chart in the PDF (one stroked polyline per season). "
                             "pdftocairo -svg recovers the polyline coordinates; "
                             "pdftotext -bbox recovers the axis labels; each PDF is "
                             "calibrated by least-squares fits of label value vs. label "
                             "position (no hardcoded scale). Line breaks in a polyline "
                             "are no-report weeks and are recorded as gaps, never filled. "
                             "Precision is bounded by the chart's rendering quantization "
                             "(~0.003 pct points on the 2024-2025 report's axis, ~0.007 on "
                             "the coarser 2023-2024 axis) plus label-fit residual "
                             "(in calibration).",
        "calibration_by_report": {
            rs: extracted[rs]["calibration"] for rs in extracted
        },
        "validation": {
            "prose_checks": prose_checks,
            "overlap_checks": overlap_checks,
            "sanity_by_season": sanity,
        },
        "ed_series_blocker": "Figure 3 (syndromic ED ILI visits, 18 Dallas County EDs via "
                             "ESSENCE) is a single raster image of daily points "
                             "(1519x637 px, 2024-2025 report) with no data table and no "
                             "ED count in the report prose. A weekly ED series cannot be "
                             "extracted to scored-run standard from the public reports; "
                             "it requires a DCHHS/ESSENCE data export (data request to "
                             "DCHHS, influenza.influenza@dallascounty.org per the reports).",
        "coverage_note": "Student-absence series only. Seasons 2022-2023 and 2023-2024 are "
                         "taken from the 2024-2025 report where available (latest revision); "
                         "2018-2019 exists only in the 2023-2024 report. 2024-2025 runs "
                         "through CDC week 16 (report week ending 4/19/2025).",
    }
    receipt_file = data_dir / "dchhs_pull_receipt.json"
    receipt_file.write_text(json.dumps(receipt, indent=2) + "\n")

    for season in sorted(by_season):
        s = sanity[season]
        print(f"{season}: {s['rows']} weeks -> {per_season_files[season]} "
              f"(peak {s['max_pct']:.3f}% @ CDC week {s['peak_week']}, "
              f"gaps {s['gap_weeks_no_report']}, flagged {len(s['flagged_points'])})")
    print(f"combined: {len(all_rows)} rows -> {combined.name}; receipt -> {receipt_file.name}")
    bad = [c for c in prose_checks if not c["within_tolerance_0.01"]]
    bad += [o for o in overlap_checks
            if o["max_abs_diff_pct_points"] is None or o["max_abs_diff_pct_points"] > 0.01]
    if bad:
        print("VALIDATION FAILURES — see receipt", file=sys.stderr)
        return 1
    print("validation: all prose + overlap checks within tolerance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
