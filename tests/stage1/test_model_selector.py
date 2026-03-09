"""Tests for Stage 1 model selector."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add stage1 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage1'))

from model_selector import select_model, compute_vram_budget, QUANT_PRIORITY, MODEL_SIZES
from contracts.models.hardware_profile import HardwareProfile, GPU


class TestModelSelector:
    """Test model selection functionality."""

    def test_compute_vram_budget_single_gpu(self):
        """Test VRAM budget computation for single GPU."""
        hardware = HardwareProfile(
            gpus=[GPU(id="RTX 4090", vram=24.0)],
            system_ram=64.0,
            platform="cuda"
        )
        
        budget = compute_vram_budget(hardware)
        
        assert budget.total_vram_gb == 24.0
        assert budget.reserved_for_kv_gb == 2.0
        assert budget.reserved_for_overhead_gb == 1.5
        assert budget.available_for_model_gb == 20.5

    def test_compute_vram_budget_multi_gpu(self):
        """Test VRAM budget computation for multiple GPUs."""
        hardware = HardwareProfile(
            gpus=[
                GPU(id="RTX 4090", vram=24.0),
                GPU(id="RTX 3090", vram=24.0)
            ],
            system_ram=64.0,
            platform="cuda"
        )
        
        budget = compute_vram_budget(hardware)
        
        # Should use largest GPU
        assert budget.total_vram_gb == 24.0

    def test_compute_vram_budget_no_gpu(self):
        """Test VRAM budget with no GPU."""
        hardware = HardwareProfile(
            gpus=[],
            system_ram=16.0,
            platform="cpu"
        )
        
        budget = compute_vram_budget(hardware)
        
        assert budget.total_vram_gb == 0
        assert budget.available_for_model_gb == 0

    def test_quant_priority_order(self):
        """Test quantization priority order."""
        # Q8_0 should be highest quality
        assert QUANT_PRIORITY[0] == "Q8_0"
        # Q4_0 should be lowest quality
        assert QUANT_PRIORITY[-1] == "Q4_0"

    def test_model_sizes_defined(self):
        """Test model sizes are defined."""
        assert "7B" in MODEL_SIZES
        assert "13B" in MODEL_SIZES
        assert "70B" in MODEL_SIZES
        
        # Check Q8_0 sizes
        assert MODEL_SIZES["7B"]["Q8_0"] == 7.0
        assert MODEL_SIZES["13B"]["Q8_0"] == 13.0
        assert MODEL_SIZES["70B"]["Q8_0"] == 70.0

    @patch('stage1.model_selector._scan_models')
    def test_select_model_fits_vram(self, mock_scan):
        """Test model selection based on VRAM."""
        mock_scan.return_value = [
            ("/models/llama-7B-Q8_0.gguf", {"family": "llama", "size": "7B", "quant": "Q8_0"}),
            ("/models/llama-13B-Q8_0.gguf", {"family": "llama", "size": "13B", "quant": "Q8_0"})
        ]
        
        hardware = HardwareProfile(
            gpus=[GPU(id="RTX 4090", vram=24.0)],
            system_ram=64.0,
            platform="cuda"
        )
        
        model = select_model(hardware)
        
        assert model is not None
        # Should select best model that fits (13B Q8_0 = 13GB < 20.5GB available)
        assert "13B" in model.path

    @patch('stage1.model_selector._scan_models')
    def test_select_model_no_fit(self, mock_scan):
        """Test model selection when nothing fits."""
        mock_scan.return_value = [
            ("/models/llama-70B-Q8_0.gguf", {"family": "llama", "size": "70B", "quant": "Q8_0"})
        ]
        
        hardware = HardwareProfile(
            gpus=[GPU(id="RTX 3060", vram=12.0)],
            system_ram=16.0,
            platform="cuda"
        )
        
        model = select_model(hardware)
        
        # 70B Q8_0 = 70GB > 8.5GB available, should return None or smaller quant
        assert model is None or model.vram_required_gb <= 8.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
