"""Intelligence server - FastAPI server exposing IntelligenceAPI."""

import asyncio
import time
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from contracts.models.context_request import ContextQuery, ContextResult, ContextChunk
from contracts.models.completion_request import CompletionRequest, CompletionResult
from contracts.models.index_entry import SymbolEntry
from stage2.ast_indexer import ASTIndexer
from stage2.call_graph import CallGraph
from stage2.embedding_index import EmbeddingIndex
from stage2.embedder import Embedder
from stage2.context_packager import ContextPackager
from stage2.file_watcher import FileWatcher


# Request/Response models matching intelligence_api.yaml
class ExplainRequest(BaseModel):
    file: str
    start_line: int
    end_line: int
    question: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str
    symbols_referenced: list[str]
    context_used: list[dict]


class RefactorRequest(BaseModel):
    file: str
    start_line: int
    end_line: int
    instruction: str


class RefactorResponse(BaseModel):
    original: str
    refactored: str
    diff: str
    explanation: str


class SymbolsResponse(BaseModel):
    symbols: list[dict]


class CallGraphResponse(BaseModel):
    callers: list[dict]
    callees: list[dict]
    depth_searched: int


class IndexStatusResponse(BaseModel):
    files_indexed: int
    last_updated: str
    embedding_model: str
    index_size_mb: float
    watching: bool


class RebuildRequest(BaseModel):
    workspace_root: str
    force: bool = False


class RebuildResponse(BaseModel):
    job_id: str
    estimated_s: int


# Global state
indexer: Optional[ASTIndexer] = None
call_graph: Optional[CallGraph] = None
embedding_index: Optional[EmbeddingIndex] = None
context_packager: Optional[ContextPackager] = None
file_watcher: Optional[FileWatcher] = None
embedder: Optional[Embedder] = None
workspace_root: Optional[str] = None
last_indexed: Optional[str] = None
indexing_job: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global indexer, call_graph, embedding_index, context_packager, file_watcher, embedder
    
    # Initialize components
    indexer = ASTIndexer()
    call_graph = CallGraph()
    embedding_index = EmbeddingIndex()
    embedder = Embedder()
    context_packager = ContextPackager(embedding_index, call_graph)
    
    yield
    
    # Cleanup
    if file_watcher:
        file_watcher.stop()


app = FastAPI(title="Intelligence API", lifespan=lifespan)


@app.post("/v1/context", response_model=ContextResult)
async def get_context(request: ContextQuery):
    """Get ranked context for query."""
    if not context_packager:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await context_packager.rank(request)
    return result


@app.post("/v1/complete", response_model=CompletionResult)
async def create_completion(request: CompletionRequest):
    """Generate code completion."""
    start_time = time.time()

    # Build context from current file and surroundings
    context_query = ContextQuery(
        query=request.prefix.split('\n')[-10:] if request.prefix else [],  # Last 10 lines as query
        workspace_root=workspace_root or "",
        cursor_file=request.file,
        cursor_line=request.line,
        max_chunks=5,
        strategy="hybrid"
    )

    context = await context_packager.rank(context_query) if context_packager else ContextResult(chunks=[], total_tokens_est=0)

    # Assemble prompt
    # In production, would call Stage 1 /v1/completions here

    latency_ms = int((time.time() - start_time) * 1000)

    return CompletionResult(
        completion="# TODO: Implementation requires Stage 1 integration",
        context_used=[c.file for c in context.chunks] if context and context.chunks else [],
        model_used="apex-code-v1",
        latency_ms=latency_ms
    )


@app.post("/v1/explain", response_model=ExplainResponse)
async def explain_code(request: ExplainRequest):
    """Explain code selection."""
    # Get symbols in range
    symbols = []
    if indexer:
        # Would query symbols in the specified range
        pass
    
    # Build explanation
    # In production, would call Stage 1 /v1/completions with context
    
    return ExplainResponse(
        explanation="Explanation requires Stage 1 integration",
        symbols_referenced=[s['name'] for s in symbols] if symbols else [],
        context_used=[]
    )


@app.post("/v1/refactor", response_model=RefactorResponse)
async def refactor_code(request: RefactorRequest):
    """Refactor code with instruction."""
    # Get original code
    # In production, would read from file and call Stage 1
    
    return RefactorResponse(
        original="# Original code",
        refactored="# Refactored code",
        diff="--- original\n+++ refactored\n@@ -1 +1 @@\n-# Original\n+# Refactored",
        explanation="Refactoring requires Stage 1 integration"
    )


@app.get("/v1/symbols", response_model=SymbolsResponse)
async def list_symbols(file: str = Query(...)):
    """List symbols in file."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")
    
    # Create file ID
    import hashlib
    workspace_hash = hashlib.sha256((workspace_root or "").encode()).hexdigest()[:16]
    file_id = f"{workspace_hash}:{file}"
    
    symbols = indexer.get_symbols(file_id)
    
    return SymbolsResponse(
        symbols=[
            {
                "name": s.name,
                "kind": s.kind,
                "file": file,
                "line": s.line_start,
                "col": s.col_start,
                "docstring": s.docstring
            }
            for s in symbols
        ]
    )


@app.get("/v1/callgraph", response_model=CallGraphResponse)
async def get_callgraph(symbol: str = Query(...), depth: int = Query(default=3)):
    """Get call graph for symbol."""
    if not call_graph:
        raise HTTPException(status_code=503, detail="Call graph not initialized")
    
    # Find symbol by name (simplified - would use proper lookup)
    # For now, return empty result
    return CallGraphResponse(
        callers=[],
        callees=[],
        depth_searched=depth
    )


@app.get("/v1/index/status", response_model=IndexStatusResponse)
async def get_index_status():
    """Get index status."""
    global last_indexed, workspace_root
    
    files_indexed = 0
    index_size_mb = 0
    
    if indexer:
        # Count files in database
        import sqlite3
        try:
            conn = sqlite3.connect(indexer.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files")
            files_indexed = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pass
    
    if embedding_index:
        index_size_mb = embedding_index.size() * 384 * 4 / (1024 * 1024)  # Estimate
    
    return IndexStatusResponse(
        files_indexed=files_indexed,
        last_updated=last_indexed or "",
        embedding_model="all-MiniLM-L6-v2",
        index_size_mb=index_size_mb,
        watching=file_watcher.watching if file_watcher else False
    )


@app.post("/v1/index/rebuild", response_model=RebuildResponse)
async def rebuild_index(request: RebuildRequest):
    """Rebuild index."""
    global workspace_root, last_indexed, indexing_job, file_watcher
    
    import uuid
    job_id = str(uuid.uuid4())
    
    # Estimate time (rough: 100 files per second)
    import os
    file_count = sum(1 for _ in os.walk(request.workspace_root) for f in _[2] if f.endswith('.py'))
    estimated_s = max(10, file_count // 100)
    
    # Start indexing in background
    async def do_index():
        global last_indexed, file_watcher
        
        workspace_root = request.workspace_root
        
        # Index files
        if indexer:
            count = indexer.scan(workspace_root)
            print(f"Indexed {count} files")
        
        # Build call graph
        if call_graph:
            edges = call_graph.build()
            print(f"Built call graph with {edges} edges")
        
        # Embed chunks
        if indexer and embedder and embedding_index:
            chunks = indexer.get_all_chunks()
            embeddings = embedder.embed_chunks(chunks)
            embedding_index.build(embeddings)
            embedding_index.save()
            print(f"Embedded {len(embeddings)} chunks")
        
        last_indexed = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Start file watcher
        if indexer and not file_watcher:
            file_watcher = FileWatcher(indexer, workspace_root)
            file_watcher.start()
    
    indexing_job = asyncio.create_task(do_index())
    
    return RebuildResponse(
        job_id=job_id,
        estimated_s=estimated_s
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy" if indexer else "unhealthy",
        "indexer": indexer is not None,
        "call_graph": call_graph is not None,
        "embedding_index": embedding_index is not None
    }
