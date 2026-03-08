from fastapi import APIRouter, HTTPException
from models.optimization import OptimizationBundle
from engine.optimization_bundle import assemble_bundle
from workers.optimization_worker import run_optimization
from workers.validation_worker import run_validation
from config import Config

router = APIRouter()

@router.post("/run")
def run_optimization_request(cluster_id: str, model_sha256: str, workload_type: str, context_target: int):
    config = Config()
    optimization_id = run_optimization(cluster_id, model_sha256, workload_type, context_target)
    return {"optimization_id": optimization_id, "estimated_duration_s": 3600}

@router.get("/{optimization_id}/status")
def get_optimization_status(optimization_id: str):
    status = run_validation.get_status(optimization_id)
    return {"stage": status['stage'], "progress": status['progress'], "eta_s": status['eta_s']}

@router.get("/{optimization_id}/bundle")
def get_optimization_bundle(optimization_id: str):
    bundle = assemble_bundle(optimization_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return bundle