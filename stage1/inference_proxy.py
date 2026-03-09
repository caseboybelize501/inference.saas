"""Inference proxy - OpenAI-compatible FastAPI server."""

import asyncio
import time
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

from contracts.models.model_config import ModelSpec
from stage1.llama_server_manager import LlamaServerManager
from stage1.vram_monitor import VRAMMonitor


# Request/Response models matching inference_api.yaml
class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    stream: bool = False


class CompletionChoice(BaseModel):
    text: str
    finish_reason: str


class CompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CompletionResponse(BaseModel):
    id: str
    choices: list[CompletionChoice]
    usage: CompletionUsage


class EmbeddingsRequest(BaseModel):
    model: str
    input: list[str]


class EmbeddingData(BaseModel):
    embedding: list[float]
    index: int


class EmbeddingsResponse(BaseModel):
    data: list[EmbeddingData]
    usage: CompletionUsage


class ModelInfo(BaseModel):
    id: str
    path: str
    quant: str
    vram_gb: float
    loaded: bool


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class HealthResponse(BaseModel):
    status: str
    vram_used_gb: float
    vram_total_gb: float
    model_loaded: bool
    llama_server_pid: Optional[int]
    uptime_s: float


class LoadRequest(BaseModel):
    model_path: str
    quant_override: Optional[str] = None


class LoadResponse(BaseModel):
    loaded: bool
    vram_used_gb: float
    model_id: str


# Global state
server_manager: Optional[LlamaServerManager] = None
vram_monitor: Optional[VRAMMonitor] = None
start_time: float = 0
current_model: Optional[ModelSpec] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global server_manager, vram_monitor, start_time
    
    server_manager = LlamaServerManager()
    vram_monitor = VRAMMonitor()
    start_time = time.time()
    
    yield
    
    # Cleanup
    if server_manager:
        server_manager.stop()
    if vram_monitor:
        vram_monitor.shutdown()


app = FastAPI(title="Inference API", lifespan=lifespan)


@app.post("/v1/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """Generate completion - forwards to llama-server."""
    if not server_manager or not server_manager.process:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if request.stream:
        return StreamingResponse(
            _stream_completion(request),
            media_type="text/event-stream"
        )
    
    # Non-streaming request
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"http://127.0.0.1:{server_manager.port}/v1/completions",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "stream": False
                }
            )
            response.raise_for_status()
            return CompletionResponse(**response.json())
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")


async def _stream_completion(request: CompletionRequest) -> AsyncGenerator[str, None]:
    """Stream completion from llama-server."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream(
                "POST",
                f"http://127.0.0.1:{server_manager.port}/v1/completions",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield f"{line}\n\n"
        except httpx.HTTPError:
            yield "data: [DONE]\n\n"


@app.post("/v1/embeddings", response_model=EmbeddingsResponse)
async def create_embeddings(request: EmbeddingsRequest):
    """Generate embeddings - forwards to llama-server."""
    if not server_manager or not server_manager.process:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"http://127.0.0.1:{server_manager.port}/v1/embeddings",
                json={
                    "model": request.model,
                    "input": request.input
                }
            )
            response.raise_for_status()
            return EmbeddingsResponse(**response.json())
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")


@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """List available models."""
    models = []
    if current_model:
        models.append(ModelInfo(
            id=current_model.path.split("/")[-1],
            path=current_model.path,
            quant=current_model.quant or "unknown",
            vram_gb=current_model.vram_required_gb,
            loaded=True
        ))
    return ModelsResponse(models=models)


@app.get("/v1/health", response_model=HealthResponse)
async def get_health():
    """Get server health status."""
    global start_time
    
    uptime = time.time() - start_time if start_time else 0
    server_status = server_manager.get_status() if server_manager else {"running": False}
    
    vram_data = vram_monitor.get_usage() if vram_monitor else {"vram_used": 0, "vram_total": 0}
    
    return HealthResponse(
        status="healthy" if server_status.get("running") else "unhealthy",
        vram_used_gb=vram_data.get("vram_used", 0),
        vram_total_gb=vram_data.get("vram_total", 0),
        model_loaded=server_status.get("running", False),
        llama_server_pid=server_status.get("pid"),
        uptime_s=uptime
    )


@app.post("/v1/load", response_model=LoadResponse)
async def load_model(request: LoadRequest):
    """Load a model."""
    global current_model
    
    if not server_manager:
        raise HTTPException(status_code=503, detail="Server not initialized")
    
    # Stop existing model if running
    if server_manager.process:
        server_manager.stop()
    
    # Create model spec
    model = ModelSpec(
        path=request.model_path,
        quant=request.quant_override or "Q8_0",
        vram_required_gb=0,  # Will be computed by manager
        context_length=4096
    )
    
    # Spawn server
    if server_manager.spawn(model):
        current_model = model
        vram_data = vram_monitor.get_usage() if vram_monitor else {"vram_used": 0}
        return LoadResponse(
            loaded=True,
            vram_used_gb=vram_data.get("vram_used", 0),
            model_id=request.model_path.split("/")[-1]
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to load model")
