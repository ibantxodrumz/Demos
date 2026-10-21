import unittest
import pandas as pd
from tests import get_app_module

app = get_app_module()
process_data = app.process_data
find_local_input_file = app.find_local_input_file


class TestBaselineInvariants(unittest.TestCase):
    """Guards against regressions in canonical 2025 baseline data contracts and fleet metrics."""

    @classmethod
    def setUpClass(cls):
        annual_path = find_local_input_file("annual_summary_2025.csv")
        monthly_path = find_local_input_file("monthly_summary_2025.csv")

        cls.raw_annual = pd.read_csv(annual_path)
        cls.raw_monthly = pd.read_csv(monthly_path)

        cls.df_annual, cls.df_monthly, cls.err = process_data(
            cls.raw_annual, cls.raw_monthly, year=2025
        )

    def test_pipeline_executed_without_error(self):
        self.assertIsNone(self.err, f"Pipeline failed with error: {self.err}")
        self.assertIsNotNone(self.df_annual)
        self.assertIsNotNone(self.df_monthly)

    def test_annual_fleet_count_invariant(self):
        # Baseline fleet contract: exactly 1,449 BMUs evaluated
        self.assertEqual(len(self.df_annual), 1449)
        self.assertEqual(self.df_annual["BMU"].nunique(), 1449)

    def test_monthly_record_count_invariant(self):
        # Baseline monthly contract: exactly 14,237 records
        self.assertEqual(len(self.df_monthly), 14237)

    def test_monthly_date_coverage_invariant(self):
        # All 12 calendar months in 2025 must be present
        distinct_months = set(self.df_monthly["Month"].unique())
        self.assertEqual(distinct_months, set(range(1, 13)))

    def test_flagged_attention_count_invariant(self):
        # Operational business rule contract: exactly 559 BMUs flagged under active rules
        flagged_units = self.df_annual[self.df_annual["NeedsAttention"] == True]
        self.assertEqual(
            len(flagged_units),
            559,
            f"Flagged BMU count regressed: expected 559, got {len(flagged_units)}",
        )

    def test_data_integrity_sanity_checks(self):
        # Zero negative capacities
        self.assertTrue((self.df_annual["installedCapacity_mwh"] >= 0).all())
        # Zero null or empty BMU identifiers
        self.assertFalse(self.df_annual["BMU"].isna().any())
        self.assertFalse((self.df_annual["BMU"] == "").any())
        self.assertFalse(self.df_monthly["BMU"].isna().any())
        # All fuels populated
        self.assertFalse(self.df_annual["Fuel"].isna().any())

    def test_error_band_categories_populated(self):
        expected_bands = {"0-1%", "1-2%", "2-4%", "4-10%", ">10%"}
        present_bands = set(self.df_annual["ErrorBand"].unique())
        self.assertEqual(expected_bands, present_bands)


if __name__ == "__main__":
    unittest.main()
