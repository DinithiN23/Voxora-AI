"""
Voxora Backend — Dashboard Schemas.

Pydantic models for executive dashboard KPI cards, chart widgets,
and the aggregate dashboard response payload.
"""

from pydantic import BaseModel, Field
from typing import Any


class KPICard(BaseModel):
    """A single dashboard KPI scorecard."""
    id: str
    label: str
    value: float | int
    formatted_value: str
    delta_pct: float | None = None
    delta_label: str | None = None
    trend: str = "neutral"  # "up", "down", "neutral"
    icon: str = ""
    color: str = "#10B981"


class ChartWidget(BaseModel):
    """A dashboard chart widget (bar, line, pie, area, table)."""
    id: str
    title: str
    chart_type: str  # "bar", "line", "pie", "area", "table"
    chart_config: dict[str, Any] = Field(default_factory=dict)
    data_payload: dict[str, Any] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """Full dashboard payload."""
    kpis: list[KPICard] = Field(default_factory=list)
    charts: list[ChartWidget] = Field(default_factory=list)
    last_updated: str | None = None
    data_range: str | None = None
