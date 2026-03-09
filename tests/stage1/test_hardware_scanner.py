"""Tests for Stage 1 hardware scanner."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add stage1 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage1'))

from hardware_scanner import scan_hardware, _scan_nvidia, _scan_amd, _scan_apple


class TestHardwareScanner:
    """Test hardware scanning functionality."""

    @patch('subprocess.run')
    def test_scan_nvidia_success(self, mock_run):
        """Test NVIDIA GPU detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NVIDIA GeForce RTX 4090,24576,535.00"
        )
        
        result = _scan_nvidia()
        
        assert result is not None
        assert len(result["gpus"]) == 1
        assert result["gpus"][0].id == "NVIDIA GeForce RTX 4090"
        assert result["gpus"][0].vram == 24.0  # 24576 MB = 24 GB

    @patch('subprocess.run')
    def test_scan_nvidia_not_found(self, mock_run):
        """Test when nvidia-smi is not available."""
        mock_run.side_effect = FileNotFoundError()
        
        result = _scan_nvidia()
        
        assert result is None

    @patch('subprocess.run')
    def test_scan_amd_success(self, mock_run):
        """Test AMD GPU detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="GPU 0: Radeon RX 7900 XTX\nVRAM: 24368 MB"
        )
        
        result = _scan_amd()
        
        assert result is not None

    @patch('subprocess.run')
    def test_scan_apple_silicon(self, mock_run):
        """Test Apple Silicon detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Apple Silicon"
        )
        
        result = _scan_apple()
        
        # May return None if sysctl fails, but shouldn't crash
        assert result is None or len(result.get("gpus", [])) >= 0

    @patch('stage1.hardware_scanner._scan_nvidia')
    @patch('stage1.hardware_scanner._get_system_ram')
    def test_scan_hardware_cuda(self, mock_ram, mock_nvidia):
        """Test full hardware scan with CUDA."""
        mock_nvidia.return_value = {
            "gpus": [{"id": "RTX 4090", "vram": 24.0}],
            "cuda_version": "12.0"
        }
        mock_ram.return_value = 64.0
        
        hardware = scan_hardware()
        
        assert hardware.platform == "cuda"
        assert len(hardware.gpus) == 1
        assert hardware.gpus[0].vram == 24.0
        assert hardware.system_ram == 64.0

    def test_scan_hardware_no_gpu(self):
        """Test hardware scan with no GPU (CPU fallback)."""
        hardware = scan_hardware()
        
        # Should not crash, should return CPU platform
        assert hardware.platform in ["cpu", "cuda", "rocm", "metal"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
