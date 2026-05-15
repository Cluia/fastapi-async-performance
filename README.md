<div align="center">

# fastapi-async-performance

**Small, sharp demo: async FastAPI + strict Pydantic + Gunicorn/Uvicorn in Docker.**

[![CI](https://github.com/Cluia/fastapi-async-performance/actions/workflows/ci.yml/badge.svg)](https://github.com/Cluia/fastapi-async-performance/actions/workflows/ci.yml)

</div>

---

## What this is

A **telemetry-style ingestion API** (IoT-friendly naming) with:

- **100% async** route handlers (`async def`).
- **Pydantic v2** models with `extra="forbid"`, field bounds, and cross-field checks.
- **Concurrent per-row checks** via `asyncio.gather` (pattern you keep when later adding real I/O).
- **Production-shaped container**: **Gunicorn** + **Uvicorn workers** (multi-process), slim **Dockerfile** (no database client build chain).

No Redis, Postgres, or Celery—this repo is intentionally **atomic** so reviewers can read it in one sitting.

---

## Quick start

### Local (venv)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

### Docker Compose

```bash
docker compose up --build
```

Same URLs on port **8000**.

---

## API sketch

`POST /telemetry/ingest` accepts JSON like:

```json
{
  "source": "edge-gateway-a",
  "readings": [
    { "sensor_id": "lab-temp-01", "metric": "temperature_c", "value": 21.4 },
    { "sensor_id": "lab-hum-02", "metric": "humidity_pct", "value": 48.2 }
  ]
}
```

Response **202** with `accepted` count when both Pydantic validation and async checks pass.

`metric` is one of: `temperature_c`, `humidity_pct`, `pressure_kpa`, `custom` (see `app/schemas/telemetry.py`).

---

## Why Gunicorn + Uvicorn here

Same pattern as larger Python API services: **Gunicorn** manages worker processes; each worker runs **Uvicorn**’s ASGI stack so `async def` endpoints and `asyncio` stay first-class. This image is a reusable baseline for other micro-repos.

---

## Testing

The suite is split by concern:

| Module | Focus |
|--------|--------|
| `test_routes_health.py` | `/health`, `/openapi.json`, `/docs` |
| `test_routes_telemetry.py` | HTTP contract for ingest: happy paths, 422 cases, invalid JSON, max batch (2000), concurrency |
| `test_models_telemetry.py` | Pydantic models without HTTP |
| `test_schema_value_branches.py` | Validator branches per metric type |
| `test_validation_service.py` | `asyncio.gather` validation service |
| `test_lifespan_starlette.py` | ASGI lifespan via Starlette `TestClient` |
| `conftest.py` | Shared `async_client` fixture (httpx async) |

**Coverage gate (CI + local):** `pytest` runs with `--cov=app --cov-fail-under=92` (currently **100%** line coverage on `app/`).

```bash
pip install -r requirements-dev.txt
pytest -v --cov=app --cov-report=term-missing --cov-fail-under=92
```

---

## Development

| Command | Purpose |
|---------|---------|
| `pytest -v` | Full test suite |
| `pytest -v --cov=app --cov-fail-under=92` | Tests + coverage gate |
| `black --check app tests` | Format check |
| `flake8 app tests` | Lint |

---

## Relation to other work

This repository was bootstrapped as a **focused slice** of patterns used in larger “log pipeline” style projects: FastAPI layout, Docker healthcheck, GitHub Actions (lint + test + image build), and English README—**without** queue or persistence complexity.

---

## License

Add a license file when you publish (e.g. MIT).
