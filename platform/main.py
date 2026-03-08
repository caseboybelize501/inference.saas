from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import clusters, optimizations, telemetry, models, benchmarks, billing, auth
from workers import optimization_worker, validation_worker, telemetry_worker

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clusters.router, prefix="/api/clusters", tags=["clusters"])
app.include_router(optimizations.router, prefix="/api/optimizations", tags=["optimizations"])
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(benchmarks.router, prefix="/api/benchmarks", tags=["benchmarks"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)