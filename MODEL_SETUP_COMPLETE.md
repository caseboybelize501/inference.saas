# APEX Model Configuration Summary

**Generated:** 2026-03-09

---

## ✅ Configuration Complete

All discovered GGUF models have been configured and linked to the project.

---

## 📁 Model Locations

### Primary Models (Linked)
Location: `stage1/data/models/`

| Model | Size | VRAM Required | Best For |
|-------|------|---------------|----------|
| **mistral-7b-instruct-v0.2.Q4_K_M.gguf** | 4.1 GB | 6 GB | General, Chat, Code Assist ⭐ |
| **qwen3.5-9b.gguf** | 6.1 GB | 8 GB | Code, Reasoning, General |
| **glm-4.7-flash.gguf** | 5.0 GB | 7 GB | Fast Inference, General |
| **qwen3.5-27b.gguf** | 17.0 GB | 20 GB | Reasoning, Code, General |
| **nemotron-3-nano-30b.gguf** | 19.0 GB | 22 GB | Reasoning, General |
| **qwen2.5-coder-32b.gguf** | 20.0 GB | 24 GB | Code Generation, Code Review |
| **qwen3-coder-30b.gguf** | 20.0 GB | 24 GB | Code Generation, Code Review |
| **qwen3.5-35b-a3b.gguf** | 22.0 GB | 26 GB | Advanced Reasoning, Code |
| **qwen3.5-35b.gguf** | 22.0 GB | 26 GB | Advanced Reasoning, Code |

### Vocabulary Files (17 files)
Specialized tokenizers for various model architectures:
- Aquila, Baichuan, BERT, Command-R
- DeepSeek (Coder + LLM)
- Falcon, GPT-2, GPT-NeoX
- Llama (BPE + SPM), MPT, Nomic
- Phi-3, Qwen2, Refact, StarCoder

---

## 🔗 Source Paths

All models are **symlinked** from their original locations:

```
D:/AI/models/                          → 1 model
D:/Users/CASE/models/                  → 8 models
D:/Users/CASE/Desktop/llama.cpp/models → 17 vocab files
```

---

## ⚙️ Configuration Files

### `.env`
Updated with all model paths and llama-server location:
```
LLAMA_SERVER_PATH=D:/Users/CASE/Desktop/llama.cpp/build/bin/llama-server.exe
MODEL_DIR=d:/Users/CASE/projects/inference.saas/stage1/data/models
```

### `stage1/data/models/model_config.json`
JSON configuration with:
- Model metadata (size, VRAM, recommendations)
- Priority ordering
- Default model selection

---

## 🚀 Quick Start

### Option 1: Direct Python Run
```powershell
cd d:\Users\CASE\projects\inference.saas

# Set llama-server in PATH
$env:Path += ";D:\Users\CASE\Desktop\llama.cpp\build\bin"

# Install dependencies
pip install -r stage1\requirements.txt
pip install -r stage2\requirements.txt

# Start Stage 1
cd stage1
python main.py
```

### Option 2: Docker Compose
```powershell
cd d:\Users\CASE\projects\inference.saas
docker-compose up -d
```

---

## 📊 VRAM Recommendations

| Your GPU VRAM | Recommended Model |
|---------------|-------------------|
| 8 GB | mistral-7b-instruct-v0.2.Q4_K_M |
| 12 GB | qwen3.5-9b or glm-4.7-flash |
| 16 GB | qwen3.5-27b |
| 24 GB | qwen2.5-coder-32b or qwen3-coder-30b |
| 32+ GB | qwen3.5-35b series |

---

## 📝 Model Selection

**Default:** `mistral-7b-instruct-v0.2.Q4_K_M` (best balance of speed/quality)

To change the default model, edit `stage1/data/models/model_config.json`:
```json
{
  "defaults": {
    "primary_model": "qwen3.5-9b"
  }
}
```

---

## ✅ Next Steps

1. **Install Python dependencies** (if not done)
   ```powershell
   pip install -r stage1\requirements.txt
   pip install -r stage2\requirements.txt
   ```

2. **Test Stage 1**
   ```powershell
   cd stage1
   python main.py
   ```

3. **Access API** at `http://localhost:3000/v1/health`

---

**Status:** ✅ Ready to run (pending Python dependencies)
