import unittest
from tests import get_app_module

app = get_app_module()
categorize_error = app.categorize_error
get_reason = app.get_reason


class TestBusinessRules(unittest.TestCase):
    """Guards operational thresholds, error banding, and violation tagging."""

    # --- Error Band Categorization ---
    def test_error_band_0_to_1(self):
        self.assertEqual(categorize_error(0.0), "0-1%")
        self.assertEqual(categorize_error(0.5), "0-1%")
        self.assertEqual(categorize_error(1.0), "0-1%")

    def test_error_band_1_to_2(self):
        self.assertEqual(categorize_error(1.0001), "1-2%")
        self.assertEqual(categorize_error(1.5), "1-2%")
        self.assertEqual(categorize_error(2.0), "1-2%")

    def test_error_band_2_to_4(self):
        self.assertEqual(categorize_error(2.0001), "2-4%")
        self.assertEqual(categorize_error(3.0), "2-4%")
        self.assertEqual(categorize_error(4.0), "2-4%")

    def test_error_band_4_to_10(self):
        self.assertEqual(categorize_error(4.0001), "4-10%")
        self.assertEqual(categorize_error(7.5), "4-10%")
        self.assertEqual(categorize_error(10.0), "4-10%")

    def test_error_band_above_10(self):
        self.assertEqual(categorize_error(10.0001), ">10%")
        self.assertEqual(categorize_error(25.0), ">10%")
        self.assertEqual(categorize_error(100.0), ">10%")

    # --- Wind & Solar Thresholds (±3% Net, >= 9.4% ABS) ---
    def test_wind_within_tolerances(self):
        row = {"Fuel": "WIND", "A_NetError%": 3.0, "A_ABS_NetError%": 9.39}
        self.assertEqual(get_reason(row), "Within Tolerances")

        row_neg = {"Fuel": "Solar", "A_NetError%": -3.0, "A_ABS_NetError%": 0.0}
        self.assertEqual(get_reason(row_neg), "Within Tolerances")

    def test_wind_net_error_breach(self):
        row_pos = {"Fuel": "WIND", "A_NetError%": 3.01, "A_ABS_NetError%": 5.0}
        self.assertIn("Net Error +3.01% (outside ±3%)", get_reason(row_pos))

        row_neg = {"Fuel": "SOLAR", "A_NetError%": -3.05, "A_ABS_NetError%": 5.0}
        self.assertIn("Net Error -3.05% (outside ±3%)", get_reason(row_neg))

    def test_wind_abs_error_breach(self):
        row = {"Fuel": "Wind", "A_NetError%": 0.0, "A_ABS_NetError%": 9.40}
        self.assertIn("ABS Error 9.40% (≥ 9.4%)", get_reason(row))

    def test_wind_dual_breach(self):
        row = {"Fuel": "WIND", "A_NetError%": -5.20, "A_ABS_NetError%": 12.50}
        reason = get_reason(row)
        self.assertIn("Net Error -5.20% (outside ±3%)", reason)
        self.assertIn("ABS Error 12.50% (≥ 9.4%)", reason)
        self.assertIn("; ", reason)

    # --- Other Fuels Thresholds (±1% Net, >= 2.6% ABS) ---
    def test_other_fuels_within_tolerances(self):
        for fuel in ["CCGT", "NUCLEAR", "BIOMASS", "HYDRO", "STORAGE", "OTHER"]:
            row = {"Fuel": fuel, "A_NetError%": 1.0, "A_ABS_NetError%": 2.59}
            self.assertEqual(get_reason(row), "Within Tolerances", f"Failed for fuel {fuel}")

            row_neg = {"Fuel": fuel.lower(), "A_NetError%": -1.0, "A_ABS_NetError%": 1.0}
            self.assertEqual(get_reason(row_neg), "Within Tolerances", f"Failed for fuel {fuel.lower()}")

    def test_other_fuels_net_error_breach(self):
        row = {"Fuel": "CCGT", "A_NetError%": 1.01, "A_ABS_NetError%": 1.5}
        self.assertIn("Net Error +1.01% (outside ±1%)", get_reason(row))

        row_neg = {"Fuel": "Nuclear", "A_NetError%": -1.25, "A_ABS_NetError%": 1.5}
        self.assertIn("Net Error -1.25% (outside ±1%)", get_reason(row_neg))

    def test_other_fuels_abs_error_breach(self):
        row = {"Fuel": "BIOMASS", "A_NetError%": 0.5, "A_ABS_NetError%": 2.60}
        self.assertIn("ABS Error 2.60% (≥ 2.6%)", get_reason(row))

    def test_other_fuels_dual_breach(self):
        row = {"Fuel": "CCGT", "A_NetError%": -2.0, "A_ABS_NetError%": 3.0}
        reason = get_reason(row)
        self.assertIn("Net Error -2.00% (outside ±1%)", reason)
        self.assertIn("ABS Error 3.00% (≥ 2.6%)", reason)


if __name__ == "__main__":
    unittest.main()
