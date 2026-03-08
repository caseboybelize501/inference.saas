from pydantic import BaseModel
from typing import List

class GPU(BaseModel):
    id: str
    vram: float

class ClusterProfile(BaseModel):
    gpus: List[GPU]
    system_ram: float
    servers: List[int]
    models: dict