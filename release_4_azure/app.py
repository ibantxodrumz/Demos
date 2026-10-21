import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import base64
from azure_blob_helper import AzureBlobStorage
from constants import (
    ACCOUNT_URL,
    CONTAINER_NAME,
    PROJECT_BASE_NAME,
    PROJECT_NAME,
    VERSION,
    AVAILABLE_YEARS,
    DEFAULT_YEAR,
)

# Set page config
st.set_page_config(
    page_title="Market Monitoring: PN Accuracy Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Logo Helper ---
@st.cache_data
def get_logo_b64():
    """Load NESO logo as base64 string for zero-latency inlined rendering."""
    logo_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "neso_logo.jpg"
    )
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None


logo_b64 = get_logo_b64()


# --- Styling & Chart Rendering Helpers ---
PLOTLY_CONFIG = {
    "scrollZoom": False,  # CRITICAL: Disables mouse wheel zoom to prevent infinite zoom and scroll trapping
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "doubleClick": "reset",
}


def force_light_chart(fig):
    """Explicitly force white background, NESO typography, and sleek colors on Plotly charts."""
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1e131c", family="'Segoe UI', -apple-system, sans-serif"),
        xaxis=dict(
            gridcolor="#f3e8f1",
            linecolor="#edd8e8",
            tickfont=dict(color="#6b5967"),
            title_font=dict(color="#400732", size=13),
        ),
        yaxis=dict(
            gridcolor="#f3e8f1",
            linecolor="#edd8e8",
            tickfont=dict(color="#6b5967"),
            title_font=dict(color="#400732", size=13),
        ),
        title_font=dict(color="#400732", size=15),
    )
    return fig


def render_chart(fig, **kwargs):
    """Render Plotly chart with disabled scroll-zoom to prevent layout oscillation and infinite zoom loops."""
    fig = force_light_chart(fig)
    config = dict(PLOTLY_CONFIG)
    if "config" in kwargs:
        config.update(kwargs.pop("config"))
    st.plotly_chart(fig, use_container_width=True, config=config, **kwargs)


# Inject NESO Corporate Design System CSS
st.markdown(
    """
<style>
    /* 1. Global Background & Typography */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
        overflow-anchor: none !important;
    }

    .stApp {
        background-color: #fcfafc !important;
        color: #1e131c !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    div[data-testid="block-container"] {
        padding-top: 1.25rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    /* 2. Top Navigation Bar */
    .neso-top-navbar {
        background-color: #ffffff;
        border-bottom: 1px solid #edd8e8;
        padding: 10px 24px;
        margin: -1.25rem -2.5rem 1.5rem -2.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 4px rgba(64, 7, 50, 0.04);
    }
    .neso-nav-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .neso-nav-logo {
        height: 38px;
        border-radius: 4px;
        display: block;
    }
    .neso-nav-divider {
        height: 24px;
        width: 1px;
        background-color: #edd8e8;
    }
    .neso-nav-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #400732;
        letter-spacing: -0.01em;
    }
    .neso-nav-pill {
        background-color: #f7edf5;
        color: #73135c;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .neso-pill-btn {
        background-color: #400732;
        color: #ffffff;
        padding: 6px 18px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    /* 3. Sidebar - NESO Corporate Plum */
    section[data-testid="stSidebar"] {
        background-color: #400732 !important;
        border-right: 1px solid #330528 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h4 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {
        color: #fbf6fa !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.18) !important;
        margin: 1.2rem 0 !important;
    }

    /* Sidebar Header Branding */
    .neso-sidebar-header {
        padding: 4px 0 16px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 18px;
    }
    .neso-sidebar-logo {
        width: 155px;
        border-radius: 4px;
        display: block;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }
    .neso-sidebar-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.01em;
        line-height: 1.2;
    }
    .neso-sidebar-subtitle {
        font-size: 0.95rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: 0.01em;
        margin-top: 3px;
    }
    .neso-sidebar-tag {
        font-size: 0.68rem;
        font-weight: 600;
        color: #e9cbe4;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 5px;
    }

    /* 4. Controls inside Sidebar */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1e131c !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {
        color: #1e131c !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="tag"] {
        background-color: #f3d5ea !important;
        color: #400732 !important;
        border-radius: 12px !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="tag"] * {
        color: #400732 !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin-bottom: 6px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: rgba(255, 255, 255, 0.16) !important;
        border-color: rgba(255, 255, 255, 0.35) !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(255, 255, 255, 0.06) !important;
        border: 1px dashed rgba(255, 255, 255, 0.3) !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
        background-color: #ffffff !important;
        color: #400732 !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #f7edf5 !important;
        color: #400732 !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.12) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #ffffff !important;
        color: #400732 !important;
        border-color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }
    section[data-testid="stSidebar"] .stButton > button p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover p {
        color: #400732 !important;
    }

    /* 5. Main Area Metrics (Matching NESO card aesthetic) */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #edd8e8 !important;
        border-left: 4.5px solid #400732 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        box-shadow: 0 2px 5px rgba(64, 7, 50, 0.04) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(64, 7, 50, 0.08) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #400732 !important;
        font-weight: 700 !important;
        font-size: 1.75rem !important;
        line-height: 1.2 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #6b5967 !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 4px !important;
    }
    div[data-testid="stMetricDelta"] {
        color: #73135c !important;
        font-weight: 600 !important;
    }

    /* 6. Tabs - NESO Corporate Pills & Multi-line Wrapping */
    div[data-testid="stTabs"] {
        border-bottom: none !important;
        margin-bottom: 1.25rem !important;
        overflow-anchor: none !important;
    }
    div[data-testid="stTabs"] > div:first-child,
    div[data-testid="stTabs"] div[role="tablist"],
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        border-bottom: 2px solid #edd8e8 !important;
        padding-bottom: 10px !important;
        margin-bottom: 1.25rem !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        scrollbar-width: thin !important;
        width: 100% !important;
    }
    div[data-testid="stTabContent"] {
        overflow-anchor: none !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    div[data-testid="stTabs"] button[role="tab"],
    div[data-testid="stTabs"] [data-baseweb="tab"] {
        color: #400732 !important;
        background-color: #ffffff !important;
        border: 1.5px solid #ebd8e7 !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 6px 14px !important;
        margin: 2px 2px !important;
        height: auto !important;
        min-height: 34px !important;
        box-shadow: 0 1px 2px rgba(64, 7, 50, 0.04) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: nowrap !important;
        cursor: pointer !important;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover,
    div[data-testid="stTabs"] [data-baseweb="tab"]:hover {
        color: #400732 !important;
        background-color: #fbf2f8 !important;
        border-color: #9c1f7e !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
    div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background-color: #400732 !important;
        border-color: #400732 !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(64, 7, 50, 0.25) !important;
    }
    div[data-testid="stTabs"] button[role="tab"] p,
    div[data-testid="stTabs"] [data-baseweb="tab"] p {
        color: inherit !important;
        font-weight: inherit !important;
        font-size: inherit !important;
        margin: 0 !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
    div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* 7. Buttons in Main Area */
    .stButton > button {
        background-color: #400732 !important;
        color: #ffffff !important;
        border: 1px solid #400732 !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        padding: 7px 20px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(64, 7, 50, 0.1) !important;
    }
    .stButton > button:hover {
        background-color: #5c0b49 !important;
        border-color: #5c0b49 !important;
        color: #ffffff !important;
        box-shadow: 0 3px 6px rgba(64, 7, 50, 0.2) !important;
    }
    .stButton > button p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover p {
        color: #ffffff !important;
    }
    
    .stDownloadButton > button {
        background-color: #ffffff !important;
        color: #400732 !important;
        border: 1.5px solid #400732 !important;
        border-radius: 20px !important;
        font-weight: 600 !important;
        padding: 7px 20px !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        background-color: #fcf4fa !important;
        border-color: #400732 !important;
        color: #400732 !important;
    }
    .stDownloadButton > button p {
        color: #400732 !important;
    }

    /* 8. Headings & Text */
    h1, h2, h3, h4, h5, h6 {
        color: #400732 !important;
        font-weight: 700 !important;
        letter-spacing: -0.015em !important;
    }
    p, li, .stMarkdown {
        color: #1e131c !important;
    }
    .caption, small {
        color: #73596d !important;
    }

    /* 9. Expanders */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        color: #400732 !important;
        border: 1px solid #edd8e8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .streamlit-expanderHeader:hover {
        background-color: #fcf4fa !important;
        border-color: #400732 !important;
        color: #400732 !important;
    }
    .streamlit-expanderHeader p, .streamlit-expanderHeader span, .streamlit-expanderHeader svg {
        color: #400732 !important;
    }
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        border: 1px solid #edd8e8 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* 10. Dataframes */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border: 1px solid #edd8e8 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 3px rgba(64, 7, 50, 0.03) !important;
    }

    /* Active Review Window Banner */
    .neso-active-window-card {
        background-color: #fcf4fa;
        border: 1px solid #f0d5ea;
        border-radius: 8px;
        padding: 10px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .neso-aw-tag {
        font-size: 0.82rem;
        font-weight: 700;
        color: #400732;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .neso-aw-badge {
        background-color: #ffffff;
        border: 1px solid #edd8e8;
        padding: 3px 12px;
        border-radius: 16px;
        font-size: 0.82rem;
        color: #400732;
    }
    .neso-aw-arrow {
        color: #73135c;
        font-weight: bold;
    }
    .neso-aw-info {
        color: #73135c;
        font-size: 0.82rem;
        font-weight: 500;
        margin-left: auto;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Render Top Navigation Header Bar
if logo_b64:
    st.markdown(
        f"""
        <div class="neso-top-navbar">
            <div class="neso-nav-left">
                <img src="data:image/jpeg;base64,{logo_b64}" class="neso-nav-logo" alt="NESO Logo" />
                <span class="neso-nav-divider"></span>
                <span class="neso-nav-title">Market Monitoring: PN Accuracy Dashboard</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Business Logic & Helper Functions ---
def categorize_error(x):
    """Categorize error percentage into predefined operational bands."""
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


def get_reason(row):
    """Generate detailed reason string for BMUs exceeding operational thresholds."""
    reasons = []
    fuel_upper = str(row.get("Fuel", "")).upper()
    net_err = row.get("A_NetError%", 0.0)
    abs_err = row.get("A_ABS_NetError%", 0.0)

    if fuel_upper in ["WIND", "SOLAR"]:
        if abs(net_err) > 3.0:
            reasons.append(f"Net Error {net_err:+.2f}% (outside ±3%)")
        if abs_err >= 9.4:
            reasons.append(f"ABS Error {abs_err:.2f}% (≥ 9.4%)")
    else:
        if abs(net_err) > 1.0:
            reasons.append(f"Net Error {net_err:+.2f}% (outside ±1%)")
        if abs_err >= 2.6:
            reasons.append(f"ABS Error {abs_err:.2f}% (≥ 2.6%)")
    return "; ".join(reasons) if reasons else "Within Tolerances"


# --- Data Loading ---


@st.cache_data
def process_data(df_annual_raw, df_monthly_raw, year: int = 2025):
    # 1. Process Annual
    try:
        df_annual = df_annual_raw.copy()

        # Standardize columns
        df_annual["BMU"] = df_annual["nationalGridBmUnit"].astype(str)
        df_annual["Fuel"] = df_annual["Fuel_type"].astype(str)
        df_annual["Year"] = int(year)
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
            "max_M_ABS_NetError%",
            "installedCapacity_mwh",
            "A_NetError%",
            "A_ABS_NetError%",
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
            "M_NetError%",
            "M_ABS_NetError%",
        ]
        for col in numeric_cols_monthly:
            if col in df_monthly.columns:
                df_monthly[col] = pd.to_numeric(
                    df_monthly[col], errors="coerce"
                ).fillna(0)

    except Exception as e:
        return None, None, f"Error processing Monthly data: {str(e)}"

    # # 3. Logic: P90 Calculation
    # p90_series = df_monthly.groupby("BMU")["M_ABS_NetError%"].quantile(0.9)
    # p90_df = p90_series.reset_index(name="P90_monthly_error")

    # # Merge into Annual
    # df_annual = pd.merge(df_annual, p90_df, on="BMU", how="left")
    # df_annual["P90_monthly_error"] = df_annual["P90_monthly_error"].fillna(0)

    # 4. Logic: Needs Attention (Fuel-specific thresholds)
    # Wind and Solar: Net Error outside [-3%, +3%] OR ABS Error >= 9.4%
    # Rest of fuels: Net Error outside [-1%, +1%] OR ABS Error >= 2.6%
    is_wind_solar = df_annual["Fuel"].astype(str).str.upper().isin(["WIND", "SOLAR"])
    cond_wind_solar = is_wind_solar & (
        (df_annual["A_NetError%"].abs() > 3.0) | (df_annual["A_ABS_NetError%"] >= 9.4)
    )
    cond_other_fuels = (~is_wind_solar) & (
        (df_annual["A_NetError%"].abs() > 1.0) | (df_annual["A_ABS_NetError%"] >= 2.6)
    )
    df_annual["NeedsAttention"] = cond_wind_solar | cond_other_fuels

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

    df_annual["ErrorBand"] = df_annual["A_ABS_NetError%"].apply(categorize_error)
    # Order bands for plots
    df_annual["ErrorBand"] = pd.Categorical(
        df_annual["ErrorBand"],
        categories=["0-1%", "1-2%", "2-4%", "4-10%", ">10%"],
        ordered=True,
    )

    return df_annual, df_monthly, None


# Helper to locate local files in inputs/ directory
def find_local_input_file(filename: str):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "inputs", filename),
        os.path.join(os.getcwd(), "inputs", filename),
        os.path.join(script_dir, "..", "inputs", filename),
        os.path.join("inputs", filename),
        os.path.join(script_dir, filename),
        os.path.join(os.getcwd(), filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None


# --- Sidebar: Branding & Data Selection ---
if logo_b64:
    st.sidebar.markdown(
        f"""
        <div class="neso-sidebar-header">
            <img src="data:image/jpeg;base64,{logo_b64}" class="neso-sidebar-logo" alt="NESO Logo" />
            <div class="neso-sidebar-title">Market Monitoring</div>
            <div class="neso-sidebar-subtitle">PN Accuracy Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.subheader("Data Selection")

# Year Selection
default_year_idx = (
    AVAILABLE_YEARS.index(DEFAULT_YEAR) if DEFAULT_YEAR in AVAILABLE_YEARS else 0
)
selected_year = st.sidebar.selectbox(
    "Calendar Year",
    AVAILABLE_YEARS,
    index=default_year_idx,
    key="selected_year_selectbox",
)

annual_filename = f"annual_summary_{selected_year}.csv"
monthly_filename = f"monthly_summary_{selected_year}.csv"
default_annual_path = find_local_input_file(annual_filename)
default_monthly_path = find_local_input_file(monthly_filename)
has_local_inputs = bool(default_annual_path and default_monthly_path)

# Initialize session state for data_source if not set
if "data_source_selection" not in st.session_state:
    st.session_state["data_source_selection"] = "Azure Blob Storage"

data_source_options = [
    "Azure Blob Storage",
    "Local (inputs/ folder)",
    "Manual Upload (CSV)",
]

# Ensure valid index
current_index = 0
if st.session_state["data_source_selection"] in data_source_options:
    current_index = data_source_options.index(st.session_state["data_source_selection"])

data_source = st.sidebar.radio(
    "Data Source",
    data_source_options,
    index=current_index,
    key="data_source_radio",
)
st.session_state["data_source_selection"] = data_source

# Option for automatic fallback if Azure is unavailable
auto_fallback = st.sidebar.checkbox(
    "Auto-fallback to local inputs if Azure fails",
    value=True,
    help="When enabled, if Azure connection fails (e.g. laptop not configured), the dashboard will automatically load local files from 'inputs/'.",
)

annual_raw, monthly_raw = None, None
data_source_mode_notice = None

if data_source == "Azure Blob Storage":
    try:
        project_folder = f"{PROJECT_BASE_NAME}-{selected_year}"
        azure_blob = AzureBlobStorage(ACCOUNT_URL, CONTAINER_NAME, project_folder)
        with st.sidebar.status(
            f"Fetching {selected_year} data from Azure...", expanded=False
        ):
            st.write(
                f"Connecting to container '{CONTAINER_NAME}' ({project_folder})..."
            )
            annual_raw = azure_blob.read_annual_summary()
            st.write(f"Fetched Annual Summary ({annual_filename}).")
            monthly_raw = azure_blob.read_monthly_summary()
            st.write(f"Fetched Monthly Summary ({monthly_filename}).")
        st.sidebar.success(f"✅ Azure {selected_year} Data Loaded Successfully")
    except Exception as e:
        error_details = str(e)
        st.sidebar.error(f"❌ Azure Connection Failed: {error_details}")

        # Check if local files are available as fallback
        if has_local_inputs and auto_fallback:
            st.sidebar.warning(
                f"⚠️ Laptop is not configured for Azure. Automatically loaded local files for {selected_year} from 'inputs/' folder."
            )
            data_source_mode_notice = (
                f"⚠️ **Azure Blob Storage is unavailable on this laptop** (credentials not configured).\n\n"
                f"The dashboard has automatically fallen back to the **local version** using `{annual_filename}` and `{monthly_filename}` from the `inputs/` folder. "
                "You can also manually upload custom CSV files using the sidebar."
            )
            try:
                annual_raw = pd.read_csv(default_annual_path)
                monthly_raw = pd.read_csv(default_monthly_path)
            except Exception as read_err:
                st.error(f"Error reading local inputs folder files: {str(read_err)}")
                st.stop()
        else:
            st.warning("### ⚠️ Azure Connection Failed")
            st.error(
                f"**Error Details**: {error_details}\n\n"
                "This laptop is not configured for Azure authentication (e.g. `az login` not run, or no Azure credentials found)."
            )
            if has_local_inputs:
                st.markdown(f"#### Local data for **{selected_year}** is available:")
                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    if st.button(
                        f"📂 Access Local {selected_year} Data ('inputs/' folder)",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state["data_source_selection"] = (
                            "Local (inputs/ folder)"
                        )
                        st.rerun()
                with col_opt2:
                    if st.button(
                        "📤 Manually Upload CSV Files", use_container_width=True
                    ):
                        st.session_state["data_source_selection"] = (
                            "Manual Upload (CSV)"
                        )
                        st.rerun()
            else:
                st.warning(
                    f"ℹ️ Local data for {selected_year} was also not found in `inputs/` (`{annual_filename}`, `{monthly_filename}`)."
                )
                local_2025_ann = find_local_input_file("annual_summary_2025.csv")
                local_2025_mon = find_local_input_file("monthly_summary_2025.csv")
                if local_2025_ann and local_2025_mon and selected_year != 2025:
                    col_opt1, col_opt2 = st.columns(2)
                    with col_opt1:
                        if st.button(
                            "🔄 Switch to 2025 Local Data ('inputs/' folder)",
                            type="primary",
                            use_container_width=True,
                        ):
                            st.session_state["selected_year_selectbox"] = 2025
                            st.session_state["data_source_selection"] = (
                                "Local (inputs/ folder)"
                            )
                            st.rerun()
                    with col_opt2:
                        if st.button(
                            "📤 Manually Upload CSV Files", use_container_width=True
                        ):
                            st.session_state["data_source_selection"] = (
                                "Manual Upload (CSV)"
                            )
                            st.rerun()
                else:
                    if st.button(
                        "📤 Manually Upload CSV Files",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state["data_source_selection"] = (
                            "Manual Upload (CSV)"
                        )
                        st.rerun()
            st.stop()

elif data_source == "Local (inputs/ folder)":
    # Allow optional manual upload to override local files or supply missing files
    with st.sidebar.expander(
        f"📤 Custom CSV Files for {selected_year} (Optional)",
        expanded=not has_local_inputs,
    ):
        uploaded_annual = st.file_uploader(
            f"Annual Summary CSV ({selected_year})",
            type=["csv"],
            key=f"local_ovr_ann_{selected_year}",
        )
        uploaded_monthly = st.file_uploader(
            f"Monthly Summary CSV ({selected_year})",
            type=["csv"],
            key=f"local_ovr_mon_{selected_year}",
        )

    if not has_local_inputs and not (uploaded_annual and uploaded_monthly):
        st.sidebar.error(
            f"❌ Could not find '{annual_filename}' and '{monthly_filename}' in 'inputs/' folder."
        )
        local_2025_ann = find_local_input_file("annual_summary_2025.csv")
        local_2025_mon = find_local_input_file("monthly_summary_2025.csv")
        if local_2025_ann and local_2025_mon and selected_year != 2025:
            st.info(
                f"ℹ️ Local data for {selected_year} is not in the `inputs/` folder. You can switch back to 2025 or upload CSVs above."
            )
            if st.sidebar.button(
                "🔄 Switch to 2025 Local Data", key="switch_to_2025_local_btn"
            ):
                st.session_state["selected_year_selectbox"] = 2025
                st.rerun()
        else:
            st.info(
                f"ℹ️ Local data for {selected_year} is not in the `inputs/` folder. Please upload `{annual_filename}` and `{monthly_filename}` above or select an available year."
            )
        st.stop()

    if has_local_inputs and not (uploaded_annual and uploaded_monthly):
        st.sidebar.success(f"✅ Using Local 'inputs/' Folder ({selected_year})")
        st.sidebar.caption(f"📁 Annual: `{os.path.basename(default_annual_path)}`")
        st.sidebar.caption(f"📁 Monthly: `{os.path.basename(default_monthly_path)}`")

    try:
        annual_raw = (
            pd.read_csv(uploaded_annual)
            if uploaded_annual
            else pd.read_csv(default_annual_path)
        )
        monthly_raw = (
            pd.read_csv(uploaded_monthly)
            if uploaded_monthly
            else pd.read_csv(default_monthly_path)
        )
    except Exception as read_err:
        st.sidebar.error(f"Error reading CSV: {str(read_err)}")
        st.stop()

    if uploaded_annual or uploaded_monthly:
        st.sidebar.info(f"ℹ️ Using custom uploaded CSV for {selected_year} summaries.")

elif data_source == "Manual Upload (CSV)":
    st.sidebar.markdown(f"### 📤 Upload {selected_year} Summary CSVs")
    uploaded_annual = st.sidebar.file_uploader(
        f"Upload Annual Summary CSV ({selected_year})",
        type=["csv"],
        key=f"man_ann_{selected_year}",
    )
    uploaded_monthly = st.sidebar.file_uploader(
        f"Upload Monthly Summary CSV ({selected_year})",
        type=["csv"],
        key=f"man_mon_{selected_year}",
    )

    if uploaded_annual and uploaded_monthly:
        try:
            annual_raw = pd.read_csv(uploaded_annual)
            monthly_raw = pd.read_csv(uploaded_monthly)
            st.sidebar.success("✅ Both files uploaded successfully.")
        except Exception as read_err:
            st.sidebar.error(f"Error reading uploaded CSVs: {str(read_err)}")
            st.stop()
    else:
        st.info(
            f"ℹ️ Please upload both Annual and Monthly CSV files for {selected_year} to view the dashboard."
        )
        if has_local_inputs:
            if st.button(
                f"📂 Or Switch to Local 'inputs/' Folder Data ({selected_year})"
            ):
                st.session_state["data_source_selection"] = "Local (inputs/ folder)"
                st.rerun()
        st.stop()

# --- Process Data ---
df_annual_raw, df_monthly_raw, error_msg = process_data(
    annual_raw, monthly_raw, year=selected_year
)

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


if data_source_mode_notice:
    st.info(data_source_mode_notice, icon="ℹ️")

if data_source_mode_notice:
    st.info(data_source_mode_notice, icon="ℹ️")

# --- Main Page Header ---
st.markdown(
    """
    <div style="margin-bottom: 1rem;">
        <h1 style="color: #400732; font-size: 2.05rem; font-weight: 800; margin: 0; letter-spacing: -0.02em;">
            Market Monitoring: PN Accuracy Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- UI Tabs ---
tab1, tab1_m, tab1_gwh, tab2_cap, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Executive Summary",
        "Median Error",
        "Total GWh Error",
        "Fleet: Capacity",
        "By Technology",
        "BMU Explorer",
        "Require Attention",
        "Exports",
    ]
)

# --- TAB 1: Executive Summary ---
with tab1:
    st.markdown(
        """
        <div style="margin-bottom: 6px;">
            <h2 style="color: #400732; font-size: 1.6rem; font-weight: 700; margin-bottom: 14px; letter-spacing: -0.015em;">Executive Summary</h2>
        </div>
        <div class="neso-active-window-card">
            <span class="neso-aw-tag">Active Review Window:</span>
            <span class="neso-aw-badge">Dataset: <strong>{selected_year} Calendar Year</strong></span>
            <span class="neso-aw-arrow">➔</span>
            <span class="neso-aw-badge">Status: <strong>Fleet Baseline (Active)</strong></span>
            <span class="neso-aw-info">({len(df_annual):,} BMUs Evaluated • {len(df_monthly):,} Records)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPIs
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    fleet_median_error = df_annual["A_ABS_NetError%"].median()
    fleet_p90_error = df_annual["A_ABS_NetError%"].quantile(0.9)

    # Max error details
    max_err_idx = df_annual["A_ABS_NetError%"].idxmax()
    max_err_row = df_annual.loc[max_err_idx]
    fleet_max_error = max_err_row["A_ABS_NetError%"]
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
            Median_Error_Pct=("A_ABS_NetError%", "median"),
            P90_Error_Pct=("A_ABS_NetError%", lambda x: x.quantile(0.9)),
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
            x="A_ABS_NetError%",
            title="Distribution of Annual Error % (0-100% Range)",
            color_discrete_sequence=["#400732"],
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

        render_chart(fig_hist)

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
            file_name=f"fuel_performance_summary_{selected_year}.csv",
            mime="text/csv",
        )

# --- TAB 1.M: Median Error ---
with tab1_m:
    st.header("Median Error by Fuel")
    st.caption("Distribution of Median Absolute Net Error % across fuel types.")

    fuel_median = (
        df_annual.groupby("Fuel")["A_ABS_NetError%"]
        .median()
        .reset_index()
        .sort_values("A_ABS_NetError%", ascending=True)
    )
    fig_hm1 = px.bar(
        fuel_median,
        x="Fuel",
        y="A_ABS_NetError%",
        title="Median Error % by Fuel",
        color="A_ABS_NetError%",
        color_continuous_scale=["#fcf4fa", "#cf3e9e", "#8a156e", "#400732"],
        template="plotly_white",
        text_auto=".2f",
    )
    fig_hm1.update_layout(xaxis=dict(tickangle=-45))
    render_chart(fig_hm1)

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
        color_continuous_scale=["#fcf4fa", "#cf3e9e", "#8a156e", "#400732"],
        template="plotly_white",
        text_auto=".0f",
    )
    fig_mwh.update_layout(xaxis=dict(tickangle=-45))
    render_chart(fig_mwh)

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
        y_col = "A_ABS_NetError%"
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
        color_discrete_sequence=[
            "#400732",
            "#73135c",
            "#9c1f7e",
            "#059669",
            "#2563eb",
            "#d97706",
            "#dc2626",
            "#0891b2",
            "#6366f1",
        ],
        template="plotly_white",
        size_max=50,
        log_x=use_log_x,
    )
    render_chart(fig_bub)

    st.subheader("Detailed Fleet Table")
    st.dataframe(df_annual, use_container_width=True)


# --- TAB 3: By Technology ---
with tab3:
    st.header("By Technology Analysis")

    # Fuel selector nested in tab
    focus_fuel = st.selectbox("Select Focus Fuel to Analyze", all_fuels, index=0)

    tech_df = df_annual_raw[df_annual_raw["Fuel"] == focus_fuel].copy()
    tech_monthly = df_monthly_raw[df_monthly_raw["Fuel"] == focus_fuel].copy()

    if tech_df.empty:
        st.warning(f"No data for {focus_fuel}.")
    else:
        # KPIs
        t_median = tech_df["A_ABS_NetError%"].median()
        t_p90 = tech_df["A_ABS_NetError%"].quantile(0.9)
        t_count = tech_df["BMU"].nunique()
        t_worst = tech_df.loc[tech_df["A_ABS_NetError%"].idxmax()]["BMU"]
        t_worst_val = tech_df["A_ABS_NetError%"].max()
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
                    x="A_ABS_NetError%",
                    title="Annual Absolute Error % Distribution (0-100% Range)",
                    color_discrete_sequence=["#400732"],
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
                render_chart(fig_thist)

            with tech_tab2:
                st.caption("Distribution of Net Error (GWh) - Directional Bias")
                tech_df["NetError_GWh"] = tech_df["NetError"] / 1000

                fig_net_hist = px.histogram(
                    tech_df,
                    x="NetError_GWh",
                    title="Net GWh Error Distribution (Directional Bias)",
                    color_discrete_sequence=["#9c1f7e"],
                    template="plotly_white",
                    text_auto=True,
                )
                fig_net_hist.update_traces(textposition="outside")
                fig_net_hist.update_layout(
                    xaxis=dict(title="Net Error (GWh)"),
                    yaxis=dict(title="Count of BMUs"),
                    bargap=0.1,
                )
                render_chart(fig_net_hist)

        with tcol2:
            st.subheader("Monthly Error Trend (Median & P90)")
            if not tech_monthly.empty:
                trend = (
                    tech_monthly.groupby(["YearMonth"])
                    .agg(
                        Median_Error=("M_ABS_NetError%", "median"),
                        P90_Error=("M_ABS_NetError%", lambda x: x.quantile(0.9)),
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
                        line=dict(color="#400732", width=2.5),
                        marker=dict(color="#400732", size=6),
                    )
                )
                fig_trend.add_trace(
                    go.Scatter(
                        x=trend["YearMonth"],
                        y=trend["P90_Error"],
                        mode="lines+markers",
                        name="P90",
                        line=dict(color="#9c1f7e", width=2, dash="dash"),
                        marker=dict(color="#9c1f7e", size=6),
                    )
                )

                fig_trend.update_layout(
                    title="Monthly Error Trend", template="plotly_white"
                )
                render_chart(fig_trend)
            else:
                st.info("No monthly data for this fuel.")

        st.subheader("Top & Bottom 10 BMUs")
        tb1, tb2 = st.columns(2)
        with tb1:
            st.caption("Best Performing (Lowest Error)")
            st.dataframe(
                tech_df.nsmallest(10, "A_ABS_NetError%")[
                    ["BMU", "A_ABS_NetError%", "NeedsAttention"]
                ],
                use_container_width=True,
            )
        with tb2:
            st.caption("Worst Performing (Highest Error)")
            st.dataframe(
                tech_df.nlargest(10, "A_ABS_NetError%")[
                    ["BMU", "A_ABS_NetError%", "NeedsAttention"]
                ],
                use_container_width=True,
            )

# --- TAB 4: BMU Explorer ---
with tab4:
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <h2 style="color: #400732; font-size: 1.6rem; font-weight: 700; margin-bottom: 4px;">BMU Explorer</h2>
            <p style="color: #6b5967; font-size: 0.92rem; margin-top: 0; margin-bottom: 14px;">Detailed unit-level deep dive, operational profiles, monthly error trends, and unit data export.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # BMU Search & Selection Controls
    if "bmu_search_term" not in st.session_state:
        st.session_state["bmu_search_term"] = ""

    all_bmus = sorted(df_annual_raw["BMU"].unique().tolist())

    col_input, col_search_btn, col_reset_btn, col_select = st.columns([2.5, 1, 1, 3.5])

    with col_input:
        search_val = st.text_input(
            "Search BMU ID",
            value=st.session_state["bmu_search_term"],
            placeholder="e.g. ABER, DIDC, WBUR...",
            key="bmu_search_text_input",
        )
    with col_search_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button(
            "Search",
            key="bmu_search_submit_btn",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["bmu_search_term"] = search_val.strip().upper()
            st.rerun()
    with col_reset_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Reset", key="bmu_search_reset_btn", use_container_width=True):
            st.session_state["bmu_search_term"] = ""
            st.rerun()

    # Also sync if user typed and pressed enter directly in the input box
    if search_val.strip().upper() != st.session_state["bmu_search_term"]:
        st.session_state["bmu_search_term"] = search_val.strip().upper()

    curr_term = st.session_state["bmu_search_term"]
    if curr_term:
        matching_bmus = [b for b in all_bmus if curr_term in b]
    else:
        matching_bmus = all_bmus

    if not matching_bmus:
        st.warning(
            f"No BMUs found matching '{curr_term}'. Try another search query or click Reset."
        )
    else:
        with col_select:
            bmu_pick = st.selectbox(
                f"Select BMU ({len(matching_bmus)} available):",
                matching_bmus,
                key="bmu_active_picker_selectbox",
            )

        bmu_matches = df_annual_raw[df_annual_raw["BMU"] == bmu_pick]
        if bmu_matches.empty:
            st.warning(f"No data available for BMU '{bmu_pick}'.")
        else:
            bmu_annual = bmu_matches.iloc[0]
            bmu_monthly = df_monthly_raw[df_monthly_raw["BMU"] == bmu_pick].sort_values(
                "YearMonth"
            )

        st.subheader(f"Profile: {bmu_pick}")

        bc1, bc2, bc3 = st.columns(3)

        with bc1:
            st.markdown("### Annual Metrics")
            st.write(f"**Fuel:** {bmu_annual['Fuel']}")
            # Size Category line removed.
            st.write(f"**Annual Net Error %:** {bmu_annual['A_NetError%']:.2f}%")
            st.write(f"**Annual ABS Error %:** {bmu_annual['A_ABS_NetError%']:.2f}%")
            st.write(f"**Total ABS Error (GWh):** {bmu_annual['ABSError']/1000:,.2f}")
            st.write(f"**Net Error (GWh):** {bmu_annual['NetError']/1000:,.2f}")
            # st.write(f"**Monthly P90 Error:** {bmu_annual['P90_monthly_error']:.2f}%")
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
                    y="M_ABS_NetError%",
                    markers=True,
                    title="Monthly Absolute Error %",
                    template="plotly_white",
                    color_discrete_sequence=["#400732"],
                )
                fig_spark.add_hline(
                    y=25,
                    line_dash="dash",
                    line_color="#d90429",
                    annotation_text="25% Threshold",
                    annotation_font_color="#d90429",
                )
                render_chart(fig_spark)
            else:
                st.info("No monthly data available.")

        with bc3:
            st.markdown("### Monthly Data Table")
            st.dataframe(
                bmu_monthly[["YearMonth", "M_NetError%", "M_ABS_NetError%"]],
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

# --- TAB 5: Require Attention ---
with tab5:
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <h2 style="color: #400732; font-size: 1.6rem; font-weight: 700; margin-bottom: 4px;">Require Attention: Units Exceeding Thresholds</h2>
            <p style="color: #6b5967; font-size: 0.92rem; margin-top: 0; margin-bottom: 14px;">
                Balancing Mechanism Units exceeding operational error tolerances (Wind/Solar: Net Error outside ±3% or ABS Error ≥ 9.4%; Other Fuels: Net Error outside ±1% or ABS Error ≥ 2.6%).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    attention_df = df_annual_raw[df_annual_raw["NeedsAttention"] == True].copy()

    if attention_df.empty:
        st.success(
            "🎉 No BMUs require attention! All units within operational tolerances."
        )
    else:
        attention_df["Reason"] = attention_df.apply(get_reason, axis=1)

        st.markdown(
            f"**{len(attention_df)}** BMUs triggered attention thresholds across the fleet:<br>"
            "• **Wind & Solar**: Net Error outside ±3.0% OR Absolute Error ≥ 9.4%<br>"
            "• **All Other Fuels**: Net Error outside ±1.0% OR Absolute Error ≥ 2.6%",
            unsafe_allow_html=True,
        )

        # Download Button
        csv_att = attention_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Attention Needed Units (CSV)",
            data=csv_att,
            file_name=f"bmus_requiring_attention_{selected_year}.csv",
            mime="text/csv",
        )

        for fuel_grp in sorted(attention_df["Fuel"].unique()):
            subset = attention_df[attention_df["Fuel"] == fuel_grp].sort_values(
                "A_ABS_NetError%", ascending=False
            )
            with st.expander(f"Fuel: {fuel_grp} ({len(subset)} units)", expanded=True):
                display_cols = ["BMU", "Reason", "A_NetError%", "A_ABS_NetError%"]
                if "installedCapacity_mwh" in subset.columns:
                    display_cols.append("installedCapacity_mwh")

                st.dataframe(
                    subset[display_cols].style.format(
                        {
                            "A_NetError%": "{:+.2f}%",
                            "A_ABS_NetError%": "{:.2f}%",
                            "installedCapacity_mwh": "{:,.1f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

# --- TAB 6: Exports ---
with tab6:
    st.header("Data Exports")

    st.markdown("""
    ### Export Contents
    
    *   **Annual Summary**: High-level data for every BMU (one row per unit).
    *   **Monthly Summary**: Detailed breakdown (one row per BMU per Month).
    *   **Needs Attention List**: Only the specific BMUs that failed the thresholds.
    """)
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
            file_name=f"annual_summary_{selected_year}_filtered.csv",
            mime="text/csv",
        )

    with ec2:
        st.subheader("Monthly Summary")
        csv_monthly = convert_df(df_monthly)
        st.download_button(
            label="Download Monthly Summary (Filtered)",
            data=csv_monthly,
            file_name=f"monthly_summary_{selected_year}_filtered.csv",
            mime="text/csv",
        )

    with ec3:
        st.subheader("Needs Attention List")
        if not attention_df.empty:
            csv_attn = convert_df(attention_df)
            st.download_button(
                label="Download Attention List",
                data=csv_attn,
                file_name=f"needs_attention_list_{selected_year}.csv",
                mime="text/csv",
            )
        else:
            st.write("No attention list to download.")
