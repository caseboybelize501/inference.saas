from fastapi import APIRouter, HTTPException
from models.cluster import ClusterProfile
from learning.perf_store import PerfStore
from learning.cross_tenant_store import CrossTenantStore
from config import Config

router = APIRouter()

@router.post("/register")
def register_cluster(cluster_profile: ClusterProfile):
    config = Config()
    cluster_id = PerfStore.register_cluster(cluster_profile)
    agent_token = config.generate_token(cluster_id)
    websocket_url = f"ws://{config.IOAS_ENDPOINT}/ws/{cluster_id}"
    return {"cluster_id": cluster_id, "agent_token": agent_token, "websocket_url": websocket_url}

@router.get("/{cluster_id}/profile")
def get_cluster_profile(cluster_id: str):
    profile = PerfStore.get_cluster_profile(cluster_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return profile