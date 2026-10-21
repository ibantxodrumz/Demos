import unittest
import pandas as pd
import numpy as np
from tests import get_app_module

app = get_app_module()
process_data = app.process_data


class TestDataProcessing(unittest.TestCase):
    """Guards data ingestion, schema coercion, date parsing, and multi-year stamping."""

    def setUp(self):
        # Minimal synthetic raw Annual DataFrame
        self.raw_annual = pd.DataFrame(
            {
                "nationalGridBmUnit": ["UNIT_WIND_1", "UNIT_CCGT_1", "UNIT_DIRTY_1"],
                "Fuel_type": ["WIND", "CCGT", "SOLAR"],
                "installedCapacity_mwh": [100.0, 500.0, "invalid_num"],
                "PNLevel": [80.0, 450.0, None],
                "MELLevel": [100.0, 500.0, np.nan],
                "MILLevel": [0.0, 100.0, 0.0],
                "BidVolume": [0.0, 0.0, 0.0],
                "OfferVolume": [0.0, 0.0, 0.0],
                "Metered": [75.0, 448.0, 10.0],
                "ExpectOT": [75.0, 448.0, 10.0],
                "CapacityCalibrated": [1.0, 1.0, 1.0],
                "NetError": [-5.0, -2.0, 0.0],
                "ABSError": [5.0, 2.0, 0.0],
                "max_M_ABS_NetError%": [6.2, 0.4, 0.0],
                "A_NetError%": [-6.25, -0.44, 0.0],
                "A_ABS_NetError%": [6.25, 0.44, 0.0],
            }
        )

        # Minimal synthetic raw Monthly DataFrame
        self.raw_monthly = pd.DataFrame(
            {
                "nationalGridBmUnit": ["UNIT_WIND_1", "UNIT_WIND_1", "UNIT_CCGT_1"],
                "Fuel_type": ["WIND", "WIND", "CCGT"],
                "year_month": ["2025-01", "2025-02", "2025-01"],
                "PNLevel": [40.0, 40.0, 450.0],
                "MELLevel": [50.0, 50.0, 500.0],
                "MILLevel": [0.0, 0.0, 100.0],
                "BidVolume": [0.0, 0.0, 0.0],
                "OfferVolume": [0.0, 0.0, 0.0],
                "Metered": [37.0, 38.0, 448.0],
                "ExpectOT": [37.0, 38.0, 448.0],
                "CapacityCalibrated": [1.0, 1.0, 1.0],
                "NetError": [-3.0, -2.0, -2.0],
                "ABSError": [3.0, 2.0, 2.0],
                "installedCapacity_mwh": [100.0, 100.0, 500.0],
                "M_NetError%": [-7.5, -5.0, -0.44],
                "M_ABS_NetError%": [7.5, 5.0, 0.44],
            }
        )

    def test_clean_processing_pipeline(self):
        df_a, df_m, err = process_data(self.raw_annual, self.raw_monthly, year=2025)
        self.assertIsNone(err)
        self.assertIsNotNone(df_a)
        self.assertIsNotNone(df_m)

        # Standard column names
        self.assertIn("BMU", df_a.columns)
        self.assertIn("Fuel", df_a.columns)
        self.assertIn("Year", df_a.columns)
        self.assertIn("Grain", df_a.columns)
        self.assertIn("NeedsAttention", df_a.columns)
        self.assertIn("ErrorBand", df_a.columns)
        self.assertIn("P90_monthly_error", df_a.columns)

    def test_multi_year_stamping(self):
        df_2025, _, _ = process_data(self.raw_annual, self.raw_monthly, year=2025)
        self.assertTrue((df_2025["Year"] == 2025).all())

        df_2026, _, _ = process_data(self.raw_annual, self.raw_monthly, year=2026)
        self.assertTrue((df_2026["Year"] == 2026).all())

    def test_monthly_date_parsing(self):
        _, df_m, _ = process_data(self.raw_annual, self.raw_monthly, year=2025)
        jan_row = df_m[df_m["year_month"] == "2025-01"].iloc[0]

        self.assertEqual(jan_row["Year"], 2025)
        self.assertEqual(jan_row["Month"], 1)
        self.assertEqual(jan_row["MonthName"], "January")
        self.assertEqual(jan_row["YearMonth"], "2025-01")

    def test_numeric_coercion_and_nan_handling(self):
        df_a, _, _ = process_data(self.raw_annual, self.raw_monthly, year=2025)
        dirty_row = df_a[df_a["BMU"] == "UNIT_DIRTY_1"].iloc[0]

        # String was coerced to 0.0
        self.assertEqual(dirty_row["installedCapacity_mwh"], 0.0)
        # NaN MELLevel coerced to 0.0
        self.assertEqual(dirty_row["MELLevel"], 0.0)

    def test_needs_attention_assignment(self):
        df_a, _, _ = process_data(self.raw_annual, self.raw_monthly, year=2025)
        wind_unit = df_a[df_a["BMU"] == "UNIT_WIND_1"].iloc[0]
        ccgt_unit = df_a[df_a["BMU"] == "UNIT_CCGT_1"].iloc[0]

        # Wind with NetError -6.25% (outside ±3%) -> NeedsAttention = True
        self.assertTrue(wind_unit["NeedsAttention"])
        # CCGT with NetError -0.44% (within ±1%) and ABS 0.44% (< 2.6%) -> NeedsAttention = False
        self.assertFalse(ccgt_unit["NeedsAttention"])


if __name__ == "__main__":
    unittest.main()
