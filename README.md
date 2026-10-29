# Biscayne Bay Water Quality Dashboard

An interactive Streamlit app for exploring water-quality data collected by an autonomous survey vehicle in Biscayne Bay, Florida.

> **Status:** Sprint 0 – project setup. Sections marked _TODO_ are filled in as later sprints are completed.

- **Live app:** _TODO – Streamlit Community Cloud URL_
- **Repository:** _TODO – GitHub URL_

## Purpose

_TODO – who the app is for and what questions it helps answer (e.g. how temperature, salinity and dissolved oxygen vary along the survey route)._

## Dataset

**File:** `biscayneBay_waterquality.csv` (provided by the course)

| Item | Detail |
|---|---|
| Location | Biscayne Bay, near Haulover (≈ 25.91° N, 80.14° W) |
| Date | February 4, 2022 |
| Duration | ≈ 16 minutes, one reading per second |
| Size | 942 rows × 69 columns |

The columns fall into three groups:

- **Position:** `Latitude`, `Longitude`, `Total Water Column (m)` (water depth)
- **Water quality:** `Temp C`, `Salinity (ppt)`, `SpCond mS/cm`, `pH`, `ODO mg/L`, `ODOsat %`, `Turbid+ NTU`, `Chl ug/L`, `BGA-PC cells/mL`
- **Vehicle telemetry:** battery, heading, fin positions, GPS quality, and so on

**Known data-quality notes**

- `Turbid+ NTU` is negative in every row, and `Chl ug/L` and `BGA-PC cells/mL` go negative in places. These are physically impossible and point to sensor calibration offsets.
- `DVL-Depth (m)` is the placeholder value `9999.99` in every row.
- Several columns never change (e.g. `Conductivity (mmhos/cm)` is always 0).
- There are three temperature columns. `Temperature (c)` and `DVL-Temperature` read 23.6–26.6 °C, while the water-quality sonde's `Temp C` reads 22.4–22.9 °C.

## How to use the app

_TODO – describe each section and widget once built._

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Project management (Agile)

The work is planned as user stories in [BACKLOG.md](BACKLOG.md) and delivered in short sprints. Each sprint ends with a working, deployed version of the app.

| Sprint | Goal |
|---|---|
| 0 | Project setup: repo, dependencies, README, backlog |
| 1 | Make it correct: finish TODOs, curate parameters, labels and legends, modular code |
| 2 | Make it polished: Overview and Insights sections, filters, layout |
| 3 | Ship it: deploy to Streamlit Community Cloud, finish docs, retrospective |

## Retrospective

_TODO – what went well, what didn't, what to change next time._
