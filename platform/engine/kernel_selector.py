from models.optimization import OptimizationConfig

def select_attention_kernel(compute_cap, model_arch):
    # Placeholder for kernel selection logic
    if compute_cap >= 8.9:
        return {"kernel": "FA3", "expected_tps_delta_pct": 20}
    elif compute_cap >= 8.0:
        return {"kernel": "FA2", "expected_tps_delta_pct": 15}
    else:
        return {"kernel": "torch SDPA", "expected_tps_delta_pct": 5}