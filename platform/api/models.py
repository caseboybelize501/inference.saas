from fastapi import APIRouter, HTTPException
from models.model import ModelProfile
from learning.recommender import get_recommendations
from learning.perf_store import PerfStore

router = APIRouter()

@router.get("/catalog")
def get_model_catalog():
    catalog = PerfStore.get_model_catalog()
    return catalog

@router.get("/{sha256}/recommendations")
def get_model_recommendations(sha256: str):
    recommendations = get_recommendations(sha256)
    if not recommendations:
        raise HTTPException(status_code=404, detail="Recommendations not found")
    return recommendations