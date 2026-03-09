"""Context request Pydantic models - Stage 2 context packager contract."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ContextChunk(BaseModel):
    """Ranked context chunk."""
    file: str = Field(..., description="File path")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Relevance score")
    reason: str = Field(..., description="Reason for inclusion")


class ContextQuery(BaseModel):
    """Context query parameters."""
    query: str = Field(..., description="Search query")
    workspace_root: str = Field(..., description="Workspace root path")
    cursor_file: Optional[str] = Field(None, description="Current file path")
    cursor_line: Optional[int] = Field(None, description="Current line number")
    max_chunks: int = Field(default=10, description="Maximum chunks to return")
    strategy: Literal["semantic", "callgraph", "hybrid"] = Field(
        default="hybrid", description="Ranking strategy"
    )


class ContextResult(BaseModel):
    """Context result with ranked chunks."""
    chunks: List[ContextChunk] = Field(..., description="Ranked context chunks")
    total_tokens_est: int = Field(..., description="Estimated token count")
