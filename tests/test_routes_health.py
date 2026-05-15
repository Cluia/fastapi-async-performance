"""HTTP contract for health and root metadata."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(async_client: AsyncClient) -> None:
    r = await async_client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/json")
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_openapi_json_exposes_paths(async_client: AsyncClient) -> None:
    r = await async_client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["openapi"].startswith("3.")
    paths = spec["paths"]
    assert "/health" in paths
    assert "/telemetry/ingest" in paths


@pytest.mark.asyncio
async def test_docs_ui_available(async_client: AsyncClient) -> None:
    r = await async_client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower() or "openapi" in r.text.lower()
