import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.dashboard_service import dashboard_service
from app.integrations.bigquery.client import bigquery_client

async def run_regression_tests():
    print("--- YTD Fix Regression Tests ---")
    bq = bigquery_client
    dataset = bq.full_dataset_path

    # Test 1: time_range="ytd" + end_date in a past year (2025-06-15)
    print("\\n1. Test: YTD with end_date=2025-06-15")
    ytd_2025 = await dashboard_service.get_executive_dashboard(time_range="ytd", end_date="2025-06-15")
    rev_2025 = next((k["value"] for k in ytd_2025.get("kpis", []) if k["id"] == "kpi-revenue"), None)
    
    manual_q1 = f"SELECT SUM(total_amount) as sum_rev FROM `{dataset}.orders` WHERE order_date >= '2025-01-01' AND order_date <= '2025-06-15'"
    res1 = await bq.execute_query(manual_q1)
    manual_rev_2025 = res1["rows"][0]["sum_rev"]
    
    print(f"Executive YTD Revenue on 2025-06-15: {rev_2025}")
    print(f"Manual YTD Revenue on 2025-06-15: {manual_rev_2025}")
    assert rev_2025 == manual_rev_2025, "Test 1 Failed!"
    print("-> Test 1 PASS")

    # Test 2: Leap year boundary (2024-02-29)
    print("\\n2. Test: YTD with end_date=2024-02-29 (Leap Year)")
    ytd_leap = await dashboard_service.get_executive_dashboard(time_range="ytd", end_date="2024-02-29")
    rev_leap = next((k["value"] for k in ytd_leap.get("kpis", []) if k["id"] == "kpi-revenue"), None)

    manual_q2 = f"SELECT SUM(total_amount) as sum_rev FROM `{dataset}.orders` WHERE order_date >= '2024-01-01' AND order_date <= '2024-02-29'"
    res2 = await bq.execute_query(manual_q2)
    manual_rev_leap = res2["rows"][0]["sum_rev"]

    print(f"Executive YTD Revenue on 2024-02-29: {rev_leap}")
    print(f"Manual YTD Revenue on 2024-02-29: {manual_rev_leap}")
    assert rev_leap == (manual_rev_leap or 0.0), "Test 2 Failed!"
    print("-> Test 2 PASS")

    # Test 3: Sales Dashboard regression
    print("\\n3. Test: Sales Dashboard YTD check")
    sales_ytd = await dashboard_service.get_sales_dashboard(time_range="ytd")
    sales_rev = next((k["value"] for k in sales_ytd.get("kpis", []) if k["id"] == "kpi-sales-revenue"), None)
    
    exec_ytd = await dashboard_service.get_executive_dashboard(time_range="ytd")
    exec_rev = next((k["value"] for k in exec_ytd.get("kpis", []) if k["id"] == "kpi-revenue"), None)

    print(f"Sales YTD Revenue: {sales_rev}")
    print(f"Executive YTD Revenue: {exec_rev}")
    assert sales_rev == exec_rev, "Test 3 Failed!"
    print("-> Test 3 PASS")

    # Test 4: Default load with NO end_date (2026-09-12 YTD)
    print("\\n4. Test: Default load with NO end_date")
    print(f"Executive YTD Revenue (No end_date): {exec_rev}")
    assert exec_rev == 9522700.0, f"Test 4 Failed! Expected 9522700.0, got {exec_rev}"
    print("-> Test 4 PASS")

if __name__ == "__main__":
    asyncio.run(run_regression_tests())
