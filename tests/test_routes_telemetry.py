"""HTTP contract for telemetry ingest (happy path + validation errors)."""

from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient

from app.schemas.telemetry import SensorReading


def _valid_batch(n: int = 3) -> dict:
    return {
        "source": "integration",
        "readings": [
            {"sensor_id": f"s{i}", "metric": "temperature_c", "value": float(i % 40)}
            for i in range(n)
        ],
    }


@pytest.mark.asyncio
async def test_ingest_202_response_shape(async_client: AsyncClient) -> None:
    payload = _valid_batch(2)
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 202
    data = r.json()
    assert data["accepted"] == 2
    assert data["source"] == "integration"
    assert "message" in data


@pytest.mark.asyncio
async def test_ingest_mixed_metrics_boundaries(async_client: AsyncClient) -> None:
    payload = {
        "source": "boundary-test",
        "readings": [
            {"sensor_id": "t-min", "metric": "temperature_c", "value": -80.0},
            {"sensor_id": "t-max", "metric": "temperature_c", "value": 80.0},
            {"sensor_id": "h0", "metric": "humidity_pct", "value": 0.0},
            {"sensor_id": "h100", "metric": "humidity_pct", "value": 100.0},
            {"sensor_id": "p80", "metric": "pressure_kpa", "value": 80.0},
            {"sensor_id": "p120", "metric": "pressure_kpa", "value": 120.0},
            {"sensor_id": "c", "metric": "custom", "value": 1e9},
        ],
    }
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 202
    assert r.json()["accepted"] == 7


@pytest.mark.asyncio
async def test_ingest_with_explicit_recorded_at(async_client: AsyncClient) -> None:
    ts = "2024-01-15T12:00:00+00:00"
    payload = {
        "source": "clock-sync",
        "readings": [{"sensor_id": "s1", "metric": "custom", "value": 0.0, "recorded_at": ts}],
    }
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 202


@pytest.mark.asyncio
async def test_ingest_strips_whitespace_source(async_client: AsyncClient) -> None:
    readings = [{"sensor_id": "a", "metric": "custom", "value": 0.0}]
    payload = {"source": "  trimmed  ", "readings": readings}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 202
    assert r.json()["source"] == "trimmed"


_READING = {"sensor_id": "a", "metric": "custom", "value": 0}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "desc"),
    [
        ({}, "empty body"),
        ({"source": "x"}, "missing readings"),
        ({"readings": []}, "missing source"),
        ({"source": "", "readings": [_READING]}, "empty source"),
        (
            {"source": "x", "readings": [{**_READING, "extra": 1}]},
            "extra field forbidden",
        ),
        (
            {
                "source": "x",
                "readings": [{"sensor_id": "a", "metric": "not-a-metric", "value": 0}],
            },
            "invalid metric literal",
        ),
    ],
)
async def test_ingest_validation_422(async_client: AsyncClient, payload: dict, desc: str) -> None:
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422, desc


@pytest.mark.asyncio
async def test_ingest_temperature_out_of_range_422(async_client: AsyncClient) -> None:
    r_item = {"sensor_id": "a", "metric": "temperature_c", "value": 80.01}
    payload = {"source": "x", "readings": [r_item]}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_humidity_out_of_range_422(async_client: AsyncClient) -> None:
    r_item = {"sensor_id": "a", "metric": "humidity_pct", "value": 100.01}
    payload = {"source": "x", "readings": [r_item]}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_pressure_out_of_range_422(async_client: AsyncClient) -> None:
    r_item = {"sensor_id": "a", "metric": "pressure_kpa", "value": 79.9}
    payload = {"source": "x", "readings": [r_item]}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_custom_magnitude_too_large_422(async_client: AsyncClient) -> None:
    r_item = {"sensor_id": "a", "metric": "custom", "value": 1e9 + 1}
    payload = {"source": "x", "readings": [r_item]}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_too_many_readings_422(async_client: AsyncClient) -> None:
    many = [{"sensor_id": f"id{i}", "metric": "custom", "value": 0.0} for i in range(2001)]
    payload = {"source": "x", "readings": many}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_ingest_max_batch_size_accepted(async_client: AsyncClient) -> None:
    cap = [{"sensor_id": f"id{i}", "metric": "custom", "value": 0.0} for i in range(2000)]
    payload = {"source": "max-batch", "readings": cap}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 202
    assert r.json()["accepted"] == 2000


@pytest.mark.asyncio
async def test_ingest_blocked_sensor_detail(async_client: AsyncClient) -> None:
    payload = {
        "source": "x",
        "readings": [{"sensor_id": "blocked-99", "metric": "custom", "value": 1.0}],
    }
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body
    assert "blocked" in str(body["detail"]).lower()


@pytest.mark.asyncio
async def test_ingest_invalid_json_returns_422(async_client: AsyncClient) -> None:
    headers = {"Content-Type": "application/json"}
    r = await async_client.post("/telemetry/ingest", content=b"not-json", headers=headers)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_concurrent_ingest_requests_all_succeed(async_client: AsyncClient) -> None:
    async def one(i: int) -> int:
        payload = _valid_batch(5)
        payload["source"] = f"conc-{i}"
        resp = await async_client.post("/telemetry/ingest", json=payload)
        return resp.status_code

    codes = await asyncio.gather(*(one(i) for i in range(24)))
    assert all(c == 202 for c in codes)


@pytest.mark.asyncio
async def test_recorded_at_defaults_to_utc_aware(async_client: AsyncClient) -> None:
    payload = {"source": "tz", "readings": [{"sensor_id": "a", "metric": "custom", "value": 0.0}]}
    r = await async_client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 202
    reading = SensorReading.model_validate(payload["readings"][0])
    assert reading.recorded_at.tzinfo is not None
