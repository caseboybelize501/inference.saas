"""Tests for Stage 3 isolation."""

import pytest
import subprocess
import sys
import os


def grep_search(directory: str, pattern: str) -> list:
    """Search for pattern in directory using grep."""
    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*.ts", "--include=*.tsx", pattern, directory],
            capture_output=True,
            text=True
        )
        if result.stdout:
            return result.stdout.strip().split("\n")
        return []
    except Exception:
        return []


def test_stage3_no_stage1_imports():
    """Stage 3 TypeScript must not import stage1."""
    violations = grep_search("stage3", r"from.*stage1|import.*stage1")
    assert not violations, f"Stage 3 imports stage1: {violations}"


def test_stage3_no_stage2_imports():
    """Stage 3 TypeScript must not import stage2."""
    violations = grep_search("stage3", r"from.*stage2|import.*stage2")
    assert not violations, f"Stage 3 imports stage2: {violations}"


def test_stage3_only_localhost():
    """Stage 3 must only connect to localhost."""
    # Check for any non-localhost URLs in intelligence_client.ts
    violations = grep_search("stage3/vscodium", r"http[s]?://(?!localhost|127\.0\.0\.1)")
    assert not violations, f"Stage 3 has non-localhost URLs: {violations}"


def test_intelligence_client_localhost_only():
    """Verify intelligence client enforces localhost."""
    client_file = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "stage3", "vscodium", "intelligence_client.ts"
    )
    
    if os.path.exists(client_file):
        with open(client_file, "r") as f:
            content = f.read()
        
        # Should have localhost URL
        assert "localhost" in content or "127.0.0.1" in content


def test_extension_uses_intelligence_client():
    """Verify extension uses intelligence client for API calls."""
    extension_file = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "stage3", "vscodium", "extension.ts"
    )
    
    if os.path.exists(extension_file):
        with open(extension_file, "r") as f:
            content = f.read()
        
        # Should import and use IntelligenceClient
        assert "IntelligenceClient" in content


def test_no_direct_fetch_to_stage_apis():
    """Stage 3 should use intelligence_client.ts, not direct fetch to Stage 1/2."""
    # Check that completion.ts, hover.ts, etc. use intelligence_client
    for file in ["completion.ts", "hover.ts", "status_bar.ts"]:
        filepath = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "stage3", "vscodium", file
        )
        
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                content = f.read()
            
            # Should not have direct fetch to port 3000 (Stage 1)
            assert "localhost:3000" not in content, f"{file} has direct Stage 1 URL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
