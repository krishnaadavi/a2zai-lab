#!/usr/bin/env python3
"""Pull real CDC ILINet data via the Delphi epidata API (CMU mirror, public).

Saves weekly weighted %ILI (wili) + the 5-24 age-band ILI counts (num_age_1)
per region into data/. Source verified live Oct 27, 2026:
delphi.cmu.edu/epidata/api.php?source=fluview — result:1, real rows returned.

DCHHS Dallas County series (student absences due to ILI by week; syndromic ED
ILI from 18 Dallas County EDs) is the documented flagship calibration key —
it ships as weekly county reports, so its loader lands separately; ILINet TX
is the prototype's calibration signal until then.
"""
import csv
import json
import pathlib
import urllib.request

HERE = pathlib.Path(__file__).parent
API = "https://delphi.cmu.edu/epidata/api.php"


def pull(region: str, start: int, end: int) -> list[dict]:
    url = f"{API}?source=fluview&regions={region}&epiweeks={start}-{end}"
    req = urllib.request.Request(url, headers={"User-Agent": "a2zai-lab-prototype/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    if data.get("result") != 1:
        raise RuntimeError(f"Delphi returned result={data.get('result')}: {data.get('message')}")
    return sorted(data["epidata"], key=lambda d: d["epiweek"])


def main():
    # 2022-23 season: epiweeks 202240 .. 202335
    for region in ("tx", "nat"):
        rows = pull(region, 202240, 202335)
        out = HERE / "data" / f"ilinet_{region}_2022-23.csv"
        with out.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["epiweek", "wili", "num_ili", "num_patients", "num_age_1_ili_5_24"])
            for d in rows:
                w.writerow([d["epiweek"], d["wili"], d["num_ili"], d["num_patients"], d.get("num_age_1")])
        print(f"{region}: {len(rows)} weeks -> {out.name} "
              f"(peak wili {max(d['wili'] for d in rows):.2f} @ {max(rows, key=lambda d: d['wili'])['epiweek']})")


if __name__ == "__main__":
    main()
