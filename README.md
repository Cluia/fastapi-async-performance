<div align="center">

# fastapi-async-performance

**Async FastAPI demo: strict telemetry validation, Docker, and automated quality checks.**

[![CI](https://github.com/Cluia/fastapi-async-performance/actions/workflows/ci.yml/badge.svg)](https://github.com/Cluia/fastapi-async-performance/actions/workflows/ci.yml)

</div>

---

## Why this application exists

Edge devices and gateways (sensors, PLCs, IoT nodes) often send **bursts of readings** to a central service. Before those readings are stored, routed to analytics, or forwarded to a queue, something must **validate them quickly** and reject garbage early—without blocking the whole pipeline on a single slow row.

This project is a **small, self-contained API** that models that first hop:

- Accept a **batch of sensor readings** in one HTTP request.
- Apply **strict schema rules** (types, allowed metrics, plausible ranges, no unknown fields).
- Run **per-row checks concurrently** with `async/await`, so the handler stays responsive under load.

It deliberately **does not** include a database, Redis, or Celery. That keeps the repository easy to read in one sitting and isolates **“fast validation at the edge”** from distributed processing (covered in sibling portfolio repos such as a full log/telemetry pipeline).

**Typical use cases this demo represents**

| Scenario | What this API stands in for |
|----------|----------------------------|
| Factory / lab telemetry | Gateways posting temperature, humidity, or pressure samples. |
| Pre-ingest filter | A service that returns **202 Accepted** only when a batch is structurally valid. |
| Portfolio / interview piece | Proof of async FastAPI, Pydantic v2 discipline, Docker, pytest, and CI—not a production product by itself. |

---

## What is in the box

- **100% async** route handlers (`async def`).
- **Pydantic v2** models with `extra="forbid"`, field bounds, and cross-field checks.
- **Concurrent per-row validation** via `asyncio.gather` (ready to swap in real I/O later).
- **Docker Compose** with a healthcheck on `/health`.
- **GitHub Actions**: Black, Flake8, pytest with coverage gate, Docker image build.

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

On **Windows (PowerShell)** — from the repository root (the folder created by `git clone`):

```powershell
.\.venv\Scripts\Activate.ps1   # if you created a venv in Quick start
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
| **IDE** | Open the `tests/` folder; use *Run Test* / Testing sidebar on any `test_…` function. |
| **`htmlcov/index.html`** | Line-by-line coverage after `pytest --cov=app --cov-report=html`. |
| **GitHub Actions** | Tab *Actions* on the repo: each run shows lint, pytest+coverage, and Docker build. |

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

This repository is a **focused slice** of patterns used in larger “log pipeline” style projects: FastAPI layout, Docker healthcheck, GitHub Actions (lint + test + image build)—**without** queue or persistence complexity.

