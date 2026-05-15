from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.routes.telemetry import router as telemetry_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="Async Telemetry Performance Lab",
    version="0.1.0",
    lifespan=lifespan,
    description="FastAPI + async validation for high-rate IoT-style telemetry (no database).",
)

app.include_router(telemetry_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
