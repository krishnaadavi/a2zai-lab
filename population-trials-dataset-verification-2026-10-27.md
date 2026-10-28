# Population Trials — dataset verification addendum
Checked Tue Oct 27, 2026 (late morning CT), against primary sources.
Companion to population-trials-vision-2026-10-27.md — where this file disagrees, this file wins.

## Verdict in one line
The vision holds. Two numbers need fixing before anything public quotes them, and the
flu flagship gets *stronger* locally: Dallas County publishes its own school/ED flu
series, which is a better calibration key than national ILINet alone.

## 1. School Flu Season — VERIFIED, with a local upgrade
- CDC ILINet age table is real and weekly, with a **5–24 years** band (plus 0–4, 25–49,
  50–64, 65+). Example verified table: 2024–2025 season, Week 45, CDC FluView archive.
  That band is school-age + college, not school-only — say "5–24" in public copy, not "school-age" alone.
  Source: https://www.cdc.gov/flu/weekly/weeklyarchives2024-2025/data/iliage45.html
- NOT verified in this check: the vision doc's "2,700+ providers / 30M+ visits/year" line.
  Do not quote it publicly until checked on CDC's ILINet methods page.
- **Dallas County upgrade (new):** Dallas County Health and Human Services (DCHHS)
  publishes (a) syndromic surveillance of ED visits for ILI from **18 Dallas County EDs**
  via ESSENCE, and (b) **"Percentage of Student Absences Due to ILI by Week, Dallas County"**
  for 2018–2019 and 2022–2024 seasons. That is a county-level, school-specific answer key
  sitting in Krish's home county — use DCHHS as the prototype's calibration target and
  ILINet (Texas / national) as context, not the other way round.
  Source: DCHHS 2023–2024 Influenza Weekly Report, week ending 12/9/2023 (dallascounty.org PDF).
  DCHHS also maintains a Respiratory Virus Surveillance Dashboard (weekly, Dallas County /
  Texas / US lab data).
- Hugging Face: a search for HF flu/ILINet datasets returned no ILINet mirror — only
  unrelated medical QA sets. Plan on pulling flu data from **CDC FluView + DCHHS directly**,
  and mirroring it into the Lab ourselves. HF is a distribution convenience, not the source.

## 2. Crime Map — VERIFIED dataset, WRONG count in the vision doc
- Chicago Crimes — 2001 to Present is real: Chicago Police CLEAR system, via Chicago Data
  Portal and catalog.data.gov, **addresses at block level only** for victim privacy,
  minus the most recent 7 days. Dataset last updated **Oct 21, 2026** per data.gov.
  Source: https://catalog.data.gov/dataset/crimes-2001-to-present
- **Correction:** the vision doc says "2.7M incidents." That understates the full file by
  roughly 3x. A peer-reviewed comparative study counts **7,724,493 records, 1.17 GB,
  2001–2023, 22 columns**; an ArcGIS sample counts 7,061,128 records through Jan 2020.
  Public copy should say "7.7M+ incidents since 2001" or scope the number explicitly
  (e.g. a filtered violent-crime subset) and name the filter.
- Scoring claim still holds: predicted hotspot vs. actual next-month incidents is computable
  from date + beat/block fields in this dataset.

## 3. Screening Gap — row count VERIFIED exactly, citation should change
- The **11,048,853 incidence rows** figure is exact — verified in the medRxiv paper
  describing the versioned State Cancer Profiles archive: the 2026-08-24 release totals
  **20,275,578 rows across four topics** (incidence 11,048,853; mortality 5,866,632;
  demographics 3,281,295; screening/risk 78,798), **3,193 county-level area codes**,
  ~383 MB gzipped CSV / ~132 MB Parquet, with Zenodo vintage DOIs
  (V1 10.5281/zenodo.12685787; V2 10.5281/zenodo.22085047; V3 10.5281/zenodo.22085273).
  Source: https://www.medrxiv.org/content/medrxiv/early/2026/08/27/2026.08.24.26361254.full.pdf
- **Citation fix:** this check did NOT confirm a Hugging Face repo named
  `seandavis/state-cancer-profiles`. Sean Davis does maintain a state-cancer-profiles
  programmatic-access project, but the verifiable, citable source is
  **statecancerprofiles.cancer.gov + the Zenodo archive above**. Use those in public copy
  until the HF repo is opened directly and its card read.
- Framing in the vision doc stands: county-level, planning only, never patient advice.
  Note the archive paper's suppression point — earlier vintages are preserved as-scraped
  without retroactive suppression columns, so the dataset card must state the vintage used.

## Prototype tightening (flu first, if Trial #2 lands Sat Oct 31)
- Calibration target: DCHHS Dallas County student-absence ILI % + ED ILI, one full season.
- Holdout design unchanged: pool sees weeks up to N, must reproduce N+1 onward; score is
  curve distance on the held-out weeks, printed on every what-if.
- 100 agents first is still the right bound; 1,000 is a config change after the harness holds.
- Name check: nothing in this verification changes the Nov 4 placement — closing beat only.

## What remains unverified
- ILINet provider/visit totals (above).
- HF repo name for the cancer mirror (above).
- Chicago count after 2023 (data.gov is current to Oct 2026, but the 7.7M count is 2001–2023).
