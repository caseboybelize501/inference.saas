# APEX Requirements Specification

**Autonomous Production Engineering Executor**

A unified three-stage system: Stage 1 inference runtime (llama.cpp, VRAM-optimized, OpenAI-compatible), Stage 2 codebase intelligence (tree-sitter AST, embedding index, call graph, context packager), Stage 3 abstract swappable editor interface — built contract-first so each stage is independently replaceable without touching the others.

---

## System Overview

### Core Philosophy

- **Contracts First**: Interfaces generated before any implementation. Immutable after Step 0.
- **Stage Isolation**: No stage imports from another stage's source. All communication via typed HTTP contracts.
- **On-Demand Only**: One full model, fully loaded, triggered by explicit user action. Zero background polling.
- **Swappable Editor**: Stage 3 is fully replaceable (VSCodium today, Zed tomorrow, custom Tauri when ready).

### Architecture

```
USER KEYPRESS
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 3: EDITOR ADAPTER                                   │
│  VSCodium Extension (.vsix)                                │
│  - Calls: POST intelligence_api/v1/complete                │
│  - Knows: IntelligenceAPI only                             │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP localhost:3001
                       ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 2: CODEBASE INTELLIGENCE                            │
│  Python FastAPI server (port 3001)                         │
│  - AST Indexer (tree-sitter)                               │
│  - Call Graph (networkx)                                   │
│  - Embedding Index (hnswlib/faiss)                         │
│  - Context Packager                                        │
│  Calls: InferenceAPI /v1/embeddings, /v1/completions       │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP localhost:3000
                       ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 1: INFERENCE RUNTIME                                │
│  Python FastAPI proxy (port 3000)                          │
│  - Hardware Scanner (nvidia-smi/rocm-smi)                  │
│  - Model/Quant Selector (VRAM budget → best fit)           │
│  - llama-server subprocess (managed, auto-restart)         │
└────────────────────────────────────────────────────────────┘
```

---

## Stage 1 — Inference Runtime

### Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-01 | GPU Detection | Detect GPU via `nvidia-smi` (NVIDIA) or `rocm-smi` (AMD). Extract GPU name, VRAM, CUDA/ROCm version. |
| FR-02 | Model Selection | Select model + quantization from VRAM budget automatically. Match model size to available memory. |
| FR-03 | Subprocess Management | Spawn and manage `llama-server` subprocess. Restart on crash. Isolate failures. |
| FR-04 | OpenAI-Compatible API | Expose API matching `inference_api.yaml`: `/v1/completions`, `/v1/embeddings`, `/v1/models`, `/v1/health`, `/v1/load`. |
| FR-05 | Streaming | Stream completions via SSE (`text/event-stream`). |
| FR-06 | Batch Embeddings | Support batch embeddings for indexer using small dedicated embedder model. |
| FR-07 | Hot-Swap Models | Hot-swap models without editor restart. |
| FR-08 | Health Endpoint | Expose VRAM budget + model status via `/v1/health`. |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Cold Start | Cold start to first completion < 30s on 32GB VRAM GPU |
| NFR-02 | On-Demand Only | Zero background inference — on-demand only |
| NFR-03 | Crash Isolation | `llama-server` crash must not crash Stage 1 process |
| NFR-04 | Read-Only Access | All model files accessed read-only |

---

## Stage 2 — Codebase Intelligence

### Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-09 | AST Indexing | Tree-sitter AST parse all supported languages on index. |
| FR-10 | Symbol Map | Build symbol map: functions, classes, imports per file. |
| FR-11 | Call Graph | Build call graph across files from AST output. |
| FR-12 | Chunking + Embedding | Chunk files + embed via Stage 1 `/v1/embeddings` endpoint. |
| FR-13 | Semantic Search | Query → ranked relevant chunks. |
| FR-14 | Context Packager | Assemble ranked chunks into LLM prompt. |
| FR-15 | File Watching | Watch filesystem: re-index changed files only (dedup). |
| FR-16 | Intelligence API | Expose API matching `intelligence_api.yaml`: `/v1/context`, `/v1/complete`, `/v1/explain`, `/v1/refactor`, `/v1/symbols`, `/v1/callgraph`, `/v1/index/status`, `/v1/index/rebuild`. |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-05 | Index Speed | Index 10,000 file repo in < 5 minutes on first build |
| NFR-06 | Incremental Re-index | Incremental re-index changed file < 500ms |
| NFR-07 | Context Assembly | Context assembly < 100ms (before LLM call) |
| NFR-08 | Persistence | Embedding index survives process restart (persisted) |

---

## Stage 3 — Editor Adapter

### Functional Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| FR-17 | Adapter Interface | Define `EditorAdapter` interface (swappable). |
| FR-18 | VSCodium Extension | VSCodium `.vsix` extension consuming IntelligenceAPI only. |
| FR-19 | On-Demand Completion | On-demand completion via keybind (no background polling). |
| FR-20 | Inline Diff View | Inline diff view for refactor suggestions. |
| FR-21 | Symbol Hover | Symbol hover calls IntelligenceAPI `/v1/explain`. |
| FR-22 | Status Bar | Status bar shows: model loaded, index status, VRAM usage. |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-09 | Memory Footprint | Extension adds < 20MB to VSCodium memory footprint |
| NFR-10 | Cancellable | All LLM calls cancellable (user presses Escape) |
| NFR-11 | Localhost Only | No network calls — localhost only, enforced |

---

## Contracts (Step 0 — Immutable)

### inference_api.yaml (Stage 1 Output)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/completions` | POST | body: `{ model, prompt, max_tokens, temperature, stream }` → resp: `{ id, choices: [{text, finish_reason}], usage }` |
| `/v1/embeddings` | POST | body: `{ model, input: string[] }` → resp: `{ data: [{embedding: float[], index}], usage }` |
| `/v1/models` | GET | resp: `{ models: [{id, path, quant, vram_gb, loaded: bool}] }` |
| `/v1/health` | GET | resp: `{ status, vram_used_gb, vram_total_gb, model_loaded, llama_server_pid, uptime_s }` |
| `/v1/load` | POST | body: `{ model_path, quant_override? }` → resp: `{ loaded: bool, vram_used_gb, model_id }` |

### intelligence_api.yaml (Stage 2 Output)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/context` | POST | body: `{ query, workspace_root, cursor_file?, cursor_line?, max_chunks, strategy }` → resp: `{ chunks: [{file, start_line, end_line, content, score, reason}], total_tokens_est }` |
| `/v1/complete` | POST | body: `{ file, line, col, prefix, suffix, max_tokens }` → resp: `{ completion, context_used, model_used, latency_ms }` |
| `/v1/explain` | POST | body: `{ file, start_line, end_line, question? }` → resp: `{ explanation, symbols_referenced[], context_used[] }` |
| `/v1/refactor` | POST | body: `{ file, start_line, end_line, instruction }` → resp: `{ original, refactored, diff, explanation }` |
| `/v1/symbols` | GET | resp: `{ symbols: [{name, kind, file, line, col, docstring}] }` |
| `/v1/callgraph` | GET | resp: `{ callers: [], callees: [], depth_searched: int }` |
| `/v1/index/status` | GET | resp: `{ files_indexed, last_updated, embedding_model, index_size_mb, watching: bool }` |
| `/v1/index/rebuild` | POST | body: `{ workspace_root, force: bool }` → resp: `{ job_id, estimated_s }` |

### contracts/models/ (Pydantic Schemas)

| File | Purpose |
|------|---------|
| `hardware_profile.py` | GPU, VRAM, CUDA, llama_server path |
| `model_config.py` | ModelSpec, QuantLevel, VRAMBudget |
| `index_entry.py` | FileEntry, SymbolEntry, ChunkEntry |
| `context_request.py` | ContextQuery, ContextResult, Chunk |
| `completion_request.py` | CompletionRequest, CompletionResult |
| `editor_adapter.py` | AdapterCapabilities, EditorEvent |

---

## Hard Requirements

1. **CONTRACTS FIRST (Step 0)**: `inference_api.yaml` and `intelligence_api.yaml` generated before any implementation. Immutable after Step 0. All three stages generated against these contracts as ground truth.

2. **STAGE ISOLATION**: 
   - Stage 1 source has zero knowledge of Stage 2 or 3.
   - Stage 2 source has zero knowledge of Stage 3.
   - Stage 3 source calls only `intelligence_api.yaml` endpoints — never Stage 1 directly.

3. **HARDWARE SCAN BOOTSTRAP**: Stage 1 scans GPU (`nvidia-smi` / `rocm-smi`), VRAM, CUDA version, installed `llama-server` binary before any model loads. Writes `HardwareProfile`. Model + quant selected from profile.

4. **CRITIC GATE**: No topo level advances until all files in that level pass all 4 critic passes. Max 3 repair attempts. HALT on failure.

5. **DEDUP**: All runs keyed by `(workspace_hash + query_hash)`. Never re-index unchanged files. Never re-run identical completions.

---

## File Structure

```
contracts/                   ← LEVEL 0, immutable after GATE-1
  inference_api.yaml         OpenAPI spec for Stage 1
  intelligence_api.yaml      OpenAPI spec for Stage 2
  models/
    hardware_profile.py
    model_config.py
    index_entry.py
    context_request.py
    completion_request.py
    editor_adapter.py

stage1/                      ← Inference Runtime
  hardware_scanner.py        nvidia-smi/rocm-smi → HardwareProfile
  model_selector.py          VRAM budget → model + quant choice
  llama_server_manager.py    subprocess spawn + watchdog + restart
  inference_proxy.py         FastAPI: forwards to llama-server
  vram_monitor.py            pynvml polling → /v1/health data
  main.py                    startup: scan → select → spawn → serve
  requirements.txt

stage2/                      ← Codebase Intelligence
  ast_indexer.py             tree-sitter → symbol map + SQLite
  call_graph.py              networkx graph from AST output
  embedder.py                calls Stage1 /v1/embeddings
  embedding_index.py         hnswlib: build + query + persist
  context_packager.py        hybrid rank: semantic + call graph
  file_watcher.py            watchdog: re-index changed files
  intelligence_server.py     FastAPI: IntelligenceAPI routes
  search.py                  BM25 fallback when embedder absent
  main.py                    startup: index → watch → serve
  requirements.txt

stage3/                      ← Editor Adapter
  adapter_interface.py       abstract EditorAdapter (Python ref)
  vscodium/
    package.json             extension manifest + contributes
    extension.ts             activate: register all commands
    completion.ts            on-demand completion provider
    hover.ts                 symbol hover → /v1/explain
    refactor.ts              selection → /v1/refactor + diff view
    status_bar.ts            model + index + VRAM status bar
    intelligence_client.ts   typed HTTP client for intelligence_api
    tsconfig.json

tests/
  test_stage_isolation.py    grep-based isolation enforcement
  stage1/
    test_hardware_scanner.py
    test_model_selector.py
    test_server_manager.py
    test_inference_api.py
  stage2/
    test_ast_indexer.py
    test_call_graph.py
    test_context_packager.py
    test_intelligence_api.py
  stage3/
    test_adapter_interface.py
    test_isolation.py
  integration/
    test_full_pipeline.py

shared/
  hardware_profile.json      written Stage1 startup, read by all
  ports.py                   STAGE1_PORT=3000, STAGE2_PORT=3001

.vscode/                     ← generated workspace config
  settings.json
  extensions.json
  launch.json
  tasks.json
  apex.code-workspace

tasks.md                     ← build checklist
docker-compose.yml
.env.example
README.md
```

---

## Build Pipeline

### Topological Sort Levels

| Level | Files |
|-------|-------|
| 0 | All contracts (immutable ground truth) |
| 1 | `hardware_scanner.py`, `ast_indexer.py`, `embedder.py`, `adapter_interface.py` |
| 2 | `model_selector.py`, `call_graph.py`, `embedding_index.py`, `extension.ts` |
| 3 | `llama_server_manager.py`, `context_packager.py`, `file_watcher.py`, `completion.ts`, `hover.ts`, `status_bar.ts` |
| 4 | `inference_proxy.py`, `intelligence_server.py`, `package.json` |
| 5 | `stage1/main.py`, `stage2/main.py` |

### Critic Passes (Per Level)

1. **PASS 1 — SYNTAX** (no LLM): `ast.parse()`, `mypy --strict`, `ruff check`, `tsc --noEmit`, `eslint`, `yamllint`, `openapi-spec-validator`
2. **PASS 2 — CONTRACT** (no LLM): Function signatures match contracts, HTTP methods/paths correct, Pydantic imports resolve, stage isolation enforced
3. **PASS 3 — COMPLETENESS** (LLM): No `pass`/`TODO`/`NotImplemented` in FR-required functions
4. **PASS 4 — LOGIC** (LLM): Hardware scanner parses correctly, VRAM math prevents OOM, ranking prefers higher-score chunks, SSE streaming correct

---

## Test Strategy

### Test Types

1. **Contract Tests**: Validate response schemas match YAML specs
2. **Acceptance Tests**: Per-FR validation with mocked inputs
3. **Isolation Tests**: Grep-based enforcement of stage boundaries

### Execution Order

1. `test_stage_isolation.py` (run first, always)
2. `tests/stage1/` (Stage 1 — no Stage 2/3 running)
3. `tests/stage2/` (Stage 2 — Stage 1 mocked)
4. `tests/stage3/` (Stage 3 — Stage 2 mocked)
5. `tests/integration/` (all three live, localhost ports)

---

## Self-Repair Triggers

| Trigger | Response |
|---------|----------|
| T1 — llama-server exits | Catch exit → restart with same args → log crash → emit `/v1/health` warning |
| T2 — OOM kill | Detect exit 137 or CUDA OOM → drop one quant level → reload |
| T3 — Index corruption | Drop and rebuild index automatically |
| T4 — Stage 2 → Stage 1 connection refused | Retry with backoff (1s, 2s, 4s, 8s) → attempt Stage 1 restart |
| T5 — Embedding model not found | Fall back to BM25 keyword search → log degraded mode |

---

## Ports

| Service | Port |
|---------|------|
| Stage 1 (Inference Runtime) | 3000 |
| Stage 2 (Codebase Intelligence) | 3001 |
| llama-server (internal) | 8080 |

---

## Prerequisites

- `llama-server` binary in PATH (build from llama.cpp)
- At least one GGUF model in `stage1/models/`
- Python 3.11+
- Node 20+
- NVIDIA GPU (CUDA 12+) or Apple Silicon (Metal) or CPU fallback

---

## Quick Start

```bash
# Start Stage 1 + Stage 2
docker-compose up -d

# Install Stage 3
code --install-extension apex.vsix

# Open any project folder in VSCodium → APEX indexes automatically
```

---

## Keybindings

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+A` | On-demand completion at cursor |
| `Ctrl+Shift+E` | Explain selected code |
| `Ctrl+Shift+R` | Refactor with instruction |
| `Hover symbol` | Inline explanation + callers/callees |

---

## Pricing Model

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Stage 1 + Stage 2 + VSCodium extension (self-hosted) |
| Pro | $20/mo | Model management UI, index dashboard, multi-workspace, priority support |
| Teams | $50/user/mo | Shared inference server, team context, codebase snapshots, audit log |
