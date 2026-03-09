# File Manifest

**Inference SaaS Platform**

Complete inventory of every file in the project. This manifest serves as the single source of truth for all artifacts that exist or will exist in the codebase.

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Total Files** | 62 |
| Python Source (`.py`) | 31 |
| JavaScript/TypeScript (`.jsx`, `.ts`, `.tsx`) | 6 |
| Configuration (`.json`, `.yaml`, `.yml`, `.txt`) | 12 |
| Documentation (`.md`) | 6 |
| Docker (`.Dockerfile`) | 1 |
| Database Migrations | 3 |
| Other | 3 |

---

## Directory Structure

```
inference.saas/
├── agent/                           # 10 files
├── platform/                        # 28 files
├── dashboard/                       # 8 files
├── .gitignore
├── architecture.md
├── dependency_graph.md
├── docker-compose.prod.yml
├── docker-compose.yml
├── file_manifest.md                 # This file
├── module_dependencies.md
├── prompt.md
├── README.md
└── requirements.md
```

---

## File Inventory

### Root Directory (10 files)

| # | File | Type | Size (est.) | Purpose | Status |
|---|------|------|-------------|---------|--------|
| 1 | `.gitignore` | Config | 50 B | Git ignore patterns | ✓ Exists |
| 2 | `README.md` | Docs | 2 KB | Project overview | ✓ Exists |
| 3 | `architecture.md` | Docs | 25 KB | System architecture specification | ✓ Exists |
| 4 | `dependency_graph.md` | Docs | 30 KB | Complete dependency graph with cycle detection | ✓ Exists |
| 5 | `module_dependencies.md` | Docs | 20 KB | Module dependency mapping | ✓ Exists |
| 6 | `file_manifest.md` | Docs | 15 KB | This file - complete file inventory | ✓ Exists |
| 7 | `prompt.md` | Docs | 5 KB | Agent instructions | ✓ Exists |
| 8 | `requirements.md` | Docs | 10 KB | Functional requirements | ✓ Exists |
| 9 | `docker-compose.yml` | Config | 500 B | Development Docker Compose | ✓ Exists |
| 10 | `docker-compose.prod.yml` | Config | 800 B | Production Docker Compose | ✓ Exists |

---

### Agent Module (10 files)

**Path:** `agent/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 11 | `Dockerfile` | Docker | 300 B | Agent container build | — | ✓ Exists |
| 12 | `config.py` | Python | 400 B | Configuration and JWT validation | `os`, `python_jose` | ✓ Exists |
| 13 | `hw_scanner.py` | Python | 500 B | Hardware scanning (GPU, RAM) | `subprocess`, `psutil`, `pynvml` | ✓ Exists |
| 14 | `server_probe.py` | Python | 200 B | Server port probing | `socket` | ✓ Exists |
| 15 | `model_watcher.py` | Python | 600 B | Model file watcher with hashing | `hashlib`, `os`, `watchdog` | ✓ Exists |
| 16 | `telemetry.py` | Python | 700 B | Telemetry data collection | `pynvml`, `asyncio`, `httpx` | ✓ Exists |
| 17 | `opt_applier.py` | Python | 200 B | Optimization bundle applier | `subprocess` | ✓ Exists |
| 18 | `main.py` | Python | 600 B | Agent entry point and orchestrator | All agent modules, `asyncio`, `httpx` | ✓ Exists |
| 19 | `requirements.txt` | Config | 150 B | Python dependencies | — | ✓ Exists |
| 20 | `telemetry.py` | Python | See #16 | (Duplicate entry in glob) | — | ✓ Exists |

**Agent Module Totals:**
- Python files: 8
- Config files: 1
- Docker files: 1

---

### Platform Module (28 files)

**Path:** `platform/`

#### Platform Root (2 files)

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 21 | `main.py` | Python | 800 B | FastAPI application entry point | All API routers, workers | ✓ Exists |
| 22 | `requirements.txt` | Config | 200 B | Python dependencies | — | ✓ Exists |

#### Platform Models (5 files)

**Path:** `platform/models/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 23 | `benchmark.py` | Python | 500 B | BenchmarkResult Pydantic model | `pydantic` | ✓ Exists |
| 24 | `cluster.py` | Python | 300 B | ClusterProfile, GPU Pydantic models | `pydantic` | ✓ Exists |
| 25 | `optimization.py` | Python | 400 B | OptimizationConfig, OptimizationBundle models | `pydantic` | ✓ Exists |
| 26 | `telemetry.py` | Python | 300 B | GPUUtilization, TelemetrySnapshot models | `pydantic` | ✓ Exists |
| 27 | `tenant.py` | Python | 400 B | Tenant, SubscriptionTier models | `pydantic` | ✓ Exists |

#### Platform API (7 files)

**Path:** `platform/api/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 28 | `auth.py` | Python | 700 B | Authentication routes (login, refresh, API key) | `fastapi`, `python_jose`, `config` | ✓ Exists |
| 29 | `benchmarks.py` | Python | 300 B | Benchmark history routes | `fastapi`, `perf_store` | ✓ Exists |
| 30 | `billing.py` | Python | 900 B | Billing and Stripe webhook routes | `fastapi`, `stripe`, `perf_store` | ✓ Exists |
| 31 | `clusters.py` | Python | 600 B | Cluster registration and profile routes | `fastapi`, `perf_store`, `config` | ✓ Exists |
| 32 | `models.py` | Python | 400 B | Model catalog and recommendations routes | `fastapi`, `recommender`, `perf_store` | ✓ Exists |
| 33 | `optimizations.py` | Python | 800 B | Optimization run and status routes | `fastapi`, `optimization_worker`, `validation_worker` | ✓ Exists |
| 34 | `telemetry.py` | Python | 500 B | Telemetry ingestion and live data routes | `fastapi`, `perf_store`, `config` | ✓ Exists |

#### Platform Engine (7 files)

**Path:** `platform/engine/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 35 | `batch_tuner.py` | Python | 400 B | Batch size optimization | `optimization` models | ✓ Exists |
| 36 | `kernel_selector.py` | Python | 400 B | Attention kernel selection | `optimization` models | ✓ Exists |
| 37 | `kv_cache_optimizer.py` | Python | 400 B | KV cache dtype and page size selection | `optimization` models | ✓ Exists |
| 38 | `optimization_bundle.py` | Python | 900 B | Bundle assembly orchestrator | All engine modules | ✓ Exists |
| 39 | `quant_optimizer.py` | Python | 500 B | Quantization format selection | `optimization` models | ✓ Exists |
| 40 | `speculative_evaluator.py` | Python | 500 B | Draft model evaluation | `optimization` models | ✓ Exists |
| 41 | `validation_runner.py` | Python | 500 B | Validation stage runner | `optimization` models | ✓ Exists |

#### Platform Learning (4 files)

**Path:** `platform/learning/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 42 | `cross_tenant_store.py` | Python | 500 B | Cross-tenant benchmark storage | `psycopg2`, models | ✓ Exists |
| 43 | `perf_store.py` | Python | 1.2 KB | Performance data storage (PostgreSQL) | `psycopg2`, models | ✓ Exists |
| 44 | `recommender.py` | Python | 500 B | Model recommendation engine | `perf_store`, `semantic_store` | ✓ Exists |
| 45 | `semantic_store.py` | Python | 600 B | Semantic index (ChromaDB) | `chromadb` | ✓ Exists |

#### Platform Workers (3 files)

**Path:** `platform/workers/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 46 | `optimization_worker.py` | Python | 400 B | Celery worker for optimization tasks | `celery`, `optimization_bundle`, `config` | ✓ Exists |
| 47 | `telemetry_worker.py` | Python | 300 B | Celery worker for telemetry aggregation | `celery`, `perf_store`, `config` | ✓ Exists |
| 48 | `validation_worker.py` | Python | 400 B | Celery worker for validation tasks | `celery`, `validation_runner`, `config` | ✓ Exists |

#### Platform Database (4 files)

**Path:** `platform/db/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 49 | `seed.py` | Python | 500 B | Database seeding script | `psycopg2` | ✓ Exists |
| 50 | `migrations/alembic.ini` | Config | 1 KB | Alembic configuration | — | ✓ Exists |
| 51 | `migrations/env.py` | Python | 800 B | Alembic environment setup | `alembic` | ✓ Exists |
| 52 | `migrations/versions/initial_migration.py` | Python | 2 KB | Initial database schema | `alembic` | ✓ Exists |

**Platform Module Totals:**
- Python files: 25
- Config files: 3

---

### Dashboard Module (8 files)

**Path:** `dashboard/`

#### Dashboard Root (1 file)

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 53 | `package.json` | Config | 400 B | NPM package manifest and scripts | — | ✓ Exists |

#### Dashboard Pages (6 files)

**Path:** `dashboard/src/pages/`

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 54 | `ClusterOverview.jsx` | React | 800 B | Cluster telemetry dashboard | `react`, `recharts` | ✓ Exists |
| 55 | `OptimizationHistory.jsx` | React | 700 B | Optimization history visualization | `react`, `recharts` | ✓ Exists |
| 56 | `Recommendations.jsx` | React | 600 B | Model recommendations display | `react`, `recharts` | ✓ Exists |
| 57 | `Settings.jsx` | React | 400 B | Application settings page | `react` | ✓ Exists |
| 58 | `ThroughputDashboard.jsx` | React | 700 B | Throughput metrics dashboard | `react`, `recharts` | ✓ Exists |
| 59 | `VRAMBudget.jsx` | React | 600 B | VRAM budget visualization | `react`, `recharts` | ✓ Exists |

#### Dashboard Source Root (1 file - implied)

| # | File | Type | Size (est.) | Purpose | Dependencies | Status |
|---|------|------|-------------|---------|--------------|--------|
| 60 | `src/index.js` | React | 300 B | React application entry point | `react`, `react-dom` | ⏳ Implied |

**Dashboard Module Totals:**
- React files: 7 (6 pages + 1 entry point implied)
- Config files: 1

---

### Missing/Implied Files (2 files)

These files are required for the project to function but were not found in the glob:

| # | File | Type | Size (est.) | Purpose | Priority |
|---|------|------|-------------|---------|----------|
| 61 | `dashboard/src/index.js` | React | 300 B | React app entry point (ReactDOM.render) | High |
| 62 | `dashboard/src/App.jsx` | React | 500 B | Main App component with routing | High |

---

## File Type Distribution

| Extension | Count | Percentage |
|-----------|-------|------------|
| `.py` | 31 | 50.0% |
| `.md` | 6 | 9.7% |
| `.jsx` | 6 | 9.7% |
| `.txt` | 2 | 3.2% |
| `.yml` | 2 | 3.2% |
| `.json` | 2 | 3.2% |
| `.ini` | 1 | 1.6% |
| `Dockerfile` | 1 | 1.6% |
| `.gitignore` | 1 | 1.6% |
| Other (migrations) | 3 | 4.8% |
| Implied/Missing | 2 | 3.2% |

---

## Lines of Code (Estimated)

| Module | Source Files | Avg Lines/File | Total LOC |
|--------|--------------|----------------|-----------|
| Agent | 8 | 40 | 320 |
| Platform Models | 5 | 25 | 125 |
| Platform API | 7 | 35 | 245 |
| Platform Engine | 7 | 30 | 210 |
| Platform Learning | 4 | 40 | 160 |
| Platform Workers | 3 | 25 | 75 |
| Platform DB | 4 | 50 | 200 |
| Dashboard | 7 | 30 | 210 |
| **Total** | **45** | **34** | **~1,545** |

---

## Build Artifacts (Generated/Excluded)

These files are generated during build/runtime and excluded via `.gitignore`:

| Pattern | Location | Generated By |
|---------|----------|--------------|
| `__pycache__/` | `agent/`, `platform/` | Python interpreter |
| `*.pyc` | `agent/`, `platform/` | Python compiler |
| `node_modules/` | `dashboard/` | npm install |
| `.env` | Root, `agent/`, `platform/` | Environment configuration |
| `*.log` | Root, `agent/`, `platform/` | Application logs |

---

## File Dependencies by Layer

```
Layer 4: Entry Points
  ├── platform/main.py (imports all API routes + workers)
  ├── agent/main.py (imports all agent modules)
  └── dashboard/src/index.js (imports App)

Layer 3: Routes + Workers
  ├── platform/api/*.py (import models, learning, config)
  └── platform/workers/*.py (import engine, learning, config)

Layer 2: Business Logic
  ├── platform/engine/*.py (import models)
  └── platform/learning/*.py (import models, external DBs)

Layer 1: Models (Contracts)
  └── platform/models/*.py (pydantic only)

Layer 0: Configuration
  ├── requirements.txt
  ├── package.json
  ├── docker-compose.yml
  └── Dockerfile
```

---

## File Status Legend

| Symbol | Meaning |
|--------|---------|
| ✓ | File exists and is complete |
| ⏳ | File is implied/required but not found |
| ⚠ | File exists but may need updates |
| ✗ | File is missing and required |

---

## Checksums (For Verification)

To verify file integrity, generate SHA256 checksums:

```bash
# Root
sha256sum README.md architecture.md dependency_graph.md module_dependencies.md file_manifest.md

# Agent
sha256sum agent/*.py agent/requirements.txt agent/Dockerfile

# Platform
sha256sum platform/**/*.py platform/requirements.txt

# Dashboard
sha256sum dashboard/package.json dashboard/src/**/*.jsx
```

---

## Manifest Version

| Field | Value |
|-------|-------|
| **Manifest Version** | 1.0.0 |
| **Generated** | 2026-03-08 |
| **Total Files Tracked** | 62 |
| **Files Existing** | 60 |
| **Files Missing** | 2 |
| **Completion** | 96.8% |
