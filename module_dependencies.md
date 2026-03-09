# Module Dependencies

**Inference SaaS Platform**

Complete module dependency mapping for the actual implementation, derived from `dependency_graph.md` and mapped to existing codebase structure.

---

## Module Overview

| Module | Path | Type | Stage |
|--------|------|------|-------|
| `agent` | `agent/` | Python Agent | Stage 1 (Runtime) |
| `platform` | `platform/` | Python API | Stage 2 (Intelligence) |
| `dashboard` | `dashboard/` | React UI | Stage 3 (Editor/UI) |

---

## Level 0: Core Models (Contracts)

### Platform Models

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `M0` | `platform.models.cluster` | `platform/models/cluster.py` | `pydantic` |
| `M1` | `platform.models.optimization` | `platform/models/optimization.py` | `pydantic` |
| `M2` | `platform.models.telemetry` | `platform/models/telemetry.py` | `pydantic` |
| `M3` | `platform.models.benchmark` | `platform/models/benchmark.py` | `pydantic` |
| `M4` | `platform.models.tenant` | `platform/models/tenant.py` | `pydantic` |

**Dependency Graph:**
```
M0 → {pydantic}
M1 → {pydantic}
M2 → {pydantic}
M3 → {pydantic}
M4 → {pydantic}
```

---

## Level 1: Base Components

### Agent Module (Stage 1)

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `A0` | `agent.config` | `agent/config.py` | `os`, `python_jose` |
| `A1` | `agent.hw_scanner` | `agent/hw_scanner.py` | `subprocess`, `psutil`, `pynvml` |
| `A2` | `agent.server_probe` | `agent/server_probe.py` | `socket` |
| `A3` | `agent.model_watcher` | `agent/model_watcher.py` | `hashlib`, `os`, `watchdog` |
| `A4` | `agent.telemetry` | `agent/telemetry.py` | `pynvml`, `asyncio`, `httpx` |
| `A5` | `agent.opt_applier` | `agent/opt_applier.py` | `subprocess` |

### Platform Learning (Stage 2 Base)

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `L0` | `platform.learning.perf_store` | `platform/learning/perf_store.py` | `M3`, `M0`, `M1`, `psycopg2` |
| `L1` | `platform.learning.semantic_store` | `platform/learning/semantic_store.py` | `chromadb` |
| `L2` | `platform.learning.cross_tenant_store` | `platform/learning/cross_tenant_store.py` | `M3`, `M0`, `M1`, `psycopg2` |
| `L3` | `platform.learning.recommender` | `platform/learning/recommender.py` | `L0`, `L1` |

### Platform Engine (Stage 2 Core)

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `E0` | `platform.engine.kv_cache_optimizer` | `platform/engine/kv_cache_optimizer.py` | `M1` |
| `E1` | `platform.engine.quant_optimizer` | `platform/engine/quant_optimizer.py` | `M1` |
| `E2` | `platform.engine.kernel_selector` | `platform/engine/kernel_selector.py` | `M1` |
| `E3` | `platform.engine.batch_tuner` | `platform/engine/batch_tuner.py` | `M1` |
| `E4` | `platform.engine.speculative_evaluator` | `platform/engine/speculative_evaluator.py` | `M1` |
| `E5` | `platform.engine.validation_runner` | `platform/engine/validation_runner.py` | `M1` |
| `E6` | `platform.engine.optimization_bundle` | `platform/engine/optimization_bundle.py` | `M1`, `E0`, `E1`, `E2`, `E3`, `E4` |

**Dependency Graph:**
```
A0 → {os, python_jose}
A1 → {subprocess, psutil, pynvml}
A2 → {socket}
A3 → {hashlib, os, watchdog}
A4 → {pynvml, asyncio, httpx}
A5 → {subprocess}

L0 → {M3, M0, M1, psycopg2}
L1 → {chromadb}
L2 → {M3, M0, M1, psycopg2}
L3 → {L0, L1}

E0 → {M1}
E1 → {M1}
E2 → {M1}
E3 → {M1}
E4 → {M1}
E5 → {M1}
E6 → {M1, E0, E1, E2, E3, E4}
```

---

## Level 2: API Routes + Workers

### Platform API Routes

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `R0` | `platform.api.clusters` | `platform/api/clusters.py` | `fastapi`, `M0`, `L0`, `A0` |
| `R1` | `platform.api.optimizations` | `platform/api/optimizations.py` | `fastapi`, `M1`, `E6`, `W0`, `W1` |
| `R2` | `platform.api.telemetry` | `platform/api/telemetry.py` | `fastapi`, `M2`, `L0`, `A0` |
| `R3` | `platform.api.models` | `platform/api/models.py` | `fastapi`, `M3`, `L3`, `L0` |
| `R4` | `platform.api.benchmarks` | `platform/api/benchmarks.py` | `fastapi`, `M3`, `L0` |
| `R5` | `platform.api.billing` | `platform/api/billing.py` | `fastapi`, `M4`, `L0`, `stripe` |
| `R6` | `platform.api.auth` | `platform/api/auth.py` | `fastapi`, `python_jose`, `A0` |

### Platform Workers

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `W0` | `platform.workers.optimization_worker` | `platform/workers/optimization_worker.py` | `celery`, `E6`, `A0` |
| `W1` | `platform.workers.validation_worker` | `platform/workers/validation_worker.py` | `celery`, `E5`, `A0` |
| `W2` | `platform.workers.telemetry_worker` | `platform/workers/telemetry_worker.py` | `celery`, `L0`, `A0` |

**Dependency Graph:**
```
R0 → {fastapi, M0, L0, A0}
R1 → {fastapi, M1, E6, W0, W1}
R2 → {fastapi, M2, L0, A0}
R3 → {fastapi, M3, L3, L0}
R4 → {fastapi, M3, L0}
R5 → {fastapi, M4, L0, stripe}
R6 → {fastapi, python_jose, A0}

W0 → {celery, E6, A0}
W1 → {celery, E5, A0}
W2 → {celery, L0, A0}
```

---

## Level 3: Entry Points

### Main Applications

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `P0` | `platform.main` | `platform/main.py` | `fastapi`, `R0`, `R1`, `R2`, `R3`, `R4`, `R5`, `R6` |
| `A6` | `agent.main` | `agent/main.py` | `asyncio`, `httpx`, `A0`, `A1`, `A2`, `A3`, `A4`, `A5` |

### Dashboard Components

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `D0` | `dashboard.pages.ClusterOverview` | `dashboard/src/pages/ClusterOverview.jsx` | `react`, `recharts` |
| `D1` | `dashboard.pages.OptimizationHistory` | `dashboard/src/pages/OptimizationHistory.jsx` | `react`, `recharts` |
| `D2` | `dashboard.pages.Recommendations` | `dashboard/src/pages/Recommendations.jsx` | `react`, `recharts` |
| `D3` | `dashboard.pages.Settings` | `dashboard/src/pages/Settings.jsx` | `react` |
| `D4` | `dashboard.pages.ThroughputDashboard` | `dashboard/src/pages/ThroughputDashboard.jsx` | `react`, `recharts` |
| `D5` | `dashboard.pages.VRAMBudget` | `dashboard/src/pages/VRAMBudget.jsx` | `react`, `recharts` |

**Dependency Graph:**
```
P0 → {fastapi, R0, R1, R2, R3, R4, R5, R6}
A6 → {asyncio, httpx, A0, A1, A2, A3, A4, A5}

D0 → {react, recharts}
D1 → {react, recharts}
D2 → {react, recharts}
D3 → {react}
D4 → {react, recharts}
D5 → {react, recharts}
```

---

## Level 4: Configuration

| ID | Module | File | Dependencies |
|----|--------|------|--------------|
| `C0` | `platform.requirements` | `platform/requirements.txt` | All platform modules |
| `C1` | `agent.requirements` | `agent/requirements.txt` | All agent modules |
| `C2` | `dashboard.package` | `dashboard/package.json` | All dashboard modules |
| `C3` | `docker-compose` | `docker-compose.yml` | `P0`, `A6` |
| `C4` | `docker-compose.prod` | `docker-compose.prod.yml` | `P0`, `A6` |

---

## Complete Dependency Graph (Edge List)

```
# Level 0: Models (no internal dependencies)
M0 → {pydantic}
M1 → {pydantic}
M2 → {pydantic}
M3 → {pydantic}
M4 → {pydantic}

# Level 1: Base Components
A0 → {os, python_jose}
A1 → {subprocess, psutil, pynvml}
A2 → {socket}
A3 → {hashlib, os, watchdog}
A4 → {pynvml, asyncio, httpx}
A5 → {subprocess}

L0 → {M3, M0, M1, psycopg2}
L1 → {chromadb}
L2 → {M3, M0, M1, psycopg2}
L3 → {L0, L1}

E0 → {M1}
E1 → {M1}
E2 → {M1}
E3 → {M1}
E4 → {M1}
E5 → {M1}
E6 → {M1, E0, E1, E2, E3, E4}

# Level 2: API Routes + Workers
R0 → {fastapi, M0, L0, A0}
R1 → {fastapi, M1, E6, W0, W1}
R2 → {fastapi, M2, L0, A0}
R3 → {fastapi, M3, L3, L0}
R4 → {fastapi, M3, L0}
R5 → {fastapi, M4, L0, stripe}
R6 → {fastapi, python_jose, A0}

W0 → {celery, E6, A0}
W1 → {celery, E5, A0}
W2 → {celery, L0, A0}

# Level 3: Entry Points
P0 → {fastapi, R0, R1, R2, R3, R4, R5, R6}
A6 → {asyncio, httpx, A0, A1, A2, A3, A4, A5}

D0 → {react, recharts}
D1 → {react, recharts}
D2 → {react, recharts}
D3 → {react}
D4 → {react, recharts}
D5 → {react, recharts}

# Level 4: Configuration
C0 → {E6, W0, W1, W2, R0, R1, R2, R3, R4, R5, R6, P0}
C1 → {A0, A1, A2, A3, A4, A5, A6}
C2 → {D0, D1, D2, D3, D4, D5}
C3 → {P0, A6, C0, C1}
C4 → {P0, A6, C0, C1}
```

---

## Topological Build Order

### Phase 1: Models (Level 0)

```
Generate in parallel:
  ├── platform/models/cluster.py
  ├── platform/models/optimization.py
  ├── platform/models/telemetry.py
  ├── platform/models/benchmark.py
  └── platform/models/tenant.py
```

### Phase 2: Base Components (Level 1)

```
Agent (parallel):
  ├── agent/config.py
  ├── agent/hw_scanner.py
  ├── agent/server_probe.py
  ├── agent/model_watcher.py
  ├── agent/telemetry.py
  └── agent/opt_applier.py

Learning (parallel):
  ├── platform/learning/perf_store.py
  ├── platform/learning/semantic_store.py
  ├── platform/learning/cross_tenant_store.py
  └── platform/learning/recommender.py

Engine (parallel):
  ├── platform/engine/kv_cache_optimizer.py
  ├── platform/engine/quant_optimizer.py
  ├── platform/engine/kernel_selector.py
  ├── platform/engine/batch_tuner.py
  ├── platform/engine/speculative_evaluator.py
  ├── platform/engine/validation_runner.py
  └── platform/engine/optimization_bundle.py
```

### Phase 3: API Routes + Workers (Level 2)

```
API Routes (parallel):
  ├── platform/api/clusters.py
  ├── platform/api/optimizations.py
  ├── platform/api/telemetry.py
  ├── platform/api/models.py
  ├── platform/api/benchmarks.py
  ├── platform/api/billing.py
  └── platform/api/auth.py

Workers (parallel):
  ├── platform/workers/optimization_worker.py
  ├── platform/workers/validation_worker.py
  └── platform/workers/telemetry_worker.py
```

### Phase 4: Entry Points (Level 3)

```
  ├── platform/main.py
  ├── agent/main.py
  └── dashboard/src/pages/*.jsx (all 6 pages)
```

### Phase 5: Configuration (Level 4)

```
  ├── platform/requirements.txt
  ├── agent/requirements.txt
  ├── dashboard/package.json
  ├── docker-compose.yml
  └── docker-compose.prod.yml
```

---

## Critical Path Analysis

### Longest Dependency Chain (Agent)

```
agent/config.py
  → agent/hw_scanner.py
    → agent/model_watcher.py
      → agent/telemetry.py
        → agent/main.py

Total: 5 hops
```

### Longest Dependency Chain (Platform)

```
platform/models/optimization.py
  → platform/engine/quant_optimizer.py
    → platform/engine/optimization_bundle.py
      → platform/workers/optimization_worker.py
        → platform/api/optimizations.py
          → platform/main.py

Total: 6 hops
```

### Longest Dependency Chain (Learning)

```
platform/models/benchmark.py
  → platform/learning/perf_store.py
    → platform/learning/recommender.py
      → platform/api/models.py
        → platform/main.py

Total: 5 hops
```

---

## Import Isolation Rules

| Module | Can Import | Cannot Import |
|--------|------------|---------------|
| `agent/*` | `agent/*`, stdlib, external libs | `platform/*`, `dashboard/*` |
| `platform/models/*` | stdlib, `pydantic` | `agent/*`, `platform/api/*`, `platform/workers/*`, `platform/engine/*`, `platform/learning/*` |
| `platform/engine/*` | `platform/models/*`, stdlib, external libs | `agent/*`, `platform/api/*`, `platform/workers/*`, `platform/learning/*` |
| `platform/learning/*` | `platform/models/*`, stdlib, external libs | `agent/*`, `platform/api/*`, `platform/workers/*`, `platform/engine/*` |
| `platform/api/*` | `fastapi`, `platform/models/*`, `platform/learning/*`, `platform/workers/*`, `agent/config` | `agent/*` (except config), `dashboard/*` |
| `platform/workers/*` | `celery`, `platform/engine/*`, `platform/learning/*`, `agent/config` | `platform/api/*`, `agent/*` (except config), `dashboard/*` |
| `dashboard/*` | `react`, external npm packages | `agent/*`, `platform/*` (communicates via HTTP only) |

---

## External Dependencies

### Agent (agent/requirements.txt)

```
pynvml>=11.0.0
psutil>=5.9.0
watchdog>=3.0.0
httpx>=0.24.0
python-jose>=3.3.0
```

### Platform (platform/requirements.txt)

```
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
psycopg2-binary>=2.9.0
celery>=5.3.0
redis>=4.5.0
stripe>=5.0.0
chromadb>=0.4.0
python-jose>=3.3.0
```

### Dashboard (dashboard/package.json)

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "recharts": "^2.1.15",
  "websocket": "^1.0.34"
}
```

---

## Module Dependency Matrix

| From \ To | M0 | M1 | M2 | M3 | M4 | A0 | L0 | L1 | L3 | E0-E5 | E6 | R0-R6 | W0-W2 | P0 | A6 |
|-----------|----|----|----|----|----|----|----|----|----|-------|----|-------|-------|----|----|
| M0-M4     | —  | —  | —  | —  | —  | —  | —  | —  | —  | —     | —  | —     | —     | —  | —  |
| A0-A5     | —  | —  | —  | —  | —  | —  | —  | —  | —  | —     | —  | —     | —     | —  | —  |
| L0        | ✓  | ✓  | —  | ✓  | —  | —  | —  | —  | —  | —     | —  | —     | —     | —  | —  |
| L1        | —  | —  | —  | —  | —  | —  | —  | —  | —  | —     | —  | —     | —     | —  | —  |
| L3        | —  | —  | —  | —  | —  | —  | ✓  | ✓  | —  | —     | —  | —     | —     | —  | —  |
| E0-E5     | —  | ✓  | —  | —  | —  | —  | —  | —  | —  | —     | —  | —     | —     | —  | —  |
| E6        | —  | ✓  | —  | —  | —  | —  | —  | —  | —  | ✓     | —  | —     | —     | —  | —  |
| R0        | —  | —  | —  | —  | —  | ✓  | ✓  | —  | —  | —     | —  | —     | —     | —  | —  |
| R1        | —  | ✓  | —  | —  | —  | —  | —  | —  | —  | —     | ✓  | —     | ✓     | —  | —  |
| R2        | —  | —  | ✓  | —  | —  | ✓  | ✓  | —  | —  | —     | —  | —     | —     | —  | —  |
| R3        | —  | —  | —  | ✓  | —  | —  | ✓  | —  | ✓  | —     | —  | —     | —     | —  | —  |
| R4        | —  | —  | —  | ✓  | —  | —  | ✓  | —  | —  | —     | —  | —     | —     | —  | —  |
| R5        | —  | —  | —  | —  | ✓  | —  | ✓  | —  | —  | —     | —  | —     | —     | —  | —  |
| R6        | —  | —  | —  | —  | —  | ✓  | —  | —  | —  | —     | —  | —     | —     | —  | —  |
| W0        | —  | —  | —  | —  | —  | ✓  | —  | —  | —  | —     | ✓  | —     | —     | —  | —  |
| W1        | —  | —  | —  | —  | —  | ✓  | —  | —  | —  | —     | —  | —     | —     | —  | —  |
| W2        | —  | —  | —  | —  | —  | ✓  | ✓  | —  | —  | —     | —  | —     | —     | —  | —  |
| P0        | —  | —  | —  | —  | —  | —  | —  | —  | —  | —     | —  | ✓     | —     | —  | —  |
| A6        | —  | —  | —  | —  | —  | ✓  | —  | —  | —  | —     | —  | —     | —     | —  | —  |

---

## Build Order (Linearized)

```
1.  platform/models/cluster.py
2.  platform/models/optimization.py
3.  platform/models/telemetry.py
4.  platform/models/benchmark.py
5.  platform/models/tenant.py
6.  agent/config.py
7.  agent/hw_scanner.py
8.  agent/server_probe.py
9.  agent/model_watcher.py
10. agent/telemetry.py
11. agent/opt_applier.py
12. platform/learning/perf_store.py
13. platform/learning/semantic_store.py
14. platform/learning/cross_tenant_store.py
15. platform/learning/recommender.py
16. platform/engine/kv_cache_optimizer.py
17. platform/engine/quant_optimizer.py
18. platform/engine/kernel_selector.py
19. platform/engine/batch_tuner.py
20. platform/engine/speculative_evaluator.py
21. platform/engine/validation_runner.py
22. platform/engine/optimization_bundle.py
23. platform/api/clusters.py
24. platform/api/optimizations.py
25. platform/api/telemetry.py
26. platform/api/models.py
27. platform/api/benchmarks.py
28. platform/api/billing.py
29. platform/api/auth.py
30. platform/workers/optimization_worker.py
31. platform/workers/validation_worker.py
32. platform/workers/telemetry_worker.py
33. platform/main.py
34. agent/main.py
35. dashboard/src/pages/ClusterOverview.jsx
36. dashboard/src/pages/OptimizationHistory.jsx
37. dashboard/src/pages/Recommendations.jsx
38. dashboard/src/pages/Settings.jsx
39. dashboard/src/pages/ThroughputDashboard.jsx
40. dashboard/src/pages/VRAMBudget.jsx
41. platform/requirements.txt
42. agent/requirements.txt
43. dashboard/package.json
44. docker-compose.yml
45. docker-compose.prod.yml
```

**Total Modules**: 45

---

## Parallelization Summary

| Level | Modules | Parallel Factor |
|-------|---------|-----------------|
| 0 | 5 (models) | 5× |
| 1 | 16 (agent + learning + engine) | 16× |
| 2 | 10 (api + workers) | 10× |
| 3 | 8 (entry points + dashboard) | 8× |
| 4 | 5 (configuration) | 5× |

**Maximum Parallelism**: Level 1 (16 modules simultaneously)

---

## Module Status

| Module | Status | Notes |
|--------|--------|-------|
| `agent/*` | ✓ Implemented | 9 files |
| `platform/models/*` | ✓ Implemented | 5 files |
| `platform/learning/*` | ✓ Implemented | 4 files |
| `platform/engine/*` | ✓ Implemented | 7 files |
| `platform/api/*` | ✓ Implemented | 7 files |
| `platform/workers/*` | ✓ Implemented | 3 files |
| `platform/main.py` | ✓ Implemented | Entry point |
| `agent/main.py` | ✓ Implemented | Entry point |
| `dashboard/*` | ✓ Implemented | 6 pages + package.json |

**Total Files**: 45 (excluding configuration files)
