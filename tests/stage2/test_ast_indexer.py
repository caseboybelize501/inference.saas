"""Tests for Stage 2 AST indexer."""

import pytest
import tempfile
import os
import sys
from datetime import datetime

# Add stage2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage2'))

from ast_indexer import ASTIndexer, LANGUAGE_MAP
from contracts.models.index_entry import FileEntry, SymbolEntry


class TestASTIndexer:
    """Test AST indexing functionality."""

    @pytest.fixture
    def indexer(self):
        """Create indexer with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_index.db")
            yield ASTIndexer(db_path=db_path)

    @pytest.fixture
    def test_workspace(self):
        """Create test workspace with Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test Python file
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, "w") as f:
                f.write("""
def hello():
    '''Say hello.'''
    print("Hello, World!")

class Greeter:
    '''A simple greeter.'''
    
    def greet(self, name):
        return f"Hello, {name}!"
""")
            yield tmpdir

    def test_language_map_defined(self):
        """Test language mappings are defined."""
        assert ".py" in LANGUAGE_MAP
        assert LANGUAGE_MAP[".py"] == "python"
        assert ".js" in LANGUAGE_MAP
        assert ".ts" in LANGUAGE_MAP

    def test_init_db(self, indexer):
        """Test database initialization."""
        # Database should be created
        assert os.path.exists(indexer.db_path)

    def test_scan_workspace(self, indexer, test_workspace):
        """Test workspace scanning."""
        count = indexer.scan(test_workspace)
        
        assert count >= 1

    def test_index_file(self, indexer, test_workspace):
        """Test single file indexing."""
        test_file = os.path.join(test_workspace, "test.py")
        
        entry = indexer.index_file(test_file, test_workspace)
        
        assert entry is not None
        assert entry.language == "python"
        assert "test.py" in entry.path

    def test_index_file_dedup(self, indexer, test_workspace):
        """Test file deduplication."""
        test_file = os.path.join(test_workspace, "test.py")
        
        # First index
        entry1 = indexer.index_file(test_file, test_workspace)
        assert entry1 is not None
        
        # Second index (should be skipped - no changes)
        entry2 = indexer.index_file(test_file, test_workspace)
        assert entry2 is None

    def test_parse_python_symbols(self, indexer, test_workspace):
        """Test Python symbol extraction."""
        test_file = os.path.join(test_workspace, "test.py")
        indexer.index_file(test_file, test_workspace)
        
        # Get file ID
        import hashlib
        workspace_hash = hashlib.sha256(test_workspace.encode()).hexdigest()[:16]
        file_id = f"{workspace_hash}:test.py"
        
        symbols = indexer.get_symbols(file_id)
        
        # Should find hello function and Greeter class
        symbol_names = [s.name for s in symbols]
        assert "hello" in symbol_names
        assert "Greeter" in symbol_names

    def test_get_all_symbols(self, indexer, test_workspace):
        """Test getting all symbols."""
        indexer.scan(test_workspace)
        
        symbols = indexer.get_all_symbols()
        
        assert len(symbols) >= 2  # At least hello and Greeter

    def test_create_chunks(self, indexer):
        """Test chunk creation."""
        content = "line1\nline2\nline3\n" * 100  # 300 lines
        
        chunks = indexer._create_chunks(content, "test.py")
        
        # Should create multiple chunks (50 lines each with overlap)
        assert len(chunks) > 1
        
        # Each chunk should have required fields
        for chunk in chunks:
            assert "id" in chunk
            assert "line_start" in chunk
            assert "line_end" in chunk
            assert "content" in chunk

    def test_hash_file(self, indexer, test_workspace):
        """Test file hashing."""
        test_file = os.path.join(test_workspace, "test.py")
        
        hash1 = indexer._hash_file(test_file)
        hash2 = indexer._hash_file(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
