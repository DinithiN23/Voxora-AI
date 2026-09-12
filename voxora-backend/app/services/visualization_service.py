"""
Voxora Backend — Visualization Recommender & Payload Generator.

Inspects SQL query result schemas and automatically selects the optimal visualization
(bar, line, pie, kpi, or table) with Recharts-ready configurations.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

DATE_KEYWORDS = {"date", "order_date", "day", "month", "year", "week", "quarter", "created_at"}


class VisualizationService:
    """Recommends and structures charts for analytical query results."""

    def recommend_visualization(
        self,
        question: str,
        sql: str,
        query_result: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Analyze columns and row data to build a chart config.
        Returns a dict conforming to Visualization schema or None if no chart needed.
        """
        columns: list[str] = query_result.get("columns", [])
        rows: list[dict[str, Any]] = query_result.get("rows", [])
        row_count: int = query_result.get("row_count", 0)

        # 0. Zero-row results
        if not rows or not columns or row_count == 0:
            return None

        # 1. Single row with 1-2 aggregate numbers (or single-point time series) -> KPI card
        if row_count == 1:
            # We handle single-point time series by falling back to a KPI card for the primary metric.
            first_row = rows[0]
            numeric_cols = [c for c in columns if isinstance(first_row.get(c), (int, float))]
            if numeric_cols:
                primary_col = numeric_cols[0]
                secondary_col = numeric_cols[1] if len(numeric_cols) > 1 else None

                return {
                    "chart_type": "kpi",
                    "title": self._format_title(primary_col),
                    "chart_config": {
                        "primary_key": primary_col,
                        "secondary_key": secondary_col,
                        "primary_label": self._format_title(primary_col),
                        "secondary_label": self._format_title(secondary_col) if secondary_col else None,
                    },
                    "data_payload": {
                        "row": first_row,
                    },
                }

        # Identify date/time columns and numeric columns
        first_row = rows[0]
        date_col = next((c for c in columns if c.lower() in DATE_KEYWORDS or "date" in c.lower()), None)
        numeric_cols = [c for c in columns if isinstance(first_row.get(c), (int, float))]
        text_cols = [c for c in columns if c not in numeric_cols and c != date_col]

        # 2. Multi-dimensional group-bys -> Table
        if len(text_cols) >= 2 and len(columns) >= 3:
            return {
                "chart_type": "table",
                "title": "Multi-dimensional Breakdown",
                "chart_config": {
                    "columns": columns,
                    "column_labels": {c: self._format_title(c) for c in columns},
                },
                "data_payload": {"rows": rows},
            }

        # 3. Time Series -> Line Chart
        if date_col and numeric_cols and row_count > 1:
            return {
                "chart_type": "line",
                "title": f"{self._format_title(numeric_cols[0])} Trend Over Time",
                "chart_config": {
                    "x_key": date_col,
                    "y_keys": numeric_cols[:2],
                    "x_label": self._format_title(date_col),
                    "y_label": self._format_title(numeric_cols[0]),
                },
                "data_payload": {"rows": rows},
            }

        # 4. Categorical breakdown -> Bar or Pie Chart
        category_col = text_cols[0] if text_cols else None
        if category_col and numeric_cols:
            metric_col = numeric_cols[0]

            # Pie Chart if <= 5 categories and user asked for share, breakdown, or distribution
            q_lower = question.lower()
            if row_count <= 6 and any(k in q_lower for k in ("share", "percent", "proportion", "distribution", "pie")):
                return {
                    "chart_type": "pie",
                    "title": f"{self._format_title(metric_col)} by {self._format_title(category_col)}",
                    "chart_config": {
                        "name_key": category_col,
                        "value_key": metric_col,
                    },
                    "data_payload": {"rows": rows},
                }

            # Otherwise Bar Chart (standard executive comparison)
            return {
                "chart_type": "bar",
                "title": f"{self._format_title(metric_col)} by {self._format_title(category_col)}",
                "chart_config": {
                    "x_key": category_col,
                    "y_keys": [metric_col],
                    "x_label": self._format_title(category_col),
                    "y_label": self._format_title(metric_col),
                },
                "data_payload": {"rows": rows},
            }

        # 5. Multi-column detailed table (Fallback)
        if len(columns) > 0:
            return {
                "chart_type": "table",
                "title": "Query Results Data Table",
                "chart_config": {
                    "columns": columns,
                    "column_labels": {c: self._format_title(c) for c in columns},
                },
                "data_payload": {"rows": rows},
            }

        return None

    def _format_title(self, key: str | None) -> str:
        if not key:
            return ""
        return key.replace("_", " ").title()


visualization_service = VisualizationService()
