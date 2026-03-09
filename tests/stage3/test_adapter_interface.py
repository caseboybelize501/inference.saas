"""Tests for Stage 3 adapter interface."""

import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add stage3 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage3'))

from adapter_interface import EditorAdapter, EditorCapabilities, EditorEvent, AdapterState
from contracts.models.completion_request import CompletionRequest, CompletionResult
from contracts.models.context_request import ContextQuery, ContextResult


class MockEditorAdapter(EditorAdapter):
    """Mock implementation for testing."""

    def __init__(self):
        self.events = []
        self.completions = []
        self.status = AdapterState(
            connected=False,
            model_loaded=False,
            index_ready=False
        )

    def get_capabilities(self) -> EditorCapabilities:
        return EditorCapabilities()

    def on_event(self, event: EditorEvent) -> None:
        self.events.append(event)

    async def request_completion(self, request: CompletionRequest) -> CompletionResult:
        self.completions.append(request)
        return CompletionResult(
            completion="test",
            context_used=[],
            model_used="test",
            latency_ms=100
        )

    async def request_context(self, query: ContextQuery) -> ContextResult:
        return ContextResult(chunks=[], total_tokens_est=0)

    def render_completion(self, completion: CompletionResult) -> None:
        pass

    def render_diff(self, original: str, refactored: str, explanation: str) -> None:
        pass

    def render_hover(self, explanation: str, symbols: list) -> None:
        pass

    def update_status(self, state: AdapterState) -> None:
        self.status = state

    async def connect(self, base_url: str) -> bool:
        return True

    def disconnect(self) -> None:
        self.status.connected = False

    def get_state(self) -> AdapterState:
        return self.status


class TestEditorAdapter:
    """Test editor adapter interface."""

    @pytest.fixture
    def adapter(self):
        """Create mock adapter."""
        return MockEditorAdapter()

    def test_get_capabilities(self, adapter):
        """Test getting capabilities."""
        caps = adapter.get_capabilities()
        
        assert caps.supports_ghost_text is True
        assert caps.supports_diff_view is True
        assert caps.supports_hover_panel is True
        assert caps.supports_status_bar is True
        assert caps.max_context_tokens == 8192

    def test_on_event(self, adapter):
        """Test event handling."""
        event = EditorEvent(
            event_type="cursor_moved",
            file="test.py",
            line=10,
            col=5
        )
        
        adapter.on_event(event)
        
        assert len(adapter.events) == 1
        assert adapter.events[0].event_type == "cursor_moved"

    @pytest.mark.asyncio
    async def test_request_completion(self, adapter):
        """Test completion request."""
        request = CompletionRequest(
            file="test.py",
            line=10,
            col=5,
            prefix="def ",
            suffix="():",
            max_tokens=100
        )
        
        result = await adapter.request_completion(request)
        
        assert result is not None
        assert result.completion == "test"
        assert len(adapter.completions) == 1

    @pytest.mark.asyncio
    async def test_request_context(self, adapter):
        """Test context request."""
        query = ContextQuery(
            query="test",
            workspace_root="/test",
            max_chunks=5
        )
        
        result = await adapter.request_context(query)
        
        assert result is not None
        assert result.chunks == []

    def test_update_status(self, adapter):
        """Test status update."""
        state = AdapterState(
            connected=True,
            model_loaded=True,
            index_ready=True,
            vram_used_gb=10.5
        )
        
        adapter.update_status(state)
        
        assert adapter.status.connected is True
        assert adapter.status.model_loaded is True
        assert adapter.status.index_ready is True
        assert adapter.status.vram_used_gb == 10.5

    @pytest.mark.asyncio
    async def test_connect(self, adapter):
        """Test connection."""
        result = await adapter.connect("http://localhost:3001")
        
        assert result is True

    def test_disconnect(self, adapter):
        """Test disconnection."""
        adapter.disconnect()
        
        assert adapter.status.connected is False

    def test_get_state(self, adapter):
        """Test getting state."""
        state = adapter.get_state()
        
        assert isinstance(state, AdapterState)


class TestEditorCapabilities:
    """Test editor capabilities model."""

    def test_default_capabilities(self):
        """Test default capability values."""
        caps = EditorCapabilities()
        
        assert caps.supports_ghost_text is True
        assert caps.supports_diff_view is True
        assert caps.supports_hover_panel is True
        assert caps.supports_status_bar is True
        assert caps.max_context_tokens == 8192

    def test_custom_capabilities(self):
        """Test custom capability values."""
        caps = EditorCapabilities(
            supports_ghost_text=False,
            max_context_tokens=4096
        )
        
        assert caps.supports_ghost_text is False
        assert caps.max_context_tokens == 4096


class TestEditorEvent:
    """Test editor event model."""

    def test_cursor_moved_event(self):
        """Test cursor moved event."""
        event = EditorEvent(
            event_type="cursor_moved",
            file="test.py",
            line=10,
            col=5
        )
        
        assert event.event_type == "cursor_moved"
        assert event.file == "test.py"
        assert event.line == 10

    def test_completion_requested_event(self):
        """Test completion requested event."""
        event = EditorEvent(
            event_type="completion_requested",
            file="test.py",
            line=10,
            col=5
        )
        
        assert event.event_type == "completion_requested"


class TestAdapterState:
    """Test adapter state model."""

    def test_disconnected_state(self):
        """Test disconnected state."""
        state = AdapterState(
            connected=False,
            model_loaded=False,
            index_ready=False
        )
        
        assert state.connected is False
        assert state.model_loaded is False
        assert state.index_ready is False
        assert state.last_error is None

    def test_connected_state(self):
        """Test connected state."""
        state = AdapterState(
            connected=True,
            model_loaded=True,
            index_ready=True,
            vram_used_gb=12.5
        )
        
        assert state.connected is True
        assert state.model_loaded is True
        assert state.index_ready is True
        assert state.vram_used_gb == 12.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
