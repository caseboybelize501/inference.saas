"""Shared port configuration for all stages."""

# Stage 1: Inference Runtime
STAGE1_PORT = 3000
STAGE1_HOST = "127.0.0.1"

# Stage 2: Codebase Intelligence
STAGE2_PORT = 3001
STAGE2_HOST = "127.0.0.1"

# llama-server (internal only - not exposed)
LLAMA_SERVER_PORT = 8080
LLAMA_SERVER_HOST = "127.0.0.1"

# API URLs
INFERENCE_API_URL = f"http://localhost:{STAGE1_PORT}"
INTELLIGENCE_API_URL = f"http://localhost:{STAGE2_PORT}"
