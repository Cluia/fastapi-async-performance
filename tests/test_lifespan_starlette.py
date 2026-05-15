"""Sync Starlette TestClient exercises ASGI lifespan (startup/shutdown hooks)."""

from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app


def test_lifespan_and_health_via_test_client() -> None:
    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
