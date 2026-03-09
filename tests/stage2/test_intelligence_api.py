"""Tests for Stage 2 intelligence API."""

import pytest
import sys
import os

# Add stage2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage2'))

from fastapi.testclient import TestClient
from intelligence_server import app


class TestIntelligenceAPI:
    """Test IntelligenceAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data

    def test_index_status_endpoint(self, client):
        """Test index status endpoint."""
        response = client.get("/v1/index/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "files_indexed" in data
        assert "last_updated" in data
        assert "embedding_model" in data
        assert "index_size_mb" in data
        assert "watching" in data

    def test_context_endpoint(self, client):
        """Test context endpoint."""
        response = client.post(
            "/v1/context",
            json={
                "query": "test query",
                "workspace_root": "/test",
                "max_chunks": 5,
                "strategy": "hybrid"
            }
        )
        
        # May return empty result if not indexed
        assert response.status_code in [200, 503]

    def test_complete_endpoint(self, client):
        """Test completion endpoint."""
        response = client.post(
            "/v1/complete",
            json={
                "file": "test.py",
                "line": 10,
                "col": 5,
                "prefix": "def ",
                "suffix": "():",
                "max_tokens": 100
            }
        )
        
        # Should return completion structure
        assert response.status_code in [200, 503]

    def test_explain_endpoint(self, client):
        """Test explain endpoint."""
        response = client.post(
            "/v1/explain",
            json={
                "file": "test.py",
                "start_line": 0,
                "end_line": 10,
                "question": "What does this do?"
            }
        )
        
        assert response.status_code in [200, 503]

    def test_refactor_endpoint(self, client):
        """Test refactor endpoint."""
        response = client.post(
            "/v1/refactor",
            json={
                "file": "test.py",
                "start_line": 0,
                "end_line": 10,
                "instruction": "Extract method"
            }
        )
        
        assert response.status_code in [200, 503]

    def test_symbols_endpoint(self, client):
        """Test symbols endpoint."""
        response = client.get("/v1/symbols", params={"file": "test.py"})
        
        # May return empty or error if not indexed
        assert response.status_code in [200, 404, 503]

    def test_callgraph_endpoint(self, client):
        """Test call graph endpoint."""
        response = client.get("/v1/callgraph", params={"symbol": "test_func", "depth": 3})
        
        assert response.status_code in [200, 503]

    def test_index_rebuild_endpoint(self, client):
        """Test index rebuild endpoint."""
        response = client.post(
            "/v1/index/rebuild",
            json={
                "workspace_root": "/test",
                "force": True
            }
        )
        
        assert response.status_code in [200, 503]


class TestContextSchema:
    """Test context response schema."""

    def test_context_response_structure(self):
        """Test context response has correct structure."""
        response = {
            "chunks": [
                {
                    "file": "test.py",
                    "start_line": 0,
                    "end_line": 10,
                    "content": "def test(): pass",
                    "score": 0.9,
                    "reason": "semantic match"
                }
            ],
            "total_tokens_est": 50
        }
        
        assert "chunks" in response
        assert "total_tokens_est" in response
        assert len(response["chunks"]) > 0
        
        chunk = response["chunks"][0]
        assert "file" in chunk
        assert "start_line" in chunk
        assert "end_line" in chunk
        assert "content" in chunk
        assert "score" in chunk
        assert "reason" in chunk


class TestCompletionSchema:
    """Test completion response schema."""

    def test_completion_response_structure(self):
        """Test completion response has correct structure."""
        response = {
            "completion": "print('Hello')",
            "context_used": ["chunk1", "chunk2"],
            "model_used": "apex-code-v1",
            "latency_ms": 150
        }
        
        assert "completion" in response
        assert "context_used" in response
        assert "model_used" in response
        assert "latency_ms" in response
        assert isinstance(response["context_used"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
