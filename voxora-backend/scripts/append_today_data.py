"""
Append real-time orders for 2026-09-11 and 2026-09-12 (Today) into Postgres and BigQuery.
"""
import asyncio
from datetime import date
import random
import os
from google.cloud import bigquery
from sqlalchemy import text
from dotenv import load_dotenv

from app.db.session import async_session_factory

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("gcp-service-account.json")

REGIONS = ["Eastern", "Western", "Central", "Southern"]
CHANNELS = ["Direct Sales", "Online Portal", "Partner Referral", "Inside Sales"]

async def append_today_data():
    async with async_session_factory() as db:
        # Check existing max date and order id
        res = await db.execute(text("SELECT MAX(order_date), MAX(id), COUNT(*) FROM analytics_orders;"))
        max_date, max_id, total_cnt = res.fetchone()
        print(f"Current Postgres max date: {max_date}, max id: {max_id}, total orders: {total_cnt}")

        start_counter = int(max_id.replace("ORD-", "")) + 1 if max_id else 6658

        # Fetch products and customer IDs directly from DB
        prod_res = await db.execute(text("SELECT id, CAST(unit_price AS FLOAT) as unit_price, CAST(unit_cost AS FLOAT) as unit_cost FROM analytics_products;"))
        products = [dict(r._mapping) for r in prod_res]

        cust_res = await db.execute(text("SELECT id, segment FROM analytics_customers;"))
        customers = [dict(row._mapping) for row in cust_res]
        ent_customers = [c["id"] for c in customers if c["segment"] == "Enterprise"]
        mid_customers = [c["id"] for c in customers if c["segment"] == "Mid-Market"]
        smb_customers = [c["id"] for c in customers if c["segment"] == "SMB"]

        dates_to_add = []
        if max_date < date(2026, 9, 11):
            dates_to_add.append(date(2026, 9, 11))
        if max_date < date(2026, 9, 12):
            dates_to_add.append(date(2026, 9, 12))

        if not dates_to_add:
            print("Today's date is already present in Postgres!")
        else:
            orders_to_insert = []
            kpis_to_insert = []

            for target_date in dates_to_add:
                # 2026-09-11: 14 orders, 2026-09-12 (Saturday): 10 orders
                day_orders_count = 14 if target_date.day == 11 else 10
                day_revenue = 0.0
                day_profit = 0.0

                for _ in range(day_orders_count):
                    order_id = f"ORD-{start_counter:06d}"
                    start_counter += 1

                    segment_pick = random.choices(["Enterprise", "Mid-Market", "SMB"], weights=[35, 45, 20])[0]
                    if segment_pick == "Enterprise":
                        cust_id = random.choice(ent_customers)
                        channel = random.choices(CHANNELS, weights=[50, 10, 25, 15])[0]
                        units = random.choices([2, 3, 5, 8], weights=[35, 35, 20, 10])[0]
                    elif segment_pick == "Mid-Market":
                        cust_id = random.choice(mid_customers)
                        channel = random.choices(CHANNELS, weights=[25, 35, 20, 20])[0]
                        units = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
                    else:
                        cust_id = random.choice(smb_customers)
                        channel = random.choices(CHANNELS, weights=[10, 60, 10, 20])[0]
                        units = random.choices([1, 2], weights=[80, 20])[0]

                    prod = random.choice(products)
                    unit_price = prod["unit_price"]
                    unit_cost = prod["unit_cost"]
                    total_amount = round(float(units * unit_price), 2)
                    profit = round(float(units * (unit_price - unit_cost)), 2)
                    region = random.choice(REGIONS)

                    day_revenue += total_amount
                    day_profit += profit

                    orders_to_insert.append({
                        "id": order_id,
                        "customer_id": cust_id,
                        "product_id": prod["id"],
                        "order_date": target_date,
                        "units": units,
                        "unit_price": unit_price,
                        "total_amount": total_amount,
                        "profit": profit,
                        "region": region,
                        "channel": channel,
                        "status": "Completed"
                    })

                avg_val = round(day_revenue / max(1, day_orders_count), 2)
                margin_pct = round((day_profit / max(1.0, day_revenue)) * 100.0, 2)

                kpis_to_insert.append({
                    "date": target_date,
                    "total_revenue": round(day_revenue, 2),
                    "total_orders": day_orders_count,
                    "avg_order_value": avg_val,
                    "gross_profit": round(day_profit, 2),
                    "profit_margin_pct": margin_pct,
                })

            print(f"Inserting {len(orders_to_insert)} orders into Postgres analytics_orders...")
            for o in orders_to_insert:
                await db.execute(text("""
                    INSERT INTO analytics_orders (id, customer_id, product_id, order_date, units, unit_price, total_amount, profit, region, channel, status)
                    VALUES (:id, :customer_id, :product_id, :order_date, :units, :unit_price, :total_amount, :profit, :region, :channel, :status)
                    ON CONFLICT (id) DO NOTHING;
                """), o)

            for k in kpis_to_insert:
                await db.execute(text("""
                    INSERT INTO analytics_daily_kpis (date, total_revenue, total_orders, avg_order_value, gross_profit, profit_margin_pct)
                    VALUES (:date, :total_revenue, :total_orders, :avg_order_value, :gross_profit, :profit_margin_pct)
                    ON CONFLICT (date) DO UPDATE SET
                        total_revenue = EXCLUDED.total_revenue,
                        total_orders = EXCLUDED.total_orders,
                        avg_order_value = EXCLUDED.avg_order_value,
                        gross_profit = EXCLUDED.gross_profit,
                        profit_margin_pct = EXCLUDED.profit_margin_pct;
                """), k)

            await db.commit()
            print("✅ Successfully committed to Postgres!")

    # Now Sync to Google BigQuery
    bq_client = bigquery.Client(project=os.environ.get("BIGQUERY_PROJECT"))
    dataset_id = os.environ.get("BIGQUERY_DATASET", "voxora_bigquery_sa")
    full_dataset_id = f"{bq_client.project}.{dataset_id}"

    async with async_session_factory() as db:
        # Sync all orders to BigQuery
        print("Fetching all orders from Postgres to sync to BigQuery...")
        ord_res = await db.execute(text("""
            SELECT id, customer_id, product_id, CAST(order_date AS TEXT) as order_date, 
                   units, CAST(unit_price AS FLOAT) as unit_price, CAST(total_amount AS FLOAT) as total_amount, 
                   CAST(profit AS FLOAT) as profit, region, channel, status 
            FROM analytics_orders;
        """))
        orders = [dict(row._mapping) for row in ord_res]
        ord_table_id = f"{full_dataset_id}.orders"
        print(f"Loading {len(orders)} orders into BigQuery: {ord_table_id}")
        ord_job = bq_client.load_table_from_json(
            orders,
            ord_table_id,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        ord_job.result()
        print("✅ Successfully loaded all orders into BigQuery!")

        # Sync daily_kpis to BigQuery
        kpi_res = await db.execute(text("""
            SELECT CAST(date AS TEXT) as date, CAST(total_revenue AS FLOAT) as total_revenue, 
                   total_orders, CAST(avg_order_value AS FLOAT) as avg_order_value, 
                   CAST(gross_profit AS FLOAT) as gross_profit, CAST(profit_margin_pct AS FLOAT) as profit_margin_pct 
            FROM analytics_daily_kpis;
        """))
        kpis = [dict(row._mapping) for row in kpi_res]
        kpi_table_id = f"{full_dataset_id}.daily_kpis"
        print(f"Loading {len(kpis)} daily_kpis into BigQuery: {kpi_table_id}")
        kpi_job = bq_client.load_table_from_json(
            kpis,
            kpi_table_id,
            job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        )
        kpi_job.result()
        print("✅ Successfully loaded all daily_kpis into BigQuery!")

if __name__ == "__main__":
    asyncio.run(append_today_data())
