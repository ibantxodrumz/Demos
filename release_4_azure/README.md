# Physical Notification (PN) Accuracy Dashboard — Release 4

## 🎯 Overview
This enterprise analytical dashboard monitors and assesses the Physical Notification (PN) accuracy of Balancing Mechanism Units (BMUs) across the GB power generation fleet. It evaluates volume risk, directional bias, and compliance tolerances across multiple calendar years (2025, 2026+).

---

## 🌟 What's New in Release 4
- **Multi-Year Data Selection**: Toggle between calendar years (2025, 2026, etc.) dynamically from the sidebar. Azure streams from `pn-accuracy-{year}/internal/` while local mode automatically picks up corresponding files from `inputs/`.
- **Hybrid Data Sourcing & Graceful Fallback**: Seamless switching between **Azure Blob Storage**, **Local `inputs/` folder**, and **Manual CSV Upload**. When Azure credentials are not present, the app never crashes; it displays an informative notice and falls back to bundled local inputs.
- **Guardian Regression Test Suite**: Integrated test suite (`tests/`) ensuring fuel thresholds, schema parsing, blob URLs, and baseline fleet metrics remain regression-free.
- **Corporate NESO Visual Design**: Fully aligned with brand guidelines (Plum `#400732`, Raspberry `#d02670`, custom header navbar, embedded logo, and unified Plotly theming).
- **BMU Explorer Filter & Search**: Quick text search with dedicated Search and Reset buttons.
- **Fuel-Specific "Require Attention" Rules**: Automated flagging for Wind/Solar (Net Error outside $\pm3\%$ or ABS $\ge 9.4\%$) and Other Fuels (Net Error outside $\pm1\%$ or ABS $\ge 2.6\%$).

---

## 💻 Windows 11 Setup Guide (VS Code + Conda)

This package is designed to run self-contained on **Windows 11** using **Conda** and **Visual Studio Code**.

### 1. Prerequisites on Windows 11
* **Miniconda or Anaconda**: [Install Miniconda for Windows](https://docs.conda.io/en/latest/miniconda.html)
* **Visual Studio Code**: [Install VS Code](https://code.visualstudio.com/)
* **Azure CLI (Optional for Azure mode)**: [Install Azure CLI for Windows](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows)

---

### 2. Environment Setup (Terminal in VS Code)
Open VS Code, press `Ctrl + ~` to open the integrated terminal (Command Prompt or PowerShell), and run:

```powershell
# 1. Create a clean Conda environment with Python 3.11
conda create -n dashboard python=3.11 -y

# 2. Activate the environment
conda activate dashboard

# 3. Navigate into the release directory (if not already there)
cd release_4_azure

# 4. Install dependencies
pip install -r requirements.txt
```

---

### 3. Verification: Run Guardian Test Suite
Before launching the application, verify that your environment passes all analytical and schema invariants:

```powershell
python tests/run_tests.py
```
*(All 31 guardian tests should execute and report `✅ ALL TEST SUITES PASSED` in < 1 second).*

---

### 4. Running the Dashboard

#### Option A: Offline / Local Mode (Default)
If you do not have corporate Azure credentials configured, simply launch:
```powershell
streamlit run app.py
```
The dashboard will open automatically in your default browser at `http://localhost:8501`. If Azure authentication is unavailable, the application will automatically load the baseline data from `inputs/annual_summary_2025.csv` and `inputs/monthly_summary_2025.csv`.

#### Option B: Enterprise Azure Blob Storage Mode
If running on a corporate Windows 11 machine connected to the NESO network:
```powershell
# Authenticate with your corporate Microsoft account
az login

# Launch Streamlit
streamlit run app.py
```
In the sidebar, ensure **Azure Blob Storage** is selected. The application will authenticate seamlessly via `AzureCliCredential` and fetch data directly from `datalake/pn-accuracy-{year}/internal/`.

---

## 📂 Project Structure

```
release_4_azure/
├── app.py                      # Main Streamlit application
├── constants.py                # Endpoints, container names, and multi-year configuration
├── azure_blob_helper.py        # Authenticated Azure Blob Storage reader
├── requirements.txt            # Pinned dependencies
├── README.md                   # This documentation
├── assets/                     # Corporate logos and branding
│   └── neso_logo.jpg
├── inputs/                     # Bundled local fallback datasets
│   ├── annual_summary_2025.csv
│   └── monthly_summary_2025.csv
├── documentation/              # Supporting stakeholder guides
│   └── How_to.docx
└── tests/                      # Guardian regression test suite
    ├── run_tests.py            # Single-command test runner / release gate
    ├── test_business_rules.py  # Unit tests for thresholds & reason tagging
    ├── test_data_processing.py # Unit tests for parsing & multi-year stamping
    ├── test_azure_and_fallback.py # Unit tests for Azure paths & fallback
    └── test_baseline_invariants.py # Invariant audit on 2025 canonical data
```

---

## 📊 Dashboard Tabs & Operational Views

1. **Executive Summary**: High-level KPIs (Fleet Median Error, P90, Total ABS GWh, Net Directional Bias) and Fuel Performance table.
2. **Median Error**: Visual distribution of Median Absolute Net Error % grouped by fuel technology.
3. **Total GWh Error**: Aggregate volume impact in Gigawatt-hours (GWh).
4. **Fleet: Capacity**: Fleet capacity scatter and bubble charts comparing installed capacity against forecasting error.
5. **By Technology**: Deep-dive into individual fuel performance, efficiency vs. bias, and monthly trends.
6. **BMU Explorer**: Search and inspect individual unit profiles with 12-month error bars, Net Error trends, and unit-level CSV export.
7. **Require Attention**: Automated operational queue filtering BMUs exceeding tolerances:
   * **Wind & Solar**: Net Error outside $\pm3.0\%$ OR Absolute Error $\ge 9.4\%$
   * **All Other Fuels**: Net Error outside $\pm1.0\%$ OR Absolute Error $\ge 2.6\%$
   Includes one-click CSV export: `bmus_requiring_attention_{year}.csv`.
8. **Exports**: Filtered data exports for Annual Summary, Monthly Summary, and the Attention List.
