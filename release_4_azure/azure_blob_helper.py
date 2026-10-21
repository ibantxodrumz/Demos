import pandas as pd
from io import BytesIO

try:
    from azure.storage.blob import BlobServiceClient
    from azure.identity import AzureCliCredential
    AZURE_PACKAGES_AVAILABLE = True
except ImportError:
    AZURE_PACKAGES_AVAILABLE = False
    BlobServiceClient = None
    AzureCliCredential = None


class AzureBlobStorage:
    def __init__(self, account_url, container_name, project_name):
        self.account_url = account_url
        self.container_name = container_name
        self.project_name = project_name
        self._container_client = None

    @property
    def container_client(self):
        if self._container_client is not None:
            return self._container_client

        if not AZURE_PACKAGES_AVAILABLE or AzureCliCredential is None:
            raise RuntimeError(
                "Azure SDK packages ('azure-storage-blob' and 'azure-identity') are not installed in this Python environment."
            )

        credential = AzureCliCredential()
        self._container_client = BlobServiceClient(
            self.account_url, credential=credential
        ).get_container_client(self.container_name)
        return self._container_client

    @container_client.setter
    def container_client(self, client):
        self._container_client = client

    def _read_csv(self, blob_path: str) -> pd.DataFrame:
        blob_client = self.container_client.get_blob_client(blob_path)
        data = blob_client.download_blob().readall()
        return pd.read_csv(BytesIO(data))

    def _resolve_path(self, prefix: str, year=None) -> str:
        if year is not None:
            y = str(year)
            parts = self.project_name.rsplit("-", 1)
            if len(parts) == 2 and parts[1].isdigit():
                base = parts[0]
            else:
                base = self.project_name
            folder = f"{base}-{y}"
        else:
            folder = self.project_name
            y = folder.split("-")[-1] if ("-" in folder and folder.split("-")[-1].isdigit()) else "2025"
        return f"{folder}/internal/{prefix}_{y}.csv"

    def read_annual_summary(self, year=None) -> pd.DataFrame:
        return self._read_csv(self._resolve_path("annual_summary", year))

    def read_monthly_summary(self, year=None) -> pd.DataFrame:
        return self._read_csv(self._resolve_path("monthly_summary", year))
