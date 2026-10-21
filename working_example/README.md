# PN Accuracy Dashboard 2025 ------ Not migrated yet

## 🎯 Overview
This application analyzes the forecasting accuracy of power generation assets (PN vs Metered) for the year 2025. It is designed to identify "Volume Risk", "Directional Bias", and exceptional performers across the fleet.

## 🚀 Quick Start
This folder is self-contained. To run the dashboard:

1.  **Install Dependencies**:
    
    pip install -r requirements.txt
    

2.  **Run Application**:
    
    python -m streamlit run app.py
    

## 📊 Key Features
*   **Executive Summary**: High-level KPIs and Fleet Health.
*   **Fleet Overview**: Distribution and Capacity analysis (Bubble Charts).
*   **By Technology**: Deep dive into Fuel types (Efficiency vs Bias).
*   **BMU Explorer**: Detailed monthly trends for specific units.
*   **Attention Needed**: Automated flagging of non-compliant units (>25% error).

