"""VRAM monitor - real-time VRAM usage polling."""

import subprocess
from typing import Dict, Any, Optional, List


class VRAMMonitor:
    """Monitors VRAM usage in real-time."""
    
    def __init__(self):
        """Initialize VRAM monitor."""
        self._nvml_initialized = False
        self._nvml_handle = None
        self._init_nvml()
    
    def _init_nvml(self) -> None:
        """Initialize NVML for NVIDIA GPUs."""
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml_initialized = True
            self._nvml_handle = pynvml
        except (ImportError, Exception):
            self._nvml_initialized = False
    
    def get_usage(self, gpu_index: int = 0) -> Dict[str, Any]:
        """
        Get VRAM usage for specified GPU.
        
        Args:
            gpu_index: GPU index (0 for first GPU)
        
        Returns:
            Dictionary with vram_used, vram_total, gpu_util, memory_util
        """
        if self._nvml_initialized:
            return self._get_nvidia_usage(gpu_index)
        
        # Fallback to nvidia-smi
        return self._get_nvidia_smi_usage(gpu_index)
    
    def get_all_gpus_usage(self) -> List[Dict[str, Any]]:
        """
        Get VRAM usage for all GPUs.
        
        Returns:
            List of usage dictionaries for each GPU
        """
        if self._nvml_initialized:
            try:
                import pynvml
                device_count = pynvml.nvmlDeviceGetCount()
                return [self._get_nvidia_usage(i) for i in range(device_count)]
            except Exception:
                pass
        
        # Fallback
        return [self._get_nvidia_smi_usage(0)]
    
    def _get_nvidia_usage(self, gpu_index: int) -> Dict[str, Any]:
        """Get NVIDIA GPU usage via NVML."""
        try:
            import pynvml
            
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            return {
                "gpu_index": gpu_index,
                "vram_used": memory_info.used / (1024 ** 3),  # Bytes to GB
                "vram_total": memory_info.total / (1024 ** 3),
                "vram_free": memory_info.free / (1024 ** 3),
                "gpu_util": utilization.gpu,
                "memory_util": utilization.memory
            }
        except Exception as e:
            return {
                "gpu_index": gpu_index,
                "vram_used": 0,
                "vram_total": 0,
                "vram_free": 0,
                "gpu_util": 0,
                "memory_util": 0,
                "error": str(e)
            }
    
    def _get_nvidia_smi_usage(self, gpu_index: int) -> Dict[str, Any]:
        """Get NVIDIA GPU usage via nvidia-smi."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total,utilization.gpu,utilization.memory",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return self._empty_usage(gpu_index)
            
            lines = result.stdout.strip().split("\n")
            if gpu_index >= len(lines):
                return self._empty_usage(gpu_index)
            
            parts = [p.strip() for p in lines[gpu_index].split(",")]
            if len(parts) < 4:
                return self._empty_usage(gpu_index)
            
            return {
                "gpu_index": gpu_index,
                "vram_used": float(parts[0]) / 1024,  # MB to GB
                "vram_total": float(parts[1]) / 1024,
                "vram_free": (float(parts[1]) - float(parts[0])) / 1024,
                "gpu_util": float(parts[2]),
                "memory_util": float(parts[3])
            }
        except Exception:
            return self._empty_usage(gpu_index)
    
    def _empty_usage(self, gpu_index: int) -> Dict[str, Any]:
        """Return empty usage dictionary."""
        return {
            "gpu_index": gpu_index,
            "vram_used": 0,
            "vram_total": 0,
            "vram_free": 0,
            "gpu_util": 0,
            "memory_util": 0
        }
    
    def shutdown(self) -> None:
        """Shutdown NVML."""
        if self._nvml_initialized and self._nvml_handle:
            try:
                self._nvml_handle.nvmlShutdown()
                self._nvml_initialized = False
            except Exception:
                pass
    
    def __del__(self):
        """Cleanup on destruction."""
        self.shutdown()
