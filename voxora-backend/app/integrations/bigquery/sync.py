"""
Voxora Backend — Sync PostgreSQL Analytics to Google BigQuery.

Reads all tables from Supabase/Postgres and loads them into BigQuery dataset.
"""

import asyncio
import os
from google.cloud import bigquery
from sqlalchemy import text
from dotenv import load_dotenv
from app.db.session import async_session_factory

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("gcp-service-account.json")


async def sync_to_bigquery():
    client = bigquery.Client(project=os.environ.get("BIGQUERY_PROJECT"))
    dataset_id = os.environ.get("BIGQUERY_DATASET", "voxora_bigquery_sa")
    full_dataset_id = f"{client.project}.{dataset_id}"

    print(f"🚀 Starting sync to BigQuery dataset: {full_dataset_id}")

    async with async_session_factory() as db:
        # 1. Products
        prod_res = await db.execute(text("SELECT id, name, category, subcategory, CAST(unit_price AS FLOAT) as unit_price, CAST(unit_cost AS FLOAT) as unit_cost FROM analytics_products;"))
        products = [dict(row._mapping) for row in prod_res]
        print(f"Fetched {len(products)} products from Postgres.")

        prod_table_id = f"{full_dataset_id}.products"
        prod_job = client.load_table_from_json(
            products,
            prod_table_id,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        prod_job.result()
        print(f"✅ Loaded {len(products)} products into BigQuery: {prod_table_id}")

        # 2. Customers
        cust_res = await db.execute(text("SELECT id, name, email, segment, region, country, CAST(created_at AS TEXT) as created_at FROM analytics_customers;"))
        customers = [dict(row._mapping) for row in cust_res]
        print(f"Fetched {len(customers)} customers from Postgres.")

        cust_table_id = f"{full_dataset_id}.customers"
        cust_job = client.load_table_from_json(
            customers,
            cust_table_id,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        cust_job.result()
        print(f"✅ Loaded {len(customers)} customers into BigQuery: {cust_table_id}")

        # 3. Orders
        ord_res = await db.execute(text("SELECT id, customer_id, product_id, CAST(order_date AS TEXT) as order_date, units, CAST(unit_price AS FLOAT) as unit_price, CAST(total_amount AS FLOAT) as total_amount, CAST(profit AS FLOAT) as profit, region, channel, status FROM analytics_orders;"))
        orders = [dict(row._mapping) for row in ord_res]
        print(f"Fetched {len(orders)} orders from Postgres.")

        ord_table_id = f"{full_dataset_id}.orders"
        ord_job = client.load_table_from_json(
            orders,
            ord_table_id,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        ord_job.result()
        print(f"✅ Loaded {len(orders)} orders into BigQuery: {ord_table_id}")

        # 4. Daily KPIs
        kpi_res = await db.execute(text("SELECT CAST(date AS TEXT) as date, CAST(total_revenue AS FLOAT) as total_revenue, total_orders, CAST(avg_order_value AS FLOAT) as avg_order_value, CAST(gross_profit AS FLOAT) as gross_profit, CAST(profit_margin_pct AS FLOAT) as profit_margin_pct FROM analytics_daily_kpis;"))
        kpis = [dict(row._mapping) for row in kpi_res]
        print(f"Fetched {len(kpis)} daily KPIs from Postgres.")

        kpi_table_id = f"{full_dataset_id}.daily_kpis"
        kpi_job = client.load_table_from_json(
            kpis,
            kpi_table_id,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        kpi_job.result()
        print(f"✅ Loaded {len(kpis)} daily KPIs into BigQuery: {kpi_table_id}")

    print("\n🎉 BigQuery Sync Complete! All 4 tables are live in Google BigQuery!")


if __name__ == "__main__":
    asyncio.run(sync_to_bigquery())
