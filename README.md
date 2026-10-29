# 🌊 Biscayne Bay Water Quality Dashboard

An interactive Streamlit app for exploring water-quality data collected by an autonomous survey vehicle in Biscayne Bay, Florida.

- **Live app:** _TODO – Streamlit Community Cloud URL_
- **Repository:** https://github.com/rafael-paz-esq/biscayne-bay-water-quality

Built for CIS 3590 – Internship-Ready Software Development (Prof. Gregory Reis).

## Purpose

Raw sensor logs are hard to read: this survey's CSV has 942 rows and 69 columns, most of them vehicle telemetry. The dashboard turns that file into something a student, researcher or member of the public can explore in a few minutes. It answers questions such as:

- How did temperature, salinity and dissolved oxygen change along the vehicle's route?
- Was the water saltier or fresher than the open ocean, and did that depend on depth?
- Were oxygen levels healthy for marine life?
- Which sensor readings can be trusted?

## Dataset

**File:** `biscayneBay_waterquality.csv` (provided by the course)

| Item | Detail |
|---|---|
| Location | Biscayne Bay, near Haulover Inlet (≈ 25.91° N, 80.14° W) |
| Date | February 4, 2022 |
| Duration | ≈ 16 minutes, one reading per second |
| Route | ≈ 480 m looping track |
| Size | 942 rows × 69 columns |

The columns fall into three groups:

- **Position:** `Latitude`, `Longitude`, `Total Water Column (m)` (water depth)
- **Water quality (sonde):** `Temp C`, `Salinity (ppt)`, `SpCond mS/cm`, `pH`, `ODO mg/L`, `ODOsat %`, `Turbid+ NTU`, `Chl ug/L`, `BGA-PC cells/mL`
- **Vehicle telemetry:** battery, heading, fin positions, GPS quality, and so on

### Data quality and how the app handles it

| Issue | How the app handles it |
|---|---|
| `Turbid+ NTU` is negative in every row; `Chl ug/L` and `BGA-PC cells/mL` are negative in most rows. These are physically impossible and point to sensor calibration offsets. | Hidden by default (a sidebar checkbox turns this off), with a warning banner showing how many were found. |
| `DVL-Depth (m)` is the placeholder `9999.99` in every row. | Treated as missing. |
| Several columns never change (e.g. `Conductivity (mmhos/cm)` is always 0). | Left out of the chart's parameter list. |
| Three temperature columns disagree: `Temperature (c)` and `DVL-Temperature` read 23.6–26.6 °C, while the water-quality sonde's `Temp C` reads 22.4–22.9 °C. | Charts use the sonde's `Temp C`, since that's the water-quality instrument. |
| The `Time` column is text in minutes:seconds form (e.g. `43:39.1`). | Converted to "minutes since start of survey" for a proper time axis. |
| A stray empty column and trailing spaces in a column name. | Removed and trimmed on load. |

## How to use the app

**Sidebar controls**

- **Time Range:** drag the slider to focus on part of the survey. Every tab updates.
- **Data Quality:** untick to include the impossible negative sensor readings.
- **Your Own Data:** upload a CSV in the same format as the survey file. If it can't be read or is missing required columns, the app explains why and keeps showing the original data.

**Tabs**

| Tab | What it shows |
|---|---|
| Overview | What the survey was, six headline metrics, and a guide to the app. |
| Data | The data table with a picker for which columns to show, plus summary statistics. |
| Charts | Any water-quality parameter over time (with a 30-second average trend line); temperature vs. salinity colored by depth; a rotatable 3D view of the bay floor. |
| Map | The vehicle's route on a street map, colored by water temperature. Hover a point for its salinity and depth. |
| Insights | Four key findings, each backed by a number and, for salinity, a box plot by depth. |

## Run locally

Requires Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Project structure

```
app.py                         # the Streamlit app
biscayneBay_waterquality.csv   # survey data
requirements.txt               # pinned Python dependencies
BACKLOG.md                     # user stories and sprint status (Agile)
README.md                      # this file
```

`app.py` is organized top to bottom as configuration constants, data loading and cleaning functions, one `render_…` function per page section, and a `main()` that wires them together. Each function has a docstring.

## Project management (Agile)

The work was planned as user stories with acceptance criteria in [BACKLOG.md](BACKLOG.md) and delivered in four short sprints. Each sprint ended with a working version of the app, and each story was committed separately, so the commit history shows the order in which features were built.

| Sprint | Goal | Stories |
|---|---|---|
| 0 | Project setup: repo, dependencies, README, backlog | S0-1 – S0-4 |
| 1 | Make it correct: finish the starter TODOs, curate parameters, labels and legends, handle bad data and bad uploads, modular code | S1-1 – S1-6 |
| 2 | Make it polished: Overview and Insights sections, time filter, layout | S2-1 – S2-4 |
| 3 | Ship it: deploy to Streamlit Community Cloud, finish docs, retrospective | S3-1 – S3-3 |

## Retrospective

**What went well**

- Writing the backlog first, with acceptance criteria, made each story easy to start and easy to call "done".
- Doing the refactor story (S1-6) first made every later story smaller, since each feature had an obvious function to live in.
- Committing once per story kept changes small and made it easy to see what each step changed.

**What was harder than expected**

- The data needed more cleaning than it first appeared. Negative sensor readings, a placeholder value and three disagreeing temperature columns only showed up after looking at every column's range.
- Some problems only appeared when using the app in a browser, such as a trend line that was hard to see in dark mode and a 3D plot that captured page scrolling. Automated checks alone didn't catch them.

**What to do differently in Project 2**

- Profile the dataset (ranges, constant columns, missing values) during Sprint 0, before writing user stories.
- Check the app in a browser at the end of every story, not just at the end of a sprint.
- Deploy early, at the end of Sprint 1, so cloud-only problems surface sooner.
