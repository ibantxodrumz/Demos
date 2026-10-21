import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from azure_blob_helper import AzureBlobStorage
from constants import ACCOUNT_URL, CONTAINER_NAME, PROJECT_NAME

# Set page config
st.set_page_config(
    page_title="PN Accuracy Dashboard 2025",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Styling Helper ---
def force_light_chart(fig):
    """Explicitly force white background and dark text on Plotly charts."""
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#000000"),
        xaxis=dict(
            gridcolor="#e5e7eb",
            linecolor="#000000",
            tickfont=dict(color="#000000"),
            title_font=dict(color="#000000"),
        ),
        yaxis=dict(
            gridcolor="#e5e7eb",
            linecolor="#000000",
            tickfont=dict(color="#000000"),
            title_font=dict(color="#000000"),
        ),
        title_font=dict(color="#000000"),
    )
    return fig


# Inject Force-Light CSS
st.markdown(
    """
<style>
    /* 1. Global Background - Safe */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* 2. Sidebar - Safe */
    section[data-testid="stSidebar"] {
        background-color: #f9fafb !important;
    }
    section[data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    
    /* 3. Text - Safe */
    h1, h2, h3, h4, h5, h6, p, li, .stMarkdown, label {
        color: #000000 !important;
    }
    
    /* 4. Inputs & Dropdowns - AGGRESSIVE FIX */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #d1d5db !important;
    }
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
    }
    div[data-baseweb="popover"] > div {
        background-color: #ffffff !important;
    }
    div[data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    ul {
        background-color: #ffffff !important;
    }
    li[role="option"], div[role="option"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    li[role="option"] *, div[role="option"] * {
        color: #000000 !important;
    }
    li[role="option"]:hover, div[role="option"]:hover {
        background-color: #f3f4f6 !important;
    }
    li[role="option"][aria-selected="true"], div[role="option"][aria-selected="true"] {
        background-color: #eff6ff !important;
        color: #1d4ed8 !important;
    }
    div[data-testid="stSelectbox"] div[class*="singleValue"] {
        color: #000000 !important;
    }
    
    /* 5. File Uploader - Safe */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #f9fafb !important;
        border: 1px dashed #d1d5db !important;
    }
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] span, [data-testid="stFileUploaderDropzone"] small {
        color: #000000 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* 6. Metrics - Safe */
    .stMetric {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
    }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {
        color: #000000 !important;
    }

    /* 7. General Buttons - Fix */
    .stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #d1d5db !important;
    }
    .stButton > button:hover {
        background-color: #f9fafb !important;
        border-color: #4A90E2 !important;
        color: #4A90E2 !important;
    }
    .stButton > button p {
        color: #000000 !important; 
    }
    .stButton > button:hover p {
        color: #4A90E2 !important;
    }
    /* 8. Expanders - Fix */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e5e7eb !important;
    }
    .streamlit-expanderHeader:hover {
        background-color: #f9fafb !important;
        color: #4A90E2 !important;
    }
    .streamlit-expanderHeader p, .streamlit-expanderHeader span, .streamlit-expanderHeader svg {
        color: #000000 !important;
    }
    .streamlit-expanderHeader:hover p, .streamlit-expanderHeader:hover span, .streamlit-expanderHeader:hover svg {
        color: #4A90E2 !important;
    }
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e5e7eb !important;
        border-top: none !important;
    }
    .streamlit-expanderContent p {
        color: #000000 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- Data Loading ---


@st.cache_data
def process_data(df_annual_raw, df_monthly_raw):
    # 1. Process Annual
    try:
        df_annual = df_annual_raw.copy()

        # Standardize columns
        df_annual["BMU"] = df_annual["nationalGridBmUnit"].astype(str)
        df_annual["Fuel"] = df_annual["Fuel_type"].astype(str)
        df_annual["Year"] = 2025
        df_annual["Grain"] = "annual"

        # Coerce numerics
        numeric_cols_annual = [
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
            "max_M_ABS_Error%",
            "installedCapacity_mwh",
            "A_Net_Error%",
            "A_ABS_Error%",
        ]
        for col in numeric_cols_annual:
            if col in df_annual.columns:
                df_annual[col] = pd.to_numeric(df_annual[col], errors="coerce").fillna(
                    0
                )

        # Define SizeBasis for charts based on capacity
        df_annual["SizeBasis"] = pd.to_numeric(
            df_annual["installedCapacity_mwh"], errors="coerce"
        ).fillna(0)

    except Exception as e:
        return None, None, f"Error processing Annual data: {str(e)}"

    # 2. Process Monthly
    try:
        df_monthly = df_monthly_raw.copy()

        # Date Parsing
        def parse_date(x):
            try:
                parts = str(x).split("-")
                if len(parts) == 2:
                    return datetime(int(parts[0]), int(parts[1]), 1)
                return pd.NaT
            except:
                return pd.NaT

        df_monthly["YearMonthObj"] = df_monthly["year_month"].apply(parse_date)
        df_monthly["Year"] = df_monthly["YearMonthObj"].dt.year
        df_monthly["Month"] = df_monthly["YearMonthObj"].dt.month
        df_monthly["MonthName"] = df_monthly["YearMonthObj"].dt.month_name()
        df_monthly["YearMonth"] = df_monthly["YearMonthObj"].dt.strftime("%Y-%m")

        df_monthly["BMU"] = df_monthly["nationalGridBmUnit"].astype(str)
        df_monthly["Fuel"] = df_monthly["Fuel_type"].astype(str)
        df_monthly["Grain"] = "monthly"

        # Coerce numerics
        numeric_cols_monthly = [
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
            "M_Net_Error%",
            "M_ABS_Error%",
        ]
        for col in numeric_cols_monthly:
            if col in df_monthly.columns:
                df_monthly[col] = pd.to_numeric(
                    df_monthly[col], errors="coerce"
                ).fillna(0)

    except Exception as e:
        return None, None, f"Error processing Monthly data: {str(e)}"

    # 3. Logic: P90 Calculation
    p90_series = df_monthly.groupby("BMU")["M_ABS_Error%"].quantile(0.9)
    p90_df = p90_series.reset_index(name="P90_monthly_error")

    # Merge into Annual
    df_annual = pd.merge(df_annual, p90_df, on="BMU", how="left")
    df_annual["P90_monthly_error"] = df_annual["P90_monthly_error"].fillna(0)

    # 4. Logic: Needs Attention
    df_annual["NeedsAttention"] = (df_annual["A_ABS_Error%"] >= 25) | (
        df_annual["P90_monthly_error"] >= 25
    )

    # 5. Logic: Error Band Classification
    def categorize_error(x):
        if x <= 1:
            return "0-1%"
        elif x <= 2:
            return "1-2%"
        elif x <= 4:
            return "2-4%"
        elif x <= 10:
            return "4-10%"
        else:
            return ">10%"

    df_annual["ErrorBand"] = df_annual["A_ABS_Error%"].apply(categorize_error)
    # Order bands for plots
    df_annual["ErrorBand"] = pd.Categorical(
        df_annual["ErrorBand"],
        categories=["0-1%", "1-2%", "2-4%", "4-10%", ">10%"],
        ordered=True,
    )

    return df_annual, df_monthly, None


# --- Sidebar ---
st.sidebar.title("Configuration")

# Data Source Toggle
data_source = st.sidebar.radio("Data Source", ["Azure Blob Storage", "Local Upload"])

annual_raw, monthly_raw = None, None

if data_source == "Azure Blob Storage":
    try:
        azure_blob = AzureBlobStorage(ACCOUNT_URL, CONTAINER_NAME, PROJECT_NAME)
        with st.sidebar.status("Fetching data from Azure...", expanded=False):
            st.write("Connecting to blob storage...")
            annual_raw = azure_blob.read_annual_summary()
            st.write("Fetched Annual Summary.")
            monthly_raw = azure_blob.read_monthly_summary()
            st.write("Fetched Monthly Summary.")
        st.sidebar.success("Azure Data Loaded Successfully")
    except Exception as e:
        st.sidebar.error(f"Azure Loading Error: {str(e)}")
        st.stop()
else:
    # File Uploader
    uploaded_annual = st.sidebar.file_uploader("Upload Annual Summary", type=["csv"])
    uploaded_monthly = st.sidebar.file_uploader("Upload Monthly Summary", type=["csv"])

    if uploaded_annual and uploaded_monthly:
        annual_raw = pd.read_csv(uploaded_annual)
        monthly_raw = pd.read_csv(uploaded_monthly)
    else:
        st.info("Please upload both Annual and Monthly CSV files.")
        st.stop()

# --- Process Data ---
df_annual_raw, df_monthly_raw, error_msg = process_data(annual_raw, monthly_raw)

if error_msg:
    st.error(error_msg)
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

# Filters
all_fuels = sorted(df_annual_raw["Fuel"].unique().tolist())
selected_fuels = st.sidebar.multiselect("Select Fuel(s)", all_fuels, default=all_fuels)

all_bmus = sorted(df_annual_raw["BMU"].unique().tolist())
# Filter BMU list based on selected fuels for convenience
available_bmus = sorted(
    df_annual_raw[df_annual_raw["Fuel"].isin(selected_fuels)]["BMU"].unique().tolist()
)
selected_bmus = st.sidebar.multiselect(
    "Select BMU(s)", available_bmus, default=available_bmus
)

needs_attention_only = st.sidebar.checkbox("🚩 'Needs Attention' only", value=False)

st.sidebar.markdown("---")
st.sidebar.info("PN Accuracy Dashboard v1.0 (Azure Enabled)")


# --- Filtering Logic ---
def apply_filters(df_a, df_m, fuels, bmus, attention_only):
    # Annual
    res_a = df_a[df_a["Fuel"].isin(fuels)]
    res_a = res_a[res_a["BMU"].isin(bmus)]
    if attention_only:
        res_a = res_a[res_a["NeedsAttention"] == True]

    # Monthly
    filtered_bmus = res_a["BMU"].unique()
    res_m = df_m[df_m["BMU"].isin(filtered_bmus)]
    res_m = res_m[res_m["Fuel"].isin(fuels)]

    return res_a, res_m


df_annual, df_monthly = apply_filters(
    df_annual_raw, df_monthly_raw, selected_fuels, selected_bmus, needs_attention_only
)

if df_annual.empty:
    st.warning("No BMUs match the current filters.")
    st.stop()


# --- UI Tabs ---
tab1, tab1_m, tab1_p90, tab1_gwh, tab2_dist, tab2_cap, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🚀 Executive Summary",
        "📉 Median Error",
        "📈 P90 Error",
        "🔋 Total GWh Error",
        "📊 Fleet: Distribution",
        "📉 Fleet: Capacity",
        "⚡ By Technology",
        "🔍 BMU Explorer",
        "🚩 Attention Needed",
        "📥 Exports",
    ]
)

# --- TAB 1: Executive Summary ---
with tab1:
    st.title("Executive Summary")

    # KPIs
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    fleet_median_error = df_annual["A_ABS_Error%"].median()
    fleet_p90_error = df_annual["A_ABS_Error%"].quantile(0.9)

    # Max error details
    max_err_idx = df_annual["A_ABS_Error%"].idxmax()
    max_err_row = df_annual.loc[max_err_idx]
    fleet_max_error = max_err_row["A_ABS_Error%"]
    max_bmu_info = f"{max_err_row['BMU']} ({max_err_row['Fuel']})"

    bmu_count = df_annual["BMU"].nunique()

    # New MWh Metrics -> Converted to GWh
    fleet_abs_gwh = df_annual["ABSError"].sum() / 1000
    fleet_net_gwh = df_annual["NetError"].sum() / 1000

    kpi1.metric("Fleet Median Error %", f"{fleet_median_error:.2f}%")
    kpi2.metric("Fleet P90 Error %", f"{fleet_p90_error:.2f}%")
    kpi3.metric(
        "Max Individual Error %",
        f"{fleet_max_error:.2f}%",
        delta=max_bmu_info,
        delta_color="off",
    )
    kpi4.metric("BMU Count", f"{bmu_count}")
    kpi5.metric("Total ABS Error (GWh)", f"{fleet_abs_gwh:,.2f}")
    kpi6.metric("Net Bias (GWh)", f"{fleet_net_gwh:,.2f}")

    # Consolidated view
    fuel_summary = (
        df_annual.groupby("Fuel")
        .agg(
            Median_Error_Pct=("A_ABS_Error%", "median"),
            P90_Error_Pct=("A_ABS_Error%", lambda x: x.quantile(0.9)),
            Total_ABS_GWh=("ABSError", lambda x: x.sum() / 1000),
            Net_Bias_GWh=("NetError", lambda x: x.sum() / 1000),
            BMU_Count=("BMU", "nunique"),
        )
        .reset_index()
    )

    # Sort by Total GWh Descending
    fuel_summary = fuel_summary.sort_values("Total_ABS_GWh", ascending=False)

    st.markdown("---")

    # Split Layout: Histogram (Left) | Summary Table (Right)
    col_main1, col_main2 = st.columns(2)

    with col_main1:
        st.subheader("Fleet Error Distribution")
        fig_hist = px.histogram(
            df_annual,
            x="A_ABS_Error%",
            title="Distribution of Annual Error % (0-100% Range)",
            color_discrete_sequence=["#4A90E2"],
            template="plotly_white",
            range_x=[0, 100],
            text_auto=True,
        )

        fig_hist.update_traces(
            xbins=dict(start=0, end=100, size=2.5),
            textposition="outside",
        )
        fig_hist.update_layout(
            xaxis=dict(
                tickmode="linear",
                tick0=0,
                dtick=5,
                title="Annual Error %",
            ),
            yaxis=dict(title="Count of BMUs"),
            bargap=0.1,
        )

        fig_hist = force_light_chart(fig_hist)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_main2:
        st.subheader("Fuel Performance Summary")
        st.caption("Detailed breakdown by Fuel type.")
        st.dataframe(
            fuel_summary.style.format(
                {
                    "Median_Error_Pct": "{:.2f}%",
                    "P90_Error_Pct": "{:.2f}%",
                    "Total_ABS_GWh": "{:,.2f}",
                    "Net_Bias_GWh": "{:,.2f}",
                }
            ),
            use_container_width=True,
            height=400,
            hide_index=True,
        )

        # Download Button
        csv = fuel_summary.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Fuel Summary (CSV)",
            data=csv,
            file_name="fuel_performance_summary_2025.csv",
            mime="text/csv",
        )

# --- TAB 1.M: Median Error ---
with tab1_m:
    st.header("Median Error by Fuel")
    st.caption("Distribution of Median Absolute Net Error % across fuel types.")

    fuel_median = (
        df_annual.groupby("Fuel")["A_ABS_Error%"]
        .median()
        .reset_index()
        .sort_values("A_ABS_Error%", ascending=True)
    )
    fig_hm1 = px.bar(
        fuel_median,
        x="Fuel",
        y="A_ABS_Error%",
        title="Median Error % by Fuel",
        color="A_ABS_Error%",
        color_continuous_scale="Reds",
        template="plotly_white",
        text_auto=".2f",
    )
    fig_hm1.update_layout(xaxis=dict(tickangle=-45))
    fig_hm1 = force_light_chart(fig_hm1)
    st.plotly_chart(fig_hm1, use_container_width=True)

# --- TAB 1.P90: P90 Error ---
with tab1_p90:
    st.header("P90 Error by Fuel")
    st.caption(
        "Distribution of P90 Absolute Net Error % (High Uncertainty) across fuel types."
    )

    fuel_p90 = (
        df_annual.groupby("Fuel")["A_ABS_Error%"]
        .quantile(0.9)
        .reset_index()
        .sort_values("A_ABS_Error%", ascending=True)
    )
    fig_hm2 = px.bar(
        fuel_p90,
        x="Fuel",
        y="A_ABS_Error%",
        title="P90 Annual Error % by Fuel",
        color="A_ABS_Error%",
        color_continuous_scale="Reds",
        template="plotly_white",
        text_auto=".2f",
    )
    fig_hm2.update_layout(xaxis=dict(tickangle=-45))
    fig_hm2 = force_light_chart(fig_hm2)
    st.plotly_chart(fig_hm2, use_container_width=True)

# --- TAB 1.GWh: Total GWh Error ---
with tab1_gwh:
    st.header("Total GWh Error by Fuel")
    st.caption(
        "Total Absolute Error Volume (GWh) across fuel types. Indicates total system impact."
    )

    # Calculate in GWh
    fuel_mwh = df_annual.groupby("Fuel")["ABSError"].sum().reset_index()
    fuel_mwh["ABSError_GWh"] = fuel_mwh["ABSError"] / 1000
    fuel_mwh = fuel_mwh.sort_values("ABSError_GWh", ascending=True)

    fig_mwh = px.bar(
        fuel_mwh,
        x="Fuel",
        y="ABSError_GWh",
        title="Total Absolute Error (GWh) by Fuel",
        color="ABSError_GWh",
        color_continuous_scale="Reds",
        template="plotly_white",
        text_auto=".0f",
    )
    fig_mwh.update_layout(xaxis=dict(tickangle=-45))
    fig_mwh = force_light_chart(fig_mwh)
    st.plotly_chart(fig_mwh, use_container_width=True)

# --- TAB 2.1: Fleet Overview - Distribution ---
with tab2_dist:
    st.header("Fleet Overview: Error Distribution")

    col_fo1, col_fo2 = st.columns(2)

    with col_fo1:
        st.subheader("Error Band Composition")
        band_counts = df_annual["ErrorBand"].value_counts().sort_index().reset_index()
        band_counts.columns = ["ErrorBand", "Count"]

        fig_band = px.bar(
            band_counts,
            x="ErrorBand",
            y="Count",
            title="BMU Count by Error Band",
            color="ErrorBand",
            color_discrete_sequence=px.colors.sequential.Bluyl,
            template="plotly_white",
            text="Count",
        )
        fig_band.update_traces(textposition="outside")
        fig_band = force_light_chart(fig_band)
        st.plotly_chart(fig_band, use_container_width=True)

        # Download CSV for Error Band Composition
        band_export = df_annual[
            ["BMU", "Fuel", "ErrorBand", "A_ABS_Error%"]
        ].sort_values(["ErrorBand", "A_ABS_Error%"])
        csv_band = band_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Error Band List (CSV)",
            data=csv_band,
            file_name="error_band_composition.csv",
            mime="text/csv",
        )

    # Note: Size Category Analysis removed due to data quality.


# --- TAB 2.2: Fleet Overview - Capacity ---
with tab2_cap:
    st.header("Fleet Overview: Capacity Analysis")

    st.subheader("Capacity vs. Error Analysis")

    # Controls for the bubble chart
    bc_col1, bc_col2 = st.columns(2)
    with bc_col1:
        y_axis_choice = st.radio(
            "Select Y-Axis Metric:",
            ["Annual Error %", "Total Error (GWh)"],
            horizontal=True,
            key="y_axis_radio",
        )
    with bc_col2:
        use_log_x = st.checkbox(
            "Log Scale X-Axis (Capacity)", value=True, key="log_x_cb"
        )

    # Prepare data
    df_annual["SizeBasis_Abs"] = df_annual["SizeBasis"].abs()
    if "ABSError_GWh" not in df_annual.columns:
        df_annual["ABSError_GWh"] = df_annual["ABSError"] / 1000

    if y_axis_choice == "Annual Error %":
        y_col = "A_ABS_Error%"
        y_title = "Annual Absolute Net Error %"
    else:
        y_col = "ABSError_GWh"
        y_title = "Total Absolute Error (GWh)"

    fig_bub = px.scatter(
        df_annual,
        x="SizeBasis",
        y=y_col,
        size="SizeBasis_Abs",
        color="Fuel",
        hover_name="BMU",
        title=f"Installed Capacity (MWh) vs. {y_title}",
        template="plotly_white",
        size_max=50,
        log_x=use_log_x,
    )
    fig_bub = force_light_chart(fig_bub)
    st.plotly_chart(fig_bub, use_container_width=True)

    st.subheader("Detailed Fleet Table")
    st.dataframe(df_annual, use_container_width=True)


# --- TAB 3: By Technology ---
with tab3:
    st.header("By Technology Analysis")

    # Fuel selector nested in tab
    focus_fuel = st.selectbox("Select Focus Fuel to Analyze", all_fuels, index=0)

    tech_df = df_annual_raw[df_annual_raw["Fuel"] == focus_fuel]
    tech_monthly = df_monthly_raw[df_monthly_raw["Fuel"] == focus_fuel]

    if tech_df.empty:
        st.warning(f"No data for {focus_fuel}.")
    else:
        # KPIs
        t_median = tech_df["A_ABS_Error%"].median()
        t_p90 = tech_df["A_ABS_Error%"].quantile(0.9)
        t_count = tech_df["BMU"].nunique()
        t_worst = tech_df.loc[tech_df["A_ABS_Error%"].idxmax()]["BMU"]
        t_worst_val = tech_df["A_ABS_Error%"].max()
        t_attention = tech_df["NeedsAttention"].sum()
        t_abs_gwh = tech_df["ABSError"].sum() / 1000
        t_net_gwh = tech_df["NetError"].sum() / 1000

        tk1, tk2, tk3, tk4, tk5, tk6, tk7 = st.columns(7)
        tk1.metric("Median Error", f"{t_median:.2f}%")
        tk2.metric("Annual P90", f"{t_p90:.2f}%")
        tk3.metric("BMU Count", f"{t_count}")
        tk4.metric("Worst BMU", f"{t_worst} ({t_worst_val:.1f}%)")
        tk5.metric("Needs Attention", f"{t_attention}")
        tk6.metric("Total ABS (GWh)", f"{t_abs_gwh:,.2f}")
        tk7.metric("Net Bias (GWh)", f"{t_net_gwh:,.2f}")

        st.markdown("---")

        tcol1, tcol2 = st.columns(2)
        with tcol1:
            st.subheader(f"{focus_fuel} Performance Analysis")
            tech_tab1, tech_tab2 = st.tabs(["Efficiency (Annual %)", "Bias (Net GWh)"])

            with tech_tab1:
                st.caption("Distribution of Absolute Error % (Normalized by Capacity)")
                fig_thist = px.histogram(
                    tech_df,
                    x="A_ABS_Error%",
                    title="Annual Absolute Error % Distribution (0-100% Range)",
                    color_discrete_sequence=["#1f77b4"],
                    template="plotly_white",
                    range_x=[0, 100],
                    text_auto=True,
                )
                fig_thist.update_traces(
                    xbins=dict(start=0, end=100, size=2.5), textposition="outside"
                )
                fig_thist.update_layout(
                    xaxis=dict(
                        tickmode="linear", tick0=0, dtick=5, title="Annual Error %"
                    ),
                    yaxis=dict(title="Count of BMUs"),
                    bargap=0.1,
                )
                fig_thist = force_light_chart(fig_thist)
                st.plotly_chart(fig_thist, use_container_width=True)

            with tech_tab2:
                st.caption("Distribution of Net Error (GWh) - Directional Bias")
                tech_df["NetError_GWh"] = tech_df["NetError"] / 1000

                fig_net_hist = px.histogram(
                    tech_df,
                    x="NetError_GWh",
                    title="Net GWh Error Distribution (Directional Bias)",
                    color_discrete_sequence=["#FF7F0E"],
                    template="plotly_white",
                    text_auto=True,
                )
                fig_net_hist.update_traces(textposition="outside")
                fig_net_hist.update_layout(
                    xaxis=dict(title="Net Error (GWh)"),
                    yaxis=dict(title="Count of BMUs"),
                    bargap=0.1,
                )
                fig_net_hist = force_light_chart(fig_net_hist)
                st.plotly_chart(fig_net_hist, use_container_width=True)

        with tcol2:
            st.subheader("Monthly Error Trend (Median & P90)")
            if not tech_monthly.empty:
                trend = (
                    tech_monthly.groupby(["YearMonth"])
                    .agg(
                        Median_Error=("M_ABS_Error%", "median"),
                        P90_Error=("M_ABS_Error%", lambda x: x.quantile(0.9)),
                    )
                    .sort_index()
                    .reset_index()
                )

                fig_trend = go.Figure()
                fig_trend.add_trace(
                    go.Scatter(
                        x=trend["YearMonth"],
                        y=trend["Median_Error"],
                        mode="lines+markers",
                        name="Median",
                    )
                )
                fig_trend.add_trace(
                    go.Scatter(
                        x=trend["YearMonth"],
                        y=trend["P90_Error"],
                        mode="lines+markers",
                        name="P90",
                        line=dict(dash="dash"),
                    )
                )

                fig_trend.update_layout(
                    title="Monthly Error Trend", template="plotly_white"
                )
                fig_trend = force_light_chart(fig_trend)
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("No monthly data for this fuel.")

        st.subheader("Top & Bottom 10 BMUs")
        tb1, tb2 = st.columns(2)
        with tb1:
            st.caption("Best Performing (Lowest Error)")
            st.dataframe(
                tech_df.nsmallest(10, "A_ABS_Error%")[
                    ["BMU", "A_ABS_Error%", "NeedsAttention"]
                ],
                use_container_width=True,
            )
        with tb2:
            st.caption("Worst Performing (Highest Error)")
            st.dataframe(
                tech_df.nlargest(10, "A_ABS_Error%")[
                    ["BMU", "A_ABS_Error%", "NeedsAttention"]
                ],
                use_container_width=True,
            )

# --- TAB 4: BMU Explorer ---
with tab4:
    st.header("BMU Explorer")

    col_search, col_select = st.columns([1, 2])
    with col_search:
        bmu_search = st.text_input("Filter BMU ID", placeholder="Search...").upper()

    bmu_list = sorted(df_annual_raw["BMU"].unique().tolist())

    if bmu_search:
        bmu_list = [b for b in bmu_list if bmu_search in b]

    if not bmu_list:
        st.warning(f"No BMUs matching '{bmu_search}' found.")
    else:
        with col_select:
            bmu_pick = st.selectbox("Select BMU", bmu_list)

        bmu_annual = df_annual_raw[df_annual_raw["BMU"] == bmu_pick].iloc[0]
        bmu_monthly = df_monthly_raw[df_monthly_raw["BMU"] == bmu_pick].sort_values(
            "YearMonth"
        )

        st.subheader(f"Profile: {bmu_pick}")

        bc1, bc2, bc3 = st.columns(3)

        with bc1:
            st.markdown("### Annual Metrics")
            st.write(f"**Fuel:** {bmu_annual['Fuel']}")
            st.write(f"**Annual Net Error %:** {bmu_annual['A_Net_Error%']:.2f}%")
            st.write(f"**Annual ABS Error %:** {bmu_annual['A_ABS_Error%']:.2f}%")
            st.write(f"**Total ABS Error (GWh):** {bmu_annual['ABSError']/1000:,.2f}")
            st.write(f"**Net Error (GWh):** {bmu_annual['NetError']/1000:,.2f}")
            st.write(f"**Monthly P90 Error:** {bmu_annual['P90_monthly_error']:.2f}%")
            if bmu_annual["NeedsAttention"]:
                st.error("⚠️ Flagged: Needs Attention")
            else:
                st.success("✅ Status: OK")

        with bc2:
            st.markdown("### Monthly Trend")
            if not bmu_monthly.empty:
                fig_spark = px.line(
                    bmu_monthly,
                    x="YearMonth",
                    y="M_ABS_Error%",
                    markers=True,
                    title="Monthly Absolute Error %",
                    template="plotly_white",
                )
                fig_spark.add_hline(
                    y=25,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="25% Threshold",
                )
                fig_spark = force_light_chart(fig_spark)
                st.plotly_chart(fig_spark, use_container_width=True)
            else:
                st.info("No monthly data available.")

        with bc3:
            st.markdown("### Monthly Data Table")
            st.dataframe(
                bmu_monthly[["YearMonth", "M_Net_Error%", "M_ABS_Error%"]],
                use_container_width=True,
                hide_index=True,
            )

            # Download CSV
            csv_bmu = bmu_monthly.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Download {bmu_pick} Data (CSV)",
                data=csv_bmu,
                file_name=f"{bmu_pick}_monthly_data.csv",
                mime="text/csv",
            )

# --- TAB 5: Attention Needed ---
with tab5:
    st.header("Action Required: BMUs Needing Attention")

    attention_df = df_annual_raw[df_annual_raw["NeedsAttention"] == True].copy()

    if attention_df.empty:
        st.success("🎉 No BMUs require attention! All below thresholds.")
    else:

        def get_reason(row):
            reasons = []
            if row["A_ABS_Error%"] >= 25:
                reasons.append(f"Annual Error {row['A_ABS_Error%']:.1f}% >= 25%")
            if row["P90_monthly_error"] >= 25:
                reasons.append(f"Monthly P90 {row['P90_monthly_error']:.1f}% >= 25%")
            return "; ".join(reasons)

        attention_df["Reason"] = attention_df.apply(get_reason, axis=1)

        st.markdown(
            f"**{len(attention_df)}** BMUs triggered the threshold (Annual Error ≥ 25% OR Monthly P90 ≥ 25%)."
        )

        for fuel_grp in sorted(attention_df["Fuel"].unique()):
            st.subheader(f"Fuel: {fuel_grp}")
            subset = attention_df[attention_df["Fuel"] == fuel_grp]
            st.dataframe(
                subset[
                    [
                        "BMU",
                        "Reason",
                        "A_ABS_Error%",
                        "P90_monthly_error",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

# --- TAB 6: Exports ---
with tab6:
    st.header("Data Exports")

    st.markdown(
        """
    ### Export Contents
    
    *   **Annual Summary**: High-level data for every BMU (one row per unit).
    *   **Monthly Summary**: Detailed breakdown (one row per BMU per Month).
    *   **Needs Attention List**: Only the specific BMUs that failed the thresholds.
    """
    )
    st.markdown("---")

    def convert_df(df):
        return df.to_csv(index=False).encode("utf-8")

    ec1, ec2, ec3 = st.columns(3)

    with ec1:
        st.subheader("Annual Summary")
        csv_annual = convert_df(df_annual)
        st.download_button(
            label="Download Annual Summary (Filtered)",
            data=csv_annual,
            file_name="annual_summary_2025_filtered.csv",
            mime="text/csv",
        )

    with ec2:
        st.subheader("Monthly Summary")
        csv_monthly = convert_df(df_monthly)
        st.download_button(
            label="Download Monthly Summary (Filtered)",
            data=csv_monthly,
            file_name="monthly_summary_2025_filtered.csv",
            mime="text/csv",
        )

    with ec3:
        st.subheader("Needs Attention List")
        if not attention_df.empty:
            csv_attn = convert_df(attention_df)
            st.download_button(
                label="Download Attention List",
                data=csv_attn,
                file_name="needs_attention_list.csv",
                mime="text/csv",
            )
        else:
            st.write("No attention list to download.")
