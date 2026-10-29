"""Biscayne Bay Water Quality Dashboard.

An interactive Streamlit app for exploring water-quality data collected by an
autonomous survey vehicle in Biscayne Bay, Florida.

Run locally with:
    streamlit run app.py
If that doesn't work, try:
    python -m streamlit run app.py
"""

from pathlib import Path

import pandas as pd  # data manipulation
import plotly.express as px  # data visualization
import streamlit as st

# The CSV lives next to this script. Building the path from __file__ means the
# app finds it no matter which folder it is launched from (including on
# Streamlit Community Cloud).
DATA_PATH = Path(__file__).parent / "biscayneBay_waterquality.csv"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_data(source) -> pd.DataFrame:
    """Read a CSV from a file path or an uploaded file.

    Cached so the file is only parsed once instead of on every widget change.
    """
    return pd.read_csv(source)


def get_data(uploaded_file) -> pd.DataFrame:
    """Return the uploaded dataset if there is one, otherwise the default CSV."""
    if uploaded_file is not None:
        return load_data(uploaded_file)
    return load_data(DATA_PATH)


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
    """Show the sidebar controls and return the uploaded file (or None)."""
    st.sidebar.header("File Upload")
    st.sidebar.info("Upload a CSV file with water quality data")
    return st.sidebar.file_uploader("Upload a CSV file", type=["csv"])


def render_data_tab(df: pd.DataFrame) -> None:
    """Show the raw data table and descriptive statistics."""
    st.dataframe(df)
    st.caption("Raw Data")
    st.dataframe(df.describe())
    st.caption("Descriptive Statistics")


def render_charts_tab(df: pd.DataFrame) -> None:
    """Show the line chart, scatter plot and 3D bay-floor plot."""
    st.subheader("Line Chart")
    parameter = st.selectbox("Select a parameter", options=df.columns.tolist())
    fig1 = px.line(df, x="Time", y=parameter, title=f"{parameter} over Time")
    st.plotly_chart(fig1)

    fig2 = px.scatter(df,
                      x="Temperature (c)",
                      y="Salinity (ppt)",
                      title="Temperature vs Salinity")
    st.plotly_chart(fig2)

    fig3 = px.scatter_3d(df,
                         x="Longitude",
                         y="Latitude",
                         z="Total Water Column (m)",
                         color="Temperature (c)",
                         title="3D Visualization of the Bay Floor")
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
                               title="Vehicle Track on a Map",
                               center={"lat": 25.9121, "lon": -80.1371},
                               zoom=16,
                               color="Temperature (c)",
                               color_continuous_scale="viridis")
    st.plotly_chart(first_map)


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    render_header()
    uploaded_file = render_sidebar()
    df = get_data(uploaded_file)

    tables, plots, maps = st.tabs(["Data", "Charts", "Maps"])
    with tables:
        render_data_tab(df)
    with plots:
        render_charts_tab(df)
    with maps:
        render_map_tab(df)


main()
