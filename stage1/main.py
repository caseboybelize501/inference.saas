"""Stage 1 main entry point - orchestrates startup."""

import asyncio
import uvicorn

from stage1.hardware_scanner import scan_hardware
from stage1.model_selector import select_model, compute_vram_budget
from stage1.llama_server_manager import LlamaServerManager
from stage1.vram_monitor import VRAMMonitor
from stage1.inference_proxy import app


# Global state
server_manager: LlamaServerManager | None = None
vram_monitor: VRAMMonitor | None = None


async def startup():
    """Initialize Stage 1 components."""
    global server_manager, vram_monitor
    
    print("Stage 1: Starting up...")
    
    # Scan hardware
    print("Scanning hardware...")
    hardware = scan_hardware()
    print(f"  Platform: {hardware.platform}")
    print(f"  GPUs: {len(hardware.gpus)}")
    for gpu in hardware.gpus:
        print(f"    - {gpu.id}: {gpu.vram}GB")
    print(f"  System RAM: {hardware.system_ram}GB")
    print(f"  llama-server: {hardware.llama_server_path or 'NOT FOUND'}")
    
    # Compute VRAM budget
    budget = compute_vram_budget(hardware)
    print(f"\nVRAM Budget:")
    print(f"  Total: {budget.total_vram_gb}GB")
    print(f"  Available for model: {budget.available_for_model_gb}GB")
    
    # Select model
    print("\nSelecting model...")
    model = select_model(hardware)
    if model:
        print(f"  Selected: {model.path}")
        print(f"  Quantization: {model.quant}")
        print(f"  VRAM required: {model.vram_required_gb}GB")
    else:
        print("  No suitable model found - will wait for manual load")
    
    # Initialize managers
    server_manager = LlamaServerManager(hardware.llama_server_path)
    vram_monitor = VRAMMonitor()
    
    # Load model if found
    if model:
        print("\nLoading model...")
        if server_manager.spawn(model):
            print(f"  Model loaded (PID: {server_manager.pid})")
        else:
            print("  Failed to load model")
    
    print("\nStage 1 ready on http://0.0.0.0:3000")


def main():
    """Main entry point."""
    # Run startup
    asyncio.run(startup())
    
    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=3000)


if __name__ == "__main__":
    main()
