from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_telemetry_ingest_accepted() -> None:
    payload = {
        "source": "pytest",
        "readings": [
            {"sensor_id": "s1", "metric": "temperature_c", "value": 22.5},
            {"sensor_id": "s2", "metric": "humidity_pct", "value": 55.0},
        ],
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 202
    data = r.json()
    assert data["accepted"] == 2
    assert data["source"] == "pytest"


@pytest.mark.asyncio
async def test_telemetry_invalid_temperature_returns_422() -> None:
    payload = {
        "source": "pytest",
        "readings": [{"sensor_id": "s1", "metric": "temperature_c", "value": 200.0}],
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_telemetry_blocked_sensor_async_rule_returns_422() -> None:
    payload = {
        "source": "pytest",
        "readings": [{"sensor_id": "blocked-01", "metric": "custom", "value": 1.0}],
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/telemetry/ingest", json=payload)
    assert r.status_code == 422
