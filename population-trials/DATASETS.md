# Population Trials — dataset registry

Rule (set Oct 27): **scored runs pull from the primary source, and the pull
itself gets a receipt** — source, endpoint, query, timestamp, row count —
filed in the run's trace bundle. Hugging Face / Kaggle mirrors are dev
fixtures only, never the basis of a scored run: they're snapshots with
unclear provenance, and receipts are the product.

## Flu — flagship (county health)

| Series | Source | Access | Status |
|---|---|---|---|
| CDC ILINet, weekly, national + state (TX), incl. age band 5–24 | CDC FluView via **Delphi epidata API** (CMU) | `delphi.cmu.edu/epidata/api.php?source=fluview` — public, no key | ✅ VERIFIED LIVE Oct 27 — TX + national 2022–23 and TX 2025–26 pulled (49 wks, peak wILI 8.32 @ 202552) |
| Student absences due to ILI by week, Dallas County schools | **DCHHS** (Dallas County Health & Human Services) weekly reports | County-published reports (PDF/dashboard) | Documented as existing (addendum Oct 27); loader = v1 work |
| Syndromic ED ILI visits, 18 Dallas County EDs | **DCHHS** | Same county reports | Same as above |

Hugging Face status: **no ILINet mirror found on HF** (checked Oct 27).
Kaggle has ILINet snapshots — fixtures only, per the rule above.

## Crime — second case

| Series | Source | Access | Status |
|---|---|---|---|
| Chicago Crimes 2001–present, 7.7M+ records, block-level | **Chicago Data Portal** (Socrata) | SODA API, dataset `ijzp-q8t2`, paginated JSON | Source + dataset ID verified Oct 27; live API pull is the crime-prototype's first task |

HF/Kaggle mirrors of Chicago crime exist and are widely used — same rule:
fixtures for development, Socrata primary for anything scored.

## Cancer — third case (planning only, never patient advice)

| Series | Source | Access | Status |
|---|---|---|---|
| State Cancer Profiles, county incidence, 11,048,853 rows | **NCI** statecancerprofiles.cancer.gov + **Zenodo** archive (DOI) | Download / archive | Row count verified exactly Oct 27. A HF repo under the name `seandavis/state-cancer-profiles` could NOT be confirmed — do not cite it |

## Pull receipt (written into every run's trace bundle)

```json
{"dataset": "ilinet_tx_2025-26", "source": "CDC ILINet via Delphi epidata",
 "endpoint": "delphi.cmu.edu/epidata/api.php?source=fluview",
 "query": "regions=tx&epiweeks=202540-202635", "pulled_at": "<iso8601>",
 "rows": 49, "file": "data/ilinet_tx_2025-26.csv"}
```
