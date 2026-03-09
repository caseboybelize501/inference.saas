"""Completion request Pydantic models - Stage 3 editor contract."""

from pydantic import BaseModel, Field
from typing import List, Optional


class CompletionRequest(BaseModel):
    """Code completion request from editor."""
    file: str = Field(..., description="Current file path")
    line: int = Field(..., description="Current line number")
    col: int = Field(..., description="Current column number")
    prefix: str = Field(..., description="Code before cursor")
    suffix: str = Field(..., description="Code after cursor")
    max_tokens: int = Field(default=256, description="Maximum tokens to generate")


class CompletionResult(BaseModel):
    """Code completion result."""
    completion: str = Field(..., description="Generated completion text")
    context_used: List[str] = Field(..., description="Chunk IDs used as context")
    model_used: str = Field(..., description="Model ID that generated completion")
    latency_ms: int = Field(..., description="Generation latency in milliseconds")
