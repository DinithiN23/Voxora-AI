"""
Voxora Backend — Dashboard API Endpoints.

Provides the executive dashboard data including KPI scorecards
and chart widgets populated from BigQuery analytics.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.services.dashboard_service import dashboard_service
from app.schemas.dashboard import DashboardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("/executive", response_model=DashboardResponse)
async def get_executive_dashboard():
    """
    Fetch the full executive dashboard payload.
    Returns KPI scorecards and chart widgets with live BigQuery data.
    """
    try:
        data = await dashboard_service.get_executive_dashboard()
        return DashboardResponse(**data)
    except Exception as e:
        logger.error(f"Dashboard fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {str(e)}")
