"""Adapter interface - abstract EditorAdapter definition."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from contracts.models.editor_adapter import EditorCapabilities, EditorEvent, AdapterState
from contracts.models.completion_request import CompletionRequest, CompletionResult
from contracts.models.context_request import ContextQuery, ContextResult


class EditorAdapter(ABC):
    """
    Abstract editor adapter interface.
    
    This defines the contract for any editor integration.
    First implementation: VSCodium extension (stage3/vscodium/).
    Future implementations could include: Zed extension, Neovim plugin, etc.
    """
    
    @abstractmethod
    def get_capabilities(self) -> EditorCapabilities:
        """
        Get editor capabilities.
        
        Returns:
            EditorCapabilities describing what this editor supports
        """
        pass
    
    @abstractmethod
    def on_event(self, event: EditorEvent) -> None:
        """
        Handle editor event.
        
        Args:
            event: Editor event (cursor moved, file changed, etc.)
        """
        pass
    
    @abstractmethod
    async def request_completion(self, request: CompletionRequest) -> Optional[CompletionResult]:
        """
        Request code completion from intelligence server.
        
        Args:
            request: Completion request with cursor position and context
        
        Returns:
            Completion result or None if failed
        """
        pass
    
    @abstractmethod
    async def request_context(self, query: ContextQuery) -> Optional[ContextResult]:
        """
        Request context from intelligence server.
        
        Args:
            query: Context query
        
        Returns:
            Context result or None if failed
        """
        pass
    
    @abstractmethod
    def render_completion(self, completion: CompletionResult) -> None:
        """
        Render completion in editor.
        
        Args:
            completion: Completion to render (ghost text, inline suggestion, etc.)
        """
        pass
    
    @abstractmethod
    def render_diff(self, original: str, refactored: str, explanation: str) -> None:
        """
        Render diff view for refactoring.
        
        Args:
            original: Original code
            refactored: Refactored code
            explanation: Explanation of changes
        """
        pass
    
    @abstractmethod
    def render_hover(self, explanation: str, symbols: List[str]) -> None:
        """
        Render hover panel with explanation.
        
        Args:
            explanation: Explanation text
            symbols: Referenced symbols
        """
        pass
    
    @abstractmethod
    def update_status(self, state: AdapterState) -> None:
        """
        Update status bar with current state.
        
        Args:
            state: Current adapter state
        """
        pass
    
    @abstractmethod
    async def connect(self, base_url: str) -> bool:
        """
        Connect to intelligence server.
        
        Args:
            base_url: Intelligence server base URL
        
        Returns:
            True if connected successfully
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from intelligence server."""
        pass
    
    @abstractmethod
    def get_state(self) -> AdapterState:
        """
        Get current adapter state.
        
        Returns:
            Current state
        """
        pass


# Default implementation constants
INTELLIGENCE_API_URL = "http://localhost:3001"
DEFAULT_MAX_TOKENS = 256
DEFAULT_MAX_CONTEXT_TOKENS = 4096
