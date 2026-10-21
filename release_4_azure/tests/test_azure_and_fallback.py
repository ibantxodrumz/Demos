import os
import unittest
from tests import get_app_module, APP_DIR
import sys
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
import constants
from azure_blob_helper import AzureBlobStorage

app = get_app_module()
find_local_input_file = app.find_local_input_file


class TestAzureAndFallback(unittest.TestCase):
    """Guards Azure blob storage paths, configuration constants, and local fallback file resolution."""

    def test_constants_configuration(self):
        self.assertTrue(constants.ACCOUNT_URL.startswith("https://"))
        self.assertIn("blob.core.windows.net", constants.ACCOUNT_URL)
        self.assertEqual(constants.CONTAINER_NAME, "datalake")
        self.assertEqual(constants.PROJECT_BASE_NAME, "pn-accuracy")
        self.assertIn(2025, constants.AVAILABLE_YEARS)
        self.assertIn(2026, constants.AVAILABLE_YEARS)
        self.assertIn(constants.DEFAULT_YEAR, constants.AVAILABLE_YEARS)

    def test_azure_multi_year_blob_paths(self):
        storage = AzureBlobStorage(
            account_url=constants.ACCOUNT_URL,
            container_name=constants.CONTAINER_NAME,
            project_name=constants.PROJECT_BASE_NAME,
        )

        recorded_paths = []
        storage._read_csv = lambda path: recorded_paths.append(path)

        storage.read_annual_summary(2025)
        storage.read_monthly_summary(2025)
        storage.read_annual_summary(2026)
        storage.read_monthly_summary(2026)

        expected = [
            "pn-accuracy-2025/internal/annual_summary_2025.csv",
            "pn-accuracy-2025/internal/monthly_summary_2025.csv",
            "pn-accuracy-2026/internal/annual_summary_2026.csv",
            "pn-accuracy-2026/internal/monthly_summary_2026.csv",
        ]
        self.assertEqual(recorded_paths, expected)

    def test_azure_backward_compatibility_folder_name(self):
        # Even if legacy code passes 'pn-accuracy-2025' as project_name
        storage = AzureBlobStorage(
            account_url=constants.ACCOUNT_URL,
            container_name=constants.CONTAINER_NAME,
            project_name="pn-accuracy-2025",
        )

        recorded_paths = []
        storage._read_csv = lambda path: recorded_paths.append(path)

        storage.read_annual_summary(2025)
        self.assertEqual(recorded_paths, ["pn-accuracy-2025/internal/annual_summary_2025.csv"])

    def test_azure_direct_year_project_name_read(self):
        storage_2025 = AzureBlobStorage(
            account_url=constants.ACCOUNT_URL,
            container_name=constants.CONTAINER_NAME,
            project_name="pn-accuracy-2025",
        )
        paths_2025 = []
        storage_2025._read_csv = lambda path: paths_2025.append(path)
        storage_2025.read_annual_summary()
        storage_2025.read_monthly_summary()
        self.assertEqual(
            paths_2025,
            [
                "pn-accuracy-2025/internal/annual_summary_2025.csv",
                "pn-accuracy-2025/internal/monthly_summary_2025.csv",
            ],
        )

        storage_2026 = AzureBlobStorage(
            account_url=constants.ACCOUNT_URL,
            container_name=constants.CONTAINER_NAME,
            project_name="pn-accuracy-2026",
        )
        paths_2026 = []
        storage_2026._read_csv = lambda path: paths_2026.append(path)
        storage_2026.read_annual_summary()
        storage_2026.read_monthly_summary()
        self.assertEqual(
            paths_2026,
            [
                "pn-accuracy-2026/internal/annual_summary_2026.csv",
                "pn-accuracy-2026/internal/monthly_summary_2026.csv",
            ],
        )

    def test_find_local_input_files_exist(self):
        annual_path = find_local_input_file("annual_summary_2025.csv")
        self.assertIsNotNone(annual_path)
        self.assertTrue(os.path.exists(annual_path))

        monthly_path = find_local_input_file("monthly_summary_2025.csv")
        self.assertIsNotNone(monthly_path)
        self.assertTrue(os.path.exists(monthly_path))

    def test_find_local_input_file_missing_returns_none(self):
        missing_path = find_local_input_file("non_existent_data_file_9999.csv")
        self.assertIsNone(missing_path)


if __name__ == "__main__":
    unittest.main()
