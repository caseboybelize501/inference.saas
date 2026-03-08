from pydantic import BaseModel
from typing import Dict

class OptimizationConfig(BaseModel):
    quant: Dict
    kernel: Dict
    kv: Dict
    batch: Dict

class OptimizationBundle(BaseModel):
    cluster_id: str
    model_sha256: str
    config: OptimizationConfig
    predicted_tps_gain_pct: float
    validation_required: bool