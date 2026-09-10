"""
Voxora Backend — Analytical Data Warehouse Seed Script.

Creates and seeds analytical tables in PostgreSQL with 2 full years (730 days) of data:
- analytics_products
- analytics_customers
- analytics_orders
- analytics_daily_kpis
"""

import asyncio
import logging
import sys
from datetime import date, datetime, timedelta, timezone
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
    channel VARCHAR(50) NOT NULL, -- Direct Sales, Online Portal, Partner Referral, Inside Sales
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

-- Performance Indexes for fast multi-year slicing
CREATE INDEX IF NOT EXISTS idx_analytics_orders_date ON analytics_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_analytics_orders_region ON analytics_orders(region);
CREATE INDEX IF NOT EXISTS idx_analytics_orders_channel ON analytics_orders(channel);
CREATE INDEX IF NOT EXISTS idx_analytics_orders_customer ON analytics_orders(customer_id);
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
    ("PROD-011", "High-Throughput Storage Array", "Hardware", "Storage", 4200.00, 2600.00),
    ("PROD-012", "Data Governance & Lineage Pack", "Software", "Security & Governance", 1100.00, 220.00),
]

REGIONS = ["Eastern", "Western", "Central", "Southern"]
SEGMENTS = ["Enterprise", "Mid-Market", "SMB"]
CHANNELS = ["Direct Sales", "Online Portal", "Partner Referral", "Inside Sales"]

FIRST_NAMES = [
    "Apex", "Vertex", "Summit", "Quantum", "Nexus", "Horizon", "Catalyst", "Pinnacle",
    "Vanguard", "Synergy", "Beacon", "Crest", "Starlight", "Orbit", "Pulse", "Aegis",
    "Nova", "Solaris", "Zenith", "Stratus", "Cipher", "Dynamo", "Echelon", "Matrix"
]
COMPANY_SUFFIXES = [
    "Corp", "Technologies", "Logistics", "Financial", "Health", "Cloud",
    "Solutions", "Global", "Systems", "Enterprises", "Industries", "Group"
]


async def init_and_seed_analytics(force: bool = True, days_history: int = 730):
    """
    Create tables and seed analytical dataset with 2 full years of data.
    
    Args:
        force: If True, truncates existing orders and re-populates with full 2-year timeline.
        days_history: Number of historical days to generate (default 730 = 2 years).
    """
    logger.info(f"Connecting to database to initialize analytics tables (history: {days_history} days)...")
    async with async_session_factory() as db:
        # Create tables and indexes
        statements = [stmt.strip() for stmt in CREATE_TABLES_SQL.split(";") if stmt.strip()]
        for stmt in statements:
            await db.execute(text(stmt))
        await db.commit()
        logger.info("Analytics schema and indexes verified successfully.")

        # Check existing orders
        count_res = await db.execute(text("SELECT COUNT(*) FROM analytics_orders;"))
        count = count_res.scalar() or 0

        if count >= 3000 and not force:
            logger.info(f"Analytics tables already populated with {count} orders across multi-year timeline. Skipping.")
            return

        if force and count > 0:
            logger.info(f"Force reseed requested. Clearing previous {count} orders and daily KPIs...")
            await db.execute(text("DELETE FROM analytics_orders;"))
            await db.execute(text("DELETE FROM analytics_daily_kpis;"))
            await db.commit()

        # 1. Seed Products
        logger.info(f"Seeding {len(PRODUCTS)} products...")
        for prod in PRODUCTS:
            await db.execute(
                text("""
                INSERT INTO analytics_products (id, name, category, subcategory, unit_price, unit_cost)
                VALUES (:id, :name, :category, :subcategory, :unit_price, :unit_cost)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    subcategory = EXCLUDED.subcategory,
                    unit_price = EXCLUDED.unit_price,
                    unit_cost = EXCLUDED.unit_cost;
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
        await db.commit()

        # 2. Seed 120 Customers across Segments and Regions
        logger.info("Seeding 120 customer accounts with realistic cohorts...")
        customer_records = []
        random.seed(42) # Reproducible realistic distribution

        # Generate 120 unique customer companies
        existing_names = set()
        c_idx = 1
        while len(customer_records) < 120:
            name = f"{random.choice(FIRST_NAMES)} {random.choice(COMPANY_SUFFIXES)}"
            if name in existing_names:
                name = f"{name} {random.choice(['Americas', 'North', 'Solutions', 'Holdings'])}"
            existing_names.add(name)

            c_id = f"CUST-{c_idx:03d}"
            email = f"procurement@{name.lower().replace(' ', '').replace('-', '')[:18]}.com"
            
            # 25% Enterprise, 45% Mid-Market, 30% SMB
            segment = random.choices(SEGMENTS, weights=[25, 45, 30])[0]
            region = random.choice(REGIONS)
            
            # Acquisition date spread across the 2-year window (some old, some recent)
            acq_days_ago = random.randint(30, days_history + 30)
            created_at = datetime.now(timezone.utc) - timedelta(days=acq_days_ago)

            customer_records.append({
                "id": c_id,
                "name": name,
                "email": email,
                "segment": segment,
                "region": region,
                "created_at": created_at,
            })
            c_idx += 1

        for c in customer_records:
            await db.execute(
                text("""
                INSERT INTO analytics_customers (id, name, email, segment, region, country, created_at)
                VALUES (:id, :name, :email, :segment, :region, 'USA', :created_at)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    segment = EXCLUDED.segment,
                    region = EXCLUDED.region;
                """),
                c
            )
        await db.commit()

        # Categorize customer IDs by segment for weighted purchasing behavior
        ent_customers = [c["id"] for c in customer_records if c["segment"] == "Enterprise"]
        mid_customers = [c["id"] for c in customer_records if c["segment"] == "Mid-Market"]
        smb_customers = [c["id"] for c in customer_records if c["segment"] == "SMB"]
        all_customers = [c["id"] for c in customer_records]

        # 3. Generate Orders across 730 days (2 Full Years)
        logger.info(f"Generating orders and daily KPIs for past {days_history} days...")
        today = date.today()
        
        all_orders_to_insert = []
        daily_kpis_to_insert = []
        order_counter = 1

        for day_offset in range(days_history, -1, -1):
            order_date = today - timedelta(days=day_offset)
            
            # Growth curve: Earlier dates have fewer baseline orders (~7-10/day),
            # scaling up to ~12-16/day today (+30% YoY growth)
            progress_factor = (days_history - day_offset) / days_history # 0.0 at start, 1.0 today
            base_orders = int(8 + progress_factor * 5)
            
            # Seasonal modifiers:
            # Q4 Surge (Nov & Dec): +35%
            # Summer dip (July): -15%
            # Jan budget release: +15%
            month = order_date.month
            season_multiplier = 1.0
            if month in (11, 12):
                season_multiplier = 1.35
            elif month == 1:
                season_multiplier = 1.15
            elif month in (6, 7):
                season_multiplier = 0.88

            # Weekend modifier (lighter B2B volume)
            if order_date.weekday() in (5, 6):
                season_multiplier *= 0.55

            day_orders_count = max(3, int(random.randint(base_orders - 2, base_orders + 3) * season_multiplier))

            day_revenue = 0.0
            day_profit = 0.0

            for _ in range(day_orders_count):
                order_id = f"ORD-{order_counter:06d}"
                order_counter += 1

                # Weighted customer selection: Enterprise (35%), Mid-Market (45%), SMB (20%)
                segment_pick = random.choices(["Enterprise", "Mid-Market", "SMB"], weights=[35, 45, 20])[0]
                if segment_pick == "Enterprise":
                    cust_id = random.choice(ent_customers)
                    channel = random.choices(CHANNELS, weights=[50, 10, 25, 15])[0] # Direct/Partner favored
                    units = random.choices([2, 3, 5, 8, 12], weights=[35, 30, 20, 10, 5])[0]
                elif segment_pick == "Mid-Market":
                    cust_id = random.choice(mid_customers)
                    channel = random.choices(CHANNELS, weights=[25, 35, 20, 20])[0]
                    units = random.choices([1, 2, 3, 4], weights=[45, 35, 15, 5])[0]
                else:
                    cust_id = random.choice(smb_customers)
                    channel = random.choices(CHANNELS, weights=[10, 60, 10, 20])[0] # Online favored
                    units = random.choices([1, 2], weights=[80, 20])[0]

                prod = random.choice(PRODUCTS)
                unit_price = prod[4]
                unit_cost = prod[5]
                total_amount = round(float(units * unit_price), 2)
                profit = round(float(units * (unit_price - unit_cost)), 2)
                region = random.choice(REGIONS)

                day_revenue += total_amount
                day_profit += profit

                all_orders_to_insert.append({
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
                    "status": "Completed"
                })

            avg_val = round(day_revenue / max(1, day_orders_count), 2)
            margin_pct = round((day_profit / max(1.0, day_revenue)) * 100.0, 2)

            daily_kpis_to_insert.append({
                "date": order_date,
                "total_revenue": round(day_revenue, 2),
                "total_orders": day_orders_count,
                "avg_order_value": avg_val,
                "gross_profit": round(day_profit, 2),
                "profit_margin_pct": margin_pct,
            })

        # Batch Insert Orders in chunks of 500 for high performance
        logger.info(f"Inserting {len(all_orders_to_insert)} orders in fast batches...")
        batch_size = 500
        for i in range(0, len(all_orders_to_insert), batch_size):
            chunk = all_orders_to_insert[i:i + batch_size]
            await db.execute(
                text("""
                INSERT INTO analytics_orders (
                    id, customer_id, product_id, order_date, units, unit_price,
                    total_amount, profit, region, channel, status
                )
                VALUES (
                    :id, :customer_id, :product_id, :order_date, :units, :unit_price,
                    :total_amount, :profit, :region, :channel, :status
                )
                ON CONFLICT (id) DO NOTHING;
                """),
                chunk
            )
            if (i // batch_size) % 4 == 0 or i + batch_size >= len(all_orders_to_insert):
                logger.info(f"Progress: {min(i + batch_size, len(all_orders_to_insert))}/{len(all_orders_to_insert)} orders inserted...")
        await db.commit()

        # Batch Insert Daily KPIs
        logger.info(f"Inserting {len(daily_kpis_to_insert)} daily KPIs...")
        for i in range(0, len(daily_kpis_to_insert), batch_size):
            chunk = daily_kpis_to_insert[i:i + batch_size]
            await db.execute(
                text("""
                INSERT INTO analytics_daily_kpis (
                    date, total_revenue, total_orders, avg_order_value, gross_profit, profit_margin_pct
                )
                VALUES (:date, :total_revenue, :total_orders, :avg_order_value, :gross_profit, :profit_margin_pct)
                ON CONFLICT (date) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    total_orders = EXCLUDED.total_orders,
                    avg_order_value = EXCLUDED.avg_order_value,
                    gross_profit = EXCLUDED.gross_profit,
                    profit_margin_pct = EXCLUDED.profit_margin_pct;
                """),
                chunk
            )
        await db.commit()

        logger.info(f"Seeding complete! Successfully stored {len(all_orders_to_insert)} orders and {len(daily_kpis_to_insert)} days of KPIs spanning 2 full years.")


if __name__ == "__main__":
    force_run = "--force" in sys.argv or True
    asyncio.run(init_and_seed_analytics(force=force_run, days_history=730))
