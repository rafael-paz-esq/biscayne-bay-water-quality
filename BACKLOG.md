# Product Backlog

User stories for the Biscayne Bay Water Quality Dashboard, grouped by sprint.
Each story uses the format *As a … I want … so that …* and has acceptance criteria that define "done".

**Status key:** ⬜ To do · 🔄 In progress · ✅ Done

---

## Sprint 0 – Project setup

| ID | Story | Acceptance criteria | Status |
|---|---|---|---|
| S0-1 | As a developer, I want a project repo with the starter code and dataset so that the team works from one source. | Repo contains `app.py` and the CSV, and the app runs locally. | ✅ |
| S0-2 | As a developer, I want pinned dependencies so that the app behaves the same locally and in the cloud. | `requirements.txt` lists every imported package with versions. | ✅ |
| S0-3 | As a grader, I want a README so that I understand the app's purpose, data and usage. | README has Purpose, Dataset, Usage and Run sections (some may be TODO). | ✅ |
| S0-4 | As a team, I want a backlog of user stories so that the work is planned in sprints. | This file exists with stories for every sprint. | ✅ |

## Sprint 1 – Make it correct

| ID | Story | Acceptance criteria | Status |
|---|---|---|---|
| S1-1 | As a user, I want to choose which columns appear in the data table so that I can focus on what matters to me. | A multiselect controls the table's columns, with a sensible default set (starter TODO #1). | ✅ |
| S1-2 | As a user, I want the chart's parameter dropdown to list only meaningful water-quality measurements so that I never get an empty or flat chart. | The dropdown lists only numeric, non-constant water-quality columns, and the y-axis updates on selection (starter TODO #2). | ✅ |
| S1-3 | As a user, I want every chart to have a clear title, axis labels with units, and a legend so that I can read it correctly. | All Plotly charts have a title, readable axis labels and a legend or color bar. | ✅ |
| S1-4 | As a user, I want the app to warn me about bad sensor data so that I don't draw wrong conclusions. | Negative turbidity, chlorophyll and algae values and the 9999.99 placeholders are handled or flagged in the UI. | ✅ |
| S1-5 | As a user, I want an uploaded CSV with different columns to show a helpful message instead of crashing. | Uploading a file without the required columns shows an error message, and the app keeps working. | ✅ |
| S1-6 | As a developer, I want the code split into functions with comments so that it's easy to extend in Project 2. | Data loading, filtering, charts and page sections are separate functions, and the CSV loads via a path relative to `app.py` with caching. | ✅ |

## Sprint 2 – Make it polished

| ID | Story | Acceptance criteria | Status |
|---|---|---|---|
| S2-1 | As a first-time user, I want an Overview section so that I know what the data is and how to use the app. | Overview explains the survey, the location and the controls, and shows key metrics. | ✅ |
| S2-2 | As a user, I want an Insights section so that I can see the main takeaways without analyzing the data myself. | At least 3 written findings, each backed by a chart or number. | ✅ |
| S2-3 | As a user, I want to filter the data by time range so that I can zoom in on part of the survey. | A sidebar slider filters every table and chart. | ✅ |
| S2-4 | As a user, I want a clean, consistent layout so that the app is easy to navigate. | Page config set (title, icon, wide layout), controls in the sidebar, consistent headings, no clutter. | ✅ |

## Sprint 3 – Ship it

| ID | Story | Acceptance criteria | Status |
|---|---|---|---|
| S3-1 | As a grader, I want the app at a public URL so that I can use it without installing anything. | The app is deployed on Streamlit Community Cloud and loads without errors. | ⬜ |
| S3-2 | As a grader, I want complete documentation so that I can evaluate the project. | README is complete with live URL, repo URL and usage instructions. | ⬜ |
| S3-3 | As a team, I want a retrospective so that we improve the process for Project 2. | README has a Retrospective section. | ⬜ |
