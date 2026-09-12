import asyncio
import os
import sys

# Add the project root to sys.path so 'app' module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.integrations.bigquery.client import bigquery_client
from app.services.dashboard_service import dashboard_service
import httpx

async def run_tests():
    print("--- Test Suite Execution ---")
    bq = bigquery_client
    dataset = bq.full_dataset_path
    
    # Mocking today as Sept 12, 2026 for now
    
    # 1. Dashboard YTD sum via API
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as http_client:
        resp = await http_client.get("/api/v1/dashboards/executive?time_range=ytd")
        exec_ytd_data = resp.json()
        kpis = exec_ytd_data.get("kpis", [])
        dashboard_ytd_rev = next((k["value"] for k in kpis if k["id"] == "kpi-revenue"), None)
        print(f"1. Executive Dashboard YTD Revenue KPI: {dashboard_ytd_rev}")

    # 2. Manual BQ query for YTD
    query_ytd = f"SELECT SUM(total_amount) as sum_rev FROM `{dataset}.orders` WHERE order_date BETWEEN '2026-01-01' AND '2026-09-12'"
    res_ytd = await bq.execute_query(query_ytd)
    bq_ytd_rev = res_ytd["rows"][0]["sum_rev"]
    print(f"1. Manual BQ YTD Query Result (Jan 1 - Sep 12): {bq_ytd_rev}")

    # 3. Manual BQ query for FULL RANGE (daily_kpis sum)
    query_full = f"SELECT SUM(total_revenue) as sum_rev FROM `{dataset}.daily_kpis`"
    res_full = await bq.execute_query(query_full)
    bq_full_rev = res_full["rows"][0]["sum_rev"]
    print(f"2. Manual BQ Full Range Query Result (daily_kpis): {bq_full_rev}")

if __name__ == "__main__":
    asyncio.run(run_tests())
