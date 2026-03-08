# IOAS — Inference Optimization as a Service
## Deploy the Agent (customer side — 2 commands)
docker pull ioas/agent:latest
docker run -d --gpus all --pid=host
  -v /proc:/host/proc:ro
  -e IOAS_TOKEN=your_token
  -e IOAS_ENDPOINT=https://api.ioas.io
  ioas/agent:latest
## That's it. The agent discovers everything else automatically.
## Self-host the Platform
git clone + cp .env.example .env → fill POSTGRES_URL, REDIS_URL,
STRIPE_KEY, JWT_SECRET → docker-compose up -d
## API Quickstart
POST /api/optimizations/run { cluster_id, model_sha256 }
GET  /api/optimizations/:id/status → { stage, progress, eta_s }
GET  /api/optimizations/:id/bundle → validated config to apply
## Billing
Metered by GPU-count × days active. Stripe usage records sent
hourly from telemetry_worker. Webhooks handle plan changes.