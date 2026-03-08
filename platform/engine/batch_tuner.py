from models.optimization import OptimizationConfig

def find_optimal_batch_size(memory_bandwidth):
    # Placeholder for batch size tuning logic
    batch_size = 1
    while True:
        if batch_size * memory_bandwidth > 0.8:
            return {"optimal_batch": batch_size, "tps_at_batch": 100, "bw_util_pct": 85}
        batch_size *= 2