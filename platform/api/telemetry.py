from fastapi import APIRouter, HTTPException
from models.telemetry import TelemetrySnapshot
from learning.perf_store import PerfStore
from config import Config

router = APIRouter()

@router.post("/ingest")
def ingest_telemetry(telemetry_data: list[TelemetrySnapshot], token: str = None):
    config = Config()
    if not config.validate_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    PerfStore.store_telemetry(telemetry_data)
    return {"received": True}

@router.get("/{cluster_id}/live")
def get_live_telemetry(cluster_id: str):
    telemetry = PerfStore.get_live_telemetry(cluster_id)
    if not telemetry:
        raise HTTPException(status_code=404, detail="Telemetry not found")
    return telemetry