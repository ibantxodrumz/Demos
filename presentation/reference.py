import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Set page config
st.set_page_config(
    page_title="Interconnector Trading Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading & Transformation ---
def force_light_chart(fig):
    """Explicitly force white background and dark text on Plotly charts."""
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#111827"),
        xaxis=dict(gridcolor="#e5e7eb", linecolor="#111827"),
        yaxis=dict(gridcolor="#e5e7eb", linecolor="#111827"),
        title_font=dict(color="#111827")
    )
    return fig

@st.cache_data
def load_and_transform_data(files_or_paths):
    all_dfs = []
    required_cols = ["HourStartLocal", "Interconnector", "Trade_Abs_MW", "Trade_Direction", "IsPartialHour", "Trade_Bucket_All"]
    
    for source in files_or_paths:
        try:
            if isinstance(source, str):
                df = pd.read_csv(source)
            else:
                df = pd.read_csv(source)
                
            # Basic validation
            if not all(col in df.columns for col in required_cols):
                continue
                
            # Date parsing - First pass, just ensure it's loaded as object/string usually, we will convert later
            # Note: We skip per-file transformation to avoid the 'Can only use .dt accessor' errors if read fails to imply type
            
            all_dfs.append(df)
        except Exception as e:
            st.error(f"Error loading {source}: {e}")
            continue
            
    if not all_dfs:
        return pd.DataFrame()
        
    fact_trades = pd.concat(all_dfs, ignore_index=True)
    
    # Ensure datetime (UTC) after concatenation for robustness
    fact_trades["HourStartLocal"] = pd.to_datetime(fact_trades["HourStartLocal"], errors='coerce', utc=True)
    
    # Drop invalid
    fact_trades = fact_trades.dropna(subset=["HourStartLocal", "Trade_Abs_MW", "Interconnector"])
    
    # Derived Columns (Safe now that HourStartLocal is definitely datetime)
    fact_trades["Date"] = fact_trades["HourStartLocal"].dt.date
    fact_trades["Hour"] = fact_trades["HourStartLocal"].dt.hour
    fact_trades["Year"] = fact_trades["HourStartLocal"].dt.year
    fact_trades["Month"] = fact_trades["HourStartLocal"].dt.month
    fact_trades["MonthName"] = fact_trades["HourStartLocal"].dt.month_name()
    fact_trades["YearMonth"] = fact_trades["HourStartLocal"].dt.strftime("%Y-%m")

    # Interconnector Group Mapping
    def map_group(name):
        name_str = str(name).upper()
        if "IFA" in name_str:
            return "IFA"
        return name
    
    fact_trades["Interconnector Group"] = fact_trades["Interconnector"].apply(map_group)

    return fact_trades

# Inject Force-Light CSS
st.markdown("""
<style>
    /* 1. Global Background - Safe */
    .stApp {
        background-color: #ffffff !important;
        color: #111827 !important;
    }
    
    /* 2. Sidebar - Safe */
    section[data-testid="stSidebar"] {
        background-color: #f9fafb !important;
    }
    section[data-testid="stSidebar"] * {
        color: #111827 !important;
    }
    
    /* 3. Text - Safe */
    h1, h2, h3, h4, h5, h6, p, li, .stMarkdown, label {
        color: #111827 !important;
    }
    
    /* 4. Inputs & Dropdowns - AGGRESSIVE FIX */
    /* Input Box Container */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #111827 !important;
        border-color: #d1d5db !important;
    }
    
    /* POPOVER CONTAINER (The Dropdown List) */
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
    }
    
    div[data-baseweb="popover"] > div {
        background-color: #ffffff !important;
    }
    
    /* THE ACTUAL LIST */
    div[data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    
    ul {
        background-color: #ffffff !important;
    }
    
    /* OPTIONS */
    li[role="option"], div[role="option"] {
        background-color: #ffffff !important;
        color: #111827 !important;
    }
    
    /* FORCE TEXT COLOR INSIDE OPTIONS */
    li[role="option"] *, div[role="option"] * {
        color: #111827 !important;
    }
    
    /* HOVER STATE */
    li[role="option"]:hover, div[role="option"]:hover {
        background-color: #f3f4f6 !important;
    }
    
    /* ACTIVE/SELECTED STATE */
    li[role="option"][aria-selected="true"], div[role="option"][aria-selected="true"] {
        background-color: #eff6ff !important;
        color: #1d4ed8 !important;
    }
    
    /* Selected Value Text in Input */
    div[data-testid="stSelectbox"] div[class*="singleValue"] {
        color: #111827 !important;
    }
    
    /* 5. File Uploader - Safe */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #f9fafb !important;
        border: 1px dashed #d1d5db !important;
    }
    [data-testid="stFileUploaderDropzone"] div, [data-testid="stFileUploaderDropzone"] span, [data-testid="stFileUploaderDropzone"] small {
        color: #111827 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        color: #111827 !important;
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* 6. Metrics - Safe */
    .stMetric {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
    }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {
        color: #111827 !important;
    }

    /* 7. General Buttons - Fix */
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
    .stButton > button p {
        color: #111827 !important; 
    }
    .stButton > button:hover p {
        color: #4A90E2 !important;
    }
    /* 8. Expanders - Fix */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #e5e7eb !important;
    }
    .streamlit-expanderHeader:hover {
        background-color: #f9fafb !important;
        color: #4A90E2 !important;
    }
    .streamlit-expanderHeader p, .streamlit-expanderHeader span, .streamlit-expanderHeader svg {
        color: #111827 !important;
    }
    .streamlit-expanderHeader:hover p, .streamlit-expanderHeader:hover span, .streamlit-expanderHeader:hover svg {
        color: #4A90E2 !important;
    }
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #e5e7eb !important;
        border-top: none !important;
    }
    .streamlit-expanderContent p {
        color: #111827 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Controls ---
st.sidebar.title("Configuration")

# Local files or Upload
data_dir = "inputs"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

local_filenames = [
    "ifa1_hourly_2025.csv", "ifa2_hourly_2025.csv", "nemo_hourly_2025.csv",
    "viking_hourly_2025.csv", "eleclink_hourly_2025.csv", "britned_hourly_2025.csv"
]
existing_paths = [os.path.join(data_dir, f) for f in local_filenames if os.path.exists(os.path.join(data_dir, f))]

uploaded_files = st.sidebar.file_uploader("Upload CSVs", type=["csv"], accept_multiple_files=True)

sources = uploaded_files if uploaded_files else existing_paths

if not sources:
    st.info("Please upload CSV files or ensure they exist in the 'inputs' folder.")
    st.stop()

fact_trades_raw = load_and_transform_data(sources)

if fact_trades_raw is None or fact_trades_raw.empty:
    st.warning("No data loaded. Check file schemas.")
    st.stop()

# --- Global Filters ---
st.sidebar.markdown("---")
st.sidebar.subheader("Focus Mode")

# Single IC or Global Selector
focus_options = ["Global Network (All)"] + sorted(fact_trades_raw["Interconnector"].unique().tolist())
focus_mode = st.sidebar.selectbox("Select Interconnector", focus_options, index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("Threshold & Logic")

# Threshold
mw_threshold = st.sidebar.slider("MW threshold (X)", 0, 2000, 500, step=10, format="%d MW")

# Hidden Detail Filters (Optional Expand)
with st.sidebar.expander("Advanced Filter Controls"):
    groups = sorted(fact_trades_raw["Interconnector Group"].unique())
    selected_groups = st.multiselect("Interconnector Group", groups, default=groups)
    direction_mode = st.selectbox("Direction", ["Both", "Import", "Export"], index=0)
    include_partial = st.checkbox("Include partial hours", value=False)

# --- Filtering Logic ---
def apply_filters(df, dr, groups_sel, ics_sel, dir_mode, inc_partial):
    temp_df = df.copy()
    
    # Date filter
    if isinstance(dr, (list, tuple)) and len(dr) == 2:
        temp_df = temp_df[(temp_df["Date"] >= dr[0]) & (temp_df["Date"] <= dr[1])]
    
    # Interconnector filters
    temp_df = temp_df[temp_df["Interconnector Group"].isin(groups_sel)]
    temp_df = temp_df[temp_df["Interconnector"].isin(ics_sel)]
    
    # Partial hour
    if not inc_partial:
        temp_df = temp_df[temp_df["IsPartialHour"] == False]
        
    # Direction filter for metrics (Import/Export only rows)
    if dir_mode == "Import":
        temp_df = temp_df[temp_df["Trade_Direction"] == "Import"]
    elif dir_mode == "Export":
        temp_df = temp_df[temp_df["Trade_Direction"] == "Export"]
        
    return temp_df

# --- Main Analysis Logic ---
is_single_ic = focus_mode != "Global Network (All)"
current_display_name = focus_mode if is_single_ic else "Global Network"

# Apply selections
primary_ics = [focus_mode] if is_single_ic else fact_trades_raw["Interconnector"].unique().tolist()
# We use full date span for boss overview unless they use sliders (defaulting to full range for simplicity)
date_range = [fact_trades_raw["Date"].min(), fact_trades_raw["Date"].max()]

filtered_fact = apply_filters(fact_trades_raw, date_range, groups, primary_ics, direction_mode, include_partial)

# Calculations
def get_measures(df, threshold):
    subset = df[df["Trade_Abs_MW"] > threshold]
    # For global view, we use Interconnector-Hours (sum of all IC activity)
    # but for consistent counting, we'll label it clearly in the UI
    ic_hours_above = subset.shape[0]
    # Network hours means how many hours of the year had AT LEAST one breach
    network_hours_above = subset["HourStartLocal"].nunique()
    days_above = subset["Date"].nunique()
    # If using hourly data, sum of MW = MWh
    total_energy_mwh = subset["Trade_Abs_MW"].sum()
    avg_power_mw = subset["Trade_Abs_MW"].mean() if ic_hours_above > 0 else 0
    return ic_hours_above, network_hours_above, days_above, total_energy_mwh, avg_power_mw

ic_hours, network_hours, days_above, total_energy_mwh, avg_power_mw = get_measures(filtered_fact, mw_threshold)
# Comparison baseline
h_above_total, _, _, _, _ = get_measures(fact_trades_raw, mw_threshold)

# --- UI Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Executive Summary", "📅 Daily Activity", "📈 Monthly Breakdown", "🔍 Detail Log", "📥 Exports"])

with tab1:
    st.title(f"Executive Analysis: {current_display_name} ({direction_mode})")
    st.markdown(f"**Performance summary of {direction_mode.lower() if direction_mode != 'Both' else 'all'} activity exceeding {mw_threshold} MW.**")
    
    # KPI Row
    c1, c2, c3, c4 = st.columns(4)
    hour_label = "Interconnector-Hours" if not is_single_ic else "Hours Above Threshold"
    c1.metric(hour_label, f"{ic_hours:,}", 
              help=f"The total cumulative hours across all selected interconnectors that exceeded {mw_threshold} MW.")
    c2.metric("Active Days", f"{days_above:,}",
              help=f"Number of distinct days that had at least one hour above {mw_threshold} MW.")
    c3.metric("Avg Power (Active)", f"{avg_power_mw:,.0f} MW",
              help=f"The average trading level maintained during the hours it was above {mw_threshold} MW.")
    c4.metric("Total Energy", f"{total_energy_mwh/1000:,.1f} GWh",
              help="The total cumulative electricity transferred (Volume) during these high-capacity hours over the whole year.")

    st.markdown("---")
    
    # Quick Summary
    st.subheader("� Quick Summary")
    if not filtered_fact.empty:
        heavy_trades = filtered_fact[filtered_fact["Trade_Abs_MW"] > mw_threshold]
        if not heavy_trades.empty:
            peak_day = heavy_trades.groupby("Date").size().idxmax()
            best_month = heavy_trades.groupby("MonthName").size().idxmax()
            fav_direction = heavy_trades["Trade_Direction"].mode()[0]
            
            st.info(f"📊 **Trend:** `{current_display_name}` most frequently operates above your {mw_threshold} MW threshold in **{best_month}**.")
            st.info(f"↔️ **Market:** Most high-capacity trades move in the **{fav_direction}** direction.")
            st.info(f"📅 **Peak:** The busiest individual day was **{peak_day.strftime('%A, %b %d')}**.")
        else:
            st.warning(f"No periods found where {current_display_name} traded more than {mw_threshold} MW.")
    
    # Capacity Profile
    st.subheader("Capacity Utilization Profile")
    st.write(f"This shows how many times (frequency) the interconnector reaches specific MW levels.")
    
    fig_prof = px.histogram(filtered_fact, x="Trade_Abs_MW", nbins=50, 
                            title=f"Frequency of Power Levels (MW)", 
                            labels={"Trade_Abs_MW": "Power Level (MW)", "count": "Frequency (Hours)"},
                            range_x=[0, 2000],
                            color_discrete_sequence=['#4A90E2'],
                            template="plotly_white")
    
    # Ensure x-axis shows clear ticks
    fig_prof.update_xaxes(dtick=50, tick0=0, range=[0, 2000])
    fig_prof.add_vline(x=mw_threshold, line_dash="dash", line_color="red", 
                       annotation_text=f"Your {mw_threshold} MW Threshold")
    
    # FORCE LIGHT MODE
    fig_prof = force_light_chart(fig_prof)
    st.plotly_chart(fig_prof, use_container_width=True, theme=None)

    with st.expander("📊 View Precise Utilization Breakdown (50 MW steps)"):
        st.write("This table shows the exact number of hours spent at each power level.")
        
        # Calculate frequencies in 50 MW increments
        bins = list(range(0, 2050, 50))
        labels = [f"{i} to {i+50} MW" for i in bins[:-1]]
        
        dist_df = filtered_fact.copy()
        dist_df["MW Range"] = pd.cut(dist_df["Trade_Abs_MW"], bins=bins, labels=labels, include_lowest=True)
        
        stats = dist_df.groupby("MW Range", observed=True).size().reset_index(name="Hour Count")
        
        # Display as a clean table
        st.dataframe(stats, use_container_width=True, hide_index=True)

with tab2:
    st.header(f"Daily {direction_mode} Breakdown")
    
    if not filtered_fact.empty:
        st.subheader("Birds-eye View (Full Year)")
        st.write(f"This chart shows how many hours each day exceeded your {mw_threshold} MW limit.")
        
        # Use nunique to ensure we don't exceed 24 hours per day in the visual
        daily_data = filtered_fact[filtered_fact["Trade_Abs_MW"] > mw_threshold].groupby("Date")["Hour"].nunique().reset_index(name="Hours Over Threshold")
        if not daily_data.empty:
            fig_daily = px.bar(daily_data, x="Date", y="Hours Over Threshold", 
                               title=f"Network Activity Hours (Max 24h per day)", 
                               color="Hours Over Threshold", color_continuous_scale="Blues",
                               template="plotly_white")
            fig_daily = force_light_chart(fig_daily)
            st.plotly_chart(fig_daily, use_container_width=True, theme=None)
        
        st.markdown("---")
        st.subheader("🔍 Single Day Drill-down")
        st.write("Select a specific day to verify the hourly capacity profile.")
        
        # Date selection within the tab
        min_d = filtered_fact["Date"].min()
        max_d = filtered_fact["Date"].max()
        
        # Default to the peak day identified in the summary if available
        peak_day_val = min_d
        heavy_trades = filtered_fact[filtered_fact["Trade_Abs_MW"] > mw_threshold]
        if not heavy_trades.empty:
            peak_day_val = heavy_trades.groupby("Date").size().idxmax()

        selected_day = st.date_input("Choose a day to analyze", value=peak_day_val, min_value=min_d, max_value=max_d)
        
        # Hourly profile for that day
        day_df = filtered_fact[filtered_fact["Date"] == selected_day].sort_values("Hour")
        
        if not day_df.empty:
            fig_hour = px.bar(day_df, x="Hour", y="Trade_Abs_MW", 
                             title=f"Hourly Capacity Profile: {selected_day.strftime('%A, %b %d %Y')}",
                             labels={"Trade_Abs_MW": "Capacity (MW)", "Hour": "Hour of Day"},
                             color="Trade_Abs_MW", color_continuous_scale="YlGnBu",
                             template="plotly_white")
            
            fig_hour.add_hline(y=mw_threshold, line_dash="dash", line_color="red", 
                              annotation_text=f"Threshold: {mw_threshold} MW")
            
            # Forced range for consistency
            fig_hour.update_yaxes(range=[0, max(2000, day_df["Trade_Abs_MW"].max() + 100)])
            fig_hour.update_xaxes(dtick=1)
            
            fig_hour = force_light_chart(fig_hour)
            st.plotly_chart(fig_hour, use_container_width=True, theme=None)
            
            # Table view for precision
            with st.expander("View hourly data values"):
                st.write(day_df[["Hour", "Interconnector", "Trade_Direction", "Trade_Abs_MW"]].reset_index(drop=True))
        else:
            st.warning(f"No data available for {selected_day}.")
            
    else:
        st.info(f"No data matches current filters.")

with tab3:
    st.header(f"Monthly {direction_mode} Summary")
    st.write(f"Aggregated view of {direction_mode.lower() if direction_mode != 'Both' else 'all'} activity exceeding the {mw_threshold} MW threshold.")
    
    if not filtered_fact.empty:
        monthly_data = filtered_fact[filtered_fact["Trade_Abs_MW"] > mw_threshold].groupby(["Month", "MonthName"]).agg(
            Hours_Above_Limit=("Trade_Abs_MW", "count"),
            Total_Capacity_MW=("Trade_Abs_MW", "sum")
        ).sort_index().reset_index()
        
        if not monthly_data.empty:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                fig_m1 = px.bar(monthly_data, x="MonthName", y="Hours_Above_Limit", 
                                title=f"Total Hours Above {mw_threshold} MW", 
                                labels={"Hours_Above_Limit": "Hours Over Limit"},
                                color_discrete_sequence=['#1f77b4'],
                                template="plotly_white")
                fig_m1 = force_light_chart(fig_m1)
                st.plotly_chart(fig_m1, use_container_width=True, theme=None)
            with col_b2:
                fig_m2 = px.bar(monthly_data, x="MonthName", y="Total_Capacity_MW", 
                                title=f"Total Capacity Traded (MW sum)", 
                                labels={"Total_Capacity_MW": "Capacity (MW)"},
                                color_discrete_sequence=['#45adff'],
                                template="plotly_white")
                fig_m2 = force_light_chart(fig_m2)
                st.plotly_chart(fig_m2, use_container_width=True, theme=None)
            
            st.markdown("---")
            st.subheader("🔍 Single Month Drill-down")
            st.write("Select a month to see the daily capacity distribution.")
            
            # Month selection
            months_available = monthly_data["MonthName"].tolist()
            # Default to peak month
            peak_m = monthly_data.loc[monthly_data["Hours_Above_Limit"].idxmax(), "MonthName"]
            selected_m_name = st.selectbox("Choose a month to analyze", options=months_available, index=months_available.index(peak_m))
            
            # Filter for that month
            month_df = filtered_fact[filtered_fact["MonthName"] == selected_m_name]
            
            if not month_df.empty:
                # Daily breakdown for that month - ensure 24h limit for visual
                month_daily = month_df[month_df["Trade_Abs_MW"] > mw_threshold].groupby("Date").agg(
                    Daily_Hours=("Hour", "nunique"),
                    Daily_Capacity_MW=("Trade_Abs_MW", "sum")
                ).reset_index()
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    fig_dm1 = px.bar(month_daily, x="Date", y="Daily_Hours", 
                                    title=f"Daily Active Hours (Max 24h) in {selected_m_name}",
                                    color="Daily_Hours", color_continuous_scale="Blues",
                                    template="plotly_white")
                    fig_dm1 = force_light_chart(fig_dm1)
                    st.plotly_chart(fig_dm1, use_container_width=True, theme=None)
                with col_d2:
                    fig_dm2 = px.line(month_daily, x="Date", y="Daily_Capacity_MW", 
                                     title=f"Daily Energy Volume (MWh) in {selected_m_name}",
                                     labels={"Daily_Capacity_MW": "Energy (MWh)"},
                                     markers=True,
                                     template="plotly_white")
                    fig_dm2 = force_light_chart(fig_dm2)
                    st.plotly_chart(fig_dm2, use_container_width=True, theme=None)
            else:
                st.warning(f"No specific data breakdown available for {selected_m_name}.")
                
        else:
            st.info(f"No monthly breaches of the {mw_threshold} MW threshold found.")

with tab4:
    st.header("Search Detail Logs")
    st.write(f"Chronological list of every hour exceeding {mw_threshold} MW.")
    log_data = filtered_fact[filtered_fact["Trade_Abs_MW"] > mw_threshold].sort_values("HourStartLocal", ascending=False)
    st.dataframe(log_data[["HourStartLocal", "Interconnector", "Trade_Direction", "Trade_Abs_MW", "Trade_Bucket_All"]], use_container_width=True)

with tab5:
    st.header("Data Exports")
    st.write("Ready-to-use data for external reporting.")

    # Helper for saving
    def save_to_outputs(df, filename):
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, filename)
        try:
            df.to_csv(save_path, index=False)
            st.success(f"✅ Saved: `{save_path}`")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.subheader("Focused Intelligence")
    st.write(f"Data for: **{current_display_name}** ({direction_mode})")
    
    # High capacity set
    high_cap_set = filtered_fact[filtered_fact["Trade_Abs_MW"] > mw_threshold]
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save High-Capacity Data to 'outputs'"):
            save_to_outputs(high_cap_set, f"{current_display_name}_High_Capacity_{mw_threshold}MW.csv")

    with col2:
        if st.button("💾 Save Full Report to 'outputs'"):
            save_to_outputs(filtered_fact, f"{current_display_name}_Full_Report.csv")
                      
    st.markdown("---")
    st.subheader("Master Repository")
    st.write(f"Total entries in system: {len(fact_trades_raw):,}")
    
    if st.button("💾 Save Master Network Table to 'outputs'"):
        save_to_outputs(fact_trades_raw, "Full_Network_2025_Master.csv")

    st.markdown("---")
    st.subheader("🖼️ Save Charts as Pictures")
    st.write("Export the current visualizations (Executive, Daily, Monthly) as images to your 'outputs' folder.")
    
    if st.button("📸 Save All Charts to 'outputs'"):
        output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        saved_count = 0
        
        # List of potential figures to save
        figures_to_save = {}
        # We access local variables safely. In Streamlit script execution, they should avail if tabs ran.
        # However, purely local variables inside 'with' might strictly need care. 
        # But 'fig_prof', 'fig_daily', etc. are assigned in the script flow.
        
        if 'fig_prof' in locals(): figures_to_save['Capacity_Utilization_Profile.png'] = locals()['fig_prof']
        if 'fig_daily' in locals(): figures_to_save['Daily_Activity_Summary.png'] = locals()['fig_daily']
        if 'fig_hour' in locals(): figures_to_save[f'Daily_Drilldown_{selected_day}.png'] = locals()['fig_hour']
        if 'fig_m1' in locals(): figures_to_save['Monthly_Hours_Distribution.png'] = locals()['fig_m1']
        if 'fig_m2' in locals(): figures_to_save['Monthly_Energy_Distribution.png'] = locals()['fig_m2']
        if 'fig_dm1' in locals(): figures_to_save[f'Monthly_Drilldown_Hours_{selected_m_name}.png'] = locals()['fig_dm1']
        if 'fig_dm2' in locals(): figures_to_save[f'Monthly_Drilldown_Energy_{selected_m_name}.png'] = locals()['fig_dm2']
        
        try:
            import plotly.io as pio
            for fname, fig in figures_to_save.items():
                if fig:
                    save_path = os.path.join(output_dir, fname)
                    fig.write_image(save_path)
                    saved_count += 1
            
            if saved_count > 0:
                st.success(f"✅ Successfully saved {saved_count} charts to `{output_dir}`")
            else:
                st.warning("No charts found to save. (Did the other tabs load?)")
                
        except ImportError:
            st.error("Missing 'kaleido' package. Please run `pip install kaleido` to enable image export.")
        except Exception as e:
            st.error(f"Error saving images: {e}")
                          



