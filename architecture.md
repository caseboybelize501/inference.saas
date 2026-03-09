# APEX Architecture Specification

**Autonomous Production Engineering Executor**

A unified three-stage system: Stage 1 inference runtime (llama.cpp, VRAM-optimized, OpenAI-compatible), Stage 2 codebase intelligence (tree-sitter AST, embedding index, call graph, context packager), Stage 3 abstract swappable editor interface — built contract-first so each stage is independently replaceable without touching the others.

---

## System Architecture

### High-Level Data Flow

```
USER KEYPRESS
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 3: EDITOR ADAPTER                                   │
│  VSCodium Extension (.vsix)                                │
│  - Captures: cursor position, file, selection              │
│  - Calls:    POST intelligence_api/v1/complete             │
│  - Renders:  ghost text / diff view / hover panel          │
│  - Knows:    IntelligenceAPI only                          │
│  - Does NOT: import stage1/ or stage2/ source              │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP localhost:3001
                       ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 2: CODEBASE INTELLIGENCE                            │
│  Python FastAPI server (port 3001)                         │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ AST Indexer  │  │ Call Graph   │  │ Embedding Index │  │
│  │ (tree-sitter)│  │ (networkx)   │  │ (hnswlib/faiss) │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  │
│         └─────────────────┴──────────────────┘            │
│                           │                               │
│                    ┌──────▼────────────────────────────┐  │
│                    │  Context Packager                 │  │
│                    │  (ranks + assembles prompt)       │  │
│                    └───────────────────────────────────┘  │
│                                                            │
│  Calls: InferenceAPI /v1/embeddings (embedder model)      │
│  Calls: InferenceAPI /v1/completions (main model)         │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP localhost:3000
                       ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 1: INFERENCE RUNTIME                                │
│  Python FastAPI proxy (port 3000)                          │
│                                                            │
│  ┌──────────────────┐    ┌────────────────────────────┐   │
│  │ Hardware Scanner │    │ Model/Quant Selector       │   │
│  │ nvidia-smi probe │───▶│ VRAM budget → best fit     │   │
│  └──────────────────┘    └─────────────┬──────────────┘   │
│                                         │                  │
│                          ┌──────────────▼──────────────┐   │
│                          │ llama-server subprocess     │   │
│                          │ (managed, auto-restart)     │   │
│                          │ port 8080 (internal only)   │   │
│                          └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Persistence Layer

| Path | Purpose | Owner |
|------|---------|-------|
| `stage2/data/index.db` | SQLite: symbols, files, chunks | Stage 2 |
| `stage2/data/embeddings/` | hnswlib index (persisted vectors) | Stage 2 |
| `stage1/data/models/` | GGUF model files (user-managed) | Stage 1 |
| `shared/hardware_profile.json` | Written by Stage 1, read by all | Shared |

---

## Stage 1: Inference Runtime

### Components

```
┌─────────────────────────────────────────────────────────────┐
│  stage1/main.py                                             │
│  - Entry point                                              │
│  - Orchestrates: scan → select → spawn → serve              │
└─────────────────────────────────────────────────────────────┘
         │
         ├──▶ hardware_scanner.py
         │    - nvidia-smi / rocm-smi parsing
         │    - Writes: shared/hardware_profile.json
         │
         ├──▶ model_selector.py
         │    - Reads: hardware_profile.json
         │    - Selects: model + quant from VRAM budget
         │
         ├──▶ llama_server_manager.py
         │    - Spawns llama-server subprocess
         │    - Watches for crashes, auto-restarts
         │    - Exposes: pid, status, restart count
         │
         ├──▶ vram_monitor.py
         │    - pynvml polling
         │    - Feeds: /v1/health endpoint
         │
         └──▶ inference_proxy.py
              - FastAPI server (port 3000)
              - Routes: /v1/completions, /v1/embeddings, /v1/models, /v1/health, /v1/load
              - Forwards to llama-server (port 8080)
```

### Component Responsibilities

| Component | Responsibility | Dependencies |
|-----------|----------------|--------------|
| `hardware_scanner.py` | Detect GPU, VRAM, CUDA/ROCm version | `contracts/models/hardware_profile.py` |
| `model_selector.py` | Match model to VRAM budget | `hardware_scanner.py`, `contracts/models/model_config.py` |
| `llama_server_manager.py` | Subprocess lifecycle management | `model_selector.py` |
| `vram_monitor.py` | Real-time VRAM usage polling | None (direct pynvml) |
| `inference_proxy.py` | OpenAI-compatible HTTP API | `contracts/inference_api.yaml`, `llama_server_manager.py` |
| `main.py` | Startup orchestration | All above |

### Internal Data Flow

```
Startup:
  main.py
    │
    ├──▶ hardware_scanner.scan() ──▶ hardware_profile.json
    │
    ├──▶ model_selector.select(hardware_profile) ──▶ ModelSpec
    │
    ├──▶ llama_server_manager.spawn(ModelSpec) ──▶ llama-server (pid)
    │
    └──▶ inference_proxy.serve() ──▶ FastAPI (port 3000)

Runtime:
  POST /v1/completions
    │
    ├──▶ inference_proxy
    │
    └──▶ llama-server:8080/v1/completions (forward)
         │
         └──▶ SSE stream back to client

  GET /v1/health
    │
    ├──▶ vram_monitor.get_usage()
    ├──▶ llama_server_manager.get_status()
    │
    └──▶ { status, vram_used_gb, vram_total_gb, model_loaded, pid, uptime_s }
```

### Self-Repair Mechanisms

| Trigger | Detection | Response |
|---------|-----------|----------|
| T1 — llama-server exits | Process exit event | Catch exit → restart with same args → log crash → emit `/v1/health` warning |
| T2 — OOM kill | Exit code 137 or CUDA error | Drop one quant level → reload model |
| T4 — Connection refused | HTTP 503 from llama-server | Retry with backoff (1s, 2s, 4s, 8s) → attempt Stage 1 restart |

---

## Stage 2: Codebase Intelligence

### Components

```
┌─────────────────────────────────────────────────────────────┐
│  stage2/main.py                                             │
│  - Entry point                                              │
│  - Orchestrates: index → watch → serve                      │
└─────────────────────────────────────────────────────────────┘
         │
         ├──▶ ast_indexer.py
         │    - tree-sitter AST parsing
         │    - Extracts: symbols (functions, classes, imports)
         │    - Writes: stage2/data/index.db (FileEntry, SymbolEntry)
         │
         ├──▶ call_graph.py
         │    - networkx graph from AST output
         │    - Tracks: callers, callees across files
         │    - Writes: stage2/data/index.db (CallEntry)
         │
         ├──▶ embedder.py
         │    - Calls Stage1 /v1/embeddings
         │    - Batches requests for efficiency
         │
         ├──▶ embedding_index.py
         │    - hnswlib: build + query + persist
         │    - Stores: chunk vectors in stage2/data/embeddings/
         │
         ├──▶ context_packager.py
         │    - Hybrid rank: semantic + call graph
         │    - Assembles: ranked chunks into LLM prompt
         │
         ├──▶ file_watcher.py
         │    - watchdog: re-index changed files only
         │    - Dedup: keyed by (workspace_hash + file_hash)
         │
         ├──▶ search.py
         │    - BM25 fallback when embedder absent
         │
         └──▶ intelligence_server.py
              - FastAPI server (port 3001)
              - Routes: /v1/context, /v1/complete, /v1/explain, /v1/refactor,
              │         /v1/symbols, /v1/callgraph, /v1/index/status, /v1/index/rebuild
```

### Component Responsibilities

| Component | Responsibility | Dependencies |
|-----------|----------------|--------------|
| `ast_indexer.py` | Parse files → symbol map | `contracts/models/index_entry.py` |
| `call_graph.py` | Build cross-file call graph | `ast_indexer.py`, `contracts/models/index_entry.py` |
| `embedder.py` | Generate embeddings via Stage 1 | `contracts/inference_api.yaml` |
| `embedding_index.py` | Vector index (hnswlib) | `embedder.py`, `contracts/models/index_entry.py` |
| `context_packager.py` | Rank + assemble context | `call_graph.py`, `embedding_index.py` |
| `file_watcher.py` | Incremental re-indexing | `ast_indexer.py`, `embedding_index.py` |
| `search.py` | BM25 keyword fallback | None |
| `intelligence_server.py` | IntelligenceAPI HTTP server | `contracts/intelligence_api.yaml`, all above |
| `main.py` | Startup orchestration | All above |

### Internal Data Flow

```
Startup (first run):
  main.py
    │
    ├──▶ ast_indexer.scan(workspace_root) ──▶ index.db (symbols)
    │
    ├──▶ call_graph.build(index.db) ──▶ index.db (calls)
    │
    ├──▶ embedder.batch_embed(chunks) ──▶ Stage1 /v1/embeddings
    │
    ├──▶ embedding_index.build(vectors) ──▶ embeddings/ (hnswlib index)
    │
    ├──▶ file_watcher.start(workspace_root)
    │
    └──▶ intelligence_server.serve() ──▶ FastAPI (port 3001)

Runtime (incremental):
  File changed
    │
    ├──▶ file_watcher detects change
    │
    ├──▶ ast_indexer.reindex(file) ──▶ update index.db
    │
    └──▶ embedder.embed(new_chunks) ──▶ update embeddings/

Query:
  POST /v1/context
    │
    ├──▶ context_packager.rank(query, strategy)
    │    │
    │    ├──▶ embedding_index.search(query_vector) ──▶ semantic chunks
    │    ├──▶ call_graph.get_related(symbol) ──▶ call graph chunks
    │    │
    │    └──▶ hybrid_merge(semantic, callgraph, weights)
    │
    └──▶ { chunks: [{file, start_line, end_line, content, score, reason}] }
```

### Index Schema (SQLite)

```sql
-- FileEntry
CREATE TABLE files (
    id TEXT PRIMARY KEY,           -- workspace_hash + relative_path
    path TEXT NOT NULL,
    workspace_root TEXT NOT NULL,
    hash TEXT NOT NULL,            -- content hash for dedup
    language TEXT NOT NULL,
    indexed_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- SymbolEntry
CREATE TABLE symbols (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id),
    name TEXT NOT NULL,
    kind TEXT NOT NULL,            -- function, class, import, etc.
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    col_start INTEGER NOT NULL,
    col_end INTEGER NOT NULL,
    docstring TEXT,
    signature TEXT
);

-- CallEntry
CREATE TABLE calls (
    id TEXT PRIMARY KEY,
    caller_symbol_id TEXT REFERENCES symbols(id),
    callee_symbol_id TEXT REFERENCES symbols(id),
    call_site_line INTEGER NOT NULL,
    call_site_col INTEGER NOT NULL
);

-- ChunkEntry
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id),
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding_index TEXT           -- reference to hnswlib index
);
```

### Self-Repair Mechanisms

| Trigger | Detection | Response |
|---------|-----------|----------|
| T3 — Index corruption | SQLite integrity check fails | Drop and rebuild index automatically |
| T5 — Embedding model not found | Stage 1 returns 404 | Fall back to BM25 keyword search → log degraded mode |

---

## Stage 3: Editor Adapter

### Components

```
┌─────────────────────────────────────────────────────────────┐
│  stage3/adapter_interface.py                                │
│  - Abstract EditorAdapter class (Python reference)          │
│  - Defines: capabilities, event handlers                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  stage3/vscodium/                                           │
│                                                             │
│  package.json                                               │
│    - Extension manifest                                     │
│    - Contributes: commands, keybindings, configuration      │
│                                                             │
│  extension.ts                                               │
│    - Entry point: activate()                                │
│    - Registers: all commands                                │
│                                                             │
│  completion.ts                                              │
│    - CompletionProvider                                     │
│    - Trigger: Ctrl+Shift+A (on-demand)                      │
│    - Calls: POST /v1/complete                               │
│    - Renders: ghost text                                    │
│                                                             │
│  hover.ts                                                   │
│    - HoverProvider                                          │
│    - Calls: POST /v1/explain                                │
│    - Renders: inline explanation                            │
│                                                             │
│  refactor.ts                                                │
│    - Command handler                                        │
│    - Calls: POST /v1/refactor                               │
│    - Renders: diff view                                     │
│                                                             │
│  status_bar.ts                                              │
│    - StatusBarItem                                          │
│    - Polls: GET /v1/index/status, GET /v1/health            │
│    - Shows: model loaded, index status, VRAM usage          │
│                                                             │
│  intelligence_client.ts                                     │
│    - Typed HTTP client for intelligence_api                 │
│    - Base URL: http://localhost:3001                        │
│    - Enforces: localhost only                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Dependencies |
|-----------|----------------|--------------|
| `adapter_interface.py` | Abstract interface definition | `contracts/intelligence_api.yaml`, `contracts/models/editor_adapter.py` |
| `package.json` | Extension manifest | VSCode extension API |
| `extension.ts` | Activation + command registration | All below |
| `completion.ts` | On-demand completion provider | `intelligence_client.ts` |
| `hover.ts` | Symbol hover handler | `intelligence_client.ts` |
| `refactor.ts` | Refactor command + diff view | `intelligence_client.ts` |
| `status_bar.ts` | Status display | `intelligence_client.ts` |
| `intelligence_client.ts` | Typed HTTP client | `contracts/intelligence_api.yaml` |

### Internal Data Flow

```
Activation:
  extension.ts.activate()
    │
    ├──▶ registerCompletionProvider()
    │
    ├──▶ registerHoverProvider()
    │
    ├──▶ registerCommand('apex.refactor')
    │
    └──▶ createStatusBarItem() ──▶ start polling

Completion Request:
  User presses Ctrl+Shift+A
    │
    ├──▶ completion.ts.provideCompletion()
    │    │
    │    ├──▶ Capture: file, line, col, prefix, suffix
    │    │
    │    └──▶ intelligence_client.complete(request)
    │         │
    │         └──▶ POST http://localhost:3001/v1/complete
    │
    └──▶ Render: ghost text (inline suggestion)

Hover Request:
  User hovers symbol
    │
    ├──▶ hover.ts.provideHover()
    │    │
    │    ├──▶ Capture: file, symbol range
    │    │
    │    └──▶ intelligence_client.explain(request)
    │         │
    │         └──▶ POST http://localhost:3001/v1/explain
    │
    └──▶ Render: hover panel with explanation

Refactor Request:
  User selects code + presses Ctrl+Shift+R
    │
    ├──▶ refactor.ts.refactor()
    │    │
    │    ├──▶ Capture: file, selection range, instruction
    │    │
    │    └──▶ intelligence_client.refactor(request)
    │         │
    │         └──▶ POST http://localhost:3001/v1/refactor
    │
    └──▶ Render: diff view (original vs refactored)
```

### Keybindings

| Shortcut | Command | Handler |
|----------|---------|---------|
| `Ctrl+Shift+A` | `apex.complete` | `completion.ts` |
| `Ctrl+Shift+E` | `apex.explain` | `hover.ts` (selection) |
| `Ctrl+Shift+R` | `apex.refactor` | `refactor.ts` |
| `Hover symbol` | (automatic) | `hover.ts` |

---

## Contract Layer (Step 0)

### Immutable Contracts

| Contract | Purpose | Consumers |
|----------|---------|-----------|
| `contracts/inference_api.yaml` | Stage 1 output contract | Stage 2 (embedder, intelligence_server) |
| `contracts/intelligence_api.yaml` | Stage 2 output contract | Stage 3 (all components) |
| `contracts/models/hardware_profile.py` | GPU scan output schema | Stage 1 (all components) |
| `contracts/models/model_config.py` | Model selection schema | Stage 1 (model_selector, llama_server_manager) |
| `contracts/models/index_entry.py` | Index entry schema | Stage 2 (ast_indexer, call_graph, embedding_index) |
| `contracts/models/context_request.py` | Context packager schema | Stage 2 (context_packager, intelligence_server) |
| `contracts/models/completion_request.py` | Completion schema | Stage 2 (intelligence_server), Stage 3 (completion.ts) |
| `contracts/models/editor_adapter.py` | Editor capabilities schema | Stage 3 (all components) |

### Contract Enforcement

- **Immutable after Step 0**: No changes permitted after GATE-1
- **Generated before implementation**: All three stages generated against these contracts
- **Validation**: `openapi-spec-validator` for YAML, `mypy` for Pydantic models

---

## Stage Isolation

### Import Rules

| Stage | Can Import | Cannot Import |
|-------|------------|---------------|
| Stage 1 | `contracts/*` | `stage2/*`, `stage3/*` |
| Stage 2 | `contracts/*` | `stage1/*`, `stage3/*` |
| Stage 3 | `contracts/*` | `stage1/*`, `stage2/*` |

### Communication Rules

| Communication | Method |
|---------------|--------|
| Stage 3 → Stage 2 | HTTP POST/GET to `localhost:3001` (IntelligenceAPI) |
| Stage 2 → Stage 1 | HTTP POST/GET to `localhost:3000` (InferenceAPI) |
| Stage 1 → llama-server | HTTP POST/GET to `localhost:8080` (internal) |
| Stage 1 → Shared | Read/write `shared/hardware_profile.json` |
| Stage 2/3 → Shared | Read-only `shared/hardware_profile.json` |

### Enforcement Mechanism

```python
# tests/test_stage_isolation.py
def test_stage_isolation():
    """Grep-based enforcement of stage boundaries."""
    
    # Stage 1 must not import stage2 or stage3
    assert not grep("stage1/", r"from stage2|from stage3|import stage2|import stage3")
    
    # Stage 2 must not import stage1 or stage3
    assert not grep("stage2/", r"from stage1|from stage3|import stage1|import stage3")
    
    # Stage 3 must not import stage1 or stage2
    assert not grep("stage3/", r"from stage1|from stage2|import stage1|import stage2")
```

---

## Build Pipeline

### Topological Sort Levels

| Level | Files | Critic Gate |
|-------|-------|-------------|
| 0 | All contracts | GATE-1: Contract validation |
| 1 | `hardware_scanner.py`, `ast_indexer.py`, `embedder.py`, `adapter_interface.py` | GATE-2 |
| 2 | `model_selector.py`, `call_graph.py`, `embedding_index.py`, `extension.ts` | GATE-3 |
| 3 | `llama_server_manager.py`, `context_packager.py`, `file_watcher.py`, `completion.ts`, `hover.ts`, `status_bar.ts` | GATE-4 |
| 4 | `inference_proxy.py`, `intelligence_server.py`, `package.json` | GATE-5 |
| 5 | `stage1/main.py`, `stage2/main.py` | GATE-6 |

### Critic Passes (Per Level)

| Pass | Type | Tools |
|------|------|-------|
| PASS 1 | SYNTAX (no LLM) | `ast.parse()`, `mypy --strict`, `ruff check`, `tsc --noEmit`, `eslint`, `yamllint`, `openapi-spec-validator` |
| PASS 2 | CONTRACT (no LLM) | Function signatures match contracts, HTTP methods/paths correct, Pydantic imports resolve, stage isolation enforced |
| PASS 3 | COMPLETENESS (LLM) | No `pass`/`TODO`/`NotImplemented` in FR-required functions |
| PASS 4 | LOGIC (LLM) | Hardware scanner parses correctly, VRAM math prevents OOM, ranking prefers higher-score chunks, SSE streaming correct |

### Celery Execution Plan

```python
chain(
    chord(group(generate_level_0), critic_level_0),
    chord(group(generate_level_1), critic_level_1),
    chord(group(generate_level_2), critic_level_2),
    chord(group(generate_level_3), critic_level_3),
    chord(group(generate_level_4), critic_level_4),
    chord(group(generate_level_5), critic_level_5),
    chord(group(test_gen_all), test_critic_all),
    test_runner_task
)
```

**Critical Path**: `C0 → S1-A → S1-B → S1-C → S1-D → S1-E` (5 hops)

**Widest Parallel Level**: Level 3 (6 files simultaneously)

---

## Test Strategy

### Test Pyramid

```
                    ┌─────────────┐
                   │ Integration │  (test_full_pipeline.py)
                  │─────────────│
                 │   Stage 2     │  (test_ast_indexer.py, etc.)
                │───────────────│
               │    Stage 1      │  (test_hardware_scanner.py, etc.)
              │─────────────────│
             │    Isolation      │  (test_stage_isolation.py)
            └───────────────────┘
```

### Execution Order

1. `test_stage_isolation.py` (run first, always)
2. `tests/stage1/` (Stage 1 — no Stage 2/3 running)
3. `tests/stage2/` (Stage 2 — Stage 1 mocked)
4. `tests/stage3/` (Stage 3 — Stage 2 mocked)
5. `tests/integration/` (all three live, localhost ports)

### Test Types

| Type | Purpose | Example |
|------|---------|---------|
| Contract Tests | Validate response schemas match YAML specs | `test_completion_response_schema()` |
| Acceptance Tests | Per-FR validation with mocked inputs | `test_hardware_scanner_detects_gpu()` |
| Isolation Tests | Grep-based enforcement of stage boundaries | `test_no_stage2_imports_in_stage1()` |

---

## Deployment Architecture

### Docker Compose (Production)

```yaml
services:
  stage1:
    build: ./stage1
    ports:
      - "3000:3000"
    volumes:
      - ./stage1/data/models:/app/data/models:ro
      - ./shared:/app/shared
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]

  stage2:
    build: ./stage2
    ports:
      - "3001:3001"
    volumes:
      - ./workspace:/workspace:ro
      - ./stage2/data:/app/data
    environment:
      - INFERENCE_API_URL=http://stage1:3000

  stage3:
    # Distributed as .vsix, installed in user's VSCodium
```

### Port Allocation

| Service | Port | Exposure |
|---------|------|----------|
| Stage 1 (Inference Runtime) | 3000 | localhost (or Docker network) |
| Stage 2 (Codebase Intelligence) | 3001 | localhost (or Docker network) |
| llama-server (internal) | 8080 | Internal only (not exposed) |

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| Network exposure | localhost only, enforced in `intelligence_client.ts` |
| Model file access | Read-only mounts for model files |
| Subprocess isolation | `llama-server` runs in separate process, crash-isolated |
| Workspace access | Read-only mounts for workspace files (Stage 2) |

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cold start to first completion | < 30s (32GB VRAM) | End-to-end timing |
| Index 10,000 files (first build) | < 5 minutes | `ast_indexer` + `embedding_index` |
| Incremental re-index (changed file) | < 500ms | `file_watcher` → `ast_indexer` |
| Context assembly | < 100ms (before LLM call) | `context_packager.rank()` |
| Extension memory footprint | < 20MB | VSCodium process monitoring |

---

## File Structure

```
inference.saas/
├── contracts/                   # LEVEL 0, immutable after GATE-1
│   ├── inference_api.yaml       # OpenAPI spec for Stage 1
│   ├── intelligence_api.yaml    # OpenAPI spec for Stage 2
│   └── models/
│       ├── hardware_profile.py
│       ├── model_config.py
│       ├── index_entry.py
│       ├── context_request.py
│       ├── completion_request.py
│       └── editor_adapter.py
│
├── stage1/                      # Inference Runtime
│   ├── hardware_scanner.py      # nvidia-smi/rocm-smi → HardwareProfile
│   ├── model_selector.py        # VRAM budget → model + quant choice
│   ├── llama_server_manager.py  # subprocess spawn + watchdog + restart
│   ├── vram_monitor.py          # pynvml polling → /v1/health data
│   ├── inference_proxy.py       # FastAPI: forwards to llama-server
│   ├── main.py                  # startup: scan → select → spawn → serve
│   └── requirements.txt
│
├── stage2/                      # Codebase Intelligence
│   ├── ast_indexer.py           # tree-sitter → symbol map + SQLite
│   ├── call_graph.py            # networkx graph from AST output
│   ├── embedder.py              # calls Stage1 /v1/embeddings
│   ├── embedding_index.py       # hnswlib: build + query + persist
│   ├── context_packager.py      # hybrid rank: semantic + call graph
│   ├── file_watcher.py          # watchdog: re-index changed files
│   ├── search.py                # BM25 fallback when embedder absent
│   ├── intelligence_server.py   # FastAPI: IntelligenceAPI routes
│   └── main.py                  # startup: index → watch → serve
│
├── stage3/                      # Editor Adapter
│   ├── adapter_interface.py     # abstract EditorAdapter (Python ref)
│   └── vscodium/
│       ├── package.json         # extension manifest + contributes
│       ├── extension.ts         # activate: register all commands
│       ├── completion.ts        # on-demand completion provider
│       ├── hover.ts             # symbol hover → /v1/explain
│       ├── refactor.ts          # selection → /v1/refactor + diff view
│       ├── status_bar.ts        # model + index + VRAM status bar
│       ├── intelligence_client.ts  # typed HTTP client for intelligence_api
│       └── tsconfig.json
│
├── tests/
│   ├── test_stage_isolation.py  # grep-based isolation enforcement
│   ├── stage1/
│   │   ├── test_hardware_scanner.py
│   │   ├── test_model_selector.py
│   │   ├── test_server_manager.py
│   │   └── test_inference_api.py
│   ├── stage2/
│   │   ├── test_ast_indexer.py
│   │   ├── test_call_graph.py
│   │   ├── test_context_packager.py
│   │   └── test_intelligence_api.py
│   ├── stage3/
│   │   ├── test_adapter_interface.py
│   │   └── test_isolation.py
│   └── integration/
│       └── test_full_pipeline.py
│
├── shared/
│   ├── hardware_profile.json    # written Stage1 startup, read by all
│   └── ports.py                 # STAGE1_PORT=3000, STAGE2_PORT=3001
│
├── .vscode/                     # generated workspace config
│   ├── settings.json
│   ├── extensions.json
│   ├── launch.json
│   ├── tasks.json
│   └── apex.code-workspace
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── tasks.md
└── README.md
```
