"""Unit tests for async validation service."""

from __future__ import annotations

import pytest

from app.schemas.telemetry import SensorReading
from app.services.validation import validate_batch_concurrent, validate_reading_async


@pytest.mark.asyncio
async def test_validate_reading_async_passes() -> None:
    r = SensorReading.model_validate({"sensor_id": "ok-1", "metric": "custom", "value": 42.0})
    await validate_reading_async(r)


@pytest.mark.asyncio
async def test_validate_reading_async_blocked() -> None:
    r = SensorReading.model_validate({"sensor_id": "blocked-x", "metric": "custom", "value": 0.0})
    with pytest.raises(ValueError, match="blocked"):
        await validate_reading_async(r)


@pytest.mark.asyncio
async def test_validate_batch_concurrent_all_pass() -> None:
    readings = [
        SensorReading.model_validate({"sensor_id": f"n{i}", "metric": "custom", "value": float(i)})
        for i in range(50)
    ]
    await validate_batch_concurrent(readings)


@pytest.mark.asyncio
async def test_validate_batch_concurrent_propagates_error() -> None:
    readings = [
        SensorReading.model_validate({"sensor_id": "ok", "metric": "custom", "value": 0.0}),
        SensorReading.model_validate({"sensor_id": "blocked-z", "metric": "custom", "value": 0.0}),
    ]
    with pytest.raises(ValueError):
        await validate_batch_concurrent(readings)
