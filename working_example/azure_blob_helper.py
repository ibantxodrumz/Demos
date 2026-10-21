import pandas as pd
from io import BytesIO

from azure.storage.blob import BlobServiceClient
from azure.identity import AzureCliCredential


class AzureBlobStorage:
    def __init__(self, account_url, container_name, project_name):
        credential = AzureCliCredential()
        self.container_client = BlobServiceClient(
            account_url, credential=credential
        ).get_container_client(container_name)

        self.project_name = project_name

    def _read_csv(self, blob_path: str) -> pd.DataFrame:
        blob_client = self.container_client.get_blob_client(blob_path)
        data = blob_client.download_blob().readall()
        return pd.read_csv(BytesIO(data))

    def read_annual_summary(self) -> pd.DataFrame:
        return self._read_csv(f"{self.project_name}/internal/annual_summary_2025.csv")

    def read_monthly_summary(self) -> pd.DataFrame:
        return self._read_csv(f"{self.project_name}/internal/monthly_summary_2025.csv")
