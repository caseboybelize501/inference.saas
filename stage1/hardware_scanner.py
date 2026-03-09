"""Hardware scanner - detects GPU, VRAM, CUDA/ROCm version."""

import subprocess
import shutil
from typing import Dict, Any, Optional

from contracts.models.hardware_profile import HardwareProfile, GPU


def scan_hardware() -> HardwareProfile:
    """
    Scan system hardware for model selection.
    
    Detects:
    - NVIDIA GPUs via nvidia-smi
    - AMD GPUs via rocm-smi
    - Apple Silicon via system_profiler
    - System RAM
    
    Returns:
        HardwareProfile with detected hardware information
    """
    gpus = []
    platform = "cpu"
    cuda_version = None
    llama_server_path = _find_llama_server()
    
    # Try NVIDIA first
    nvidia_result = _scan_nvidia()
    if nvidia_result:
        gpus = nvidia_result["gpus"]
        platform = "cuda"
        cuda_version = nvidia_result.get("cuda_version")
    
    # Try AMD ROCm if no NVIDIA
    if not gpus:
        amd_result = _scan_amd()
        if amd_result:
            gpus = amd_result["gpus"]
            platform = "rocm"
    
    # Try Apple Silicon
    if not gpus:
        apple_result = _scan_apple()
        if apple_result:
            gpus = apple_result["gpus"]
            platform = "metal"
    
    # Get system RAM
    system_ram = _get_system_ram()
    
    return HardwareProfile(
        gpus=gpus,
        system_ram=system_ram,
        cuda_version=cuda_version,
        llama_server_path=llama_server_path,
        platform=platform
    )


def _find_llama_server() -> Optional[str]:
    """Find llama-server binary in PATH."""
    return shutil.which("llama-server")


def _scan_nvidia() -> Optional[Dict[str, Any]]:
    """Scan NVIDIA GPUs using nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None
        
        gpus = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    gpus.append(GPU(
                        id=parts[0],
                        vram=float(parts[1]) / 1024,  # Convert MB to GB
                        cuda_version=parts[2] if len(parts) > 2 else None
                    ))
        
        # Get CUDA version
        cuda_result = subprocess.run(
            ["nvcc", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        cuda_version = None
        if cuda_result.returncode == 0:
            for line in cuda_result.stdout.split("\n"):
                if "release" in line.lower():
                    cuda_version = line.strip()
                    break
        
        return {"gpus": gpus, "cuda_version": cuda_version}
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def _scan_amd() -> Optional[Dict[str, Any]]:
    """Scan AMD GPUs using rocm-smi."""
    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None
        
        gpus = []
        # Parse rocm-smi output (format varies by version)
        for line in result.stdout.strip().split("\n"):
            if "GPU" in line or "Card" in line:
                # Simplified parsing - actual implementation would be more robust
                gpus.append(GPU(
                    id=line.strip(),
                    vram=16.0  # Default assumption, would parse from output
                ))
        
        return {"gpus": gpus}
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def _scan_apple() -> Optional[Dict[str, Any]]:
    """Scan Apple Silicon using system_profiler."""
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return None
        
        gpus = []
        # Parse system_profiler output for Apple Silicon
        output = result.stdout
        if "Apple Silicon" in output or "M1" in output or "M2" in output or "M3" in output:
            # Get unified memory info
            mem_result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if mem_result.returncode == 0:
                total_ram = int(mem_result.stdout.strip()) / (1024 ** 3)  # Bytes to GB
                gpus.append(GPU(
                    id="Apple Silicon",
                    vram=total_ram * 0.75  # Assume 75% available for GPU
                ))
        
        return {"gpus": gpus}
    
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return None


def _get_system_ram() -> float:
    """Get total system RAM in GB."""
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        pass
    
    # Fallback for different platforms
    try:
        if subprocess.run(["uname", "-s"], capture_output=True, text=True).stdout.strip() == "Linux":
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb / (1024 ** 2)  # KB to GB
    except Exception:
        pass
    
    return 16.0  # Default assumption
