from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GridSnapshot(BaseModel):
    region: str = Field(..., description="Region or balancing authority, e.g. 'USA' or 'Texas'")
    timestamp: datetime = Field(..., description="UTC timestamp for the snapshot")
    demand_mw: Optional[float] = Field(
        None, description="Total system demand in MW"
    )
    generation_mw: Optional[float] = Field(
        None, description="Total generation in MW"
    )
    weather_alert: Optional[str] = Field(
        None, description="Active weather alert summary for the region"
    )
    disturbance_text: Optional[str] = Field(
        None,
        description="Free-text disturbance description (e.g. from OE-417 or other reports)",
    )


class DisturbanceEvent(BaseModel):
    region: str
    timestamp: datetime
    event_type: Optional[str] = None
    cause: Optional[str] = None
    severity: Optional[str] = None
    raw_text: Optional[str] = None

