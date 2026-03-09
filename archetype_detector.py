#!/usr/bin/env python3
"""
APEX Archetype Detector
Analyzes project structure and detects archetype from layerlimits.json
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class ArchetypeDetector:
    """Detects project archetype based on file structure and dependencies."""
    
    # File patterns that indicate specific archetypes
    ARCHETYPE_SIGNATURES = {
        "01": {  # Frontend Only
            "files": ["package.json", "vite.config.ts", "next.config.js", "tailwind.config.js"],
            "dirs": ["src/components", "src/pages", "src/app"],
            "dependencies": ["react", "vue", "next", "nuxt", "supabase"],
            "exclude": ["server.py", "main.go", "Cargo.toml"]  # No backend
        },
        "02": {  # Full Stack Web
            "files": ["package.json", "tsconfig.json"],
            "dirs": ["frontend", "backend", "api", "server"],
            "dependencies": ["next", "react", "express", "fastapi", "postgresql"],
            "exclude": []
        },
        "03": {  # REST API
            "files": ["requirements.txt", "main.py", "package.json"],
            "dirs": ["api", "routes", "endpoints"],
            "dependencies": ["fastapi", "express", "flask", "django-rest"],
            "exclude": ["unity", "unreal"]
        },
        "04": {  # CLI Tool
            "files": ["setup.py", "pyproject.toml", "Cargo.toml"],
            "dirs": ["bin", "cli", "commands"],
            "dependencies": ["click", "typer", "argparse"],
            "exclude": ["react", "vue", "unity"]
        },
        "05": {  # Game Engine
            "files": ["ProjectSettings.asset", "uproject", "CMakeLists.txt"],
            "dirs": ["Assets", "Content", "Source", "Engine"],
            "dependencies": ["unity", "unreal", "godot"],
            "exclude": []
        },
        "06": {  # ML Pipeline
            "files": ["requirements.txt", "setup.py", "dvc.yaml"],
            "dirs": ["models", "data", "notebooks", "training"],
            "dependencies": ["pytorch", "tensorflow", "scikit-learn", "pandas"],
            "exclude": ["unity", "react"]
        },
        "07": {  # Mobile App
            "files": ["pubspec.yaml", "package.json", "build.gradle"],
            "dirs": ["ios", "android", "app"],
            "dependencies": ["react-native", "flutter", "expo"],
            "exclude": []
        },
        "08": {  # Data ETL
            "files": ["dbt_project.yml", "airflow.cfg", "setup.py"],
            "dirs": ["models", "dags", "dbt", "etl"],
            "dependencies": ["airflow", "dbt", "spark", "pandas"],
            "exclude": ["react", "unity"]
        },
        "09": {  # Embedded/IoT
            "files": ["Cargo.toml", "CMakeLists.txt", "platformio.ini"],
            "dirs": ["src", "firmware", "hardware"],
            "dependencies": ["embedded-hal", "avr", "esp-idf"],
            "exclude": ["react", "django"]
        },
        "10": {  # APE Itself
            "files": ["layerlimits.json", "token_manifest.json", "architecture.md"],
            "dirs": ["stage1", "stage2", "stage3", "agent"],
            "dependencies": ["llama-cpp", "tree-sitter", "fastapi"],
            "exclude": []
        }
    }
    
    def __init__(self, layerlimits_path: str, project_root: str):
        self.layerlimits_path = layerlimits_path
        self.project_root = Path(project_root)
        self.layerlimits = self._load_layerlimits()
        
    def _load_layerlimits(self) -> dict:
        """Load layerlimits.json data."""
        with open(self.layerlimits_path, 'r') as f:
            return json.load(f)
    
    def scan_project(self) -> Dict[str, any]:
        """Scan project for archetype signatures."""
        files = set()
        dirs = set()
        dependencies = set()
        
        # Walk project tree
        for root, _, filenames in os.walk(self.project_root):
            # Skip common non-essential directories
            if any(skip in root for skip in ['node_modules', '.git', '__pycache__', 'dist', 'build']):
                continue
                
            # Collect files
            for f in filenames:
                files.add(f)
                if f == 'package.json':
                    deps = self._extract_dependencies(Path(root) / f)
                    dependencies.update(deps)
                elif f in ['requirements.txt', 'Cargo.toml']:
                    deps = self._extract_dependencies(Path(root) / f)
                    dependencies.update(deps)
            
            # Collect directories (relative paths)
            rel_path = os.path.relpath(root, self.project_root)
            dirs.add(rel_path)
        
        return {
            'files': files,
            'dirs': dirs,
            'dependencies': dependencies
        }
    
    def _extract_dependencies(self, filepath: Path) -> set:
        """Extract dependencies from package.json or requirements.txt."""
        deps = set()
        
        if not filepath.exists():
            return deps
        
        try:
            with open(filepath, 'r') as f:
                content = f.read().lower()
                
            if filepath.name == 'package.json':
                data = json.loads(content)
                for dep_type in ['dependencies', 'devDependencies']:
                    if dep_type in data:
                        deps.update(data[dep_type].keys())
            
            elif filepath.name == 'requirements.txt':
                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        dep = line.split('==')[0].split('>=')[0].strip()
                        if dep:
                            deps.add(dep)
                            
            elif filepath.name == 'Cargo.toml':
                in_deps = False
                for line in content.split('\n'):
                    if '[dependencies]' in line:
                        in_deps = True
                        continue
                    if in_deps and line.strip() and not line.startswith('['):
                        dep = line.split('=')[0].strip()
                        if dep:
                            deps.add(dep)
        except Exception as e:
            print(f"Warning: Could not parse {filepath}: {e}")
        
        return deps
    
    def detect_archetype(self) -> Tuple[str, float, str]:
        """
        Detect project archetype.
        
        Returns:
            Tuple of (archetype_id, confidence, reasoning)
        """
        project = self.scan_project()
        scores = {}
        
        for archetype_id, signatures in self.ARCHETYPE_SIGNATURES.items():
            score = 0
            matched = []
            
            # Score file matches
            for f in signatures['files']:
                if any(f in pf for pf in project['files']):
                    score += 2
                    matched.append(f"file:{f}")
            
            # Score directory matches
            for d in signatures['dirs']:
                if any(d in pd for pd in project['dirs']):
                    score += 2
                    matched.append(f"dir:{d}")
            
            # Score dependency matches
            for dep in signatures['dependencies']:
                if any(dep in pd for pd in project['dependencies']):
                    score += 1
                    matched.append(f"dep:{dep}")
            
            # Penalize excluded patterns
            for exc in signatures.get('exclude', []):
                if any(exc in pf for pf in project['files']) or \
                   any(exc in pd for pd in project['dependencies']):
                    score -= 3
                    matched.append(f"exclude:{exc}")
            
            scores[archetype_id] = (score, matched)
        
        # Find best match
        if not scores:
            return ("01", 0.3, "Default: Frontend Only (low confidence)")
        
        best_id = max(scores, key=lambda x: scores[x][0])
        best_score, matched = scores[best_id]
        
        # Normalize confidence (0-1)
        max_possible = 20  # Rough estimate
        confidence = min(1.0, best_score / max_possible)
        
        reasoning = f"Matched: {', '.join(matched[:5])}"
        
        return (best_id, confidence, reasoning)
    
    def get_archetype_data(self, archetype_id: str) -> Optional[dict]:
        """Get full archetype data from layerlimits.json."""
        for archetype in self.layerlimits.get('archetypes', []):
            if archetype['id'] == archetype_id:
                return archetype
        return None
    
    def get_context_budget(self, archetype_id: str, layer: str = "L3") -> dict:
        """
        Get recommended context budget for archetype and layer.
        
        Args:
            archetype_id: Archetype ID (01-10)
            layer: Layer (L0-L7)
        
        Returns:
            Dict with token budget info
        """
        archetype = self.get_archetype_data(archetype_id)
        if not archetype:
            return {"error": "Archetype not found"}
        
        # Find layer data
        layer_data = None
        for l in archetype.get('layers', []):
            if l['layer'] == layer:
                layer_data = l
                break
        
        if not layer_data:
            return {"error": "Layer not found"}
        
        return {
            "archetype": archetype['name'],
            "layer": layer,
            "phase": layer_data['phase'],
            "estimated_tokens": layer_data['estTokens'],
            "context_demand_percent": layer_data['ctxDemand'],
            "trust_built_percent": layer_data['trustBuilt'],
            "recommendation": self._get_recommendation(layer_data['estTokens'])
        }
    
    def _get_recommendation(self, tokens: int) -> str:
        """Get recommendation based on token count."""
        if tokens <= 10000:
            return "[OK] Safe for all GPUs (8K context)"
        elif tokens <= 20000:
            return "[OK] Safe for most GPUs (16K context)"
        elif tokens <= 35000:
            return "[WARN] Requires 24-32GB VRAM (32K context)"
        elif tokens <= 70000:
            return "[WARN] Requires 40GB+ VRAM (64K context)"
        else:
            return "[FAIL] Exceeds consumer GPU limits - use chunking/RAG"


if __name__ == '__main__':
    import sys
    
    # Default paths
    layerlimits = 'layerlimits.json'
    project = '.'
    
    if len(sys.argv) > 1:
        project = sys.argv[1]
    
    detector = ArchetypeDetector(layerlimits, project)
    
    print("=" * 60)
    print("APEX Archetype Detector")
    print("=" * 60)
    
    archetype_id, confidence, reasoning = detector.detect_archetype()
    archetype_data = detector.get_archetype_data(archetype_id)
    
    print(f"\nDetected Archetype: {archetype_data['name'] if archetype_data else 'Unknown'}")
    print(f"ID: {archetype_id}")
    print(f"Confidence: {confidence:.1%}")
    print(f"Reasoning: {reasoning}")
    
    if archetype_data:
        print(f"\nBase Tokens: {archetype_data['baseTokens']:,}")
        print(f"Peak Tokens: {archetype_data['peakTokens']:,} ({archetype_data['peakLayer']})")
        print(f"Complexity: {archetype_data['complexity']}")
        
        # Get context budget for peak layer
        budget = detector.get_context_budget(archetype_id, archetype_data['peakLayer'])
        print(f"\nPeak Layer Budget:")
        print(f"  Phase: {budget['phase']}")
        print(f"  Tokens: {budget['estimated_tokens']:,}")
        print(f"  Context Demand: {budget['context_demand_percent']}%")
        print(f"  Recommendation: {budget['recommendation']}")
    
    print("\n" + "=" * 60)
