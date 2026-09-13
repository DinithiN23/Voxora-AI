"""
Voxora Backend — Multi-Dashboard Analytics Service.

Provides three specialized executive dashboards powered by Google BigQuery:
1. Executive Overview — High-level corporate health, total revenue, profit margins, macro trajectory.
2. Sales & Regional Performance — Territory breakdown, channel attribution, quota attainment, units sold.
3. Customer Intelligence & LTV — Tier segmentation (Enterprise vs Mid vs SMB), retention, top accounts, CLV.

Supports:
- Dynamic time ranges: "2y" (default 24 months), "1y", "90d", "30d", "2024", "2025", "2026", "all"
- Custom date ranges: start_date and end_date (YYYY-MM-DD)
- Granularity: "daily", "monthly", "yearly"
"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.integrations.bigquery.client import bigquery_client

logger = logging.getLogger(__name__)


class DashboardService:
    """Fetches and structures business intelligence dashboards from BigQuery."""

    # ══════════════════════════════════════════════════════════════
    # 1. Executive Overview Dashboard
    # ══════════════════════════════════════════════════════════════

    async def get_executive_dashboard(
        self,
        time_range: str = "2y",
        start_date: str | None = None,
        end_date: str | None = None,
        granularity: str = "monthly",
    ) -> dict[str, Any]:
        """
        Build the Executive Overview dashboard payload:
        - 5 Macro KPI scorecards (Revenue, Profit, Orders, AOV, Margin)
        - Revenue & Profit Trajectory (area chart based on granularity)
        - Revenue by Territory (bar chart)
        - Revenue by Customer Segment (pie chart)
        - Top 5 Products by Revenue (horizontal bar chart)
        - Sales Channel Performance (bar chart)
        """
        dataset = bigquery_client.full_dataset_path
        date_where = self._get_date_where(time_range, start_date, end_date)
        range_label = self._get_range_label(time_range, start_date, end_date)

        kpis = await self._fetch_executive_kpis(dataset, date_where)
        for kpi in kpis:
            kpi["period_label"] = range_label
            
        revenue_trend = await self._fetch_trend(
            dataset,
            date_where,
            "Revenue & Gross Profit Trajectory",
            granularity,
            start_date=start_date,
            end_date=end_date,
        )
        revenue_by_region = await self._fetch_revenue_by_region(dataset, date_where)
        revenue_by_segment = await self._fetch_revenue_by_segment(dataset, date_where)
        top_products = await self._fetch_top_products(dataset, date_where)
        channel_performance = await self._fetch_channel_performance(dataset, date_where)

        return {
            "kpis": kpis,
            "charts": [
                revenue_trend,
                revenue_by_region,
                revenue_by_segment,
                top_products,
                channel_performance,
            ],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "data_range": range_label,
        }

    # ══════════════════════════════════════════════════════════════
    # 2. Sales & Regional Performance Dashboard
    # ══════════════════════════════════════════════════════════════

    async def get_sales_dashboard(
        self,
        time_range: str = "2y",
        start_date: str | None = None,
        end_date: str | None = None,
        granularity: str = "monthly",
    ) -> dict[str, Any]:
        """
        Build the Sales & Regional Performance dashboard payload:
        - 5 Regional & Channel scorecards (Regional Rev, Top Region, Units Sold, Avg Deal, Leading Channel)
        - Territory Revenue & Profit Comparison (grouped bar chart)
        - Territory Revenue Trajectory (area chart based on granularity)
        - Channel Revenue Attribution (pie/donut chart)
        - Product Category Performance by Units (bar chart)
        - Channel Average Deal Size (horizontal bar chart)
        """
        dataset = bigquery_client.full_dataset_path
        date_where = self._get_date_where(time_range, start_date, end_date)
        range_label = self._get_range_label(time_range, start_date, end_date)

        kpis = await self._fetch_sales_kpis(dataset, date_where)
        for kpi in kpis:
            kpi["period_label"] = range_label
            
        region_comparison = await self._fetch_region_comparison(dataset, date_where)
        monthly_sales_trend = await self._fetch_sales_trend(
            dataset, date_where, granularity, start_date=start_date, end_date=end_date
        )
        channel_share = await self._fetch_channel_share(dataset, date_where)
        product_category_sales = await self._fetch_product_category_sales(dataset, date_where)
        channel_deal_size = await self._fetch_channel_deal_size(dataset, date_where)

        return {
            "kpis": kpis,
            "charts": [
                region_comparison,
                monthly_sales_trend,
                channel_share,
                product_category_sales,
                channel_deal_size,
            ],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "data_range": range_label,
        }

    # ══════════════════════════════════════════════════════════════
    # 3. Customer Intelligence & Lifetime Value (LTV) Dashboard
    # ══════════════════════════════════════════════════════════════

    async def get_customer_dashboard(
        self,
        time_range: str = "2y",
        start_date: str | None = None,
        end_date: str | None = None,
        granularity: str = "monthly",
    ) -> dict[str, Any]:
        """
        Build the Customer Intelligence & LTV dashboard payload:
        - 5 Account scorecards (Total Accounts, Enterprise Share %, Avg LTV, Repeat Rate %, Top Account Spend)
        - Customer Tier Revenue Share (pie/donut chart)
        - Active Accounts & Spend Trajectory (area chart based on granularity)
        - Top 10 High-Value Enterprise Accounts (horizontal bar chart)
        - Average Order Value by Customer Tier (bar chart)
        - Customer Territory Distribution (bar chart)
        """
        dataset = bigquery_client.full_dataset_path
        date_where = self._get_date_where(time_range, start_date, end_date)
        range_label = self._get_range_label(time_range, start_date, end_date)

        kpis = await self._fetch_customer_kpis(dataset, date_where)
        for kpi in kpis:
            kpi["period_label"] = range_label

        tier_share = await self._fetch_revenue_by_segment(dataset, date_where, title="Revenue Share by Customer Tier")
        monthly_customers = await self._fetch_customer_trend(
            dataset, date_where, granularity, start_date=start_date, end_date=end_date
        )
        top_accounts = await self._fetch_top_enterprise_accounts(dataset, date_where)
        aov_by_tier = await self._fetch_aov_by_tier(dataset, date_where)
        customer_territory = await self._fetch_customer_territory_dist(dataset)

        return {
            "kpis": kpis,
            "charts": [
                tier_share,
                monthly_customers,
                top_accounts,
                aov_by_tier,
                customer_territory,
            ],
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "data_range": range_label,
        }

    # ══════════════════════════════════════════════════════════════
    # KPI Fetchers
    # ══════════════════════════════════════════════════════════════

    async def _fetch_executive_kpis(self, dataset: str, date_where: str) -> list[dict[str, Any]]:
        sql = f"""
        SELECT
            ROUND(SUM(total_amount), 2) AS total_revenue,
            ROUND(SUM(profit), 2) AS total_profit,
            COUNT(*) AS total_orders,
            ROUND(AVG(total_amount), 2) AS avg_order_value,
            ROUND((SUM(profit) / NULLIF(SUM(total_amount), 0)) * 100, 2) AS profit_margin_pct
        FROM `{dataset}.orders`
        {date_where}
        """
        try:
            result = await bigquery_client.execute_query(sql)
            row = result["rows"][0] if result.get("rows") else {}

            revenue = float(row.get("total_revenue") or 0)
            profit = float(row.get("total_profit") or 0)
            orders = int(row.get("total_orders") or 0)
            aov = float(row.get("avg_order_value") or 0)
            margin = float(row.get("profit_margin_pct") or 0)

            return [
                {
                    "id": "kpi-revenue",
                    "label": "Total Revenue",
                    "value": revenue,
                    "formatted_value": self._format_currency(revenue),
                    "trend": "up" if revenue > 0 else "neutral",
                    "color": "#10B981",
                },
                {
                    "id": "kpi-profit",
                    "label": "Gross Profit",
                    "value": profit,
                    "formatted_value": self._format_currency(profit),
                    "trend": "up" if profit > 0 else "neutral",
                    "color": "#059669",
                },
                {
                    "id": "kpi-orders",
                    "label": "Total Orders",
                    "value": orders,
                    "formatted_value": f"{orders:,}",
                    "trend": "up" if orders > 0 else "neutral",
                    "color": "#6366F1",
                },
                {
                    "id": "kpi-aov",
                    "label": "Avg. Order Value",
                    "value": aov,
                    "formatted_value": self._format_currency(aov),
                    "trend": "neutral",
                    "color": "#0EA5E9",
                },
                {
                    "id": "kpi-margin",
                    "label": "Profit Margin",
                    "value": margin,
                    "formatted_value": f"{margin:.1f}%",
                    "trend": "up" if margin > 50 else "neutral",
                    "color": "#10B981",
                },
            ]
        except Exception as e:
            logger.error(f"Failed to fetch executive KPIs: {e}")
            return [{"id": "error", "label": "Data Unavailable", "value": 0, "formatted_value": "Err", "status": "error", "error_message": str(e)}]

    async def _fetch_sales_kpis(self, dataset: str, date_where: str) -> list[dict[str, Any]]:
        sql_totals = f"""
        SELECT
            ROUND(SUM(total_amount), 2) AS total_revenue,
            SUM(units) AS total_units,
            COUNT(*) AS total_orders,
            ROUND(AVG(total_amount), 2) AS avg_deal_size
        FROM `{dataset}.orders`
        {date_where}
        """
        sql_top_region = f"""
        SELECT region, ROUND(SUM(total_amount), 2) AS rev
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY region
        ORDER BY rev DESC
        LIMIT 1
        """
        sql_top_channel = f"""
        SELECT channel, ROUND(SUM(total_amount), 2) AS rev
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY channel
        ORDER BY rev DESC
        LIMIT 1
        """
        try:
            totals_res = await bigquery_client.execute_query(sql_totals)
            totals_row = totals_res["rows"][0] if totals_res.get("rows") else {}

            top_reg_res = await bigquery_client.execute_query(sql_top_region)
            top_reg_row = top_reg_res["rows"][0] if top_reg_res.get("rows") else {}

            top_chan_res = await bigquery_client.execute_query(sql_top_channel)
            top_chan_row = top_chan_res["rows"][0] if top_chan_res.get("rows") else {}

            revenue = float(totals_row.get("total_revenue") or 0)
            units = int(totals_row.get("total_units") or 0)
            avg_deal = float(totals_row.get("avg_deal_size") or 0)

            top_region_name = top_reg_row.get("region", "—")
            top_region_rev = float(top_reg_row.get("rev") or 0)

            top_channel_name = top_chan_row.get("channel", "—")
            top_channel_rev = float(top_chan_row.get("rev") or 0)
            chan_pct = (top_channel_rev / revenue * 100.0) if revenue > 0 else 0.0

            return [
                {
                    "id": "kpi-sales-revenue",
                    "label": "Regional Sales Revenue",
                    "value": revenue,
                    "formatted_value": self._format_currency(revenue),
                    "trend": "up" if revenue > 0 else "neutral",
                    "color": "#10B981",
                },
                {
                    "id": "kpi-sales-top-region",
                    "label": f"Top Territory ({top_region_name})",
                    "value": top_region_rev,
                    "formatted_value": self._format_currency(top_region_rev),
                    "trend": "up" if top_region_rev > 0 else "neutral",
                    "color": "#6366F1",
                },
                {
                    "id": "kpi-sales-units",
                    "label": "Total Units Delivered",
                    "value": units,
                    "formatted_value": f"{units:,}",
                    "trend": "up" if units > 0 else "neutral",
                    "color": "#0EA5E9",
                },
                {
                    "id": "kpi-sales-aov",
                    "label": "Average Deal Size",
                    "value": avg_deal,
                    "formatted_value": self._format_currency(avg_deal),
                    "trend": "neutral",
                    "color": "#F59E0B",
                },
                {
                    "id": "kpi-sales-channel",
                    "label": f"Leading Channel ({top_channel_name})",
                    "value": round(chan_pct, 1),
                    "formatted_value": f"{chan_pct:.1f}%",
                    "trend": "up" if chan_pct > 0 else "neutral",
                    "color": "#10B981",
                },
            ]
        except Exception as e:
            logger.error(f"Failed to fetch sales KPIs: {e}")
            return [{"id": "error", "label": "Data Unavailable", "value": 0, "formatted_value": "Err", "status": "error", "error_message": str(e)}]

    async def _fetch_customer_kpis(self, dataset: str, date_where: str) -> list[dict[str, Any]]:
        sql = f"""
        WITH customer_stats AS (
            SELECT
                o.customer_id,
                c.segment,
                c.name,
                COUNT(*) AS order_count,
                SUM(o.total_amount) AS total_spend
            FROM `{dataset}.orders` o
            JOIN `{dataset}.customers` c ON o.customer_id = c.id
            {self._join_date_where(date_where, "o")}
            GROUP BY o.customer_id, c.segment, c.name
        )
        SELECT
            COUNT(DISTINCT customer_id) AS active_accounts,
            ROUND(SUM(total_spend), 2) AS total_revenue,
            ROUND(AVG(total_spend), 2) AS avg_clv,
            ROUND(COUNTIF(order_count > 1) / NULLIF(COUNT(*), 0) * 100, 2) AS repeat_rate_pct,
            ROUND(SUM(CASE WHEN segment = 'Enterprise' THEN total_spend ELSE 0 END) / NULLIF(SUM(total_spend), 0) * 100, 2) AS ent_share_pct
        FROM customer_stats
        """
        sql_top_account = f"""
        SELECT
            c.name,
            ROUND(SUM(o.total_amount), 2) AS total_spend
        FROM `{dataset}.orders` o
        JOIN `{dataset}.customers` c ON o.customer_id = c.id
        {self._join_date_where(date_where, "o")}
        GROUP BY c.name
        ORDER BY total_spend DESC
        LIMIT 1
        """
        try:
            res = await bigquery_client.execute_query(sql)
            row = res["rows"][0] if res.get("rows") else {}

            top_acc_res = await bigquery_client.execute_query(sql_top_account)
            top_acc_row = top_acc_res["rows"][0] if top_acc_res.get("rows") else {}

            active_accounts = int(row.get("active_accounts") or 0)
            avg_clv = float(row.get("avg_clv") or 0)
            repeat_rate = float(row.get("repeat_rate_pct") or 0)
            ent_share = float(row.get("ent_share_pct") or 0)

            top_acc_name = top_acc_row.get("name", "—")
            top_acc_spend = float(top_acc_row.get("total_spend") or 0)

            return [
                {
                    "id": "kpi-cust-total",
                    "label": "Active Customer Accounts",
                    "value": active_accounts,
                    "formatted_value": f"{active_accounts:,}",
                    "trend": "up" if active_accounts > 0 else "neutral",
                    "color": "#10B981",
                },
                {
                    "id": "kpi-cust-ent-share",
                    "label": "Enterprise Revenue Share",
                    "value": ent_share,
                    "formatted_value": f"{ent_share:.1f}%",
                    "trend": "up" if ent_share > 0 else "neutral",
                    "color": "#6366F1",
                },
                {
                    "id": "kpi-cust-clv",
                    "label": "Avg. Customer Lifetime Spend",
                    "value": avg_clv,
                    "formatted_value": self._format_currency(avg_clv),
                    "trend": "up" if avg_clv > 0 else "neutral",
                    "color": "#0EA5E9",
                },
                {
                    "id": "kpi-cust-repeat",
                    "label": "Multi-Order Retention Rate",
                    "value": repeat_rate,
                    "formatted_value": f"{repeat_rate:.1f}%",
                    "trend": "up" if repeat_rate > 0 else "neutral",
                    "color": "#10B981",
                },
                {
                    "id": "kpi-cust-top-spend",
                    "label": f"Top Account ({top_acc_name[:14]}..)" if top_acc_name != "—" else "Top Account",
                    "value": top_acc_spend,
                    "formatted_value": self._format_currency(top_acc_spend),
                    "trend": "up" if top_acc_spend > 0 else "neutral",
                    "color": "#F59E0B",
                },
            ]
        except Exception as e:
            logger.error(f"Failed to fetch customer KPIs: {e}")
            return [{"id": "error", "label": "Data Unavailable", "value": 0, "formatted_value": "Err", "status": "error", "error_message": str(e)}]

    # ══════════════════════════════════════════════════════════════
    # Chart Fetchers with Granularity (Daily / Monthly / Yearly)
    # ══════════════════════════════════════════════════════════════

    async def _fetch_trend(
        self,
        dataset: str,
        date_where: str,
        title: str,
        granularity: str = "monthly",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Revenue and gross profit trajectory formatted by granularity."""
        fmt_expr, label_alias = self._get_granularity_format(
            granularity, start_date=start_date, end_date=end_date
        )
        sql = f"""
        SELECT
            {fmt_expr} AS {label_alias},
            ROUND(SUM(total_amount), 2) AS revenue,
            ROUND(SUM(profit), 2) AS profit
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY {label_alias}
        ORDER BY {label_alias}
        """
        try:
            result = await bigquery_client.execute_query(sql)
            freq_label = "Hourly" if (start_date and end_date and start_date == end_date) else granularity.capitalize()
            return {
                "id": "chart-revenue-trend",
                "title": f"{title} ({freq_label})",
                "chart_type": "area",
                "chart_config": {
                    "x_key": label_alias,
                    "y_keys": ["revenue", "profit"],
                    "x_label": freq_label,
                    "y_label": "Amount (USD)",
                    "colors": ["#10B981", "#6366F1"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-revenue-trend", "title": title, "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_sales_trend(
        self,
        dataset: str,
        date_where: str,
        granularity: str = "monthly",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Sales run-rate and order volume trajectory by granularity."""
        fmt_expr, label_alias = self._get_granularity_format(
            granularity, start_date=start_date, end_date=end_date
        )
        sql = f"""
        SELECT
            {fmt_expr} AS {label_alias},
            ROUND(SUM(total_amount), 2) AS revenue,
            COUNT(*) AS orders
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY {label_alias}
        ORDER BY {label_alias}
        """
        try:
            result = await bigquery_client.execute_query(sql)
            freq_label = "Hourly" if (start_date and end_date and start_date == end_date) else granularity.capitalize()
            return {
                "id": "chart-sales-monthly-trend",
                "title": f"Sales Run-Rate & Volume ({freq_label})",
                "chart_type": "area",
                "chart_config": {
                    "x_key": label_alias,
                    "y_keys": ["revenue"],
                    "x_label": freq_label,
                    "y_label": "Revenue (USD)",
                    "colors": ["#0EA5E9"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-sales-monthly-trend", "title": "Sales Run-Rate", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_customer_trend(
        self,
        dataset: str,
        date_where: str,
        granularity: str = "monthly",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Active customer accounts and spend trajectory by granularity."""
        fmt_expr, label_alias = self._get_granularity_format(
            granularity, start_date=start_date, end_date=end_date
        )
        sql = f"""
        SELECT
            {fmt_expr} AS {label_alias},
            COUNT(DISTINCT customer_id) AS active_accounts,
            ROUND(SUM(total_amount), 2) AS monthly_spend
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY {label_alias}
        ORDER BY {label_alias}
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-cust-monthly-expansion",
                "title": f"Active Buying Accounts & Spend ({granularity.capitalize()})",
                "chart_type": "area",
                "chart_config": {
                    "x_key": label_alias,
                    "y_keys": ["monthly_spend"],
                    "x_label": granularity.capitalize(),
                    "y_label": "Spend (USD)",
                    "colors": ["#10B981"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-cust-monthly-expansion", "title": "Active Accounts", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_region_comparison(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            region,
            ROUND(SUM(total_amount), 2) AS revenue,
            ROUND(SUM(profit), 2) AS profit
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY region
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-sales-region-comparison",
                "title": "Territory Revenue & Profit Comparison",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "region",
                    "y_keys": ["revenue", "profit"],
                    "x_label": "Territory",
                    "y_label": "Amount (USD)",
                    "colors": ["#10B981", "#6366F1"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-sales-region-comparison", "title": "Territory Revenue & Profit", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_revenue_by_region(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            region,
            ROUND(SUM(total_amount), 2) AS revenue,
            COUNT(*) AS orders
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY region
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-revenue-region",
                "title": "Revenue by Territory",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "region",
                    "y_keys": ["revenue"],
                    "x_label": "Region",
                    "y_label": "Revenue (USD)",
                    "colors": ["#10B981"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-revenue-region", "title": "Revenue by Territory", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_revenue_by_segment(
        self, dataset: str, date_where: str, title: str = "Revenue by Customer Segment"
    ) -> dict[str, Any]:
        sql = f"""
        SELECT
            c.segment,
            ROUND(SUM(o.total_amount), 2) AS revenue
        FROM `{dataset}.orders` o
        JOIN `{dataset}.customers` c ON o.customer_id = c.id
        {self._join_date_where(date_where, "o")}
        GROUP BY c.segment
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-revenue-segment",
                "title": title,
                "chart_type": "pie",
                "chart_config": {
                    "name_key": "segment",
                    "value_key": "revenue",
                    "colors": ["#10B981", "#6366F1", "#0EA5E9"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-revenue-segment", "title": title, "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_channel_share(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            channel,
            ROUND(SUM(total_amount), 2) AS revenue
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY channel
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-sales-channel-share",
                "title": "Sales Channel Revenue Contribution",
                "chart_type": "pie",
                "chart_config": {
                    "name_key": "channel",
                    "value_key": "revenue",
                    "colors": ["#10B981", "#6366F1", "#0EA5E9", "#F59E0B"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-sales-channel-share", "title": "Channel Revenue Contribution", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_product_category_sales(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            p.category,
            ROUND(SUM(o.total_amount), 2) AS revenue,
            SUM(o.units) AS units_sold
        FROM `{dataset}.orders` o
        JOIN `{dataset}.products` p ON o.product_id = p.id
        {self._join_date_where(date_where, "o")}
        GROUP BY p.category
        ORDER BY revenue DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-sales-product-category",
                "title": "Product Category Sales Performance",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "category",
                    "y_keys": ["revenue"],
                    "x_label": "Category",
                    "y_label": "Revenue (USD)",
                    "colors": ["#10B981"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-sales-product-category", "title": "Product Category Sales", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_channel_deal_size(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            channel,
            ROUND(AVG(total_amount), 2) AS avg_deal_size
        FROM `{dataset}.orders`
        {date_where}
        GROUP BY channel
        ORDER BY avg_deal_size DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-channel-deal-size",
                "title": "Average Deal Size by Channel",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "channel",
                    "y_keys": ["avg_deal_size"],
                    "x_label": "Channel",
                    "y_label": "Avg Deal Size (USD)",
                    "layout": "horizontal",
                    "colors": ["#6366F1"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-channel-deal-size", "title": "Average Deal Size", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_top_enterprise_accounts(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            c.name AS account_name,
            ROUND(SUM(o.total_amount), 2) AS total_spend,
            COUNT(*) AS total_orders
        FROM `{dataset}.orders` o
        JOIN `{dataset}.customers` c ON o.customer_id = c.id
        {self._join_date_where(date_where, "o")}
        GROUP BY c.name
        ORDER BY total_spend DESC
        LIMIT 10
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-cust-top-accounts",
                "title": "Top 10 Enterprise Accounts by Spend",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "account_name",
                    "y_keys": ["total_spend"],
                    "x_label": "Account",
                    "y_label": "Total Spend (USD)",
                    "layout": "horizontal",
                    "colors": ["#10B981"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-cust-top-accounts", "title": "Top Accounts", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_aov_by_tier(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            c.segment,
            ROUND(AVG(o.total_amount), 2) AS avg_order_value
        FROM `{dataset}.orders` o
        JOIN `{dataset}.customers` c ON o.customer_id = c.id
        {self._join_date_where(date_where, "o")}
        GROUP BY c.segment
        ORDER BY avg_order_value DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-cust-aov-segment",
                "title": "Average Order Value by Customer Tier",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "segment",
                    "y_keys": ["avg_order_value"],
                    "x_label": "Tier",
                    "y_label": "Avg Order Value (USD)",
                    "colors": ["#6366F1"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-cust-aov-segment", "title": "Average Order Value by Tier", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_customer_territory_dist(self, dataset: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            region,
            COUNT(*) AS account_count
        FROM `{dataset}.customers`
        GROUP BY region
        ORDER BY account_count DESC
        """
        try:
            result = await bigquery_client.execute_query(sql)
            return {
                "id": "chart-cust-territory-dist",
                "title": "Account Territory Distribution",
                "chart_type": "bar",
                "chart_config": {
                    "x_key": "region",
                    "y_keys": ["account_count"],
                    "x_label": "Territory",
                    "y_label": "Total Accounts",
                    "colors": ["#0EA5E9"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-cust-territory-dist", "title": "Account Territory Distribution", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_top_products(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            p.name AS product,
            ROUND(SUM(o.total_amount), 2) AS revenue,
            SUM(o.units) AS units_sold
        FROM `{dataset}.orders` o
        JOIN `{dataset}.products` p ON o.product_id = p.id
        {self._join_date_where(date_where, "o")}
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
                    "colors": ["#10B981"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-top-products", "title": "Top Products", "chart_type": "error", "status": "error", "error_message": str(e)}

    async def _fetch_channel_performance(self, dataset: str, date_where: str) -> dict[str, Any]:
        sql = f"""
        SELECT
            channel,
            ROUND(SUM(total_amount), 2) AS revenue,
            COUNT(*) AS orders,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM `{dataset}.orders`
        {date_where}
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
                    "colors": ["#6366F1"],
                },
                "data_payload": {"rows": result.get("rows", [])},
            }
        except Exception as e:
            logger.error(f"Failed to fetch: {e}")
            return {"id": "chart-channel-performance", "title": "Channel Performance", "chart_type": "error", "status": "error", "error_message": str(e)}

    # ══════════════════════════════════════════════════════════════
    # Date Filtering & Helpers
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _get_date_where(
        time_range: str = "2y",
        start_date: str | None = None,
        end_date: str | None = None,
        col: str = "order_date",
    ) -> str:
        if time_range and time_range.lower() == "ytd":
            effective_end = f"DATE('{end_date}')" if end_date else "CURRENT_DATE()"
            start_date_final = f"DATE_TRUNC({effective_end}, YEAR)"
            return f"WHERE DATE({col}) >= {start_date_final} AND DATE({col}) <= {effective_end}"

        # Custom calendar date selection takes precedence
        if start_date and end_date:
            return f"WHERE DATE({col}) >= DATE('{start_date}') AND DATE({col}) <= DATE('{end_date}')"
        elif start_date:
            return f"WHERE DATE({col}) >= DATE('{start_date}')"
        elif end_date:
            return f"WHERE DATE({col}) <= DATE('{end_date}')"

        # Check if 4-digit year (e.g. 2024, 2025, 2026, or any other year)
        if time_range and len(time_range) == 4 and time_range.isdigit():
            return f"WHERE EXTRACT(YEAR FROM DATE({col})) = {int(time_range)}"
        elif time_range == "30d":
            return f"WHERE DATE({col}) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
        elif time_range == "90d":
            return f"WHERE DATE({col}) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)"
        elif time_range == "1y":
            return f"WHERE DATE({col}) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)"
        elif time_range in ("2y", "all"):
            return f"WHERE DATE({col}) >= DATE_SUB(CURRENT_DATE(), INTERVAL 730 DAY)"
        return ""

    @staticmethod
    def _get_granularity_format(
        granularity: str,
        col: str = "order_date",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[str, str]:
        if (start_date and end_date and start_date == end_date) or granularity == "hourly":
            return f"FORMAT_TIMESTAMP('%H:00', {col})", "period"
        elif granularity == "daily":
            return f"FORMAT_DATE('%Y-%m-%d', DATE({col}))", "period"
        elif granularity == "yearly":
            return f"FORMAT_DATE('%Y', DATE({col}))", "period"
        else:  # monthly default
            return f"FORMAT_DATE('%Y-%m', DATE({col}))", "period"

    @staticmethod
    def _join_date_where(date_where: str, prefix: str) -> str:
        if not date_where:
            return ""
        return (
            date_where.replace("WHERE DATE(", f"WHERE DATE({prefix}.")
            .replace("AND DATE(", f"AND DATE({prefix}.")
            .replace("WHERE EXTRACT(YEAR FROM DATE(", f"WHERE EXTRACT(YEAR FROM DATE({prefix}.")
            .replace("AND EXTRACT(YEAR FROM DATE(", f"AND EXTRACT(YEAR FROM DATE({prefix}.")
        )

    @staticmethod
    def _get_range_label(
        time_range: str = "2y",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        if start_date and end_date:
            return f"{start_date} to {end_date}"
        labels = {
            "ytd": "Year to Date",
            "2y": "Past 2 Years (2024–2026)",
            "all": "All Time (2024–2026)",
            "2024": "Year 2024",
            "2025": "Year 2025",
            "2026": "Year 2026",
            "1y": "Past 12 Months",
            "90d": "Past 90 Days",
            "30d": "Past 30 Days",
        }
        return labels.get(time_range, f"Range: {time_range}")

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
