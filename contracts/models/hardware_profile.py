"""Hardware profile Pydantic models - Stage 1 output contract."""

from pydantic import BaseModel, Field
from typing import List, Optional


class GPU(BaseModel):
    """GPU hardware information."""
    id: str = Field(..., description="GPU identifier/name")
    vram: float = Field(..., description="Total VRAM in GB")
    cuda_version: Optional[str] = Field(None, description="CUDA version (NVIDIA only)")
    compute_cap: Optional[str] = Field(None, description="Compute capability")


class HardwareProfile(BaseModel):
    """Complete hardware profile for model selection."""
    gpus: List[GPU] = Field(..., description="List of detected GPUs")
    system_ram: float = Field(..., description="Total system RAM in GB")
    cuda_version: Optional[str] = Field(None, description="System CUDA version")
    llama_server_path: Optional[str] = Field(None, description="Path to llama-server binary")
    platform: str = Field(default="auto", description="Platform: cuda, rocm, metal, cpu")
