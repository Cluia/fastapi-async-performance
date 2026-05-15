"""Concurrent validation helpers (async I/O–friendly pattern)."""

from __future__ import annotations

import asyncio

from app.schemas.telemetry import SensorReading


async def validate_reading_async(reading: SensorReading) -> None:
    """
    Per-sample async checks after Pydantic validation.
    Uses asyncio.sleep(0) to yield to the event loop (useful under load).
    """
    await asyncio.sleep(0)
    if reading.sensor_id.startswith("blocked-"):
        raise ValueError(f"sensor_id blocked: {reading.sensor_id}")


async def validate_batch_concurrent(readings: list[SensorReading]) -> None:
    await asyncio.gather(*(validate_reading_async(r) for r in readings))
