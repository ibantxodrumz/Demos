# Interconnector Intelligence Dashboard (Release 2025)

## Overview
This application provides a comprehensive analysis of cross-border electricity trading flows between the UK and its neighbors (France, Netherlands, Belgium, Denmark) for the year 2025. It allows Energy Analysts to visualize hourly capacities, detect threshold breaches (>500MW), and explore daily/monthly trends.

## Setup & Running
This release is self-contained. To run the application:

1.  **Environment**: Ensure you have Python installed (3.9+).
2.  **Dependencies**: Install the required libraries.
    ```bash
    pip install -r requirements.txt
    ```
3.  **Launch**: Run the Streamlit app.
    ```bash
    streamlit run app.py
    ```

## Folder Structure
-   **`app.py`**: The main application code.
-   **`inputs/`**: Place your source CSV files here. The app automatically loads all `.csv` files in this folder.
    -   *included*: Data for IFA1, IFA2, Nemo, Viking, Eleclink, Britned (2025).
-   **`outputs/`**: Exports (CSVs and Charts) will be saved here.
-   **`.streamlit/`**: Configuration for the UI theme.

## Features
-   **Executive Summary**: High-level KPIs (Total Energy, Active Days).
-   **Daily Activity**: Heatmaps and bar charts of daily flows.
-   **Monthly Breakdown**: Aggregated volume analysis.
-   **Detail Log**: Row-level data inspection.
-   **Exports**: Save filtered datasets and clean charts for reporting.
