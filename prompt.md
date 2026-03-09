AUTONOMOUS PRODUCTION ENGINEERING EXECUTOR — APEX
"A unified three-stage system: Stage 1 inference runtime (llama.cpp,
VRAM-optimized, OpenAI-compatible), Stage 2 codebase intelligence
(tree-sitter AST, embedding index, call graph, context packager),
Stage 3 abstract swappable editor interface — built contract-first so
each stage is independently replaceable without touching the others"

THE SPACE
─────────
Most AI coding tools fail for the same reason: they were built as
products first and systems never. The inference backend assumes it is
a standalone server. The code indexer assumes it is a plugin. The
editor assumes inference is someone else's problem. None of them
defined their interfaces before implementation so integration becomes
permanent duct tape.

APEX inverts this. Contracts are generated before a single
implementation file is touched. Stage 1 exposes InferenceAPI.
Stage 2 consumes InferenceAPI and exposes IntelligenceAPI. Stage 3
consumes IntelligenceAPI only — it does not know Stage 1 exists.
This means Stage 3 is fully swappable: VSCodium extension today,
Zed fork next month, custom Tauri editor when ready. The intelligence
is portable. The editor is a rendering decision.

On-demand completion only: one full model, fully loaded, triggered
by explicit user action. Zero background polling. 100% of VRAM goes
to model quality. The user gets the best possible response when they
ask, rather than a degraded response always running.

SYSTEM PROMPT
─────────────
Build APEX: a three-stage locally-running AI code intelligence system.
Stage 1: managed llama-server subprocess, VRAM-aware model/quant
selection, OpenAI-compatible API. Stage 2: tree-sitter AST indexer,
embedding index (small dedicated local embedder), call graph builder,
context packager — MCP server output. Stage 3: abstract adapter
interface, first implementation as VSCodium extension (.vsix).
All stages communicate via typed HTTP contracts defined in Step 0.
No stage is permitted to import from another stage's source.
All inter-stage communication goes through the contract API only.

HARD REQUIREMENTS
─────────────────
1. CONTRACTS FIRST (Step 0): inference_api.yaml and intelligence_api.yaml
   generated before any implementation. Immutable after Step 0.
   All three stages generated against these contracts as ground truth.
2. STAGE ISOLATION: Stage 1 source has zero knowledge of Stage 2 or 3.
   Stage 2 source has zero knowledge of Stage 3. Stage 3 source
   calls only intelligence_api.yaml endpoints — never Stage 1 directly.
3. HARDWARE SCAN BOOTSTRAP: Stage 1 scans GPU (nvidia-smi / rocm-smi),
   VRAM, CUDA version, installed llama-server binary before any model
   loads. Writes HardwareProfile. Model + quant selected from profile.
4. CRITIC GATE: no topo level advances until all files in that level
   pass all 4 critic passes. Max 3 repair attempts. HALT on failure.
5. DEDUP: all runs keyed by (workspace_hash + query_hash). Never
   re-index unchanged files. Never re-run identical completions.

Return valid JSON: { "files": [{ "path", "content", "language" }] }.
Minimum 45 files. Placeholder implementations acceptable.
Raw JSON only. No markdown, no code fences.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 0 — CONTRACT GENERATION (immutable ground truth)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  Generated before dependency graph. Before topological sort.       │
│  Before any implementation. Human reviews before GATE-1.           │
│                                                                     │
│  contracts/inference_api.yaml        Stage 1 output contract       │
│  ─────────────────────────────────────────────────────────────     │
│  POST /v1/completions                                               │
│    body:  { model, prompt, max_tokens, temperature, stream: bool } │
│    resp:  { id, choices: [{text, finish_reason}], usage }          │
│    stream: text/event-stream (SSE chunks)                          │
│                                                                     │
│  POST /v1/embeddings                                                │
│    body:  { model, input: string[] }                               │
│    resp:  { data: [{embedding: float[], index}], usage }           │
│                                                                     │
│  GET  /v1/models                                                    │
│    resp:  { models: [{id, path, quant, vram_gb, loaded: bool}] }  │
│                                                                     │
│  GET  /v1/health                                                    │
│    resp:  { status, vram_used_gb, vram_total_gb, model_loaded,    │
│             llama_server_pid, uptime_s }                           │
│                                                                     │
│  POST /v1/load                                                      │
│    body:  { model_path, quant_override? }                          │
│    resp:  { loaded: bool, vram_used_gb, model_id }                │
│                                                                     │
│  contracts/intelligence_api.yaml     Stage 2 output contract       │
│  ─────────────────────────────────────────────────────────────     │
│  POST /v1/context                                                   │
│    body:  { query, workspace_root, cursor_file?, cursor_line?,    │
│             max_chunks: int, strategy: semantic|callgraph|hybrid } │
│    resp:  { chunks: [{file, start_line, end_line, content,        │
│               score, reason}], total_tokens_est }                  │
│                                                                     │
│  POST /v1/complete                                                  │
│    body:  { file, line, col, prefix, suffix, max_tokens }         │
│    resp:  { completion, context_used: chunk_ids[],                │
│             model_used, latency_ms }                               │
│                                                                     │
│  POST /v1/explain                                                   │
│    body:  { file, start_line, end_line, question? }               │
│    resp:  { explanation, symbols_referenced[], context_used[] }   │
│                                                                     │
│  POST /v1/refactor                                                  │
│    body:  { file, start_line, end_line, instruction }             │
│    resp:  { original, refactored, diff, explanation }             │
│                                                                     │
│  GET  /v1/symbols?file=                                            │
│    resp:  { symbols: [{name, kind, file, line, col, docstring}] } │
│                                                                     │
│  GET  /v1/callgraph?symbol=                                        │
│    resp:  { callers: [], callees: [], depth_searched: int }       │
│                                                                     │
│  GET  /v1/index/status                                             │
│    resp:  { files_indexed, last_updated, embedding_model,         │
│             index_size_mb, watching: bool }                        │
│                                                                     │
│  POST /v1/index/rebuild                                            │
│    body:  { workspace_root, force: bool }                         │
│    resp:  { job_id, estimated_s }                                  │
│                                                                     │
│  contracts/models/                   Pydantic schemas              │
│    hardware_profile.py   GPU, VRAM, CUDA, llama_server path        │
│    model_config.py       ModelSpec, QuantLevel, VRAMBudget         │
│    index_entry.py        FileEntry, SymbolEntry, ChunkEntry        │
│    context_request.py    ContextQuery, ContextResult, Chunk        │
│    completion_request.py CompletionRequest, CompletionResult       │
│    editor_adapter.py     AdapterCapabilities, EditorEvent          │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — REQUIREMENTS EXTRACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1 — INFERENCE RUNTIME                                       │
│  FR-01  Detect GPU via nvidia-smi (NVIDIA) or rocm-smi (AMD)      │
│  FR-02  Select model + quant from VRAM budget automatically        │
│  FR-03  Spawn + manage llama-server subprocess (restart on crash)  │
│  FR-04  Expose OpenAI-compatible API matching inference_api.yaml   │
│  FR-05  Stream completions via SSE                                 │
│  FR-06  Batch embeddings for indexer (small embedder model)        │
│  FR-07  Hot-swap models without editor restart                     │
│  FR-08  Expose VRAM budget + model status via /v1/health           │
│                                                                     │
│  NFR-01  Cold start to first completion < 30s on 32GB VRAM GPU    │
│  NFR-02  Zero background inference — on-demand only                │
│  NFR-03  llama-server crash must not crash Stage 1 process         │
│  NFR-04  All model files accessed read-only                        │
│                                                                     │
│  STAGE 2 — CODEBASE INTELLIGENCE                                   │
│  FR-09  Tree-sitter AST parse all supported languages on index     │
│  FR-10  Build symbol map: functions, classes, imports per file     │
│  FR-11  Build call graph across files from AST output             │
│  FR-12  Chunk files + embed via Stage 1 embeddings endpoint        │
│  FR-13  Semantic search: query → ranked relevant chunks            │
│  FR-14  Context packager: assemble ranked chunks into LLM prompt  │
│  FR-15  Watch filesystem: re-index changed files only (dedup)     │
│  FR-16  Expose IntelligenceAPI matching intelligence_api.yaml      │
│                                                                     │
│  NFR-05  Index 10,000 file repo in < 5 minutes on first build     │
│  NFR-06  Incremental re-index changed file < 500ms                │
│  NFR-07  Context assembly < 100ms (before LLM call)               │
│  NFR-08  Embedding index survives process restart (persisted)      │
│                                                                     │
│  STAGE 3 — EDITOR ADAPTER (abstract + VSCodium first impl)        │
│  FR-17  Define EditorAdapter interface (swappable)                 │
│  FR-18  VSCodium .vsix extension consuming IntelligenceAPI only   │
│  FR-19  On-demand completion via keybind (no background polling)  │
│  FR-20  Inline diff view for refactor suggestions                 │
│  FR-21  Symbol hover: calls IntelligenceAPI /v1/explain           │
│  FR-22  Status bar: model loaded, index status, VRAM usage        │
│                                                                     │
│  NFR-09  Extension adds < 20MB to VSCodium memory footprint       │
│  NFR-10  All LLM calls cancellable (user presses Escape)          │
│  NFR-11  No network calls — localhost only, enforced              │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  USER KEYPRESS                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  STAGE 3: EDITOR ADAPTER                                   │    │
│  │  VSCodium Extension (.vsix)                                │    │
│  │  - Captures: cursor position, file, selection             │    │
│  │  - Calls:    POST intelligence_api/v1/complete             │    │
│  │  - Renders:  ghost text / diff view / hover panel         │    │
│  │  - Knows:    IntelligenceAPI only                         │    │
│  │  - Does NOT: import stage1/ or stage2/ source             │    │
│  └──────────────────────┬─────────────────────────────────────┘    │
│                         │ HTTP localhost:3001                       │
│                         ▼                                           │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  STAGE 2: CODEBASE INTELLIGENCE                            │    │
│  │  Python FastAPI server (port 3001)                         │    │
│  │                                                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │    │
│  │  │ AST Indexer  │  │ Call Graph   │  │ Embedding Index │ │    │
│  │  │ (tree-sitter)│  │ (networkx)   │  │ (hnswlib/faiss) │ │    │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘ │    │
│  │         └─────────────────┴──────────────────┘ │         │    │
│  │                           │                    │         │    │
│  │                    ┌──────▼────────────────────▼──────┐  │    │
│  │                    │  Context Packager               │  │    │
│  │                    │  (ranks + assembles prompt)      │  │    │
│  │                    └──────────────────────────────────┘  │    │
│  │                                                            │    │
│  │  Calls: InferenceAPI /v1/embeddings (embedder model)      │    │
│  │  Calls: InferenceAPI /v1/completions (main model)         │    │
│  └──────────────────────┬─────────────────────────────────────┘    │
│                         │ HTTP localhost:3000                       │
│                         ▼                                           │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  STAGE 1: INFERENCE RUNTIME                                │    │
│  │  Python FastAPI proxy (port 3000)                          │    │
│  │                                                            │    │
│  │  ┌──────────────────┐    ┌────────────────────────────┐  │    │
│  │  │ Hardware Scanner │    │ Model/Quant Selector       │  │    │
│  │  │ nvidia-smi probe │───▶│ VRAM budget → best fit    │  │    │
│  │  └──────────────────┘    └─────────────┬──────────────┘  │    │
│  │                                         │                 │    │
│  │                          ┌──────────────▼──────────────┐  │    │
│  │                          │ llama-server subprocess      │  │    │
│  │                          │ (managed, auto-restart)      │  │    │
│  │                          │ port 8080 (internal only)    │  │    │
│  │                          └─────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  PERSISTENCE:                                                       │
│  stage2/data/index.db      SQLite: symbols, files, chunks          │
│  stage2/data/embeddings/   hnswlib index (persisted vectors)       │
│  stage1/data/models/       GGUF model files (user-managed)         │
│  shared/hardware_profile.json  written by Stage 1, read by all    │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — DEPENDENCY GRAPH + CYCLE DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  NODES (files to generate):                                        │
│                                                                     │
│  [C0]  contracts/inference_api.yaml        no deps (Step 0)        │
│  [C1]  contracts/intelligence_api.yaml     no deps (Step 0)        │
│  [C2]  contracts/models/*.py               no deps (Step 0)        │
│                                                                     │
│  [S1-A] stage1/hardware_scanner.py         deps: [C2]              │
│  [S1-B] stage1/model_selector.py           deps: [C2, S1-A]        │
│  [S1-C] stage1/llama_server_manager.py     deps: [C2, S1-B]        │
│  [S1-D] stage1/inference_proxy.py          deps: [C0, S1-C]        │
│  [S1-E] stage1/main.py                     deps: [S1-D]            │
│                                                                     │
│  [S2-A] stage2/ast_indexer.py              deps: [C2]              │
│  [S2-B] stage2/call_graph.py               deps: [C2, S2-A]        │
│  [S2-C] stage2/embedder.py                 deps: [C0, C2]          │
│  [S2-D] stage2/embedding_index.py          deps: [C2, S2-C]        │
│  [S2-E] stage2/context_packager.py         deps: [C2, S2-B, S2-D] │
│  [S2-F] stage2/file_watcher.py             deps: [C2, S2-A, S2-D] │
│  [S2-G] stage2/intelligence_server.py      deps: [C1, S2-E, S2-F] │
│  [S2-H] stage2/main.py                     deps: [S2-G]            │
│                                                                     │
│  [S3-A] stage3/adapter_interface.py        deps: [C1, C2]          │
│  [S3-B] stage3/vscodium/extension.ts       deps: [C1, S3-A]        │
│  [S3-C] stage3/vscodium/completion.ts      deps: [C1, S3-B]        │
│  [S3-D] stage3/vscodium/hover.ts           deps: [C1, S3-B]        │
│  [S3-E] stage3/vscodium/status_bar.ts      deps: [C1, S3-B]        │
│  [S3-F] stage3/vscodium/package.json       deps: [S3-B]            │
│                                                                     │
│  CYCLE CHECK:                                                       │
│  Stage 1 → contracts only (no S2, no S3)    ✓ acyclic             │
│  Stage 2 → contracts + Stage 1 API only     ✓ acyclic             │
│  Stage 3 → contracts + Stage 2 API only     ✓ acyclic             │
│  No back edges detected → proceed to topo sort                     │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 — TOPOLOGICAL SORT → DERIVED BUILD PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  Kahn's algorithm on dependency graph → levels:                    │
│                                                                     │
│  LEVEL 0 (no deps — generate in parallel, critic together):        │
│    contracts/inference_api.yaml                                     │
│    contracts/intelligence_api.yaml                                  │
│    contracts/models/hardware_profile.py                             │
│    contracts/models/model_config.py                                 │
│    contracts/models/index_entry.py                                  │
│    contracts/models/context_request.py                              │
│    contracts/models/completion_request.py                           │
│    contracts/models/editor_adapter.py                               │
│                                                                     │
│  LEVEL 1 (deps: Level 0 only):                                     │
│    stage1/hardware_scanner.py                                       │
│    stage2/ast_indexer.py                                            │
│    stage2/embedder.py           (calls C0 contracts only)          │
│    stage3/adapter_interface.py                                      │
│                                                                     │
│  LEVEL 2 (deps: Level 0-1):                                        │
│    stage1/model_selector.py                                         │
│    stage2/call_graph.py                                             │
│    stage2/embedding_index.py                                        │
│    stage3/vscodium/extension.ts                                     │
│                                                                     │
│  LEVEL 3 (deps: Level 0-2):                                        │
│    stage1/llama_server_manager.py                                   │
│    stage2/context_packager.py                                       │
│    stage2/file_watcher.py                                           │
│    stage3/vscodium/completion.ts                                    │
│    stage3/vscodium/hover.ts                                         │
│    stage3/vscodium/status_bar.ts                                    │
│                                                                     │
│  LEVEL 4 (deps: Level 0-3):                                        │
│    stage1/inference_proxy.py                                        │
│    stage2/intelligence_server.py                                    │
│    stage3/vscodium/package.json                                     │
│                                                                     │
│  LEVEL 5 (deps: Level 0-4):                                        │
│    stage1/main.py                                                   │
│    stage2/main.py                                                   │
│                                                                     │
│  CELERY EXECUTION PLAN (auto-derived):                             │
│  chain(                                                             │
│    chord(group(generate_level_0), critic_level_0),                 │
│    chord(group(generate_level_1), critic_level_1),                 │
│    chord(group(generate_level_2), critic_level_2),                 │
│    chord(group(generate_level_3), critic_level_3),                 │
│    chord(group(generate_level_4), critic_level_4),                 │
│    chord(group(generate_level_5), critic_level_5),                 │
│    chord(group(test_gen_all), test_critic_all),                    │
│    test_runner_task                                                 │
│  )                                                                  │
│                                                                     │
│  CRITICAL PATH: C0→S1-A→S1-B→S1-C→S1-D→S1-E (5 hops)            │
│  WIDEST PARALLEL LEVEL: Level 3 (6 files simultaneously)           │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 — PER-LEVEL PARALLEL GENERATION + 4-PASS CRITIC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  FOR EACH LEVEL L:                                                  │
│                                                                     │
│  GENERATION (all files in L, parallel):                            │
│  Context per file: {                                                │
│    contracts: [relevant contracts/],                                │
│    fr_refs: [FRs this file satisfies],                             │
│    locked_deps: [all files from levels 0..L-1],                   │
│    language_patterns: [Python FastAPI | TypeScript VSCode API]     │
│  }                                                                  │
│                                                                     │
│  PASS 1 — SYNTAX (no LLM):                                        │
│  Python: ast.parse() + mypy --strict + ruff check                 │
│  TypeScript: tsc --noEmit + eslint                                 │
│  YAML: yamllint + openapi-spec-validator                           │
│                                                                     │
│  PASS 2 — CONTRACT (no LLM):                                      │
│  → Every function signature matches contracts/interfaces exactly   │
│  → Every HTTP call uses correct method+path from api YAML         │
│  → Every Pydantic model import resolves to contracts/models/       │
│  → Stage 3 files: grep for any stage1/ imports → FAIL immediately │
│  → Stage 2 files: grep for any stage3/ imports → FAIL immediately │
│                                                                     │
│  PASS 3 — COMPLETENESS (LLM):                                     │
│  → No pass/TODO/NotImplemented in FR-required functions           │
│  → Hardware scanner: all nvidia-smi fields actually parsed        │
│  → Model selector: VRAM math complete (not stubbed)               │
│  → Context packager: ranking logic present (not placeholder)      │
│                                                                     │
│  PASS 4 — LOGIC (LLM):                                            │
│  → hardware_scanner: does it correctly derive memory_bandwidth?   │
│  → model_selector: does VRAM budget math prevent OOM?             │
│  → context_packager: does ranking prefer higher-score chunks?     │
│  → inference_proxy: does streaming SSE correctly forward chunks?  │
│  → adapter_interface: are all EditorAdapter methods abstract?     │
│                                                                     │
│  ALL PASS → lock level → advance                                   │
│  ANY FAIL → Phase 6 micro-repair                                  │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 6 — MICRO-REPAIR LOOP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  Max 3 attempts per file. Scope: single file only.                 │
│  Never modify contracts/. Fix implementation to match contract.    │
│                                                                     │
│  REPAIR CONTEXT:                                                    │
│  { failing_file, failing_passes[], contract, fr_refs,             │
│    prior_attempts[], stage_isolation_rules }                       │
│                                                                     │
│  stage_isolation_rules (appended to every repair prompt):          │
│  "Stage 1 files MUST NOT import from stage2/ or stage3/.          │
│   Stage 2 files MUST NOT import from stage3/.                     │
│   Stage 3 files MUST ONLY call localhost:3001 endpoints.           │
│   Violation of stage isolation = automatic FAIL regardless         │
│   of all other passes."                                            │
│                                                                     │
│  HALT → CRITIC_BLOCKED.md + GATE-4 page. Full stop.               │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 7 — TEST GENERATION (topo-mirrored)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  TYPE 1 — CONTRACT TESTS (template-generated, no LLM):            │
│  tests/stage1/test_inference_api_contract.py                       │
│    → POST /v1/completions with valid body → assert response schema │
│    → POST /v1/embeddings → assert data[].embedding is float[]     │
│    → GET  /v1/health → assert all required fields present          │
│                                                                     │
│  tests/stage2/test_intelligence_api_contract.py                    │
│    → POST /v1/context → assert chunks[].score is float 0-1       │
│    → POST /v1/complete → assert completion is string              │
│    → GET  /v1/symbols → assert symbols[].kind in valid_kinds      │
│                                                                     │
│  TYPE 2 — ACCEPTANCE TESTS (per FR, LLM-generated):               │
│  tests/stage1/test_hardware_scanner.py                             │
│    → FR-01: mock nvidia-smi output → assert GPU name extracted    │
│    → FR-02: mock 24GB VRAM → assert Q4_K_M selected for 13B      │
│    → FR-03: mock llama-server crash → assert auto-restart fires   │
│                                                                     │
│  tests/stage2/test_ast_indexer.py                                  │
│    → FR-09: parse Python file → assert function symbols found     │
│    → FR-10: parse import → assert dependency edge created         │
│    → FR-15: modify file → assert only that file re-indexed        │
│                                                                     │
│  tests/stage3/test_adapter_interface.py                            │
│    → FR-17: assert adapter_interface has all abstract methods     │
│    → FR-19: mock keypress → assert exactly one /v1/complete call  │
│    → NFR-11: assert no calls to localhost:3000 from stage3        │
│                                                                     │
│  TYPE 3 — ISOLATION TESTS (enforced mechanically):                │
│  tests/test_stage_isolation.py                                     │
│    → grep stage1/ for any "from stage2" or "from stage3" → FAIL  │
│    → grep stage2/ for any "from stage3" → FAIL                    │
│    → grep stage3/ for any ":3000" (Stage 1 port) → FAIL          │
│    → These run FIRST in CI. Isolation violation = hard stop.      │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 8 — TEST EXECUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  ORDER:                                                             │
│  1. test_stage_isolation.py   (isolation — run first, always)     │
│  2. tests/stage1/             (Stage 1 — no Stage 2/3 running)    │
│  3. tests/stage2/             (Stage 2 — Stage 1 mocked)          │
│  4. tests/stage3/             (Stage 3 — Stage 2 mocked)          │
│  5. tests/integration/        (all three live, localhost ports)    │
│                                                                     │
│  All external calls mocked in unit tests (no live llama-server)   │
│  Integration tests require: llama-server binary in PATH           │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 9 — SELF-REPAIR LOOP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  RUNTIME REPAIR TRIGGERS:                                          │
│  T1 — llama-server process exits unexpectedly                      │
│       → llama_server_manager.py catches exit → restart with       │
│         same args → log crash reason → emit /v1/health warning    │
│                                                                     │
│  T2 — OOM kill (VRAM exceeded)                                     │
│       → detect exit code 137 or CUDA OOM in stderr               │
│       → model_selector: drop one quant level → reload             │
│       → if already at minimum quant → HALT + surface to user      │
│                                                                     │
│  T3 — Index corruption (SQLite integrity check fails)             │
│       → drop and rebuild index automatically                      │
│       → file_watcher pauses during rebuild                        │
│                                                                     │
│  T4 — Stage 2 cannot reach Stage 1 (connection refused)           │
│       → retry with backoff (1s, 2s, 4s, 8s)                      │
│       → after 4 retries: attempt Stage 1 restart                 │
│       → surface status in /v1/index/status                        │
│                                                                     │
│  T5 — Embedding model not found                                    │
│       → fall back to keyword search (BM25) automatically          │
│       → log degraded mode in /v1/health                           │
│       → semantic search disabled until embedder available         │
│                                                                     │
│  REPAIR PHILOSOPHY:                                                 │
│  → Degrade gracefully before halting                               │
│  → Never surface a crash to Stage 3 — always return an error      │
│    response with { error, degraded_mode, action_required }        │
│  → Stage 3 renders degraded state in status bar, never crashes    │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILES PER MODULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  contracts/                   ← LEVEL 0, immutable after GATE-1   │
│    inference_api.yaml         OpenAPI spec for Stage 1             │
│    intelligence_api.yaml      OpenAPI spec for Stage 2             │
│    models/hardware_profile.py                                       │
│    models/model_config.py                                           │
│    models/index_entry.py                                            │
│    models/context_request.py                                        │
│    models/completion_request.py                                     │
│    models/editor_adapter.py                                         │
│                                                                     │
│  stage1/                      ← Inference Runtime                  │
│    hardware_scanner.py        nvidia-smi/rocm-smi → HardwareProfile│
│    model_selector.py          VRAM budget → model + quant choice   │
│    llama_server_manager.py    subprocess spawn + watchdog + restart│
│    inference_proxy.py         FastAPI: forwards to llama-server    │
│    vram_monitor.py            pynvml polling → /v1/health data     │
│    main.py                    startup: scan → select → spawn → serve│
│    requirements.txt                                                 │
│                                                                     │
│  stage2/                      ← Codebase Intelligence              │
│    ast_indexer.py             tree-sitter → symbol map + SQLite    │
│    call_graph.py              networkx graph from AST output       │
│    embedder.py                calls Stage1 /v1/embeddings          │
│    embedding_index.py         hnswlib: build + query + persist     │
│    context_packager.py        hybrid rank: semantic + call graph   │
│    file_watcher.py            watchdog: re-index changed files     │
│    intelligence_server.py     FastAPI: IntelligenceAPI routes      │
│    search.py                  BM25 fallback when embedder absent   │
│    main.py                    startup: index → watch → serve       │
│    requirements.txt                                                 │
│                                                                     │
│  stage3/                      ← Editor Adapter                     │
│    adapter_interface.py       abstract EditorAdapter (Python ref)  │
│    vscodium/                                                        │
│      package.json             extension manifest + contributes     │
│      extension.ts             activate: register all commands      │
│      completion.ts            on-demand completion provider        │
│      hover.ts                 symbol hover → /v1/explain           │
│      refactor.ts              selection → /v1/refactor + diff view │
│      status_bar.ts            model + index + VRAM status bar      │
│      intelligence_client.ts   typed HTTP client for intelligence_api│
│      tsconfig.json                                                  │
│                                                                     │
│  tests/                                                             │
│    test_stage_isolation.py    grep-based isolation enforcement     │
│    stage1/                                                          │
│      test_hardware_scanner.py mock nvidia-smi → profile            │
│      test_model_selector.py   VRAM scenarios → correct quant       │
│      test_server_manager.py   crash → restart behavior             │
│      test_inference_api.py    contract compliance                  │
│    stage2/                                                          │
│      test_ast_indexer.py      parse fixtures → symbols             │
│      test_call_graph.py       cross-file edges correct             │
│      test_context_packager.py ranking order deterministic          │
│      test_intelligence_api.py contract compliance                  │
│    stage3/                                                          │
│      test_adapter_interface.py all methods abstract                │
│      test_isolation.py        no direct Stage 1 calls              │
│    integration/                                                     │
│      test_full_pipeline.py    live: keypress → completion          │
│                                                                     │
│  shared/                                                            │
│    hardware_profile.json      written Stage1 startup, read by all │
│    ports.py                   STAGE1_PORT=3000, STAGE2_PORT=3001  │
│                                                                     │
│  .vscode/                     ← generated workspace config        │
│    settings.json              file nesting, exclude dirs           │
│    extensions.json            pylance, ruff, eslint, gitlens       │
│    launch.json                debug Stage1 / Stage2 / both        │
│    tasks.json                 start all stages, run tests per level│
│    apex.code-workspace        multi-root: stage1/ stage2/ stage3/ │
│                                                                     │
│  tasks.md                     ← build checklist                    │
│  docker-compose.yml           stage1 + stage2 as services         │
│  .env.example                                                       │
│  README.md                                                          │
└─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASKS.MD (generated, updated by build pipeline)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────────────────────────────────────────────────────────┐
│  # APEX Build Tasks                                                 │
│                                                                     │
│  ## Step 0 — Contracts (immutable after approval)                  │
│  ( ) contracts/inference_api.yaml                                  │
│  ( ) contracts/intelligence_api.yaml                               │
│  ( ) contracts/models/*.py                                         │
│                                                                     │
│  ## Stage 1 — Inference Runtime                                    │
│  ( ) hardware_scanner         FR-01, FR-02                         │
│  ( ) model_selector           FR-02, FR-07                         │
│  ( ) llama_server_manager     FR-03, FR-08, NFR-03                 │
│  ( ) inference_proxy          FR-04, FR-05, FR-06                  │
│  ( ) vram_monitor             FR-08                                 │
│  ( ) stage1/main.py                                                 │
│                                                                     │
│  ## Stage 2 — Codebase Intelligence                                │
│  ( ) ast_indexer              FR-09, FR-10                         │
│  ( ) call_graph               FR-11                                 │
│  ( ) embedder                 FR-12                                 │
│  ( ) embedding_index          FR-13                                 │
│  ( ) context_packager         FR-14                                 │
│  ( ) file_watcher             FR-15                                 │
│  ( ) intelligence_server      FR-16                                 │
│  ( ) stage2/main.py                                                 │
│                                                                     │
│  ## Stage 3 — Editor Adapter                                       │
│  ( ) adapter_interface        FR-17                                 │
│  ( ) vscodium/extension.ts    FR-18                                 │
│  ( ) vscodium/completion.ts   FR-19                                 │
│  ( ) vscodium/hover.ts        FR-21                                 │
│  ( ) vscodium/refactor.ts     FR-20                                 │
│  ( ) vscodium/status_bar.ts   FR-22                                 │
│                                                                     │
│  ## Tests                                                           │
│  ( ) test_stage_isolation.py                                       │
│  ( ) stage1 test suite                                              │
│  ( ) stage2 test suite                                              │
│  ( ) stage3 test suite                                              │
│  ( ) integration tests                                              │
│                                                                     │
│  ## Infrastructure                                                  │
│  ( ) docker-compose.yml                                             │
│  ( ) .vscode/ workspace config                                      │
│  ( ) README.md                                                      │
└─────────────────────────────────────────────────────────────────────┘

.VSCODE/TASKS.JSON (generated — run stages independently):
┌─────────────────────────────────────────────────────────────────────┐
│  tasks:                                                             │
│  "Start Stage 1"   → cd stage1 && python main.py                  │
│  "Start Stage 2"   → cd stage2 && python main.py                  │
│  "Start All"       → docker-compose up                             │
│  "Test Isolation"  → pytest tests/test_stage_isolation.py -v      │
│  "Test Stage 1"    → pytest tests/stage1/ -v                      │
│  "Test Stage 2"    → pytest tests/stage2/ -v                      │
│  "Test Stage 3"    → pytest tests/stage3/ -v                      │
│  "Test All"        → pytest tests/ -v --tb=short                  │
│  "Build Extension" → cd stage3/vscodium && npm run compile        │
│  "Package .vsix"   → cd stage3/vscodium && vsce package           │
└─────────────────────────────────────────────────────────────────────┘

PRICING / DISTRIBUTION:
┌─────────────────────────────────────────────────────────────────────┐
│  Open core model:                                                   │
│  Free   → Stage 1 + Stage 2 + VSCodium extension (self-hosted)    │
│  Pro    → $20/mo → model management UI, index dashboard,          │
│           multi-workspace, priority support                        │
│  Teams  → $50/user/mo → shared inference server, team context,    │
│           codebase snapshots, audit log                            │
│                                                                     │
│  $1B path: 1.67M Pro users OR 333k Teams seats                    │
│  Comparable: Cursor $20/mo hit $200M ARR in 2 years               │
│  Differentiator: fully offline, no data leaves machine,            │
│  actual codebase intelligence (not file injection),                │
│  swappable editor (not locked to one surface)                      │
└─────────────────────────────────────────────────────────────────────┘

README.md spec:
┌─────────────────────────────────────────────────────────────────────┐
│  # APEX — Autonomous Production Engineering Executor               │
│  ## What this is                                                    │
│  Three stages. One system. Fully offline.                          │
│  Stage 1: runs your local LLM (llama.cpp)                         │
│  Stage 2: understands your codebase (AST + embeddings + callgraph) │
│  Stage 3: editor integration (VSCodium extension today,            │
│           Zed / custom editor when ready)                          │
│  ## Prerequisites                                                   │
│  - llama-server binary in PATH (build from llama.cpp)             │
│  - At least one GGUF model in stage1/models/                      │
│  - Python 3.11+ | Node 20+                                        │
│  - NVIDIA GPU (CUDA 12+) or Apple Silicon (Metal) or CPU fallback │
│  ## Start in 3 commands                                             │
│  docker-compose up -d          # starts Stage 1 + Stage 2         │
│  code --install-extension apex.vsix   # installs Stage 3          │
│  Open any project folder in VSCodium → APEX indexes automatically │
│  ## Use it                                                          │
│  Ctrl+Shift+A  → on-demand completion at cursor                   │
│  Ctrl+Shift+E  → explain selected code                            │
│  Ctrl+Shift+R  → refactor with instruction                        │
│  Hover symbol  → inline explanation + callers/callees             │
│  Status bar    → model loaded, index size, VRAM used              │
│  ## Add a new editor (Stage 3 is swappable)                        │
│  Implement EditorAdapter interface in stage3/                      │
│  Call only localhost:3001 endpoints (intelligence_api.yaml)        │
│  Stage 1 and Stage 2 require zero changes                          │
└─────────────────────────────────────────────────────────────────────┘

Key contracts (ground truth — never modified after GATE-1):
inference_api.yaml    → stage1/ implements, stage2/ consumes
intelligence_api.yaml → stage2/ implements, stage3/ consumes
contracts/models/     → all stages import, none modify
shared/ports.py       → single source of truth for port numbers