from pydantic import BaseModel
from typing import List

class GPUUtilization(BaseModel):
    id: str
    vram_used: float
    gpu_util: int
    memory_util: int
    power_usage: float

class TelemetrySnapshot(BaseModel):
    cluster_id: str
    gpus: List[GPUUtilization]