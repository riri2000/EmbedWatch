"""Persisted sensor readings."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ReadingRecord(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), index=True, nullable=False)
    sensor_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(10), nullable=False)
    received_at = Column(DateTime, default=utcnow, index=True)
