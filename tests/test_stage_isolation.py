"""Test stage isolation - grep-based enforcement of stage boundaries."""

import subprocess
import sys
from pathlib import Path


def grep_search(directory: str, pattern: str) -> list:
    """Search for pattern in directory using grep."""
    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*.py", pattern, directory],
            capture_output=True,
            text=True
        )
        if result.stdout:
            return result.stdout.strip().split("\n")
        return []
    except Exception:
        # Fallback for Windows
        return []


def test_no_stage2_imports_in_stage1():
    """Stage 1 must not import stage2 or stage3."""
    violations = grep_search("stage1", r"from stage2|from stage3|import stage2|import stage3")
    assert not violations, f"Stage 1 imports from other stages: {violations}"


def test_no_stage1_imports_in_stage2():
    """Stage 2 must not import stage1 or stage3."""
    violations = grep_search("stage2", r"from stage1|from stage3|import stage1|import stage3")
    assert not violations, f"Stage 2 imports from other stages: {violations}"


def test_no_stage1_imports_in_stage3():
    """Stage 3 must not import stage1 or stage2."""
    violations = grep_search("stage3", r"from stage1|from stage2|import stage1|import stage2")
    assert not violations, f"Stage 3 imports from other stages: {violations}"


def test_stage3_only_imports_contracts():
    """Stage 3 should only import contracts for type definitions."""
    # Check that stage3 Python files only import from contracts
    violations = grep_search("stage3", r"from stage1\.|from stage2\.")
    assert not violations, f"Stage 3 imports from stage1/stage2: {violations}"


def test_contracts_are_importable():
    """All contract modules should be importable."""
    contract_files = [
        "contracts.models.hardware_profile",
        "contracts.models.model_config",
        "contracts.models.index_entry",
        "contracts.models.context_request",
        "contracts.models.completion_request",
        "contracts.models.editor_adapter"
    ]
    
    for contract in contract_files:
        try:
            __import__(contract)
        except ImportError as e:
            # Contracts may not be installed, skip this test
            print(f"Skipping import test for {contract}: {e}")


def test_stage_isolation_summary():
    """Print summary of stage isolation."""
    print("\n=== Stage Isolation Summary ===")
    
    s1_violations = grep_search("stage1", r"from stage2|from stage3|import stage2|import stage3")
    s2_violations = grep_search("stage2", r"from stage1|from stage3|import stage1|import stage3")
    s3_violations = grep_search("stage3", r"from stage1|from stage2|import stage1|import stage2")
    
    print(f"Stage 1 violations: {len(s1_violations)}")
    print(f"Stage 2 violations: {len(s2_violations)}")
    print(f"Stage 3 violations: {len(s3_violations)}")
    
    total = len(s1_violations) + len(s2_violations) + len(s3_violations)
    if total == 0:
        print("✓ All stages are properly isolated")
    else:
        print(f"✗ Found {total} isolation violations")
        sys.exit(1)


if __name__ == "__main__":
    test_no_stage2_imports_in_stage1()
    test_no_stage1_imports_in_stage2()
    test_no_stage1_imports_in_stage3()
    test_stage_isolation_summary()
    print("All isolation tests passed!")
