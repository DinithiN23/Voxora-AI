"""
Voxora Backend — Dashboard Analytics Service.

Aggregates business KPIs, revenue trends, segment breakdowns,
and top products from BigQuery for the Executive Dashboards.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.integrations.bigquery.client import bigquery_client

logger = logging.getLogger(__name__)


class DashboardService:
    """Fetches and structures executive dashboard data from BigQuery."""

    async def get_executive_dashboard(self) -> dict[str, Any]:
        """
        Build the full executive dashboard payload with:
        - 5 KPI scorecards (Revenue, Profit, Orders, AOV, Margin)
        - Revenue trend line chart (monthly)
        - Revenue by region bar chart
        - Revenue by segment pie chart
        - Top 5 products bar chart
        """
        dataset = bigquery_client.full_dataset_path

        # Run all queries concurrently-ish (sequentially to keep it simple)
        kpis = await self._fetch_kpis(dataset)
        revenue_trend = await self._fetch_revenue_trend(dataset)
        revenue_by_region = await self._fetch_revenue_by_region(dataset)
        revenue_by_segment = await self._fetch_revenue_by_segment(dataset)
        top_products = await self._fetch_top_products(dataset)
        channel_performance = await self._fetch_channel_performance(dataset)

        now = datetime.now(timezone.utc).isoformat()

        return {
            "kpis": kpis,
            "charts": [
                revenue_trend,
                revenue_by_region,
                revenue_by_segment,
                top_products,
                channel_performance,
            ],
            "last_updated": now,
            "data_range": "All Time",
        }

    # ── KPI Scorecards ────────────────────────────────────────

    async def _fetch_kpis(self, dataset: str) -> list[dict[str, Any]]:
        """Fetch aggregate KPIs from orders table."""
        sql = f"""
        SELECT
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(SUM(profit), 2) AS total_profit,
            COUNT(*) AS total_orders,
            ROUND(AVG(total_amount), 2) AS avg_order_value,
            ROUND((SUM(profit) / NULLIF(SUM(total_amount), 0)) * 100, 2) AS profit_margin_pct,
            SUM(units) AS total_units
        FROM `{dataset}.orders`
        """
        try:
            result = await bigquery_client.execute_query(sql)
            row = result["rows"][0] if result["rows"] else {}

            revenue = row.get("total_revenue", 0)
            profit = row.get("total_profit", 0)
            orders = row.get("total_orders", 0)
            aov = row.get("avg_order_value", 0)
            margin = row.get("profit_margin_pct", 0)
            units = row.get("total_units", 0)

            return [
                {
                    "id": "kpi-revenue",
                    "label": "Total Revenue",
                    "value": revenue,
                    "formatted_value": self._format_currency(revenue),
                    "trend": "up",
                    "icon": "",
                    "color": "#10B981",
                },
                {
                    "id": "kpi-profit",
                    "label": "Gross Profit",
                    "value": profit,
                    "formatted_value": self._format_currency(profit),
                    "trend": "up",
                    "icon": "",
                    "color": "#059669",
                },
                {
                    "id": "kpi-orders",
                    "label": "Total Orders",
                    "value": orders,
                    "formatted_value": f"{orders:,}",
                    "trend": "up",
                    "icon": "",
                    "color": "#6366F1",
                },
                {
                    "id": "kpi-aov",
                    "label": "Avg. Order Value",
                    "value": aov,
                    "formatted_value": self._format_currency(aov),
                    "trend": "neutral",
                    "icon": "",
                    "color": "#0EA5E9",
                },
                {
                    "id": "kpi-margin",
                    "label": "Profit Margin",
                    "value": margin,
                    "formatted_value": f"{margin:.1f}%",
                    "trend": "up" if margin > 50 else "neutral",
                    "icon": "",
                    "color": "#10B981",
                },
            ]
        except Exception as e:
            logger.error(f"Failed to fetch KPIs: {e}")
            return []

    # ── Revenue Trend (Monthly) ───────────────────────────────

    async def _fetch_revenue_trend(self, dataset: str) -> dict[str, Any]:
        """Monthly revenue and profit trend."""
        sql = f"""
        SELECT
            FORMAT_DATE('%Y-%m', DATE(order_date)) AS month,
            ROUND(SUM(total_amount), 2) AS revenue,
            ROUND(SUM(profit), 2) AS profit
        FROM `{dataset}.orders`
        GROUP BY month
        ORDER BY month
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-revenue-trend",
                "title": "Monthly Revenue & Profit Trend",
                "chart_type": "area",
                "chart_config": {
                    "x_key": "month",
                    "y_keys": ["revenue", "profit"],
                    "x_label": "Month",
                    "y_label": "Amount (USD)",
                    "colors": ["#10B981", "#6366F1"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch revenue trend: {e}")
            return self._empty_chart("chart-revenue-trend", "Monthly Revenue Trend", "area")

    # ── Revenue by Region ─────────────────────────────────────

    async def _fetch_revenue_by_region(self, dataset: str) -> dict[str, Any]:
        """Revenue breakdown by region."""
        sql = f"""
        SELECT
            region,
            ROUND(SUM(total_amount), 2) AS revenue,
            COUNT(*) AS orders
        FROM `{dataset}.orders`
        GROUP BY region
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-revenue-region",
                "title": "Revenue by Region",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "region",
                    "y_keys": ["revenue"],
                    "x_label": "Region",
                    "y_label": "Revenue (USD)",
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch revenue by region: {e}")
            return self._empty_chart("chart-revenue-region", "Revenue by Region", "bar")

    # ── Revenue by Segment ────────────────────────────────────

    async def _fetch_revenue_by_segment(self, dataset: str) -> dict[str, Any]:
        """Revenue share by customer segment."""
        sql = f"""
        SELECT
            c.segment,
            ROUND(SUM(o.total_amount), 2) AS revenue
        FROM `{dataset}.orders` o
        JOIN `{dataset}.customers` c ON o.customer_id = c.id
        GROUP BY c.segment
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-revenue-segment",
                "title": "Revenue by Customer Segment",
                "chart_type": "pie",
                "chart_config": {
                    "name_key": "segment",
                    "value_key": "revenue",
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch revenue by segment: {e}")
            return self._empty_chart("chart-revenue-segment", "Revenue by Segment", "pie")

    # ── Top Products ──────────────────────────────────────────

    async def _fetch_top_products(self, dataset: str) -> dict[str, Any]:
        """Top 5 products by revenue."""
        sql = f"""
        SELECT
            p.name AS product,
            ROUND(SUM(o.total_amount), 2) AS revenue,
            SUM(o.units) AS units_sold
        FROM `{dataset}.orders` o
        JOIN `{dataset}.products` p ON o.product_id = p.id
        GROUP BY p.name
        ORDER BY revenue DESC
        LIMIT 5
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-top-products",
                "title": "Top 5 Products by Revenue",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "product",
                    "y_keys": ["revenue"],
                    "x_label": "Product",
                    "y_label": "Revenue (USD)",
                    "layout": "horizontal",
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch top products: {e}")
            return self._empty_chart("chart-top-products", "Top Products", "bar")

    # ── Channel Performance ───────────────────────────────────

    async def _fetch_channel_performance(self, dataset: str) -> dict[str, Any]:
        """Revenue by sales channel."""
        sql = f"""
        SELECT
            channel,
            ROUND(SUM(total_amount), 2) AS revenue,
            COUNT(*) AS orders,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM `{dataset}.orders`
        GROUP BY channel
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-channel-performance",
                "title": "Sales Channel Performance",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "channel",
                    "y_keys": ["revenue"],
                    "x_label": "Channel",
                    "y_label": "Revenue (USD)",
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch channel performance: {e}")
            return self._empty_chart("chart-channel-performance", "Channel Performance", "bar")

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _format_currency(value: float) -> str:
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:,.2f}M"
        if abs(value) >= 1_000:
            return f"${value / 1_000:,.1f}K"
        return f"${value:,.2f}"

    @staticmethod
    def _empty_chart(id: str, title: str, chart_type: str) -> dict[str, Any]:
        return {
            "id": id,
            "title": title,
            "chart_type": chart_type,
            "chart_config": {},
            "data_payload": {"rows": []},
        }


dashboard_service = DashboardService()
