"""Pydantic output schemas for the REST API."""
from datetime import datetime

from pydantic import BaseModel


class ReadingOut(BaseModel):
    id: int
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    received_at: datetime

    class Config:
        from_attributes = True
