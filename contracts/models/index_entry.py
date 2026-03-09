"""Index entry Pydantic models - Stage 2 storage contract."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FileEntry(BaseModel):
    """Indexed file metadata."""
    id: str = Field(..., description="Unique ID: workspace_hash + relative_path")
    path: str = Field(..., description="Relative file path")
    workspace_root: str = Field(..., description="Workspace root directory")
    hash: str = Field(..., description="Content hash for dedup")
    language: str = Field(..., description="Programming language")
    indexed_at: datetime = Field(..., description="Last index timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")


class SymbolEntry(BaseModel):
    """Symbol extracted from file."""
    id: str = Field(..., description="Unique symbol ID")
    file_id: str = Field(..., description="Parent file ID")
    name: str = Field(..., description="Symbol name")
    kind: str = Field(..., description="Symbol kind: function, class, import, etc.")
    line_start: int = Field(..., description="Start line number")
    line_end: int = Field(..., description="End line number")
    col_start: int = Field(..., description="Start column")
    col_end: int = Field(..., description="End column")
    docstring: Optional[str] = Field(None, description="Docstring content")
    signature: Optional[str] = Field(None, description="Function/class signature")


class CallEntry(BaseModel):
    """Call relationship between symbols."""
    id: str = Field(..., description="Unique call ID")
    caller_symbol_id: str = Field(..., description="Caller symbol ID")
    callee_symbol_id: str = Field(..., description="Callee symbol ID")
    call_site_line: int = Field(..., description="Line number of call site")
    call_site_col: int = Field(..., description="Column of call site")


class ChunkEntry(BaseModel):
    """Text chunk for embedding."""
    id: str = Field(..., description="Unique chunk ID")
    file_id: str = Field(..., description="Parent file ID")
    line_start: int = Field(..., description="Start line")
    line_end: int = Field(..., description="End line")
    content: str = Field(..., description="Chunk text content")
    embedding_index: Optional[str] = Field(None, description="Reference to hnswlib index")
