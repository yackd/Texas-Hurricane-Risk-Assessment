# Texas Hurricane Actuarial Risk Assessment Suite

## Overview 

A five-phase Python pipeline that ingests, cleans, and synthesizes three independent U.S. government data sources — NOAA's complete Atlantic hurricane history, FEMA's live emergency shelter registry, and the U.S. Census Bureau's zip code reference data — into a single actuarial-style hurricane risk score for any zip code in Texas. Built as an independent passion project exploring the intersection of software engineering and actuarial science, the suite combines real historical storm data, geospatial distance matching (the Haversine formula), and a weighted composite scoring model to answer a simple question with real data: how exposed is this Texas community to hurricanes, historically speaking, and how well-positioned is it to respond? The project can evaluate a single zip code interactively or generate a full, ranked risk report across every zip code in the state.

## Features 

- Downloads and locally caches NOAA's complete 1851–2025 Atlantic hurricane archive (HURDAT2), parsing its raw, non-standard text format from scratch
- Filters 174 years of storm history down to just the landfalls that struck the Texas coast, using real latitude/longitude bounding-box and landfall-marker logic
- Connects live to FEMA's National Shelter System API to pull real, currently-active emergency shelter locations and capacities
- Builds a complete reference table of every Texas zip code's coordinates from the U.S. Census Bureau's official Gazetteer files
- Uses the Haversine great-circle distance formula to measure real-world distance (not flat-map approximation) between any zip code, historical storm, and emergency shelter
- Computes a weighted, 0–100 actuarial-style risk score with a diminishing-returns (square-root) frequency term, a risk tier classification, and identifies the nearest active shelter
- Supports both a single-zip interactive lookup and a full statewide "ALL" mode that ranks and exports every Texas zip code's risk profile to CSV
- Runs entirely on Python's standard library — no external packages required

## Project Structure (Phases 1–5)

| Phase | File | Purpose |
|---|---|---|
| 1 | `hurricanes.py` | **Data Ingestion Spider.** Downloads and caches NOAA's raw HURDAT2 text archive, parses its custom storm-header/track-point format, and validates the parse with a summary report. |
| 2 | `database.py` | **Texas Landfall Database.** Filters the raw archive down to storms that made landfall within a Texas coastal bounding box, and stores them in a structured SQLite table (`TX_Storms`). |
| 3 | `shelters.py` | **Emergency Shelter Integration.** Queries FEMA's live ArcGIS-hosted shelter API for currently-active Texas shelters and stores them (`Emergency_Shelters`). |
| 4 | `zip_codes.py` | **Statewide Zip Code Reference.** Downloads the Census Bureau's national Gazetteer file, filters it to Texas zip codes, and stores every one's coordinates (`TX_ZipCodes`). |
| 5 | `risk.py` | **Actuarial Risk Engine.** The final synthesis phase — combines all three tables using Haversine distance matching to score a single zip code or the entire state. |

All five phases share one database file: `texas_hurricanes.sqlite`.

## Installation & Requirements

- Python 3.8 or later (developed and tested on Python 3.14)
- No external packages or `pip install` required — every phase runs entirely on Python's built-in standard library (`sqlite3`, `urllib`, `json`, `time`, `math`, `os`, `zipfile`)
- An internet connection (required only the first time each phase runs — every phase caches its downloaded data locally and will not re-download on later runs)

## How to Run

Run the phases from the same folder, in this order:

```bash
python3 hurricanes.py     # Phase 1 -- downloads and validates the raw NOAA archive
python3 database.py       # Phase 2 -- builds the Texas storm database (needs Phase 1's output)
python3 shelters.py       # Phase 3 -- pulls live FEMA shelter data (independent)
python3 zip_codes.py      # Phase 4 -- builds the statewide zip code table (independent)
python3 risk.py           # Phase 5 -- run the risk engine (needs Phases 2, 3, and 4)
```

Phases 3 and 4 don't depend on each other or on Phases 1/2, and can be run in any order relative to them — but Phase 5 requires Phases 2, 3, and 4 to have all been run at least once first, since it reads from all three of their tables.

## Example Output

**Single zip code lookup:**
```
=========================================================
           TEXAS HURRICANE RISK ASSESSMENT PLATFORM
=========================================================
Enter a Texas zip code, or type ALL, for a statewide risk report : 77550

PERSONAL ACTUARIAL STATEMENT
Target Postal Zone: 77550
Assessed Risk Level: 91/100 (CRITICAL / HIGH RISK ZONE)
---------------------------------------------------------
Regional Historical Data Summary (within 75 miles):
 - Documented Nearby Landfalls: 47 storms
 - Peak Historic Wind Velocity: 145 knots
 - Minimum Core Atmospheric Pressure: 908 mb
---------------------------------------------------------
EMERGENCY PREPAREDNESS ROUTING PROFILE:
 STATUS: No active Federal emergency shelters are currently open.
 ACTION: Monitor local NOAA and Red Cross alerts for shelter activations.
=========================================================
```
*(Illustrative example — actual scores depend on the live data pulled at runtime.)*

**Statewide `ALL` mode** scores every Texas zip code, writes a full ranked report to `texas_statewide_risk_report.csv`, and prints a top-10 summary to the console.

## Technologies Used

- **Language:** Python 3
- **Database:** SQLite3
- **Data formats parsed:** raw fixed-format text (HURDAT2), JSON (FEMA ArcGIS REST API), pipe-delimited text (Census Gazetteer)
- **Core algorithm:** the Haversine great-circle distance formula
- **APIs:** FEMA ArcGIS REST FeatureServer query API

## Data Sources & Works Cited

This project is built entirely on public, primary-source government data:

- **NOAA / National Hurricane Center** — HURDAT2 Atlantic hurricane database (1851–2025)
- **FEMA** — National Shelter System, Open Shelters feed (synced from the American Red Cross)
- **U.S. Census Bureau** — Gazetteer Files, ZIP Code Tabulation Areas (ZCTA)

Full citations, including the Haversine formula's original published source, are in [`works_cited.txt`](./works_cited.txt).

## Limitations

- The risk score is an educational, illustrative model built for this project — it is **not** a production actuarial pricing model. Real catastrophe models simulate thousands of physically-based storm scenarios; this uses a simplified weighted formula over historical frequency, wind, and pressure.
- FEMA's shelter feed reflects only **currently-activated** shelters, not a year-round inventory of every possible shelter site — it is expected and normal to see zero results outside an active disaster.
- Texas zip codes are identified by their numeric prefix (750xx–799xx) rather than an exact state-boundary match, so a small number of edge-case zip codes may be mis-classified.
- The 75-mile search radius and the scoring formula's weighting constants are reasoned approximations, not derived from formal actuarial ratemaking methodology (no credibility weighting, trend factors, or regulatory review).
- Each row in `TX_Storms` represents one recorded landfall track point, which does not always correspond one-to-one with a single distinct storm (a storm can make landfall more than once).

## Future Improvements

- Replace the zip-code filter with an exact Texas state-boundary match
- Incorporate a broader, FEMA facility inventory alongside the live "currently open" shelter feed, for a year-round resilience metric
- Explore a PageRank-style risk model across a storm/zip-code exposure graph, rather than a single static formula
- Add a D3.js force-directed visualization of the storm/zip code/shelter network
- Build a simple web or GUI front end in place of the console interface

## License

This project's code is licensed under the MIT License — see [`LICENSE`](./LICENSE) for details. All underlying data sources (NOAA, FEMA, and the U.S. Census Bureau) are U.S. government works and are in the public domain.

## Author

Sawayne Y.
Built as an independent passion project exploring the intersection of software engineering and actuarial science.
