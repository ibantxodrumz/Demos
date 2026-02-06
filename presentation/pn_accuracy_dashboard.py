# =========================================================
# MODULE 1 — Imports, Page Config, Global CSS, Unified Loader
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

# ---------- Streamlit Page Config ----------
st.set_page_config(
    page_title="BMU PN Accuracy Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Global CSS (your light theme preserved) ----------
st.markdown(
    """
<style>
/* Light background & dark text */
.stApp { background-color: #ffffff !important; color: #111827 !important; }
section[data-testid="stSidebar"] { background-color: #f9fafb !important; }
section[data-testid="stSidebar"] * { color: #111827 !important; }
h1, h2, h3, h4, h5, h6, p, li, .stMarkdown, label { color: #111827 !important; }

/* Inputs & dropdowns */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #111827 !important;
    border-color: #d1d5db !important;
}
div[data-baseweb="popover"] {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
}
div[data-baseweb="menu"] { background-color: #ffffff !important; }
li[role="option"], div[role="option"] {
    background-color: #ffffff !important;
    color: #111827 !important;
}
li[role="option"]:hover, div[role="option"]:hover { background-color: #f3f4f6 !important; }

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
    background-color: #f9fafb !important;
    border: 1px dashed #d1d5db !important;
}

/* Metric boxes */
.stMetric {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
}

/* Buttons */
.stButton > button {
    background-color: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
}
.stButton > button:hover {
    background-color: #f9fafb !important;
    border-color: #4A90E2 !important;
    color: #4A90E2 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------- Helper: Enforce Light Mode for Plotly ----------
def force_light(fig):
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#111827"),
        xaxis=dict(gridcolor="#e5e7eb", linecolor="#111827"),
        yaxis=dict(gridcolor="#e5e7eb", linecolor="#111827"),
    )
    return fig


# =========================================================
# UNIFIED DATA LOADER (Annual + Monthly)
# =========================================================


@st.cache_data
def load_accuracy_data(annual_files, monthly_files):
    """
    annual_files    -> list of uploaded annual_summary_2025 CSVs (usually 1)
    monthly_files   -> list of uploaded monthly_summary_2025 CSVs (usually 1)

    Returns a tuple:
    (df_annual, df_monthly)
    """

    # -------------------------
    # LOAD ANNUAL DATA
    # -------------------------
    annual_dfs = []
    for f in annual_files:
        df = pd.read_csv(f)
        # Clean column names
        df.columns = df.columns.str.strip()

        # Required columns: from your sample (Option A confirmed)
        # nationalGridBmUnit, PNLevel, MELLevel, MILLevel, BidVolume, OfferVolume,
        # Metered, ExpectOT, CapacityCalibrated, NetError, ABSError,
        # max_M_ABS_NetError%, installedCapacity_mwh, FUEL_I,
        # A_NetError%, A_ABS_NetError%, Rank_A_ABS_NetError%, PctRank_A_ABS_NetError%

        # Convert numerical fields
        num_cols = [
            "PNLevel",
            "MELLevel",
            "MILLevel",
            "BidVolume",
            "OfferVolume",
            "Metered",
            "ExpectOT",
            "CapacityCalibrated",
            "NetError",
            "ABSError",
            "max_M_ABS_NetError%",
            "installedCapacity_mwh",
            "A_NetError%",
            "A_ABS_NetError%",
            "Rank_A_ABS_NetError%",
            "PctRank_A_ABS_NetError%",
        ]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        df["BMU"] = df["nationalGridBmUnit"].astype(str)
        df["Fuel"] = df["FUEL_I"].astype(str)
        df["Year"] = 2025
        df["Grain"] = "annual"

        annual_dfs.append(df)

    df_annual = (
        pd.concat(annual_dfs, ignore_index=True) if annual_dfs else pd.DataFrame()
    )

    # -------------------------
    # LOAD MONTHLY DATA
    # -------------------------
    monthly_dfs = []
    for f in monthly_files:
        df = pd.read_csv(f)
        df.columns = df.columns.str.strip()

        # Convert year_month → YearMonth, Year, Month, MonthName
        # year_month looks like: 2025-1, 2025-2, ...
        df["year_month"] = df["year_month"].astype(str)
        df["year_month_fixed"] = df["year_month"].str.replace(
            r"-(\d)$", r"-0\1", regex=True
        )  # pad 1-digit months
        df["YearMonth"] = pd.to_datetime(
            df["year_month_fixed"], format="%Y-%m", errors="coerce"
        )
        df["Year"] = df["YearMonth"].dt.year
        df["Month"] = df["YearMonth"].dt.month
        df["MonthName"] = df["YearMonth"].dt.month_name()

        # Numeric coercion
        num_cols_m = [
            "PNLevel",
            "MELLevel",
            "MILLevel",
            "BidVolume",
            "OfferVolume",
            "Metered",
            "ExpectOT",
            "CapacityCalibrated",
            "NetError",
            "ABSError",
            "installedCapacity_mwh",
            "M_NetError%",
            "M_ABS_NetError%",
            "Rank_M_ABS_NetError%",
            "PctRank_M_ABS_NetError%",
        ]
        for c in num_cols_m:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        df["BMU"] = df["nationalGridBmUnit"].astype(str)
        df["Fuel"] = df["FUEL_I"].astype(str)
        df["Grain"] = "monthly"

        monthly_dfs.append(df)

    df_monthly = (
        pd.concat(monthly_dfs, ignore_index=True) if monthly_dfs else pd.DataFrame()
    )

    return df_annual, df_monthly


# =========================================================
# MODULE 2 — Sidebar, File Upload, and Data Orchestration
# =========================================================

st.sidebar.title("Configuration")

st.sidebar.markdown("### Upload Input Files")
st.sidebar.write("Please upload the two fixed CSVs:")

annual_file = st.sidebar.file_uploader(
    "📄 annual_summary_2025.csv",
    type=["csv"],
    accept_multiple_files=False,
    key="annual",
)

monthly_file = st.sidebar.file_uploader(
    "📄 monthly_summary_2025.csv",
    type=["csv"],
    accept_multiple_files=False,
    key="monthly",
)

# Stop until both files are uploaded
if annual_file is None or monthly_file is None:
    st.info("⬆️ Please upload BOTH files to proceed.")
    st.stop()

# ---------- Load the data ----------
df_annual, df_monthly = load_accuracy_data(
    annual_files=[annual_file], monthly_files=[monthly_file]
)

if df_annual.empty:
    st.error("Annual summary file appears empty or invalid.")
    st.stop()

if df_monthly.empty:
    st.warning("Monthly summary file is empty — monthly features will be disabled.")

# ---------- Build global helper structures ----------

ALL_FUELS = sorted(df_annual["Fuel"].dropna().unique().tolist())
ALL_BMUS = sorted(df_annual["BMU"].dropna().unique().tolist())

# Monthly only if available
if not df_monthly.empty:
    MONTH_LIST = (
        df_monthly[["YearMonth", "MonthName"]]
        .drop_duplicates()
        .sort_values("YearMonth")
    )
else:
    MONTH_LIST = pd.DataFrame(columns=["YearMonth", "MonthName"])

# ---------- Precompute monthly P90 per BMU ----------
if not df_monthly.empty:
    df_monthly_p90 = (
        df_monthly.groupby("BMU")["M_ABS_NetError%"]
        .apply(
            lambda s: (
                np.nanpercentile(s.dropna(), 90) if s.dropna().size > 0 else np.nan
            )
        )
        .reset_index()
        .rename(columns={"M_ABS_NetError%": "P90_monthly_error"})
    )
else:
    df_monthly_p90 = pd.DataFrame(columns=["BMU", "P90_monthly_error"])

# ---------- Merge P90 into annual ----------
df_annual = df_annual.merge(df_monthly_p90, on="BMU", how="left")

# ---------- Universal Error % for filtering ----------
df_annual["ErrorFlagValue"] = df_annual["A_ABS_NetError%"]

# ---------- Attention rule ≥ 25% ----------
df_annual["NeedsAttention"] = (df_annual["A_ABS_NetError%"] >= 25) | (
    df_annual["P90_monthly_error"] >= 25
)

# ---------- Sidebar Filters ----------
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

fuel_filter = st.sidebar.multiselect(
    "Filter by Fuel", options=ALL_FUELS, default=ALL_FUELS
)

bmu_filter = st.sidebar.multiselect("Filter by BMU", options=ALL_BMUS, default=[])

attention_only = st.sidebar.checkbox(
    "Show attention-needed BMUs only (≥ 25% error)", value=False
)

# ---------- Apply global filters ----------
filtered_annual = df_annual.copy()

filtered_annual = filtered_annual[filtered_annual["Fuel"].isin(fuel_filter)]

if bmu_filter:
    filtered_annual = filtered_annual[filtered_annual["BMU"].isin(bmu_filter)]

if attention_only:
    filtered_annual = filtered_annual[filtered_annual["NeedsAttention"] == True]

# If after filtering there's no data, stop gracefully
if filtered_annual.empty:
    st.warning("No BMUs match the current filter selection.")
    st.stop()


# =========================================================
# MODULE 3 — Executive Summary Tab
# =========================================================

st.title("📊 BMU PN Accuracy — 2025 Executive Summary")

# ---------- High-level KPIs ----------
colA, colB, colC, colD = st.columns(4)

fleet_median = filtered_annual["A_ABS_NetError%"].median()
fleet_p90 = np.nanpercentile(filtered_annual["A_ABS_NetError%"], 90)
fleet_max = filtered_annual["A_ABS_NetError%"].max()
fleet_count = filtered_annual["BMU"].nunique()

colA.metric("Fleet Median Error %", f"{fleet_median:.2f}%")
colB.metric("Fleet 90th Percentile %", f"{fleet_p90:.2f}%")
colC.metric("Fleet Max Error %", f"{fleet_max:.2f}%")
colD.metric("BMUs in Scope", fleet_count)

st.markdown("---")


# =========================================================
# HEATMAPS (Median & P90 by Fuel)
# =========================================================

st.subheader("🔥 Cross-Fuel Error Landscape")

# Compute aggregated fuel stats
agg = (
    df_annual.groupby("Fuel")
    .agg(
        median_err=("A_ABS_NetError%", "median"),
        p90_err=("A_ABS_NetError%", lambda s: np.nanpercentile(s.dropna(), 90)),
        max_err=("A_ABS_NetError%", "max"),
        count=("BMU", "nunique"),
    )
    .reset_index()
    .sort_values("median_err")
)

# Median heatmap
fig_med = px.imshow(
    agg[["median_err"]].T,
    color_continuous_scale="YlOrRd",
    labels={"x": "Fuel", "y": "Median Error %"},
    x=agg["Fuel"].tolist(),
)
fig_med.update_layout(title="Median Error % by Fuel")
fig_med = force_light(fig_med)
st.plotly_chart(fig_med, use_container_width=True)

# P90 heatmap
fig_p90 = px.imshow(
    agg[["p90_err"]].T,
    color_continuous_scale="YlGnBu",
    labels={"x": "Fuel", "y": "P90 Error %"},
    x=agg["Fuel"].tolist(),
)
fig_p90.update_layout(title="P90 Error % by Fuel")
fig_p90 = force_light(fig_p90)
st.plotly_chart(fig_p90, use_container_width=True)

st.markdown("---")


# =========================================================
# DISTRIBUTION CHART — Full Fleet
# =========================================================

st.subheader("📦 Error Distribution (Fleet-Wide)")

fig_dist = px.histogram(
    filtered_annual,
    x="A_ABS_NetError%",
    nbins=50,
    title="Fleet Error Distribution",
    color_discrete_sequence=["#4A90E2"],
)
fig_dist = force_light(fig_dist)
st.plotly_chart(fig_dist, use_container_width=True)

st.markdown(
    "Median and P90 thresholds give a clean picture of fleet stability and the tail of underperforming BMUs."
)

st.markdown("---")


# =========================================================
# TREEMAP — Fuel → BMU → Error
# =========================================================

st.subheader("🌳 Treemap — Error by Fuel and BMU")

fig_tree = px.treemap(
    filtered_annual,
    path=["Fuel", "BMU"],
    values="A_ABS_NetError%",
    color="A_ABS_NetError%",
    color_continuous_scale="RdYlGn_r",
    title="Treemap: A_ABS_NetError% by Fuel and BMU",
)
fig_tree = force_light(fig_tree)
st.plotly_chart(fig_tree, use_container_width=True)


# =========================================================
# MODULE 4 — Fleet Overview Tab
# =========================================================

st.header("📦 Fleet Overview")


# ---------------------------------------------------------
# Error Band Definitions
# ---------------------------------------------------------
def classify_band(v):
    if pd.isna(v):
        return "Unknown"
    if v < 1:
        return "0–1%"
    if v < 2:
        return "1–2%"
    if v < 4:
        return "2–4%"
    if v < 10:
        return "4–10%"
    return ">10%"


filtered_annual["ErrorBand"] = filtered_annual["A_ABS_NetError%"].apply(classify_band)

# ---------------------------------------------------------
# Error Band Composition
# ---------------------------------------------------------
st.subheader("🎨 Error Band Composition (Fleet)")

band_counts = (
    filtered_annual.groupby("ErrorBand")["BMU"]
    .count()
    .reset_index(name="Count")
    .sort_values("ErrorBand")
)

fig_bands = px.bar(
    band_counts,
    x="ErrorBand",
    y="Count",
    title="Fleet Error Bands",
    color="ErrorBand",
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig_bands = force_light(fig_bands)
st.plotly_chart(fig_bands, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------
# Fleet Histogram
# ---------------------------------------------------------
st.subheader("📊 Fleet Error Distribution (Filtered BMUs)")

fig_fleet_hist = px.histogram(
    filtered_annual,
    x="A_ABS_NetError%",
    nbins=60,
    title="Distribution of A_ABS_NetError%",
    color_discrete_sequence=["#4A90E2"],
)
fig_fleet_hist = force_light(fig_fleet_hist)
st.plotly_chart(fig_fleet_hist, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------
# Bubble Chart — Capacity vs Error
# ---------------------------------------------------------
st.subheader("🫧 Capacity vs Error Bubble Chart")

if "CapacityCalibrated" in filtered_annual.columns:
    fig_bubble = px.scatter(
        filtered_annual,
        x="CapacityCalibrated",
        y="A_ABS_NetError%",
        size="CapacityCalibrated",
        color="Fuel",
        hover_data=["BMU"],
        title="Capacity vs Error%",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_bubble = force_light(fig_bubble)
    st.plotly_chart(fig_bubble, use_container_width=True)
else:
    st.info("CapacityCalibrated column missing — bubble chart skipped.")

st.markdown("---")

# ---------------------------------------------------------
# Fleet Table
# ---------------------------------------------------------
st.subheader("📋 Fleet Table (Filtered)")

display_cols = [
    "BMU",
    "Fuel",
    "A_ABS_NetError%",
    "P90_monthly_error",
    "CapacityCalibrated",
    "Metered",
    "ExpectOT",
    "NetError",
    "ABSError",
    "ErrorBand",
]

available_cols = [c for c in display_cols if c in filtered_annual.columns]

st.dataframe(
    filtered_annual[available_cols].sort_values("A_ABS_NetError%", ascending=False),
    use_container_width=True,
)

# ---------------------------------------------------------
# Export Button
# ---------------------------------------------------------
st.download_button(
    "📥 Download Filtered Fleet Table (CSV)",
    data=filtered_annual[available_cols].to_csv(index=False),
    file_name="fleet_overview_filtered.csv",
    mime="text/csv",
)


# =========================================================
# PART A — By-Technology Tab: UI + Header
# =========================================================

st.header("🔌 By Technology Analysis")

selected_fuel = st.selectbox(
    "Select Fuel Type",
    options=sorted(df_annual["Fuel"].dropna().unique().tolist()),
    index=0,
)

# Filter the annual data for the selected fuel
fuel_df_annual = df_annual[df_annual["Fuel"] == selected_fuel]

# Filter the monthly data for the selected fuel (if available)
fuel_df_monthly = (
    df_monthly[df_monthly["Fuel"] == selected_fuel]
    if not df_monthly.empty
    else pd.DataFrame()
)

if fuel_df_annual.empty:
    st.warning(f"No data available for fuel type: {selected_fuel}")
    st.stop()

# =========================================================
# PART B — Fuel-Level KPIs
# =========================================================

st.subheader(f"⚙️ {selected_fuel} — Performance KPIs")

# Annual Median Error
fuel_median = fuel_df_annual["A_ABS_NetError%"].median()

# Annual P90 (from annual values just in case)
fuel_p90_annual = (
    np.nanpercentile(fuel_df_annual["A_ABS_NetError%"].dropna(), 90)
    if fuel_df_annual["A_ABS_NetError%"].dropna().size > 0
    else np.nan
)

# Monthly P90 (if monthly available)
if not fuel_df_monthly.empty:
    fuel_p90_monthly = (
        np.nanpercentile(fuel_df_monthly["M_ABS_NetError%"].dropna(), 90)
        if fuel_df_monthly["M_ABS_NetError%"].dropna().size > 0
        else np.nan
    )
else:
    fuel_p90_monthly = None

# Worst BMU (by Annual error)
worst_row = fuel_df_annual.sort_values("A_ABS_NetError%", ascending=False).iloc[0]

worst_bmu = worst_row["BMU"]
worst_err = worst_row["A_ABS_NetError%"]

# Count BMUs in this fuel
fuel_bmu_count = fuel_df_annual["BMU"].nunique()

# Attention threshold ≥ 25%
fuel_attention_count = fuel_df_annual[
    (fuel_df_annual["A_ABS_NetError%"] >= 25)
    | (fuel_df_annual.get("P90_monthly_error", 0) >= 25)
]["BMU"].nunique()

# ---- KPI Cards ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Median Error %", f"{fuel_median:.2f}%")
c2.metric("Annual P90 Error %", f"{fuel_p90_annual:.2f}%")

if fuel_p90_monthly is not None:
    c3.metric("Monthly P90 Error %", f"{fuel_p90_monthly:.2f}%")
else:
    c3.metric("Monthly P90 Error %", "N/A")

c4.metric("BMUs in Fuel", f"{fuel_bmu_count}")

st.markdown(f"**Worst BMU:** `{worst_bmu}` with **{worst_err:.2f}%** annual error.")

if fuel_attention_count > 0:
    st.warning(
        f"⚠️ {fuel_attention_count} BMUs in {selected_fuel} exceed the 25% attention threshold."
    )
else:
    st.success(f"All BMUs in {selected_fuel} are below the 25% attention threshold.")
