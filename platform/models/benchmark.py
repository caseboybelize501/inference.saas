from pydantic import BaseModel
from typing import Optional

class BenchmarkResult(BaseModel):
    cluster_id: str
    model_sha256: str
    quant_format: Optional[str]
    quant_level: Optional[int]
    backend: Optional[str]
    attention_kernel: Optional[str]
    batch_size: Optional[int]
    context_len: Optional[int]
    decode_tps: float
    prefill_tps: Optional[float]
    ttft_ms: Optional[int]
    vram_used_gb: Optional[float]
    power_w: Optional[float]
    ppl_delta_vs_fp16: Optional[float]
    tenant_id: Optional[str]
    created_at: str