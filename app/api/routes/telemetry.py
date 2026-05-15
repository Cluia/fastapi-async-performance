from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.telemetry import TelemetryAccepted, TelemetryIngest
from app.services.validation import validate_batch_concurrent

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED, response_model=TelemetryAccepted)
async def ingest_telemetry(body: TelemetryIngest) -> TelemetryAccepted:
    """
    Accept a batch of sensor readings.
    Pydantic validates the payload; asyncio.gather runs per-row async checks concurrently.
    """
    try:
        await validate_batch_concurrent(body.readings)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return TelemetryAccepted(accepted=len(body.readings), source=body.source)
