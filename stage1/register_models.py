#!/usr/bin/env python3
"""
Model Registration Script for APEX
Scans and registers all discovered GGUF models
"""

import os
import shutil
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "stage1" / "data" / "models"

# Discovered models (valid GGUF files > 100MB)
DISCOVERED_MODELS = {
    # Main inference models
    "mistral-7b-instruct-v0.2.Q4_K_M.gguf": "D:/AI/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    "glm-4.7-flash.gguf": "D:/Users/CASE/models/glm-4.7-flash.gguf",
    "nemotron-3-nano-30b.gguf": "D:/Users/CASE/models/nemotron-3-nano-30b.gguf",
    "qwen2.5-coder-32b.gguf": "D:/Users/CASE/models/qwen2.5-coder-32b.gguf",
    "qwen3-coder-30b.gguf": "D:/Users/CASE/models/qwen3-coder-30b.gguf",
    "qwen3.5-27b.gguf": "D:/Users/CASE/models/qwen3.5-27b.gguf",
    "qwen3.5-35b-a3b.gguf": "D:/Users/CASE/models/qwen3.5-35b-a3b.gguf",
    "qwen3.5-35b.gguf": "D:/Users/CASE/models/qwen3.5-35b.gguf",
    "qwen3.5-9b.gguf": "D:/Users/CASE/models/qwen3.5-9b.gguf",
    
    # Embedding models
    "nomic-embed-text-v1.5.gguf": "D:/Users/CASE/.lmstudio/.internal/bundled-models/nomic-ai/nomic-embed-text-v1.5.F16.gguf",
}

# Vocabulary files (optional, for specialized tokenizers)
VOCAB_FILES = {
    "vocab-aquila.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-aquila.gguf",
    "vocab-baichuan.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-baichuan.gguf",
    "vocab-bert-bge.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-bert-bge.gguf",
    "vocab-command-r.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-command-r.gguf",
    "vocab-deepseek-coder.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-deepseek-coder.gguf",
    "vocab-deepseek-llm.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-deepseek-llm.gguf",
    "vocab-falcon.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-falcon.gguf",
    "vocab-gpt-2.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-gpt-2.gguf",
    "vocab-gpt-neox.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-gpt-neox.gguf",
    "vocab-llama-bpe.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-llama-bpe.gguf",
    "vocab-llama-spm.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-llama-spm.gguf",
    "vocab-mpt.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-mpt.gguf",
    "vocab-nomic-bert-moe.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-nomic-bert-moe.gguf",
    "vocab-phi-3.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-phi-3.gguf",
    "vocab-qwen2.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-qwen2.gguf",
    "vocab-refact.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-refact.gguf",
    "vocab-starcoder.gguf": "D:/Users/CASE/Desktop/llama.cpp/models/ggml-vocab-starcoder.gguf",
}


def get_file_size_gb(path: str) -> float:
    """Get file size in GB"""
    try:
        return os.path.getsize(path) / (1024 ** 3)
    except Exception:
        return 0.0


def register_models(copy_mode: str = "symlink") -> dict:
    """
    Register all discovered models
    
    Args:
        copy_mode: "symlink" (default), "copy", or "reference"
    
    Returns:
        dict with registration results
    """
    results = {
        "registered": [],
        "skipped": [],
        "errors": [],
        "vocab_registered": [],
    }
    
    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Register main models
    for model_name, source_path in DISCOVERED_MODELS.items():
        target_path = MODELS_DIR / model_name
        
        # Check if source exists
        if not os.path.exists(source_path):
            results["skipped"].append({
                "model": model_name,
                "reason": f"Source not found: {source_path}"
            })
            continue
        
        # Check if already exists
        if target_path.exists():
            results["skipped"].append({
                "model": model_name,
                "reason": "Already registered"
            })
            continue
        
        try:
            if copy_mode == "symlink":
                # Create symbolic link (Windows requires admin or developer mode)
                os.symlink(source_path, target_path)
            elif copy_mode == "copy":
                # Copy file (takes more disk space)
                shutil.copy2(source_path, target_path)
            else:
                # Reference mode - just create a pointer file
                with open(target_path.with_suffix('.path'), 'w') as f:
                    f.write(source_path)
            
            size_gb = get_file_size_gb(source_path)
            results["registered"].append({
                "model": model_name,
                "source": source_path,
                "size_gb": round(size_gb, 2),
                "mode": copy_mode
            })
        except Exception as e:
            results["errors"].append({
                "model": model_name,
                "error": str(e)
            })
    
    # Register vocab files
    for vocab_name, source_path in VOCAB_FILES.items():
        target_path = MODELS_DIR / vocab_name
        
        if not os.path.exists(source_path):
            continue
        
        if target_path.exists():
            continue
        
        try:
            if copy_mode == "symlink":
                os.symlink(source_path, target_path)
            elif copy_mode == "copy":
                shutil.copy2(source_path, target_path)
            
            results["vocab_registered"].append({
                "vocab": vocab_name,
                "source": source_path
            })
        except Exception as e:
            results["errors"].append({
                "vocab": vocab_name,
                "error": str(e)
            })
    
    return results


def print_results(results: dict):
    """Print registration results"""
    print("\n" + "="*60)
    print("MODEL REGISTRATION RESULTS")
    print("="*60)
    
    print(f"\n[OK] Registered: {len(results['registered'])} models")
    for item in results['registered']:
        print(f"   + {item['model']} ({item['size_gb']} GB) [{item['mode']}]")
    
    print(f"\n[VOCAB] Vocab files: {len(results['vocab_registered'])} registered")
    for item in results['vocab_registered']:
        print(f"   + {item['vocab']}")
    
    print(f"\n[SKIP] Skipped: {len(results['skipped'])} models")
    for item in results['skipped']:
        print(f"   - {item['model']}: {item['reason']}")
    
    if results['errors']:
        print(f"\n[ERROR] Errors: {len(results['errors'])}")
        for item in results['errors']:
            print(f"   ! {item.get('model', item.get('vocab'))}: {item['error']}")
    
    print("\n" + "="*60)
    print(f"Models directory: {MODELS_DIR}")
    print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "symlink"
    if mode not in ["symlink", "copy", "reference"]:
        print("Usage: python register_models.py [symlink|copy|reference]")
        sys.exit(1)
    
    print(f"Registering models using {mode} mode...")
    results = register_models(mode)
    print_results(results)
