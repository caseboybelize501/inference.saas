"""Model selector - matches model to VRAM budget."""

import os
from typing import List, Optional, Tuple

from contracts.models.hardware_profile import HardwareProfile
from contracts.models.model_config import ModelSpec, VRAMBudget, QuantLevel


# Model size estimates in GB for different quantization levels
MODEL_SIZES = {
    "7B": {"Q4_0": 4.0, "Q4_K_M": 4.5, "Q5_0": 5.0, "Q5_K_M": 5.5, "Q6_K": 6.0, "Q8_0": 7.0, "F16": 14.0, "F32": 28.0},
    "8B": {"Q4_0": 4.5, "Q4_K_M": 5.0, "Q5_0": 5.5, "Q5_K_M": 6.0, "Q6_K": 6.5, "Q8_0": 8.0, "F16": 16.0, "F32": 32.0},
    "13B": {"Q4_0": 7.0, "Q4_K_M": 8.0, "Q5_0": 9.0, "Q5_K_M": 10.0, "Q6_K": 11.0, "Q8_0": 13.0, "F16": 26.0, "F32": 52.0},
    "34B": {"Q4_0": 18.0, "Q4_K_M": 20.0, "Q5_0": 22.0, "Q5_K_M": 24.0, "Q6_K": 26.0, "Q8_0": 34.0, "F16": 68.0, "F32": 136.0},
    "70B": {"Q4_0": 36.0, "Q4_K_M": 40.0, "Q5_0": 44.0, "Q5_K_M": 48.0, "Q6_K": 52.0, "Q8_0": 70.0, "F16": 140.0, "F32": 280.0},
}

# Priority order for quantization (best quality first that fits)
QUANT_PRIORITY = ["Q8_0", "Q6_K", "Q5_K_M", "Q5_0", "Q4_K_M", "Q4_0"]


def select_model(
    hardware: HardwareProfile,
    model_dir: str = "stage1/data/models",
    preferred_family: Optional[str] = None
) -> Optional[ModelSpec]:
    """
    Select best model and quantization for available VRAM.
    
    Args:
        hardware: Detected hardware profile
        model_dir: Directory containing GGUF model files
        preferred_family: Optional preferred model family
    
    Returns:
        ModelSpec with selected model and quantization, or None if no model fits
    """
    vram_budget = compute_vram_budget(hardware)
    available_vram = vram_budget.available_for_model_gb
    
    # Find available models
    available_models = _scan_models(model_dir)
    
    # Filter and rank models
    candidates = []
    for model_path, model_info in available_models:
        if preferred_family and model_info.get("family") != preferred_family:
            continue
        
        # Find best quantization that fits
        for quant in QUANT_PRIORITY:
            vram_required = MODEL_SIZES.get(model_info.get("size", ""), {}).get(quant, float("inf"))
            
            if vram_required <= available_vram:
                candidates.append((model_path, quant, vram_required, model_info))
                break  # Take best quantization that fits
    
    if not candidates:
        return None
    
    # Select best candidate (highest quality = first in sorted list)
    candidates.sort(key=lambda x: QUANT_PRIORITY.index(x[1]) if x[1] in QUANT_PRIORITY else 999)
    best = candidates[0]
    
    return ModelSpec(
        path=best[0],
        quant=best[1],
        vram_required_gb=best[2],
        family=best[3].get("family"),
        size=best[3].get("size")
    )


def compute_vram_budget(hardware: HardwareProfile) -> VRAMBudget:
    """
    Compute VRAM budget from hardware profile.
    
    Args:
        hardware: Detected hardware profile
    
    Returns:
        VRAMBudget with allocated memory regions
    """
    if not hardware.gpus:
        return VRAMBudget(
            total_vram_gb=0,
            reserved_for_kv_gb=0,
            reserved_for_overhead_gb=0,
            available_for_model_gb=0
        )
    
    # Use largest GPU for single-GPU case
    # TODO: Extend for multi-GPU
    largest_gpu = max(hardware.gpus, key=lambda g: g.vram)
    total_vram = largest_gpu.vram
    
    # Allocate memory
    reserved_for_kv = 2.0  # KV cache reservation
    reserved_for_overhead = 1.5  # System overhead buffer
    available = total_vram - reserved_for_kv - reserved_for_overhead
    
    return VRAMBudget(
        total_vram_gb=total_vram,
        reserved_for_kv_gb=reserved_for_kv,
        reserved_for_overhead_gb=reserved_for_overhead,
        available_for_model_gb=max(0, available)
    )


def _scan_models(model_dir: str) -> List[Tuple[str, dict]]:
    """
    Scan model directory for available GGUF files.
    
    Args:
        model_dir: Directory to scan
    
    Returns:
        List of (path, info) tuples
    """
    models = []
    
    if not os.path.exists(model_dir):
        return models
    
    for filename in os.listdir(model_dir):
        if not filename.endswith(".gguf"):
            continue
        
        filepath = os.path.join(model_dir, filename)
        info = _parse_model_filename(filename)
        models.append((filepath, info))
    
    return models


def _parse_model_filename(filename: str) -> dict:
    """
    Parse model information from GGUF filename.
    
    Expected format: {family}-{size}-{quant}.gguf
    Example: llama-7B-Q4_K_M.gguf
    """
    name = filename.replace(".gguf", "")
    parts = name.split("-")
    
    info = {
        "family": None,
        "size": None,
        "quant": None
    }
    
    if len(parts) >= 3:
        info["family"] = parts[0]
        info["size"] = parts[1]
        info["quant"] = "-".join(parts[2:])
    elif len(parts) == 2:
        info["family"] = parts[0]
        info["size"] = parts[1]
    
    return info
