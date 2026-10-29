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

import numpy as np  # math for the track-length calculation
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
    st.title("🌊 Biscayne Bay Water Quality Dashboard")
    st.caption("CIS 3590 – Internship-Ready Software Development · Prof. Gregory Reis")
    st.divider()


def render_sidebar():
    """Show the sidebar controls.

    Returns a container for the time filter (filled in once the data is
    loaded, but shown first), the uploaded file (or None), and whether to hide
    negative readings.
    """
    st.sidebar.title("Controls")
    time_filter_slot = st.sidebar.container()

    st.sidebar.header("Data Quality")
    hide_negative = st.sidebar.checkbox(
        "Hide impossible negative readings",
        value=True,
        help="Turbidity, chlorophyll and blue-green algae can't be below zero. "
             "Negative values come from sensor calibration offsets.")

    st.sidebar.header("Your Own Data")
    with st.sidebar.expander("Upload a CSV file"):
        st.caption("The file needs the same columns as the original survey file, "
                   f"including: {', '.join(REQUIRED_COLUMNS)}.")
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"],
                                         label_visibility="collapsed")
    return time_filter_slot, uploaded_file, hide_negative


def render_time_filter(df: pd.DataFrame, slot) -> tuple[float, float]:
    """Show a slider for choosing part of the survey; return its range."""
    end = float(df["Elapsed (min)"].max())
    slot.header("Time Range")
    return slot.slider("Minutes since start of survey",
                             min_value=0.0,
                             max_value=end,
                             value=(0.0, end),
                             step=0.5,
                             help="Every table, chart and map uses only the "
                                  "readings inside this range.")


def filter_by_time(df: pd.DataFrame, start: float, end: float) -> pd.DataFrame:
    """Keep only the readings between start and end minutes (inclusive)."""
    return df[df["Elapsed (min)"].between(start, end)]


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


def track_length_m(df: pd.DataFrame) -> float:
    """Approximate distance traveled along the GPS track, in meters.

    The survey covers a few hundred meters, so treating the Earth as flat
    between consecutive readings is accurate enough.
    """
    earth_radius_m = 6_371_000
    lat = np.radians(df["Latitude"])
    lon = np.radians(df["Longitude"])
    north = lat.diff() * earth_radius_m
    east = lon.diff() * earth_radius_m * np.cos(lat)
    return float(np.sqrt(north**2 + east**2).sum())


def render_overview_tab(df: pd.DataFrame) -> None:
    """Explain the dataset and app, and show headline numbers."""
    st.subheader("About this survey")
    st.markdown(
        "An autonomous survey vehicle traveled a looping route in **Biscayne Bay, "
        "Florida** (near Haulover Inlet) on **February 4, 2022**, logging its "
        "position and water conditions about once per second. A water-quality "
        "sonde on board measured temperature, salinity, dissolved oxygen, pH and "
        "more, while sonar measured the depth of the water below the vehicle.")

    st.subheader("At a glance")
    st.caption("These numbers reflect the time range selected in the sidebar.")
    row1 = st.columns(3)
    row1[0].metric("Readings", f"{len(df):,}")
    row1[1].metric("Duration", f"{df['Elapsed (min)'].max() - df['Elapsed (min)'].min():.1f} min")
    row1[2].metric("Distance traveled", f"{track_length_m(df):,.0f} m")
    row2 = st.columns(3)
    row2[0].metric("Avg. water temperature", f"{df['Temp C'].mean():.2f} °C")
    row2[1].metric("Avg. salinity", f"{df['Salinity (ppt)'].mean():.1f} ppt")
    row2[2].metric("Water depth range",
                   f"{df['Total Water Column (m)'].min():.1f}–{df['Total Water Column (m)'].max():.1f} m")

    st.subheader("How to use this app")
    st.markdown(
        "- **Sidebar → Time Range:** narrow the analysis to part of the survey.\n"
        "- **Sidebar → Data Quality:** choose whether to hide impossible negative sensor readings.\n"
        "- **Sidebar → Upload:** load your own CSV in the same format as the original survey file.\n"
        "- **Data:** pick which columns to view and see summary statistics.\n"
        "- **Charts:** plot any water-quality parameter over time and compare temperature, salinity and depth.\n"
        "- **Map:** see the vehicle's route on a map, colored by water temperature. Hover a point for details.\n"
        "- **Insights:** read the main takeaways from the data.")


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
                  color_discrete_map={"Raw reading": "#9AA5B1",
                                      "30-second average": "#2E86DE"})
    # Keep the raw readings faint so the trend line stands out in light and dark themes.
    fig.update_traces(line_width=1, opacity=0.6, selector={"name": "Raw reading"})
    fig.update_traces(line_width=3, selector={"name": "30-second average"})
    return fig


def render_charts_tab(df: pd.DataFrame) -> None:
    """Show the line chart, scatter plot and 3D bay-floor plot."""
    st.subheader("A parameter over time")
    st.caption("Pick a measurement to see how it changed during the survey. The thick "
               "line smooths out second-to-second noise so the trend is easier to see.")
    # The y axis follows whichever parameter the user picks.
    parameter = st.selectbox("Select a parameter",
                             options=get_plottable_params(df),
                             format_func=label)
    st.plotly_chart(build_line_chart(df, parameter))

    left, right = st.columns(2)

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
    with left:
        st.subheader("Temperature vs. salinity")
        st.caption("Each dot is one reading. Color shows how deep the water was, so you "
                   "can see whether deeper water was warmer or saltier.")
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
    with right:
        st.subheader("The bay floor in 3D")
        st.caption("The vehicle's route with water depth as height. Drag to rotate; "
                   "use the toolbar to zoom.")
        # Scroll-to-zoom is off so scrolling the page doesn't get stuck on the plot.
        st.plotly_chart(fig3, config={"scrollZoom": False})


def render_map_tab(df: pd.DataFrame) -> None:
    """Show the vehicle's survey track on a map."""
    st.subheader("Survey route")
    st.caption("Each dot is one reading, colored by water temperature. "
               "Hover over a dot to see its salinity and depth.")
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


# Reference values used to put the measurements in context.
OPEN_OCEAN_SALINITY_PPT = 35  # typical salinity of open seawater
LOW_OXYGEN_MG_L = 4  # common threshold below which marine life becomes stressed

# Depth bands for comparing shallow and deeper water, as (label, low, high) in meters.
DEPTH_BANDS = [("Shallow (< 2 m)", 0, 2), ("Medium (2–3 m)", 2, 3), ("Deep (> 3 m)", 3, float("inf"))]


def add_depth_band(df: pd.DataFrame) -> pd.DataFrame:
    """Label each reading with the depth band it falls in."""
    df = df.copy()
    edges = [low for _, low, _ in DEPTH_BANDS] + [DEPTH_BANDS[-1][2]]
    df["Depth band"] = pd.cut(df["Total Water Column (m)"], bins=edges,
                              labels=[name for name, _, _ in DEPTH_BANDS])
    return df


def build_salinity_by_depth_chart(df: pd.DataFrame):
    """Box plot comparing salinity across depth bands."""
    band_names = [name for name, _, _ in DEPTH_BANDS]
    fig = px.box(add_depth_band(df),
                 x="Depth band",
                 y="Salinity (ppt)",
                 color="Depth band",
                 category_orders={"Depth band": band_names},
                 title="Salinity by Water Depth",
                 labels={"Depth band": "Water depth", "Salinity (ppt)": label("Salinity (ppt)")})
    fig.add_hline(y=OPEN_OCEAN_SALINITY_PPT, line_dash="dash",
                  annotation_text=f"Typical open ocean ({OPEN_OCEAN_SALINITY_PPT} ppt)",
                  annotation_position="bottom left")
    return fig


def compare(value: float, reference: float, tolerance: float, above: str, below: str, near: str) -> str:
    """Describe a value as above, below or near a reference."""
    if value > reference + tolerance:
        return above
    if value < reference - tolerance:
        return below
    return near


def render_insights_tab(df: pd.DataFrame, negative_counts: dict[str, int]) -> None:
    """Show the main takeaways, each backed by a number or a chart."""
    st.caption("Findings are calculated from the time range selected in the sidebar.")

    # 1. Temperature
    temp = df["Temp C"]
    st.subheader("1. Water temperature was very stable" if temp.max() - temp.min() < 1
                 else "1. Water temperature varied along the route")
    left, right = st.columns([3, 1])
    left.markdown(
        f"Water temperature stayed between **{temp.min():.2f} °C** and **{temp.max():.2f} °C**, "
        f"a spread of just **{temp.max() - temp.min():.2f} °C**. The short spikes on the "
        "Charts tab are small changes as the vehicle passed through slightly warmer patches of water.")
    right.metric("Temperature spread", f"{temp.max() - temp.min():.2f} °C")

    # 2. Salinity
    salinity = df["Salinity (ppt)"]
    level = compare(salinity.mean(), OPEN_OCEAN_SALINITY_PPT, 0.5,
                    "saltier than", "fresher than", "about the same as")
    st.subheader(f"2. The water was {level} the open ocean")
    banded = add_depth_band(df).groupby("Depth band", observed=True)["Salinity (ppt)"].mean()
    left, right = st.columns([3, 1])
    text = (f"Average salinity was **{salinity.mean():.1f} ppt**, {level} the roughly "
            f"{OPEN_OCEAN_SALINITY_PPT} ppt of open seawater.")
    if level == "saltier than":
        text += (" Shallow, enclosed bays can become saltier than the ocean when evaporation "
                 "outpaces freshwater inflow, as in South Florida's dry season.")
    if len(banded) > 1:
        shallowest, deepest = banded.index[0], banded.index[-1]
        direction = "lower" if banded.iloc[0] < banded.iloc[-1] else "higher"
        text += (f" Salinity was {direction} in the **{shallowest.lower()}** band "
                 f"({banded.iloc[0]:.1f} ppt) than in the **{deepest.lower()}** band "
                 f"({banded.iloc[-1]:.1f} ppt).")
    left.markdown(text)
    right.metric("Avg. salinity", f"{salinity.mean():.1f} ppt",
                 delta=f"{salinity.mean() - OPEN_OCEAN_SALINITY_PPT:+.1f} vs. ocean",
                 delta_color="off")
    st.plotly_chart(build_salinity_by_depth_chart(df))

    # 3. Dissolved oxygen
    if "ODO mg/L" in df.columns and df["ODO mg/L"].notna().any():
        oxygen = df["ODO mg/L"]
        healthy = oxygen.min() >= LOW_OXYGEN_MG_L
        st.subheader("3. Dissolved oxygen stayed at healthy levels" if healthy
                     else "3. Dissolved oxygen dipped to stressful levels")
        left, right = st.columns([3, 1])
        if healthy:
            detail = f"It never dropped below {LOW_OXYGEN_MG_L} mg/L"
        else:
            share = (oxygen < LOW_OXYGEN_MG_L).mean()
            detail = f"{share:.0%} of readings were below {LOW_OXYGEN_MG_L} mg/L"
        left.markdown(
            f"Dissolved oxygen ranged from **{oxygen.min():.2f}** to **{oxygen.max():.2f} mg/L**. "
            f"{detail}, a level commonly used as the point where fish and other marine life "
            "start to become stressed.")
        right.metric("Lowest dissolved oxygen", f"{oxygen.min():.2f} mg/L")

    # 4. Data quality
    if negative_counts:
        st.subheader("4. Some sensors need recalibration")
        worst = max(negative_counts, key=negative_counts.get)
        left, right = st.columns([3, 1])
        left.markdown(
            f"The turbidity, chlorophyll and blue-green algae sensors reported negative values, "
            f"which can't happen in real water. The worst was **{label(worst)}**, which was "
            f"negative in {negative_counts[worst]:,} readings. Conclusions about water "
            "clarity and algae shouldn't be drawn from this survey.")
        right.metric("Negative readings", f"{sum(negative_counts.values()):,}")


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Must be the first Streamlit call: sets the browser tab title, icon and a
    # wide layout so charts can sit side by side.
    st.set_page_config(page_title="Biscayne Bay Water Quality",
                       page_icon="🌊",
                       layout="wide")
    render_header()
    time_filter_slot, uploaded_file, hide_negative = render_sidebar()
    df = get_data(uploaded_file)

    negative_counts = count_negative_readings(df)
    if hide_negative:
        df = hide_negative_readings(df)
    render_data_quality(negative_counts, hide_negative)

    start, end = render_time_filter(df, time_filter_slot)
    df = filter_by_time(df, start, end)
    if len(df) < 2:
        st.warning("The selected time range has too few readings to plot. Widen it in the sidebar.")
        return

    overview, tables, plots, maps, insights = st.tabs(
        ["Overview", "Data", "Charts", "Map", "Insights"])
    with overview:
        render_overview_tab(df)
    with tables:
        render_data_tab(df)
    with plots:
        render_charts_tab(df)
    with maps:
        render_map_tab(df)
    with insights:
        render_insights_tab(df, negative_counts)


main()
