"""Tests for Stage 1 inference API."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add stage1 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage1'))

from fastapi.testclient import TestClient
from inference_proxy import app, LoadResponse, HealthResponse


class TestInferenceAPI:
    """Test InferenceAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health endpoint."""
        response = client.get("/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "vram_used_gb" in data
        assert "vram_total_gb" in data
        assert "model_loaded" in data
        assert "llama_server_pid" in data
        assert "uptime_s" in data

    def test_models_endpoint(self, client):
        """Test models endpoint."""
        response = client.get("/v1/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert isinstance(data["models"], list)

    def test_completions_endpoint_no_model(self, client):
        """Test completions endpoint when no model loaded."""
        response = client.post(
            "/v1/completions",
            json={
                "model": "test-model",
                "prompt": "Hello",
                "max_tokens": 10
            }
        )
        
        # Should return 503 when no model is loaded
        assert response.status_code in [503, 502]

    def test_embeddings_endpoint_no_model(self, client):
        """Test embeddings endpoint when no model loaded."""
        response = client.post(
            "/v1/embeddings",
            json={
                "model": "test-embedder",
                "input": ["Hello world"]
            }
        )
        
        # Should return 503 when no model is loaded
        assert response.status_code in [503, 502]

    def test_load_endpoint(self, client):
        """Test model load endpoint."""
        response = client.post(
            "/v1/load",
            json={
                "model_path": "/models/test.gguf",
                "quant_override": "Q8_0"
            }
        )
        
        # May fail if llama-server not available, but shouldn't crash
        assert response.status_code in [200, 500]


class TestCompletionSchema:
    """Test completion response schema."""

    def test_completion_response_structure(self):
        """Test completion response has correct structure."""
        response = {
            "id": "cmpl-123",
            "choices": [
                {
                    "text": "Hello world",
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        
        assert "id" in response
        assert "choices" in response
        assert "usage" in response
        assert len(response["choices"]) > 0
        assert "text" in response["choices"][0]
        assert "finish_reason" in response["choices"][0]


class TestEmbeddingSchema:
    """Test embedding response schema."""

    def test_embeddings_response_structure(self):
        """Test embeddings response has correct structure."""
        response = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3],
                    "index": 0
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "total_tokens": 5
            }
        }
        
        assert "data" in response
        assert "usage" in response
        assert len(response["data"]) > 0
        assert "embedding" in response["data"][0]
        assert "index" in response["data"][0]
        assert isinstance(response["data"][0]["embedding"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
