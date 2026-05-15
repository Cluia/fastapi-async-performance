"""Unit tests for Pydantic telemetry models (no HTTP)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.telemetry import SensorReading, TelemetryIngest


def test_sensor_reading_rejects_unknown_metric() -> None:
    with pytest.raises(ValidationError):
        SensorReading.model_validate({"sensor_id": "a", "metric": "voltage", "value": 1.0})


def test_telemetry_ingest_rejects_source_too_long() -> None:
    long_source = "x" * 200
    reading = {"sensor_id": "a", "metric": "custom", "value": 0}
    with pytest.raises(ValidationError):
        TelemetryIngest.model_validate({"source": long_source, "readings": [reading]})


def test_sensor_id_max_length_boundary() -> None:
    sid = "a" * 128
    r = SensorReading.model_validate({"sensor_id": sid, "metric": "custom", "value": 0.0})
    assert r.sensor_id == sid


def test_sensor_id_over_max_length() -> None:
    sid = "a" * 129
    with pytest.raises(ValidationError):
        SensorReading.model_validate({"sensor_id": sid, "metric": "custom", "value": 0.0})
