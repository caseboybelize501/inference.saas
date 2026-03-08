from models.optimization import OptimizationConfig

def select_quantization_format(vram_budget, quality_floor):
    # Placeholder for quantization selection logic
    return {"quant_format": "Q8", "quant_level": 0, "vram_model_gb": vram_budget * 0.8}

def compute_vram_budget(free_vram, overhead=1.5):
    return free_vram - overhead

def score_quant_candidates(candidates, vram_fit, quality_score, tps_from_memory):
    # Placeholder for scoring quant candidates
    return sorted(candidates, key=lambda x: x['quality_score'] * tps_from_memory, reverse=True)