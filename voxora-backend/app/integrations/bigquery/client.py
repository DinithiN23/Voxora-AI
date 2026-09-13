"""
Voxora Backend — Google BigQuery Integration Client.

Executes analytical queries against Google Cloud BigQuery with safety,
timeout protection, and execution metrics.
"""

import asyncio
import logging
import os
import time
from typing import Any
from google.cloud import bigquery
from app.config import get_settings

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Async wrapper for Google Cloud BigQuery operations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: bigquery.Client | None = None

    def get_client(self) -> bigquery.Client:
        """Lazy initialize BigQuery client."""
        if self._client is None:
            project = self.settings.bigquery_project or self.settings.google_cloud_project
            if not project:
                raise ValueError("BIGQUERY_PROJECT is not configured in environment.")

            credentials = None
            
            # Check for JSON string environment variable first (Vercel serverless approach)
            gcp_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if gcp_json:
                import json
                from google.oauth2 import service_account
                try:
                    # Vercel sometimes double-escapes newlines in environment variables
                    if "\\n" in gcp_json and "\\\\n" not in gcp_json:
                        gcp_json = gcp_json.replace("\\n", "\n")
                    
                    cred_info = json.loads(gcp_json)
                    credentials = service_account.Credentials.from_service_account_info(cred_info)
                except Exception as e:
                    logger.error(f"Failed to parse GOOGLE_CREDENTIALS_JSON: {e}")

            # Fallback to local file path
            if not credentials:
                cred_path = self.settings.google_application_credentials
                if cred_path and os.path.exists(cred_path):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(cred_path)

            if credentials:
                self._client = bigquery.Client(project=project, credentials=credentials)
            else:
                # Default to environment/metadata server (will likely fail on Vercel)
                self._client = bigquery.Client(project=project)

        return self._client

    @property
    def dataset_id(self) -> str:
        return self.settings.bigquery_dataset or "voxora_bigquery_sa"

    @property
    def full_dataset_path(self) -> str:
        project = self.settings.bigquery_project or self.settings.google_cloud_project
        return f"{project}.{self.dataset_id}"

    async def execute_query(self, sql: str, timeout_seconds: float = 15.0) -> dict[str, Any]:
        """
        Execute SQL query on BigQuery asynchronously.

        Returns:
            dict with 'columns', 'rows', 'row_count', 'execution_time_ms', and 'bytes_billed'.
        """
        def _sync_execute() -> dict[str, Any]:
            client = self.get_client()
            start_time = time.perf_counter()

            max_bytes = self.settings.bigquery_max_bytes_billed or (100 * 1024 * 1024)
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                maximum_bytes_billed=max_bytes,  # Cap query scan bytes to prevent runaway billing
            )
            query_job = client.query(sql, job_config=job_config, timeout=timeout_seconds)
            results = query_job.result()

            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

            columns = [field.name for field in results.schema]
            rows: list[dict[str, Any]] = []

            for row in results:
                row_dict: dict[str, Any] = {}
                for col in columns:
                    val = row[col]
                    # Format dates and decimals into JSON serializable types
                    if hasattr(val, "isoformat"):
                        row_dict[col] = val.isoformat()
                    else:
                        row_dict[col] = val
                rows.append(row_dict)

            bytes_billed = query_job.total_bytes_billed or 0

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time_ms,
                "bytes_billed": bytes_billed,
                "job_id": query_job.job_id,
            }

        return await asyncio.to_thread(_sync_execute)


bigquery_client = BigQueryClient()
