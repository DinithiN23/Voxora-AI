"""
Voxora Backend — Analytical Data Warehouse Seed Script.

Creates and seeds analytical tables in PostgreSQL:
- analytics_customers
- analytics_products
- analytics_orders
- analytics_daily_kpis
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
import random
from sqlalchemy import text
from app.db.session import async_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CREATE_TABLES_SQL = """
-- 1. Analytics Products
CREATE TABLE IF NOT EXISTS analytics_products (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL
);

-- 2. Analytics Customers
CREATE TABLE IF NOT EXISTS analytics_customers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    segment VARCHAR(50) NOT NULL, -- Enterprise, Mid-Market, SMB
    region VARCHAR(50) NOT NULL,   -- Eastern, Western, Central, Southern
    country VARCHAR(50) DEFAULT 'USA',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Analytics Orders
CREATE TABLE IF NOT EXISTS analytics_orders (
    id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES analytics_customers(id),
    product_id VARCHAR(50) REFERENCES analytics_products(id),
    order_date DATE NOT NULL,
    units INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    profit NUMERIC(12, 2) NOT NULL,
    region VARCHAR(50) NOT NULL,
    channel VARCHAR(50) NOT NULL, -- Direct, Online, Partner, Retail
    status VARCHAR(50) DEFAULT 'Completed'
);

-- 4. Analytics Daily KPIs
CREATE TABLE IF NOT EXISTS analytics_daily_kpis (
    date DATE PRIMARY KEY,
    total_revenue NUMERIC(12, 2) NOT NULL,
    total_orders INT NOT NULL,
    avg_order_value NUMERIC(10, 2) NOT NULL,
    gross_profit NUMERIC(12, 2) NOT NULL,
    profit_margin_pct NUMERIC(5, 2) NOT NULL
);
"""

PRODUCTS = [
    ("PROD-001", "Voxora Enterprise AI Suite", "Software", "Enterprise AI", 1200.00, 240.00),
    ("PROD-002", "Voxora Analytics Pro", "Software", "BI & Analytics", 450.00, 90.00),
    ("PROD-003", "Data Pipeline Connector", "Software", "Integrations", 250.00, 40.00),
    ("PROD-004", "Predictive Forecasting Add-on", "Software", "Machine Learning", 600.00, 110.00),
    ("PROD-005", "Dedicated Inference Server", "Hardware", "Compute", 3500.00, 2100.00),
    ("PROD-006", "Smart Edge Gateway", "Hardware", "Edge Devices", 850.00, 520.00),
    ("PROD-007", "Executive Training & Onboarding", "Services", "Professional Services", 1500.00, 600.00),
    ("PROD-008", "Custom AI Fine-tuning", "Services", "Consulting", 2800.00, 1100.00),
    ("PROD-009", "Premium 24/7 SLA Support", "Services", "Support", 750.00, 200.00),
    ("PROD-010", "Automated Compliance Auditor", "Software", "Security & Governance", 950.00, 180.00),
]

REGIONS = ["Eastern", "Western", "Central", "Southern"]
SEGMENTS = ["Enterprise", "Mid-Market", "SMB"]
CHANNELS = ["Direct Sales", "Online Portal", "Partner Referral", "Inside Sales"]

FIRST_NAMES = ["Apex", "Vertex", "Summit", "Quantum", "Nexus", "Horizon", "Catalyst", "Pinnacle", "Vanguard", "Synergy", "Beacon", "Crest", "Starlight", "Orbit", "Pulse"]
COMPANY_SUFFIXES = ["Corp", "Technologies", "Logistics", "Financial", "Health", "Cloud", "Solutions", "Global", "Systems", "Enterprises"]


async def init_and_seed_analytics():
    """Create tables and seed initial dataset."""
    logger.info("Connecting to Supabase PostgreSQL to initialize analytics tables...")
    async with async_session_factory() as db:
        # Create tables one by one (asyncpg requirement)
        statements = [stmt.strip() for stmt in CREATE_TABLES_SQL.split(";") if stmt.strip()]
        for stmt in statements:
            await db.execute(text(stmt))
        await db.commit()
        logger.info("Analytics tables verified/created successfully.")

        # Check existing orders count
        count_res = await db.execute(text("SELECT COUNT(*) FROM analytics_orders;"))
        count = count_res.scalar() or 0
        if count > 50:
            logger.info(f"Analytics tables already populated with {count} orders. Skipping seed.")
            return

        logger.info("Seeding analytical data...")

        # 1. Seed Products
        for prod in PRODUCTS:
            await db.execute(
                text("""
                INSERT INTO analytics_products (id, name, category, subcategory, unit_price, unit_cost)
                VALUES (:id, :name, :category, :subcategory, :unit_price, :unit_cost)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    unit_price = EXCLUDED.unit_price;
                """),
                {
                    "id": prod[0],
                    "name": prod[1],
                    "category": prod[2],
                    "subcategory": prod[3],
                    "unit_price": prod[4],
                    "unit_cost": prod[5],
                }
            )

        # 2. Seed Customers
        customer_ids = []
        for i in range(1, 41):
            c_id = f"CUST-{i:03d}"
            customer_ids.append(c_id)
            c_name = f"{random.choice(FIRST_NAMES)} {random.choice(COMPANY_SUFFIXES)}"
            c_email = f"procurement@{c_name.lower().replace(' ', '')}.com"
            region = random.choice(REGIONS)
            segment = random.choice(SEGMENTS)
            created_at = datetime.now() - timedelta(days=random.randint(60, 365))

            await db.execute(
                text("""
                INSERT INTO analytics_customers (id, name, email, segment, region, country, created_at)
                VALUES (:id, :name, :email, :segment, :region, 'USA', :created_at)
                ON CONFLICT (id) DO NOTHING;
                """),
                {
                    "id": c_id,
                    "name": c_name,
                    "email": c_email,
                    "segment": segment,
                    "region": region,
                    "created_at": created_at,
                }
            )

        # 3. Seed Orders (spanning past 90 days)
        today = date.today()
        daily_data = {}

        order_counter = 1
        for day_offset in range(90, -1, -1):
            order_date = today - timedelta(days=day_offset)
            # 5 to 15 orders per day with seasonal/day-of-week variation
            day_orders_count = random.randint(6, 14)
            if order_date.weekday() in (5, 6): # Weekend slightly lower
                day_orders_count = max(2, day_orders_count - 5)

            day_revenue = 0.0
            day_profit = 0.0

            for _ in range(day_orders_count):
                order_id = f"ORD-{order_counter:05d}"
                order_counter += 1
                cust_id = random.choice(customer_ids)
                prod = random.choice(PRODUCTS)
                units = random.choices([1, 2, 3, 5, 10], weights=[50, 25, 15, 7, 3])[0]
                unit_price = prod[4]
                unit_cost = prod[5]
                total_amount = float(units * unit_price)
                profit = float(units * (unit_price - unit_cost))
                region = random.choice(REGIONS)
                channel = random.choice(CHANNELS)

                day_revenue += total_amount
                day_profit += profit

                await db.execute(
                    text("""
                    INSERT INTO analytics_orders (
                        id, customer_id, product_id, order_date, units, unit_price,
                        total_amount, profit, region, channel, status
                    )
                    VALUES (
                        :id, :customer_id, :product_id, :order_date, :units, :unit_price,
                        :total_amount, :profit, :region, :channel, 'Completed'
                    )
                    ON CONFLICT (id) DO NOTHING;
                    """),
                    {
                        "id": order_id,
                        "customer_id": cust_id,
                        "product_id": prod[0],
                        "order_date": order_date,
                        "units": units,
                        "unit_price": unit_price,
                        "total_amount": total_amount,
                        "profit": profit,
                        "region": region,
                        "channel": channel,
                    }
                )

            # Record KPI summary for this day
            avg_val = day_revenue / max(1, day_orders_count)
            margin_pct = (day_profit / max(1.0, day_revenue)) * 100.0
            await db.execute(
                text("""
                INSERT INTO analytics_daily_kpis (
                    date, total_revenue, total_orders, avg_order_value, gross_profit, profit_margin_pct
                )
                VALUES (:date, :rev, :orders, :aov, :profit, :margin)
                ON CONFLICT (date) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    total_orders = EXCLUDED.total_orders,
                    avg_order_value = EXCLUDED.avg_order_value,
                    gross_profit = EXCLUDED.gross_profit,
                    profit_margin_pct = EXCLUDED.profit_margin_pct;
                """),
                {
                    "date": order_date,
                    "rev": day_revenue,
                    "orders": day_orders_count,
                    "aov": avg_val,
                    "profit": day_profit,
                    "margin": margin_pct,
                }
            )

        await db.commit()
        logger.info(f"Successfully seeded {order_counter - 1} orders across 90 days!")


if __name__ == "__main__":
    asyncio.run(init_and_seed_analytics())
