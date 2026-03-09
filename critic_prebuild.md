# Code Critic: Pre-Build Assessment

**APEX Architecture vs. Current Implementation**

Assessment Date: 2026-03-08

---

## Executive Summary

**VERDICT: RETURN TO PHASE 1**

The current implementation diverges significantly from the APEX vision defined in `prompt.md` and `requirements.md`. The architecture has been reinterpreted as a cloud-based SaaS platform ("IOAS" — Inference Optimization as a Service) rather than the locally-running three-stage AI code intelligence system originally specified.

---

## Critical Gaps

### 1. Missing Contract Layer (Step 0) ✗

**Requirement:** Contracts must be generated before any implementation.

| Expected Contract | Status |
|-------------------|--------|
| `contracts/inference_api.yaml` | **Missing** |
| `contracts/intelligence_api.yaml` | **Missing** |
| `contracts/models/hardware_profile.py` | **Missing** |
| `contracts/models/model_config.py` | **Missing** |
| `contracts/models/index_entry.py` | **Missing** |
| `contracts/models/context_request.py` | **Missing** |
| `contracts/models/completion_request.py` | **Missing** |
| `contracts/models/editor_adapter.py` | **Missing** |

**Impact:** No immutable ground truth exists. All implementation is unmoored from specification.

---

### 2. Stage Architecture Violation ✗

**Requirement:** Three-stage system with strict isolation:
- Stage 1: Inference runtime (llama.cpp, VRAM-optimized, OpenAI-compatible)
- Stage 2: Codebase intelligence (tree-sitter AST, embedding index, call graph)
- Stage 3: Editor adapter (VSCodium extension)

**Current Implementation:**
| Expected Stage | Actual Implementation | Gap |
|----------------|----------------------|-----|
| Stage 1: `stage1/` with llama-server management | `agent/` — Remote telemetry agent | Complete mismatch |
| Stage 2: `stage2/` with AST indexer, call graph, context packager | `platform/` — Cloud API with optimization engine | Different purpose |
| Stage 3: `stage3/` with VSCodium extension | `dashboard/` — React web dashboard | Different interface |

**Key Missing Components:**
- `llama_server_manager.py` — No subprocess management
- `ast_indexer.py` — No tree-sitter integration
- `call_graph.py` — No networkx call graph
- `embedding_index.py` — No hnswlib/faiss vector index
- `context_packager.py` — No context assembly
- `file_watcher.py` — No watchdog file monitoring
- `vscodium/` extension — No editor integration

---

### 3. Stage Isolation Violation ✗

**Requirement:** No stage imports from another stage's source. All communication via typed HTTP contracts.

**Current Implementation Analysis:**

| Module | Imports From | Violation |
|--------|--------------|-----------|
| `platform/api/clusters.py` | `agent/config.py` | ✗ Platform imports Agent |
| `platform/api/optimizations.py` | `platform/workers/*` | Acceptable (same module) |
| `platform/learning/recommender.py` | `platform/learning/*` | Acceptable (same module) |
| `platform/engine/optimization_bundle.py` | `platform/engine/*` | Acceptable (same module) |

**Assessment:** The current architecture uses a monolithic `platform/` module rather than three isolated stages. The `agent/` module is a remote telemetry client, not a local inference runtime.

---

### 4. Core Functional Requirements Missing ✗

#### Stage 1 Requirements (FR-01 to FR-08)

| FR | Requirement | Status |
|----|-------------|--------|
| FR-01 | GPU Detection via nvidia-smi/rocm-smi | ✗ `agent/hw_scanner.py` exists but designed for telemetry, not model selection |
| FR-02 | Model + Quant Selection from VRAM | **Missing** |
| FR-03 | llama-server Subprocess Management | **Missing** |
| FR-04 | OpenAI-Compatible API | **Missing** (no `/v1/completions`, `/v1/embeddings`) |
| FR-05 | SSE Streaming | **Missing** |
| FR-06 | Batch Embeddings | **Missing** |
| FR-07 | Hot-Swap Models | **Missing** |
| FR-08 | Health Endpoint | ✗ Partial (telemetry exists but not `/v1/health` contract) |

#### Stage 2 Requirements (FR-09 to FR-16)

| FR | Requirement | Status |
|----|-------------|--------|
| FR-09 | Tree-sitter AST Indexing | **Missing** |
| FR-10 | Symbol Map | **Missing** |
| FR-11 | Call Graph Builder | **Missing** |
| FR-12 | Chunking + Embedding | **Missing** |
| FR-13 | Semantic Search | **Missing** |
| FR-14 | Context Packager | **Missing** |
| FR-15 | File Watching (dedup) | **Missing** |
| FR-16 | Intelligence API | ✗ Partial (FastAPI exists but not `intelligence_api.yaml` contract) |

#### Stage 3 Requirements (FR-17 to FR-22)

| FR | Requirement | Status |
|----|-------------|--------|
| FR-17 | EditorAdapter Interface | **Missing** |
| FR-18 | VSCodium Extension | **Missing** |
| FR-19 | On-Demand Completion (keybind) | **Missing** |
| FR-20 | Inline Diff View | **Missing** |
| FR-21 | Symbol Hover | **Missing** |
| FR-22 | Status Bar | ✗ Partial (dashboard exists but not as editor status bar) |

---

### 5. Non-Functional Requirements Gap ✗

| NFR | Target | Current Status |
|-----|--------|----------------|
| NFR-01 | Cold start < 30s | N/A — No cold start path |
| NFR-02 | Zero background inference | N/A — No inference |
| NFR-03 | Crash isolation | N/A — No subprocess |
| NFR-05 | Index 10,000 files < 5 min | N/A — No indexer |
| NFR-06 | Incremental re-index < 500ms | N/A — No file watcher |
| NFR-07 | Context assembly < 100ms | N/A — No context packager |
| NFR-09 | Extension < 20MB | N/A — No extension |

---

### 6. Missing Self-Repair Mechanisms ✗

| Trigger | Required Response | Status |
|---------|-------------------|--------|
| T1 — llama-server exits | Restart with same args | **Missing** |
| T2 — OOM kill | Drop quant level, reload | **Missing** |
| T3 — Index corruption | Rebuild index | **Missing** |
| T4 — Connection refused | Retry with backoff | **Missing** |
| T5 — Embedding model not found | Fall back to BM25 | **Missing** |

---

### 7. Missing Persistence Layer ✗

| Expected Path | Purpose | Status |
|---------------|---------|--------|
| `stage2/data/index.db` | SQLite: symbols, files, chunks | **Missing** |
| `stage2/data/embeddings/` | hnswlib index | **Missing** |
| `stage1/data/models/` | GGUF model files | **Missing** |
| `shared/hardware_profile.json` | Hardware profile | **Missing** |

**Current:** Uses PostgreSQL (`platform/learning/perf_store.py`) for telemetry storage, not the specified SQLite + hnswlib persistence for code intelligence.

---

### 8. Missing Test Infrastructure ✗

| Expected Test | Purpose | Status |
|---------------|---------|--------|
| `tests/test_stage_isolation.py` | Grep-based isolation | **Missing** |
| `tests/stage1/test_hardware_scanner.py` | Stage 1 unit tests | **Missing** |
| `tests/stage1/test_model_selector.py` | VRAM math tests | **Missing** |
| `tests/stage2/test_ast_indexer.py` | Tree-sitter tests | **Missing** |
| `tests/stage2/test_context_packager.py` | Ranking tests | **Missing** |
| `tests/stage3/test_adapter_interface.py` | Extension tests | **Missing** |
| `tests/integration/test_full_pipeline.py` | E2E tests | **Missing** |

---

### 9. Port Allocation Mismatch ✗

| Service | Expected | Actual |
|---------|----------|--------|
| Stage 1 (Inference Runtime) | 3000 | N/A |
| Stage 2 (Codebase Intelligence) | 3001 | N/A |
| Stage 3 (Editor) | localhost only | Dashboard connects via HTTP |
| llama-server (internal) | 8080 | N/A |

**Current:** Platform runs on port 8000 (FastAPI default).

---

### 10. Dependency Graph Mismatch ✗

**Expected:** 57 files across `contracts/`, `stage1/`, `stage2/`, `stage3/`, `tests/`

**Actual:** 60 files across `agent/`, `platform/`, `dashboard/`

**Key Missing Directories:**
- `contracts/` — All 8 contract files missing
- `stage1/` — All 7 implementation files missing
- `stage2/` — All 9 implementation files missing
- `stage3/` — All 7 implementation files missing
- `tests/` — All 11 test files missing
- `shared/` — Configuration missing

---

## What Exists vs. What Was Specified

### Current Implementation Strengths

The current implementation has merit as a **different product**:

| Component | Purpose | Quality |
|-----------|---------|---------|
| `platform/engine/*` | Optimization bundle assembly | Well-structured |
| `platform/learning/*` | Performance data storage | Good abstraction |
| `platform/api/*` | RESTful API routes | Follows FastAPI conventions |
| `platform/workers/*` | Celery task queues | Appropriate for async work |
| `dashboard/src/pages/*` | React dashboard | Functional UI components |
| `agent/*` | Remote telemetry agent | Reasonable for cloud monitoring |

**However**, this is a **cloud-based inference optimization SaaS platform**, not the **locally-running AI code intelligence system** specified in `prompt.md`.

---

## Root Cause Analysis

The architecture has been reinterpreted:

| Original Vision (APEX) | Current Implementation (IOAS) |
|------------------------|-------------------------------|
| Local AI pair programmer | Cloud inference optimization |
| Three-stage isolated architecture | Monolithic platform + agent |
| VSCodium extension | React web dashboard |
| llama.cpp inference | External inference servers |
| Codebase intelligence (AST, embeddings) | Performance telemetry storage |
| On-demand completion | Optimization recommendations |
| Single-user, local-first | Multi-tenant, cloud-first |

---

## Required Actions

### Option A: Pivot to APEX (Recommended)

**Return to Phase 1** and rebuild according to the original specification:

1. **Generate Contracts (Step 0):**
   - `contracts/inference_api.yaml`
   - `contracts/intelligence_api.yaml`
   - All 6 Pydantic model contracts

2. **Create Stage 1 (`stage1/`):**
   - Hardware scanner → model selector → llama-server manager → inference proxy

3. **Create Stage 2 (`stage2/`):**
   - AST indexer → call graph → embedder → embedding index → context packager → file watcher

4. **Create Stage 3 (`stage3/`):**
   - Adapter interface → VSCodium extension (TypeScript)

5. **Create Tests:**
   - Stage isolation tests
   - Per-stage unit tests
   - Integration tests

6. **Preserve Useful Components:**
   - `platform/engine/optimization_bundle.py` → Could inform model selection logic
   - `platform/learning/` patterns → Could inform Stage 2 learning from usage

### Option B: Rename and Re-specify

If the current implementation is the desired product:

1. Rename project from APEX to IOAS
2. Update `prompt.md`, `requirements.md`, `architecture.md` to reflect actual architecture
3. Document the cloud-based SaaS model explicitly
4. Remove references to three-stage local architecture

---

## Critic Gate Decision

### PASS 1 — SYNTAX ✓

All existing files pass basic syntax validation:
- Python files: Valid syntax (importable)
- JSX files: Valid React components
- YAML/JSON: Valid configuration

### PASS 2 — CONTRACT ✗

**FAIL:** No contracts exist to validate against. The `prompt.md` specification defines contracts that were never generated.

### PASS 3 — COMPLETENESS ✗

**FAIL:** Core APEX components are entirely missing:
- No llama-server management
- No AST indexing
- No call graph
- No embedding index
- No context packager
- No editor extension

### PASS 4 — LOGIC ✗

**FAIL:** Cannot evaluate logic for components that don't exist. Current logic (optimization bundles, telemetry storage) serves a different purpose.

---

## Final Verdict

**RETURN TO PHASE 1**

The current implementation does not fulfill the APEX vision. The architecture has diverged into a cloud-based SaaS platform rather than the locally-running three-stage AI code intelligence system specified.

**Next Steps:**

1. **Decision Required:** Does the team want to build APEX (local AI pair programmer) or IOAS (cloud inference optimization)?

2. **If APEX:** Discard current `agent/`, `platform/`, `dashboard/` structure. Start fresh with `contracts/`, `stage1/`, `stage2/`, `stage3/` as specified in `prompt.md`.

3. **If IOAS:** Update all specification documents to reflect the actual architecture. Remove APEX references.

4. **Hybrid Approach:** Preserve useful patterns from current implementation (Celery workers, Pydantic models, FastAPI structure) and apply them to the APEX specification.

---

## Appendix: File Mapping (Current → Expected)

| Current File | Could Inform | Gap |
|--------------|--------------|-----|
| `agent/hw_scanner.py` | `stage1/hardware_scanner.py` | Different purpose (telemetry vs. model selection) |
| `platform/models/*.py` | `contracts/models/*.py` | Different schema (telemetry vs. code intelligence) |
| `platform/engine/optimization_bundle.py` | `stage1/model_selector.py` | Different optimization (inference config vs. model selection) |
| `platform/learning/perf_store.py` | `stage2/data/index.db` | Different storage (PostgreSQL vs. SQLite + hnswlib) |
| `dashboard/src/pages/*.jsx` | `stage3/vscodium/*.ts` | Different interface (web vs. editor extension) |

**Conclusion:** Current implementation is a **different product** requiring a **fresh start** for APEX.

---

**Critic Gate Status:** ✗ **RETURN TO PHASE 1**

**Reason:** Architecture does not fulfill original vision. Contracts missing. All three stages missing. Test infrastructure missing. Core functional requirements unimplemented.
