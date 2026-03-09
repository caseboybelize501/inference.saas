"""Editor adapter Pydantic models - Stage 3 swappable interface contract."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class EditorCapabilities(BaseModel):
    """Editor capability declaration."""
    supports_ghost_text: bool = Field(default=True, description="Inline completion support")
    supports_diff_view: bool = Field(default=True, description="Diff view support")
    supports_hover_panel: bool = Field(default=True, description="Hover explanation support")
    supports_status_bar: bool = Field(default=True, description="Status bar support")
    max_context_tokens: int = Field(default=8192, description="Maximum context tokens")


class EditorEvent(BaseModel):
    """Editor event from adapter."""
    event_type: Literal["cursor_moved", "file_changed", "selection_changed", "completion_requested"]
    file: Optional[str] = Field(None, description="Current file path")
    line: Optional[int] = Field(None, description="Current line number")
    col: Optional[int] = Field(None, description="Current column number")
    selection_start: Optional[int] = Field(None, description="Selection start line")
    selection_end: Optional[int] = Field(None, description="Selection end line")


class AdapterState(BaseModel):
    """Adapter connection state."""
    connected: bool = Field(..., description="Connected to intelligence server")
    model_loaded: bool = Field(..., description="Model is loaded and ready")
    index_ready: bool = Field(..., description="Index is built and ready")
    vram_used_gb: Optional[float] = Field(None, description="Current VRAM usage")
    last_error: Optional[str] = Field(None, description="Last error message")
