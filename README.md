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

### How to run

From the repository root, install dev dependencies and run pytest:

```bash
pip install -r requirements-dev.txt
pytest -v
```

**With coverage** (same gate as CI: minimum **92%** on `app/`; the suite currently reaches **100%** line coverage):

```bash
pytest -v --cov=app --cov-report=term-missing --cov-fail-under=92
```

**HTML coverage report** (open `htmlcov/index.html` in a browser after generation):

```bash
pytest --cov=app --cov-report=html
```

On **Windows (PowerShell)**:

```powershell
cd C:\Users\julio\StudioProjects\fastapi-async-performance
pip install -r requirements-dev.txt
pytest -v --cov=app --cov-report=term-missing --cov-fail-under=92
```

**Style checks** (also run in CI):

```bash
black --check app tests
flake8 app tests
```

### How to visualize

| Where | What you see |
|-------|----------------|
| **Terminal** | `pytest -v` lists each `test_*` with PASSED/FAILED and tracebacks on failure. |
| **IDE (Cursor / VS Code)** | Open the `tests/` folder; use *Run Test* / Testing sidebar on any `test_…` function. |
| **`htmlcov/index.html`** | Line-by-line coverage after `pytest --cov=app --cov-report=html`. |
| **GitHub Actions** | Tab *Actions* on the repo: each run shows lint, pytest+coverage, and Docker build. |

### Test modules (what runs)

| File | What is exercised |
|------|-------------------|
| `tests/conftest.py` | Shared **`async_client`** fixture: httpx `AsyncClient` + `ASGITransport` against the real FastAPI app. |
| `tests/test_routes_health.py` | `GET /health`, `GET /openapi.json` (paths exist), `GET /docs` (Swagger UI loads). |
| `tests/test_routes_telemetry.py` | `POST /telemetry/ingest`: 202 shape, boundary metrics, `recorded_at`, whitespace on `source`, many **422** bodies (missing fields, extra keys, bad metric, out-of-range values, >2000 readings), **2000** readings accepted, `blocked-*` sensor + detail, invalid JSON body, **24 concurrent** ingests. |
| `tests/test_models_telemetry.py` | Pydantic **`SensorReading` / `TelemetryIngest`** without HTTP (unknown metric, long `source`, `sensor_id` length 128 vs 129). |
| `tests/test_schema_value_branches.py` | **`value_plausible`** branches: temperature, humidity, pressure, `custom` out of range. |
| `tests/test_validation_service.py` | **`validate_reading_async`** / **`validate_batch_concurrent`** (success, blocked id, batch of 50, error propagation). |
| `tests/test_lifespan_starlette.py` | ASGI **lifespan** startup/shutdown via Starlette **`TestClient`** (not only httpx async transport). |

### What problems the suite guards against

| Risk area | How tests help |
|-----------|----------------|
| **HTTP contract regressions** | Wrong status codes or JSON shape on `/health` and `/telemetry/ingest` (e.g. 202 vs 422). |
| **Bad or malicious payloads** | Extra JSON keys, empty `source`, empty `readings`, unknown `metric`, numeric out of domain, oversized batches. |
| **Async pipeline bugs** | `blocked-*` rule after Pydantic; `asyncio.gather` still raises when one row fails; concurrent posts do not trivially break the handler. |
| **Schema drift** | Direct model tests catch tightening/loosening of Pydantic rules before they hit integration. |
| **OpenAPI / docs broken** | Ensures the app still exposes spec and UI (common regression after router refactors). |
| **Lifespan / startup hooks** | `TestClient` context runs lifespan—catches mistakes in `lifespan` that async-only client might not exercise. |
| **Untested new code** | **`--cov-fail-under=92`** fails CI if coverage drops below the threshold. |

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
