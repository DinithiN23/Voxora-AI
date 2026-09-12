import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.dashboard_service import dashboard_service

async def run_tests():
    print("--- Test Suite Execution: Direct Service Call ---")
    
    try:
        data = await dashboard_service.get_executive_dashboard(time_range="ytd")
        kpis = data.get("kpis", [])
        dashboard_ytd_rev = next((k["value"] for k in kpis if k["id"] == "kpi-revenue"), None)
        print(f"1. Executive Dashboard YTD Revenue KPI (Direct): {dashboard_ytd_rev}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(run_tests())
