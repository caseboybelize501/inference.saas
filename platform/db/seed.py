from learning.perf_store import store_anonymized_benchmark
from models.benchmark import BenchmarkResult

if __name__ == "__main__":
    benchmarks = [
        BenchmarkResult(cluster_id="cluster_1", model_sha256="model_sha256_1", quant_format="Q8", quant_level=0, backend="llama.cpp", attention_kernel="FA3", batch_size=16, context_len=4096, decode_tps=120, prefill_tps=100, ttft_ms=200, vram_used_gb=10, power_w=250, ppl_delta_vs_fp16=0.05, tenant_id=None, created_at="2023-10-01T12:00:00"),
        BenchmarkResult(cluster_id="cluster_2", model_sha256="model_sha256_2", quant_format="EXL2-6", quant_level=0, backend="ExLlamaV2", attention_kernel="FA2", batch_size=8, context_len=4096, decode_tps=140, prefill_tps=120, ttft_ms=220, vram_used_gb=12, power_w=300, ppl_delta_vs_fp16=0.03, tenant_id=None, created_at="2023-10-01T12:00:00"),
        BenchmarkResult(cluster_id="cluster_3", model_sha256="model_sha256_1", quant_format="Q4_K_M", quant_level=0, backend="llama.cpp", attention_kernel="xformers", batch_size=4, context_len=4096, decode_tps=95, prefill_tps=85, ttft_ms=250, vram_used_gb=8, power_w=200, ppl_delta_vs_fp16=0.08, tenant_id=None, created_at="2023-10-01T12:00:00"),
        BenchmarkResult(cluster_id="cluster_4", model_sha256="model_sha256_3", quant_format="EXL2-3.5", quant_level=0, backend="ExLlamaV2", attention_kernel="FA3", batch_size=16, context_len=8192, decode_tps=18, prefill_tps=15, ttft_ms=300, vram_used_gb=20, power_w=400, ppl_delta_vs_fp16=0.02, tenant_id=None, created_at="2023-10-01T12:00:00"),
        BenchmarkResult(cluster_id="cluster_5", model_sha256="model_sha256_4", quant_format="EXL2-4", quant_level=0, backend="vLLM+FA3", attention_kernel="FA3", batch_size=32, context_len=8192, decode_tps=22, prefill_tps=20, ttft_ms=350, vram_used_gb=24, power_w=500, ppl_delta_vs_fp16=0.01, tenant_id=None, created_at="2023-10-01T12:00:00")
    ]
    for benchmark in benchmarks:
        store_anonymized_benchmark(benchmark)
    print("Seeding complete.")