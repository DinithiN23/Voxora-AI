"""
Voxora Backend — Semantic Layer & Schema Registry.

Defines analytical business data models, metrics, dimensions, and prompt context
for precise Text-to-SQL generation.
"""

from typing import Any
from app.integrations.bigquery.client import bigquery_client

TABLE_DEFINITIONS = """
Dataset Path: `{dataset}`

Tables:
1. `{dataset}.orders`:
   - id: STRING (Primary key, e.g. 'ORD-00001')
   - customer_id: STRING (Foreign key to customers.id)
   - product_id: STRING (Foreign key to products.id)
   - order_date: DATE / STRING (YYYY-MM-DD, stored in UTC)
   - units: INT64 (Number of units purchased)
   - unit_price: FLOAT64 (Selling price per unit in USD)
   - total_amount: FLOAT64 (Total order revenue = units * unit_price)
   - profit: FLOAT64 (Gross profit in USD)
   - region: STRING ('Eastern', 'Western', 'Central', 'Southern')
   - channel: STRING ('Direct Sales', 'Online Portal', 'Partner Referral', 'Inside Sales')
   - status: STRING ('Completed')

2. `{dataset}.products`:
   - id: STRING (Primary key, e.g. 'PROD-001')
   - name: STRING (Product name, e.g. 'Voxora Enterprise AI Suite', 'Voxora Analytics Pro')
   - category: STRING ('Software', 'Hardware', 'Services')
   - subcategory: STRING ('Enterprise AI', 'BI & Analytics', 'Integrations', 'Compute', 'Consulting')
   - unit_price: FLOAT64 (Catalog price in USD)
   - unit_cost: FLOAT64 (Cost of goods sold in USD)

3. `{dataset}.customers`:
   - id: STRING (Primary key, e.g. 'CUST-001')
   - name: STRING (Company name, e.g. 'Apex Corp', 'Vertex Technologies')
   - email: STRING
   - segment: STRING ('Enterprise', 'Mid-Market', 'SMB')
   - region: STRING ('Eastern', 'Western', 'Central', 'Southern')
   - country: STRING ('USA')
   - created_at: STRING (Timestamp in UTC)

4. `{dataset}.daily_kpis`:
   - date: DATE / STRING (YYYY-MM-DD, stored in UTC)
   - total_revenue: FLOAT64 (Daily aggregate revenue in USD)
   - total_orders: INT64 (Daily order count)
   - avg_order_value: FLOAT64 (Average order value in USD)
   - gross_profit: FLOAT64 (Daily profit in USD)
   - profit_margin_pct: FLOAT64 (Gross margin percentage, e.g. 58.4)
"""

METRIC_DEFINITIONS = """
Business Metric Definitions:
- Revenue: SUM(total_amount) or SUM(orders.total_amount)
- Profit: SUM(profit) or SUM(orders.profit)
- Profit Margin %: ROUND((SUM(profit) / NULLIF(SUM(total_amount), 0)) * 100, 2)
- Total Orders: COUNT(*) or COUNT(DISTINCT orders.id)
- Average Order Value (AOV): ROUND(AVG(total_amount), 2)
- Units Sold: SUM(units)
"""

from datetime import date, datetime, timedelta, timezone

class SemanticLayer:
    """Manages schema context and prompt generation for Text-to-SQL."""

    def get_dataset_path(self) -> str:
        return bigquery_client.full_dataset_path

    def get_temporal_context(self) -> str:
        # TIMEZONE CONVENTION: Coordinated Universal Time (UTC).
        # All temporal anchors, date filters, and aggregations are strictly calculated in UTC
        # to match the DATE partitioning and transaction boundaries in BigQuery.
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()
        yesterday = today - timedelta(days=1)
        today_str = today.isoformat()
        yesterday_str = yesterday.isoformat()
        current_year = today.year
        current_month_str = today.strftime("%Y-%m")
        current_month_name = today.strftime("%B %Y")

        # Previous month
        m1_year = today.year if today.month > 1 else today.year - 1
        m1_month = today.month - 1 if today.month > 1 else 12
        last_month_str = f"{m1_year:04d}-{m1_month:02d}"
        last_month_name = date(m1_year, m1_month, 1).strftime("%B %Y")

        # 2 months ago
        m2_month = ((today.month - 1 - 2) % 12) + 1
        m2_year = today.year if today.month > 2 else today.year - 1
        m2_str = f"{m2_year:04d}-{m2_month:02d}"

        # 3 months ago (for multi-month windows like June-September)
        m3_month = ((today.month - 1 - 3) % 12) + 1
        m3_year = today.year if today.month > 3 else today.year - 1
        m3_str = f"{m3_year:04d}-{m3_month:02d}"
        m3_start = f"{m3_str}-01"

        dataset = self.get_dataset_path()

        return f"""
Temporal Guidelines & Date Handling (GROUND TRUTH AS OF TODAY - STRICT UTC CONVENTION):
- TIMEZONE CONVENTION: All dates and timeframes are evaluated strictly in Coordinated Universal Time (UTC).
- GROUND TRUTH UTC TIMESTAMP: '{now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")}'.
- TODAY'S DATE (UTC): '{today_str}' ({today.strftime("%A, %B %d, %Y")}).
- YESTERDAY'S DATE (UTC): '{yesterday_str}'.
- CURRENT MONTH (UTC): '{current_month_str}' ({current_month_name}).
- LAST MONTH (1 MONTH AGO, UTC): '{last_month_str}' ({last_month_name}).
- 2 MONTHS AGO (UTC): '{m2_str}'.
- 3 MONTHS AGO (UTC): '{m3_str}' (Month start: '{m3_start}').
- CURRENT YEAR (UTC): {current_year}.

Rules for Temporal Queries:
1. "Today" / "today's revenue" / "sales today":
   - MUST filter for today's UTC date: `WHERE order_date = '{today_str}'`
   - Example:
     ```sql
     SELECT 
       ROUND(SUM(total_amount), 2) AS total_revenue,
       COUNT(*) AS total_orders,
       ROUND(SUM(profit), 2) AS total_profit,
       ROUND(AVG(total_amount), 2) AS avg_order_value
     FROM `{dataset}.orders`
     WHERE order_date = '{today_str}'
     ```
2. "Yesterday" / "yesterday's revenue":
   - MUST filter for yesterday's UTC date: `WHERE order_date = '{yesterday_str}'`
3. "This month" / "current month" / "MTD" (Month to Date):
   - MUST filter for '{current_month_str}': `WHERE SUBSTR(CAST(order_date AS STRING), 1, 7) = '{current_month_str}'`
4. "Last month" / "previous month":
   - MUST filter for '{last_month_str}': `WHERE SUBSTR(CAST(order_date AS STRING), 1, 7) = '{last_month_str}'`
   - CRITICAL: Never use `ORDER BY month DESC LIMIT 1` for last month, as that returns current active month.
5. "From this month to last 3 month revenue total in 2026" / "past 3 months to this month":
   - This refers to the multi-month window covering 3 months prior up to and including current date ('{m3_str}' to '{today_str}', i.e. '{m3_start}' to '{today_str}').
   - For total revenue, calculate the overall sum:
     ```sql
     SELECT 
       ROUND(SUM(total_amount), 2) AS total_revenue,
       COUNT(*) AS total_orders,
       ROUND(SUM(profit), 2) AS total_profit,
       ROUND(AVG(total_amount), 2) AS avg_order_value
     FROM `{dataset}.orders`
     WHERE order_date >= '{m3_start}' AND order_date <= '{today_str}'
     ```
   - For monthly breakdown or trend across these months:
     ```sql
     SELECT 
       SUBSTR(CAST(order_date AS STRING), 1, 7) AS month,
       ROUND(SUM(total_amount), 2) AS monthly_revenue,
       COUNT(*) AS total_orders,
       ROUND(SUM(profit), 2) AS total_profit
     FROM `{dataset}.orders`
     WHERE order_date >= '{m3_start}' AND order_date <= '{today_str}'
     GROUP BY month
     ORDER BY month
     ```
6. "Last 3 completed months" (excluding current partial month):
   - Filter: `WHERE SUBSTR(CAST(order_date AS STRING), 1, 7) IN ('{m3_str}', '{m2_str}', '{last_month_str}')`
7. "This year" / "YTD" / "in {current_year}":
   - Filter: `WHERE SUBSTR(CAST(order_date AS STRING), 1, 4) = '{current_year}'` or `WHERE order_date >= '{current_year}-01-01' AND order_date <= '{today_str}'`
8. "Last year" / "{current_year - 1}":
   - Filter: `WHERE SUBSTR(CAST(order_date AS STRING), 1, 4) = '{current_year - 1}'`
"""

    def get_system_prompt(self) -> str:
        dataset = self.get_dataset_path()
        tables = TABLE_DEFINITIONS.replace("{dataset}", dataset)
        temporal_context = self.get_temporal_context()

        return f"""You are Voxora AI's Chief Analytics Engineer.
Your task is to translate business questions into accurate, high-performance Google BigQuery SQL queries.

Database Schema:
{tables}

{METRIC_DEFINITIONS}

Rules for BigQuery SQL Generation:
1. Use Google BigQuery Standard SQL dialect.
2. ALWAYS use the full table path formatted with backticks: `{dataset}.<table_name>`.
3. Use ROUND() on financial and percentage metrics to 2 decimal places.
4. When filtering dates, format as 'YYYY-MM-DD'. All dates operate under Coordinated Universal Time (UTC).
5. When ranking or finding 'top' items, use ORDER BY ... DESC LIMIT N.
6. For monthly aggregations, format date with SUBSTR(CAST(order_date AS STRING), 1, 7).
7. Only generate SELECT queries. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE statements.
8. Always alias aggregate expressions clearly (e.g. `SUM(total_amount) AS total_revenue`).
9. CRITICAL COST & SCOPE RULE: You MUST include a date-range filter (e.g., `WHERE order_date >= ...`) on EVERY query to prevent full table scans. If the user does not specify a date, default to the last 30 days (`WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)`).

{temporal_context}

Output Format:
Return ONLY the raw SQL query inside a ```sql ... ``` code block.
Do NOT include explanatory text before or after the SQL.
"""


semantic_layer = SemanticLayer()
