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
            raw_project = (
                self.settings.bigquery_project
                or self.settings.google_cloud_project
                or os.environ.get("BIGQUERY_PROJECT")
                or os.environ.get("GOOGLE_CLOUD_PROJECT")
                or ""
            )
            project = raw_project.strip()
            if not project:
                raise ValueError("BIGQUERY_PROJECT is not configured in environment.")

            from app.integrations.gcp import get_gcp_credentials
            credentials = get_gcp_credentials()

            if credentials:
                self._client = bigquery.Client(project=project, credentials=credentials)
            else:
                self._client = bigquery.Client(project=project)

        return self._client

    @property
    def dataset_id(self) -> str:
        raw_ds = self.settings.bigquery_dataset or os.environ.get("BIGQUERY_DATASET") or "voxora_bigquery_sa"
        return raw_ds.strip()

    @property
    def full_dataset_path(self) -> str:
        raw_project = (
            self.settings.bigquery_project
            or self.settings.google_cloud_project
            or os.environ.get("BIGQUERY_PROJECT")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
            or ""
        )
        project = raw_project.strip()
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
