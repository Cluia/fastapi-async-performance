"""Branch coverage for value_plausible (Pydantic validators)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.telemetry import SensorReading


@pytest.mark.parametrize(
    ("metric", "value", "snippet"),
    [
        ("temperature_c", -80.1, "temperature_c"),
        ("humidity_pct", -0.01, "humidity_pct"),
        ("pressure_kpa", 120.01, "pressure_kpa"),
        ("custom", -(1e9 + 1), "custom"),
    ],
)
def test_sensor_value_out_of_range(metric: str, value: float, snippet: str) -> None:
    with pytest.raises(ValidationError) as exc:
        SensorReading.model_validate({"sensor_id": "x", "metric": metric, "value": value})
    assert snippet in str(exc.value).lower() or snippet.replace("_", " ") in str(exc.value).lower()
