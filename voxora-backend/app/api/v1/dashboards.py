"""
Voxora Backend — Dashboard API Endpoints.

Provides live BigQuery-powered business intelligence dashboards:
- /api/v1/dashboards/executive  (Executive Overview)
- /api/v1/dashboards/sales      (Sales & Regional Performance)
- /api/v1/dashboards/customers  (Customer Intelligence & LTV)

Supports query parameters:
- time_range: "2y" (default), "1y", "90d", "30d", "2024", "2025", "2026", "all"
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD
- granularity: "daily", "monthly" (default), "yearly"
"""

import logging
from fastapi import APIRouter, HTTPException, Query

from app.services.dashboard_service import dashboard_service
from app.schemas.dashboard import DashboardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("/executive", response_model=DashboardResponse)
async def get_executive_dashboard(
    time_range: str = Query("2y", description="Time range or year: 2y, 1y, 90d, 30d, 2024, 2025, 2026"),
    start_date: str | None = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Custom end date (YYYY-MM-DD)"),
    granularity: str = Query("monthly", description="Trend granularity: daily, monthly, yearly"),
):
    """
    Fetch Executive Overview dashboard.
    Returns high-level business KPIs and corporate trajectory.
    """
    try:
        data = await dashboard_service.get_executive_dashboard(
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
        return DashboardResponse(**data)
    except Exception as e:
        logger.error(f"Executive dashboard fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load executive dashboard: {str(e)}")


@router.get("/sales", response_model=DashboardResponse)
async def get_sales_dashboard(
    time_range: str = Query("2y", description="Time range or year: 2y, 1y, 90d, 30d, 2024, 2025, 2026"),
    start_date: str | None = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Custom end date (YYYY-MM-DD)"),
    granularity: str = Query("monthly", description="Trend granularity: daily, monthly, yearly"),
):
    """
    Fetch Sales & Regional Performance dashboard.
    Returns territory comparisons, channel attributions, and volume metrics.
    """
    try:
        data = await dashboard_service.get_sales_dashboard(
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
        return DashboardResponse(**data)
    except Exception as e:
        logger.error(f"Sales dashboard fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load sales dashboard: {str(e)}")


@router.get("/customers", response_model=DashboardResponse)
async def get_customer_dashboard(
    time_range: str = Query("2y", description="Time range or year: 2y, 1y, 90d, 30d, 2024, 2025, 2026"),
    start_date: str | None = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Custom end date (YYYY-MM-DD)"),
    granularity: str = Query("monthly", description="Trend granularity: daily, monthly, yearly"),
):
    """
    Fetch Customer Intelligence & Lifetime Value dashboard.
    Returns tier segmentation (Enterprise vs Mid vs SMB), retention, and top accounts.
    """
    try:
        data = await dashboard_service.get_customer_dashboard(
            time_range=time_range,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
        return DashboardResponse(**data)
    except Exception as e:
        logger.error(f"Customer dashboard fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load customer dashboard: {str(e)}")
