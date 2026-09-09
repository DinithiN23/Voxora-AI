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
   - order_date: DATE / STRING (YYYY-MM-DD)
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
   - created_at: STRING (Timestamp)

4. `{dataset}.daily_kpis`:
   - date: DATE / STRING (YYYY-MM-DD)
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

RULES_FOR_SQL = """
Rules for BigQuery SQL Generation:
1. Use Google BigQuery Standard SQL dialect.
2. ALWAYS use the full table path formatted with backticks: `{dataset}.<table_name>`.
3. Use ROUND() on financial and percentage metrics to 2 decimal places.
4. When filtering dates, format as 'YYYY-MM-DD'.
5. When ranking or finding 'top' items, use ORDER BY ... DESC LIMIT N.
6. For monthly trends, you can format date with SUBSTR(CAST(order_date AS STRING), 1, 7) or DATE_TRUNC(DATE(order_date), MONTH).
7. Only generate SELECT queries. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE statements.
8. Always alias aggregate expressions clearly (e.g. `SUM(total_amount) AS total_revenue`).
"""


class SemanticLayer:
    """Manages schema context and prompt generation for Text-to-SQL."""

    def get_dataset_path(self) -> str:
        return bigquery_client.full_dataset_path

    def get_system_prompt(self) -> str:
        dataset = self.get_dataset_path()
        tables = TABLE_DEFINITIONS.replace("{dataset}", dataset)
        rules = RULES_FOR_SQL.replace("{dataset}", dataset)

        return f"""You are Voxora AI's Chief Analytics Engineer.
Your task is to translate business questions into accurate, high-performance Google BigQuery SQL queries.

Database Schema:
{tables}

{METRIC_DEFINITIONS}

{rules}

Output Format:
Return ONLY the raw SQL query inside a ```sql ... ``` code block.
Do NOT include explanatory text before or after the SQL.
"""


semantic_layer = SemanticLayer()
