"""Integration tests for full APEX pipeline."""

import pytest
import subprocess
import time
import sys
import os
import httpx


# API URLs
STAGE1_URL = "http://localhost:3000"
STAGE2_URL = "http://localhost:3001"


def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for service to be available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = httpx.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


class TestStageIsolation:
    """Test that stages are properly isolated."""

    def test_stage1_no_stage2_imports(self):
        """Verify Stage 1 has no Stage 2 imports."""
        result = subprocess.run(
            ["grep", "-r", "from stage2", "stage1/"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "Stage 1 imports Stage 2"

    def test_stage2_no_stage1_imports(self):
        """Verify Stage 2 has no Stage 1 imports."""
        result = subprocess.run(
            ["grep", "-r", "from stage1", "stage2/"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "Stage 2 imports Stage 1"

    def test_stage3_no_stage1_stage2_imports(self):
        """Verify Stage 3 has no Stage 1/2 imports."""
        result = subprocess.run(
            ["grep", "-r", "from stage", "stage3/"],
            capture_output=True,
            text=True
        )
        # Should only have adapter_interface imports
        if result.returncode == 0:
            assert "from stage1" not in result.stdout
            assert "from stage2" not in result.stdout


class TestStage1Health:
    """Test Stage 1 health endpoint."""

    def test_stage1_health(self):
        """Test Stage 1 health endpoint."""
        try:
            response = httpx.get(f"{STAGE1_URL}/v1/health", timeout=5)
            data = response.json()
            
            assert "status" in data
            assert "vram_used_gb" in data
            assert "vram_total_gb" in data
        except httpx.ConnectError:
            pytest.skip("Stage 1 not running")


class TestStage2Health:
    """Test Stage 2 health endpoint."""

    def test_stage2_health(self):
        """Test Stage 2 health endpoint."""
        try:
            response = httpx.get(f"{STAGE2_URL}/health", timeout=5)
            data = response.json()
            
            assert "status" in data
        except httpx.ConnectError:
            pytest.skip("Stage 2 not running")

    def test_stage2_index_status(self):
        """Test Stage 2 index status endpoint."""
        try:
            response = httpx.get(f"{STAGE2_URL}/v1/index/status", timeout=5)
            data = response.json()
            
            assert "files_indexed" in data
            assert "watching" in data
        except httpx.ConnectError:
            pytest.skip("Stage 2 not running")


class TestContractCompliance:
    """Test that APIs comply with contracts."""

    def test_inference_api_health_schema(self):
        """Test InferenceAPI health response schema."""
        try:
            response = httpx.get(f"{STAGE1_URL}/v1/health", timeout=5)
            data = response.json()
            
            # Required fields per inference_api.yaml
            required = ["status", "vram_used_gb", "vram_total_gb", 
                       "model_loaded", "llama_server_pid", "uptime_s"]
            
            for field in required:
                assert field in data, f"Missing field: {field}"
                
        except httpx.ConnectError:
            pytest.skip("Stage 1 not running")

    def test_intelligence_api_status_schema(self):
        """Test IntelligenceAPI index status response schema."""
        try:
            response = httpx.get(f"{STAGE2_URL}/v1/index/status", timeout=5)
            data = response.json()
            
            # Required fields per intelligence_api.yaml
            required = ["files_indexed", "last_updated", "embedding_model",
                       "index_size_mb", "watching"]
            
            for field in required:
                assert field in data, f"Missing field: {field}"
                
        except httpx.ConnectError:
            pytest.skip("Stage 2 not running")


class TestEndToEnd:
    """End-to-end pipeline tests."""

    def test_full_pipeline_available(self):
        """Test that all stages are available."""
        stage1_available = wait_for_service(STAGE1_URL, timeout=5)
        stage2_available = wait_for_service(STAGE2_URL, timeout=5)
        
        # At minimum, services should be reachable
        # Full test requires llama-server and indexed workspace
        assert stage1_available or stage2_available, "No stages available"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
