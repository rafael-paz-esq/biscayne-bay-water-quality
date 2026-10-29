"""Biscayne Bay Water Quality Dashboard.

An interactive Streamlit app for exploring water-quality data collected by an
autonomous survey vehicle in Biscayne Bay, Florida.

Run locally with:
    streamlit run app.py
If that doesn't work, try:
    python -m streamlit run app.py
"""

import io
from pathlib import Path

import pandas as pd  # data manipulation
import plotly.express as px  # data visualization
import streamlit as st

# The CSV lives next to this script. Building the path from __file__ means the
# app finds it no matter which folder it is launched from (including on
# Streamlit Community Cloud).
DATA_PATH = Path(__file__).parent / "biscayneBay_waterquality.csv"

# Water-quality measurements a user can plot, mapped to readable labels with
# units. Most of the CSV's 69 columns are vehicle telemetry (battery, fins,
# GPS), so the parameter dropdown only offers these.
WATER_QUALITY_PARAMS = {
    "Temp C": "Water Temperature (°C)",
    "Salinity (ppt)": "Salinity (ppt)",
    "SpCond mS/cm": "Specific Conductance (mS/cm)",
    "pH": "pH",
    "ODO mg/L": "Dissolved Oxygen (mg/L)",
    "ODOsat %": "Dissolved Oxygen Saturation (%)",
    "Turbid+ NTU": "Turbidity (NTU)",
    "Chl ug/L": "Chlorophyll (µg/L)",
    "BGA-PC cells/mL": "Blue-Green Algae (cells/mL)",
    "Total Water Column (m)": "Water Depth (m)",
}


# Columns the charts and map can't work without. An uploaded CSV must have
# all of them, or the app falls back to the default dataset.
REQUIRED_COLUMNS = ["Time", "Latitude", "Longitude", "Temp C",
                    "Salinity (ppt)", "Total Water Column (m)"]

# Sensors write this value when they have no reading (e.g. "DVL-Depth (m)").
PLACEHOLDER_VALUE = 9999.99

# Concentrations that can't physically be below zero. Negative readings here
# come from sensor calibration offsets, not from the water.
NON_NEGATIVE_PARAMS = ["Turbid+ NTU", "Chl ug/L", "BGA-PC cells/mL"]


def label(column: str) -> str:
    """Return the readable label for a column, or the column name itself."""
    return WATER_QUALITY_PARAMS.get(column, column)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_data(source: Path | bytes) -> pd.DataFrame:
    """Read a CSV from a file path or from an uploaded file's raw bytes.

    Cached so the file is only parsed once instead of on every widget change.
    """
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    return pd.read_csv(source)


def add_elapsed_time(df: pd.DataFrame) -> pd.DataFrame:
    """Add an "Elapsed (min)" column measured from the first reading.

    The CSV's "Time" column is text in minutes:seconds form (e.g. "43:39.1"),
    which Plotly would treat as categories rather than a time axis. Converting
    it to minutes since the start gives charts a real, evenly scaled x axis.
    """
    parts = df["Time"].astype(str).str.split(":", n=1, expand=True)
    seconds = pd.to_numeric(parts[0], errors="coerce") * 60 + pd.to_numeric(parts[1], errors="coerce")
    # The clock only shows minutes and seconds, so it wraps back to 00:00 every
    # hour. Adding 3600 s to any backwards step keeps the timeline increasing.
    steps = seconds.diff().fillna(0)
    steps[steps < 0] += 3600
    df = df.copy()
    df["Elapsed (min)"] = steps.cumsum() / 60
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Fix formatting problems that are never real data.

    - Trims stray spaces from column names (e.g. "Date m/d/y   ").
    - Drops columns with no values at all.
    - Replaces the 9999.99 "no reading" placeholder with a blank (NaN).
    """
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.dropna(axis="columns", how="all")
    numeric = df.select_dtypes("number").columns
    df[numeric] = df[numeric].mask(df[numeric] == PLACEHOLDER_VALUE)
    return df


def count_negative_readings(df: pd.DataFrame) -> dict[str, int]:
    """Count the physically impossible (negative) readings in each column."""
    counts = {col: int((df[col] < 0).sum())
              for col in NON_NEGATIVE_PARAMS if col in df.columns}
    return {col: n for col, n in counts.items() if n > 0}


def hide_negative_readings(df: pd.DataFrame) -> pd.DataFrame:
    """Blank out negative readings so they don't appear in charts or stats."""
    df = df.copy()
    for col in NON_NEGATIVE_PARAMS:
        if col in df.columns:
            df[col] = df[col].mask(df[col] < 0)
    return df


def validate_upload(uploaded_file) -> pd.DataFrame | None:
    """Read and check an uploaded CSV.

    Returns the cleaned data, or None after showing an error message if the
    file can't be read or is missing columns the charts depend on.
    """
    try:
        df = clean_data(load_data(uploaded_file.getvalue()))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        st.error(f"**Couldn't read `{uploaded_file.name}`.** Make sure it's a "
                 "comma-separated text file. Showing the default dataset instead.")
        return None

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"**`{uploaded_file.name}` is missing required columns:** "
                 f"{', '.join(missing)}. Showing the default dataset instead.")
        return None
    return df


def get_data(uploaded_file) -> pd.DataFrame:
    """Return the uploaded dataset if it is valid, otherwise the default CSV."""
    df = validate_upload(uploaded_file) if uploaded_file is not None else None
    if df is None:
        df = clean_data(load_data(DATA_PATH))
    return add_elapsed_time(df)


def get_plottable_params(df: pd.DataFrame) -> list[str]:
    """Return the water-quality columns worth plotting.

    A column qualifies if it is in the dataset, is numeric, and has more than
    one distinct value (a constant column would just be a flat line).
    """
    return [col for col in WATER_QUALITY_PARAMS
            if col in df.columns
            and pd.api.types.is_numeric_dtype(df[col])
            and df[col].nunique() > 1]


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------

def render_header() -> None:
    """Show the app title and course information."""
    st.title("Water Quality Dashboard")
    st.header("CIS 3590 - Internship-Ready Software Development")
    st.subheader("Prof. Gregory Reis")
    st.divider()


def render_sidebar():
    """Show the sidebar controls.

    Returns the uploaded file (or None) and whether to hide negative readings.
    """
    st.sidebar.header("File Upload")
    st.sidebar.info("Upload a CSV file with water quality data")
    uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

    st.sidebar.header("Data Quality")
    hide_negative = st.sidebar.checkbox(
        "Hide impossible negative readings",
        value=True,
        help="Turbidity, chlorophyll and blue-green algae can't be below zero. "
             "Negative values come from sensor calibration offsets.")
    return uploaded_file, hide_negative


def render_data_quality(negative_counts: dict[str, int], hidden: bool) -> None:
    """Warn the user about negative sensor readings and how they're handled."""
    if not negative_counts:
        return
    details = ", ".join(f"{label(col)}: {n:,}" for col, n in negative_counts.items())
    action = ("They are hidden from the table, statistics and charts."
              if hidden else
              "They are currently included. Treat these parameters with caution.")
    st.warning(f"**Negative sensor readings found** ({details}). "
               f"These values are physically impossible. {action}")


def render_data_tab(df: pd.DataFrame) -> None:
    """Show the raw data table and descriptive statistics for chosen columns."""
    # Start with position, time and the water-quality readings; the user can
    # add any of the vehicle telemetry columns too.
    default_columns = [col for col in ["Time", "Elapsed (min)", "Latitude", "Longitude"]
                       if col in df.columns] + get_plottable_params(df)
    columns = st.multiselect("Columns to display",
                             options=df.columns.tolist(),
                             default=default_columns)
    if not columns:
        st.info("Select at least one column to display.")
        return

    selected = df[columns]
    st.dataframe(selected)
    st.caption(f"Raw Data ({len(selected):,} rows × {len(columns)} columns)")

    numeric = selected.select_dtypes("number")
    if numeric.empty:
        st.info("None of the selected columns are numeric, so there are no statistics to show.")
    else:
        st.dataframe(numeric.describe())
        st.caption("Descriptive Statistics")


def build_line_chart(df: pd.DataFrame, parameter: str):
    """Plot a parameter over time, with a rolling average to show the trend.

    The raw 1-second readings are noisy, so a 30-second rolling average is
    drawn alongside them. The two lines share the chart and appear in the
    legend as "Raw reading" and "30-second average".
    """
    series = pd.DataFrame({
        "Elapsed (min)": df["Elapsed (min)"],
        "Raw reading": df[parameter],
        "30-second average": df[parameter].rolling(30, center=True, min_periods=1).mean(),
    })
    long = series.melt(id_vars="Elapsed (min)", var_name="Series", value_name=parameter)
    fig = px.line(long,
                  x="Elapsed (min)",
                  y=parameter,
                  color="Series",
                  title=f"{label(parameter)} over Time",
                  labels={"Elapsed (min)": "Time since start of survey (minutes)",
                          parameter: label(parameter)},
                  color_discrete_map={"Raw reading": "#9DB8D9",
                                      "30-second average": "#1F4E8C"})
    return fig


def render_charts_tab(df: pd.DataFrame) -> None:
    """Show the line chart, scatter plot and 3D bay-floor plot."""
    st.subheader("Line Chart")
    # The y axis follows whichever parameter the user picks.
    parameter = st.selectbox("Select a parameter",
                             options=get_plottable_params(df),
                             format_func=label)
    st.plotly_chart(build_line_chart(df, parameter))

    # "Temp C" comes from the water-quality sonde. The CSV's other temperature
    # columns ("Temperature (c)", "DVL-Temperature") come from the vehicle's
    # navigation sensor and read about 2-4 °C warmer, so they aren't used here.
    fig2 = px.scatter(df,
                      x="Temp C",
                      y="Salinity (ppt)",
                      color="Total Water Column (m)",
                      title="Water Temperature vs Salinity",
                      labels={col: label(col) for col in
                              ["Temp C", "Salinity (ppt)", "Total Water Column (m)"]},
                      color_continuous_scale="viridis")
    st.plotly_chart(fig2)

    fig3 = px.scatter_3d(df,
                         x="Longitude",
                         y="Latitude",
                         z="Total Water Column (m)",
                         color="Temp C",
                         title="3D Visualization of the Bay Floor",
                         labels={"Longitude": "Longitude (°)",
                                 "Latitude": "Latitude (°)",
                                 "Total Water Column (m)": label("Total Water Column (m)"),
                                 "Temp C": label("Temp C")},
                         color_continuous_scale="viridis")
    # Depth increases downward, so flip the z axis to look like a sea floor.
    fig3.update_scenes(zaxis_autorange="reversed")
    fig3.update_traces(marker_size=3)
    st.plotly_chart(fig3)


def render_map_tab(df: pd.DataFrame) -> None:
    """Show the vehicle's survey track on a map."""
    st.subheader("Maps")
    first_map = px.scatter_map(df,
                               lat="Latitude",
                               lon="Longitude",
                               title="Survey Track Colored by Water Temperature",
                               # Center on the data so uploaded surveys elsewhere still show up.
                               center={"lat": df["Latitude"].mean(),
                                       "lon": df["Longitude"].mean()},
                               zoom=16,
                               color="Temp C",
                               labels={"Temp C": label("Temp C")},
                               hover_data={"Salinity (ppt)": True,
                                           "Total Water Column (m)": True},
                               color_continuous_scale="viridis")
    st.plotly_chart(first_map)


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    render_header()
    uploaded_file, hide_negative = render_sidebar()
    df = get_data(uploaded_file)

    negative_counts = count_negative_readings(df)
    if hide_negative:
        df = hide_negative_readings(df)
    render_data_quality(negative_counts, hide_negative)

    tables, plots, maps = st.tabs(["Data", "Charts", "Maps"])
    with tables:
        render_data_tab(df)
    with plots:
        render_charts_tab(df)
    with maps:
        render_map_tab(df)


main()
