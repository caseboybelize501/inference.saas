# APEX — Autonomous Production Engineering Executor

**AI-powered code intelligence with on-demand completions, explanations, and refactoring.**

A unified three-stage system:
- **Stage 1**: Inference runtime (llama.cpp, VRAM-optimized, OpenAI-compatible)
- **Stage 2**: Codebase intelligence (tree-sitter AST, embedding index, call graph, context packager)
- **Stage 3**: Abstract swappable editor interface (VSCodium extension first implementation)

Built **contract-first** so each stage is independently replaceable without touching the others.

---

## Quick Start

### Prerequisites

- NVIDIA GPU with CUDA 12+ (or AMD ROCm / Apple Silicon)
- `llama-server` binary in PATH (from [llama.cpp](https://github.com/ggerganov/llama.cpp))
- Python 3.11+
- Node.js 20+ (for VSCodium extension)
- Docker + Docker Compose (optional, for containerized deployment)

### Installation

#### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/inference.saas.git
cd inference.saas

# Copy environment file
cp .env.example .env

# Place GGUF models in stage1/data/models/
# Example: llama-7B-Q8_0.gguf

# Start services
docker-compose up -d

# Check status
docker-compose logs -f
```

#### Option 2: Local Development

```bash
# Stage 1: Inference Runtime
cd stage1
pip install -r requirements.txt
python main.py

# Stage 2: Codebase Intelligence (new terminal)
cd stage2
pip install -r requirements.txt
python main.py

# Stage 3: VSCodium Extension (new terminal)
cd stage3/vscodium
npm install
npm run compile
# Load extension in VSCodium: Extensions → ⋯ → Install from VSIX
```

### VSCodium Extension Installation

```bash
cd stage3/vscodium
npm install
npm run compile
vsce package  # Creates apex-code-intelligence-1.0.0.vsix

# Install in VSCodium
code --install-extension apex-code-intelligence-1.0.0.vsix
```

---

## Keybindings

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+A` | Trigger on-demand completion at cursor |
| `Ctrl+Shift+E` | Explain selected code |
| `Ctrl+Shift+R` | Refactor selection with instruction |
| `Hover symbol` | Inline explanation + callers/callees |

---

## Architecture

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
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP localhost:3001
                       ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 2: CODEBASE INTELLIGENCE                            │
│  Python FastAPI server (port 3001)                         │
│  - AST Indexer (tree-sitter) → Symbol map                  │
│  - Call Graph (networkx) → Cross-file relationships        │
│  - Embedding Index (hnswlib) → Semantic search             │
│  - Context Packager → Hybrid ranking                       │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP localhost:3000
                       ▼
┌────────────────────────────────────────────────────────────┐
│  STAGE 1: INFERENCE RUNTIME                                │
│  Python FastAPI proxy (port 3000)                          │
│  - Hardware Scanner → GPU detection (nvidia-smi/rocm-smi)  │
│  - Model Selector → VRAM budget → best fit                 │
│  - llama-server subprocess → Managed, auto-restart         │
│  - OpenAI-compatible API → /v1/completions, /v1/embeddings │
└────────────────────────────────────────────────────────────┘
```

### Stage Isolation

| Stage | Can Import | Cannot Import | Communication |
|-------|------------|---------------|---------------|
| Stage 1 | `contracts/*` | `stage2/*`, `stage3/*` | HTTP (port 3000) |
| Stage 2 | `contracts/*` | `stage1/*`, `stage3/*` | HTTP (port 3001) |
| Stage 3 | `contracts/*` | `stage1/*`, `stage2/*` | HTTP to Stage 2 only |

---

## API Endpoints

### Stage 1: Inference API (port 3000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/completions` | POST | Generate text completion (SSE streaming supported) |
| `/v1/embeddings` | POST | Generate embeddings for text |
| `/v1/models` | GET | List available/loaded models |
| `/v1/health` | GET | Server health + VRAM status |
| `/v1/load` | POST | Load model from path |

### Stage 2: Intelligence API (port 3001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/context` | POST | Get ranked context for query |
| `/v1/complete` | POST | Generate code completion |
| `/v1/explain` | POST | Explain code selection |
| `/v1/refactor` | POST | Refactor code with instruction |
| `/v1/symbols` | GET | List symbols in file |
| `/v1/callgraph` | GET | Get call graph for symbol |
| `/v1/index/status` | GET | Get index build status |
| `/v1/index/rebuild` | POST | Rebuild codebase index |

---

## Project Structure

```
inference.saas/
├── contracts/                    # Step 0: Immutable contracts
│   ├── inference_api.yaml        # Stage 1 OpenAPI spec
│   ├── intelligence_api.yaml     # Stage 2 OpenAPI spec
│   └── models/                   # Pydantic schemas
│       ├── hardware_profile.py
│       ├── model_config.py
│       ├── index_entry.py
│       ├── context_request.py
│       ├── completion_request.py
│       └── editor_adapter.py
│
├── stage1/                       # Inference Runtime
│   ├── hardware_scanner.py       # GPU detection
│   ├── model_selector.py         # VRAM-based model selection
│   ├── llama_server_manager.py   # Subprocess management
│   ├── vram_monitor.py           # VRAM polling
│   ├── inference_proxy.py        # FastAPI server
│   ├── main.py                   # Entry point
│   ├── requirements.txt
│   └── Dockerfile
│
├── stage2/                       # Codebase Intelligence
│   ├── ast_indexer.py            # Tree-sitter parsing
│   ├── call_graph.py             # NetworkX call graph
│   ├── embedder.py               # Embeddings client
│   ├── embedding_index.py        # HNSWLib vector index
│   ├── context_packager.py       # Context ranking
│   ├── file_watcher.py           # Incremental re-indexing
│   ├── search.py                 # BM25 fallback
│   ├── intelligence_server.py    # FastAPI server
│   ├── main.py                   # Entry point
│   ├── requirements.txt
│   └── Dockerfile
│
├── stage3/                       # Editor Adapter
│   ├── adapter_interface.py      # Abstract interface
│   └── vscodium/                 # VSCodium extension
│       ├── extension.ts
│       ├── intelligence_client.ts
│       ├── completion.ts
│       ├── hover.ts
│       ├── status_bar.ts
│       ├── package.json
│       └── tsconfig.json
│
├── shared/                       # Shared configuration
│   ├── ports.py
│   └── hardware_profile.json
│
├── tests/                        # Test suite
│   ├── test_stage_isolation.py   # Grep-based isolation tests
│   ├── stage1/                   # Stage 1 unit tests
│   ├── stage2/                   # Stage 2 unit tests
│   ├── stage3/                   # Stage 3 unit tests
│   └── integration/              # End-to-end tests
│
├── .vscode/                      # VS Code configuration
│   ├── settings.json
│   ├── launch.json
│   ├── tasks.json
│   └── extensions.json
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── README.md
```

---

## Development

### Running Tests

```bash
# All tests
pytest tests -v

# Stage isolation tests (run first)
pytest tests/test_stage_isolation.py -v

# Per-stage tests
pytest tests/stage1 -v
pytest tests/stage2 -v
pytest tests/stage3 -v

# Integration tests (requires running services)
pytest tests/integration -v
```

### Debugging

Use VS Code launch configurations:
- **Stage 1: Inference Runtime** — Debug Stage 1 server
- **Stage 2: Codebase Intelligence** — Debug Stage 2 server
- **Stage 3: Extension** — Debug VSCodium extension
- **Pytest: All Tests** — Run test suite with debugger

### Building the Extension

```bash
cd stage3/vscodium
npm install
npm run compile
vsce package
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Cold start to first completion | < 30s (32GB VRAM) |
| Index 10,000 files (first build) | < 5 minutes |
| Incremental re-index (changed file) | < 500ms |
| Context assembly | < 100ms |
| Extension memory footprint | < 20MB |

---

## Self-Repair Mechanisms

| Trigger | Detection | Response |
|---------|-----------|----------|
| llama-server exits | Process exit event | Auto-restart with same args |
| OOM kill | Exit code 137 / CUDA error | Drop quant level, reload |
| Index corruption | SQLite integrity check | Drop and rebuild index |
| Connection refused | HTTP 503 | Retry with backoff (1s, 2s, 4s, 8s) |
| Embedding model not found | Stage 1 returns 404 | Fall back to BM25 |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STAGE1_PORT` | Stage 1 HTTP port | 3000 |
| `STAGE2_PORT` | Stage 2 HTTP port | 3001 |
| `APEX_WORKSPACE` | Workspace to index | Current directory |
| `MODEL_DIR` | GGUF models directory | `stage1/data/models` |
| `INFERENCE_API_URL` | Stage 1 URL for Stage 2 | `http://localhost:3000` |

### Model Selection

Models are auto-selected based on available VRAM:

| GPU VRAM | Recommended Model |
|----------|-------------------|
| 8GB | 7B Q4_K_M |
| 12GB | 7B Q8_0 or 13B Q4_K_M |
| 16GB | 13B Q8_0 |
| 24GB | 34B Q4_K_M or 70B Q4_0 |
| 40GB+ | 70B Q8_0 |

---

## License

MIT License — see LICENSE file for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Python: Black formatting, Ruff linting, strict type hints
- TypeScript: ESLint, Prettier
- All changes must pass tests and stage isolation checks

---

## Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) — Efficient LLM inference
- [tree-sitter](https://tree-sitter.github.io/) — Incremental parsing
- [hnswlib](https://github.com/nmslib/hnswlib) — Approximate nearest neighbors
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [VS Code Extension API](https://code.visualstudio.com/api) — Editor integration
