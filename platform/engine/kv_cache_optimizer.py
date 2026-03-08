from models.optimization import OptimizationConfig

def select_kv_dtype_and_page_size(kv_budget, target_context):
    # Placeholder for KV dtype and page size selection logic
    return {"kv_dtype": "FP16", "page_size": 16, "chunked_prefill": True, "chunk_size": 4096}

def compute_kv_budget(free_vram, model_vram, overhead):
    return free_vram - model_vram - overhead