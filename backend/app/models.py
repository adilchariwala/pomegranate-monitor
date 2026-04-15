from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


# ── Input ──────────────────────────────────────────────────────────────────

class SensorReadingCreate(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50)
    temperature: float = Field(..., ge=-40.0, le=85.0)
    humidity: float = Field(..., ge=0.0, le=100.0)
    soil_moisture: float = Field(..., ge=0.0, le=100.0)
    light_lux: float = Field(..., ge=0.0, le=200000.0)
    timestamp: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=100)

    @field_validator("sensor_id")
    @classmethod
    def validate_sensor_id(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError("sensor_id must contain only letters, numbers, and hyphens")
        return v

    @model_validator(mode="after")
    def fill_timestamp(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        return self


# ── Output ─────────────────────────────────────────────────────────────────

class SensorReadingResponse(BaseModel):
    id: str
    sensor_id: str
    temperature: float
    humidity: float
    soil_moisture: float
    light_lux: float
    timestamp: datetime
    location: Optional[str]


class SensorResponse(BaseModel):
    sensor_id: str
    location: Optional[str]
    registered_at: datetime
    last_seen: datetime


class StatValues(BaseModel):
    min: float
    max: float
    avg: float


class StatsResponse(BaseModel):
    sensor_id: str
    period_hours: int
    temperature: StatValues
    humidity: StatValues
    soil_moisture: StatValues
    light_lux: StatValues
    reading_count: int
    health_score: float


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict = {}


class HealthCheckResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


# ── Helpers ────────────────────────────────────────────────────────────────

def doc_to_reading(doc: dict) -> SensorReadingResponse:
    return SensorReadingResponse(
        id=str(doc["_id"]),
        sensor_id=doc["sensor_id"],
        temperature=doc["temperature"],
        humidity=doc["humidity"],
        soil_moisture=doc.get("soil_moisture", 0.0),
        light_lux=doc.get("light_lux", 0.0),
        timestamp=doc["timestamp"],
        location=doc.get("location"),
    )


def compute_health_score(
    temp_avg: float,
    humidity_avg: float,
    soil_avg: float,
    lux_avg: float,
) -> float:
    if 18 <= temp_avg <= 35:
        t_score = 100.0
    elif temp_avg < 18:
        t_score = max(0, 100 - (18 - temp_avg) * 10)
    else:
        t_score = max(0, 100 - (temp_avg - 35) * 10)

    if 40 <= humidity_avg <= 60:
        h_score = 100.0
    elif humidity_avg < 40:
        h_score = max(0, 100 - (40 - humidity_avg) * 3)
    else:
        h_score = max(0, 100 - (humidity_avg - 60) * 3)

    if 30 <= soil_avg <= 60:
        s_score = 100.0
    elif soil_avg < 30:
        s_score = max(0, 100 - (30 - soil_avg) * 4)
    else:
        s_score = max(0, 100 - (soil_avg - 60) * 4)

    l_score = min(100.0, (lux_avg / 10000.0) * 100)

    score = 0.30 * t_score + 0.20 * h_score + 0.25 * s_score + 0.25 * l_score
    return round(score, 1)
