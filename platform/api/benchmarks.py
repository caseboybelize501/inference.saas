from fastapi import APIRouter, HTTPException
from models.benchmark import BenchmarkResult
from learning.perf_store import PerfStore

router = APIRouter()

@router.get("/{cluster_id}/history")
def get_benchmark_history(cluster_id: str):
    history = PerfStore.get_benchmark_history(cluster_id)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    return history