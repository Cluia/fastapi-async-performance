from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


MetricName = Literal["temperature_c", "humidity_pct", "pressure_kpa", "custom"]


class SensorReading(BaseModel):
    """Single sensor sample (strict validation before any async work)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    sensor_id: str = Field(..., min_length=1, max_length=128, examples=["lab-temp-01"])
    metric: MetricName
    value: float
    recorded_at: datetime = Field(default_factory=_utc_now)

    @field_validator("value")
    @classmethod
    def value_plausible(cls, v: float, info: ValidationInfo) -> float:
        metric = info.data.get("metric") if info.data else None
        if metric == "temperature_c" and not -80.0 <= v <= 80.0:
            raise ValueError("temperature_c out of plausible range (-80..80)")
        if metric == "humidity_pct" and not 0.0 <= v <= 100.0:
            raise ValueError("humidity_pct must be 0..100")
        if metric == "pressure_kpa" and not 80.0 <= v <= 120.0:
            raise ValueError("pressure_kpa out of plausible range (80..120)")
        if metric == "custom" and abs(v) > 1e9:
            raise ValueError("custom metric magnitude too large")
        return v


class TelemetryIngest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source: str = Field(..., min_length=1, max_length=128, examples=["edge-gateway-a"])
    readings: list[SensorReading] = Field(..., min_length=1, max_length=2_000)


class TelemetryAccepted(BaseModel):
    accepted: int
    source: str
    message: str = "batch validated concurrently"
