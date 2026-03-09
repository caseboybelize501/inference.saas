"""Model configuration Pydantic models - Stage 1 selection contract."""

from pydantic import BaseModel, Field
from typing import Optional, Literal


QuantLevel = Literal["Q4_0", "Q4_K_M", "Q5_0", "Q5_K_M", "Q6_K", "Q8_0", "F16", "F32"]


class ModelSpec(BaseModel):
    """Model specification for loading."""
    path: str = Field(..., description="Path to GGUF model file")
    quant: QuantLevel = Field(..., description="Quantization level")
    vram_required_gb: float = Field(..., description="VRAM required in GB")
    context_length: int = Field(default=4096, description="Max context length")
    family: Optional[str] = Field(None, description="Model family (llama, mistral, etc.)")
    size: Optional[str] = Field(None, description="Model size (7B, 13B, 70B, etc.)")


class VRAMBudget(BaseModel):
    """VRAM budget allocation."""
    total_vram_gb: float = Field(..., description="Total available VRAM")
    reserved_for_kv_gb: float = Field(2.0, description="Reserved for KV cache")
    reserved_for_overhead_gb: float = Field(1.5, description="System overhead buffer")
    available_for_model_gb: float = Field(..., description="Available for model weights")
