"""Tests for Stage 2 context packager."""

import pytest
import asyncio
import sys
import os

# Add stage2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage2'))

from context_packager import ContextPackager
from embedding_index import EmbeddingIndex
from call_graph import CallGraph
from contracts.models.context_request import ContextQuery


class TestContextPackager:
    """Test context packager functionality."""

    @pytest.fixture
    def packager(self):
        """Create context packager with mock dependencies."""
        with pytest.MonkeyPatch.context() as mp:
            # Mock hnswlib import
            mp.setattr("builtins.__import__", lambda name, *args: 
                __import__("unittest.mock").MagicMock() if name == "hnswlib" else __import__(name, *args))
            
            embedding_index = EmbeddingIndex()
            call_graph = CallGraph()
            
            yield ContextPackager(embedding_index, call_graph)

    def test_init(self, packager):
        """Test context packager initialization."""
        assert packager.embedding_index is not None
        assert packager.call_graph is not None
        assert packager.embedder is not None
        
        # Check ranking weights
        assert packager.semantic_weight == 0.6
        assert packager.callgraph_weight == 0.3
        assert packager.proximity_weight == 0.1

    def test_estimate_tokens(self, packager):
        """Test token estimation."""
        text = "Hello world this is a test"
        
        tokens = packager._estimate_tokens(text)
        
        # Rough estimate: 1 token ≈ 4 characters
        assert tokens > 0
        assert tokens <= len(text)

    def test_build_reason(self, packager):
        """Test reason building."""
        scores = {
            'semantic': 0.8,
            'callgraph': 0.5,
            'proximity': 0.2
        }
        
        reason = packager._build_reason(scores, "hybrid")
        
        assert "semantic" in reason
        assert "0.8" in reason

    def test_build_reason_empty(self, packager):
        """Test reason building with no scores."""
        scores = {
            'semantic': 0,
            'callgraph': 0,
            'proximity': 0
        }
        
        reason = packager._build_reason(scores, "hybrid")
        
        assert reason == "fallback"

    def test_assemble_prompt(self, packager):
        """Test prompt assembly."""
        from contracts.models.context_request import ContextChunk
        
        chunks = [
            ContextChunk(
                file="test.py",
                start_line=0,
                end_line=10,
                content="def hello():\n    print('Hello')",
                score=0.9,
                reason="semantic match"
            )
        ]
        
        prompt = packager.assemble_prompt(chunks, "Test query", max_tokens=1000)
        
        assert "Query:" in prompt
        assert "test.py" in prompt
        assert "def hello():" in prompt

    def test_assemble_prompt_max_tokens(self, packager):
        """Test prompt assembly respects max tokens."""
        from contracts.models.context_request import ContextChunk
        
        # Create many chunks
        chunks = [
            ContextChunk(
                file=f"test{i}.py",
                start_line=0,
                end_line=10,
                content="x" * 1000,  # Large content
                score=0.9,
                reason="test"
            )
            for i in range(10)
        ]
        
        prompt = packager.assemble_prompt(chunks, "Test", max_tokens=500)
        
        # Should not include all chunks due to token limit
        assert len(prompt) < sum(len(c.content) for c in chunks)

    @pytest.mark.asyncio
    async def test_rank_no_embedding(self, packager):
        """Test ranking when embedding fails."""
        query = ContextQuery(
            query="test query",
            workspace_root="/test",
            max_chunks=10,
            strategy="hybrid"
        )
        
        result = await packager.rank(query)
        
        # Should return empty result, not crash
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
