"""Tests for Stage 2 call graph."""

import pytest
import tempfile
import os
import sys

# Add stage2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stage2'))

from call_graph import CallGraph
from contracts.models.index_entry import SymbolEntry


class TestCallGraph:
    """Test call graph functionality."""

    @pytest.fixture
    def call_graph(self):
        """Create call graph with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_index.db")
            yield CallGraph(db_path=db_path)

    def test_init(self, call_graph):
        """Test call graph initialization."""
        assert call_graph.graph is not None
        assert call_graph.symbol_map == {}

    def test_build_empty(self, call_graph):
        """Test building call graph with no data."""
        edges = call_graph.build()
        
        assert edges == 0

    def test_get_callers_empty(self, call_graph):
        """Test getting callers with no data."""
        callers = call_graph.get_callers("nonexistent")
        
        assert callers == []

    def test_get_callees_empty(self, call_graph):
        """Test getting callees with no data."""
        callees = call_graph.get_callees("nonexistent")
        
        assert callees == []

    def test_get_call_graph(self, call_graph):
        """Test getting call graph for symbol."""
        result = call_graph.get_call_graph("nonexistent", depth=3)
        
        assert "callers" in result
        assert "callees" in result
        assert "depth_searched" in result
        assert result["depth_searched"] == 3

    def test_add_symbol_and_edge(self, call_graph):
        """Test adding symbols and edges."""
        # Add nodes manually
        call_graph.graph.add_node("func_a", symbol={"name": "func_a"})
        call_graph.graph.add_node("func_b", symbol={"name": "func_b"})
        call_graph.graph.add_edge("func_a", "func_b")
        
        # Test edge exists
        assert call_graph.graph.has_edge("func_a", "func_b")
        
        # Test callers/callees
        callees = call_graph.get_callees("func_a")
        assert len(callees) == 1
        
        callers = call_graph.get_callers("func_b")
        assert len(callers) == 1

    def test_get_symbol_path(self, call_graph):
        """Test finding path between symbols."""
        # Create a chain: A -> B -> C
        call_graph.graph.add_node("A")
        call_graph.graph.add_node("B")
        call_graph.graph.add_node("C")
        call_graph.graph.add_edge("A", "B")
        call_graph.graph.add_edge("B", "C")
        
        # Find path
        path = call_graph.get_symbol_path("A", "C")
        
        assert path is not None
        assert "A" in path
        assert "B" in path
        assert "C" in path

    def test_get_symbol_path_no_path(self, call_graph):
        """Test finding path when none exists."""
        # Create disconnected nodes
        call_graph.graph.add_node("A")
        call_graph.graph.add_node("B")
        
        path = call_graph.get_symbol_path("A", "B")
        
        assert path is None

    def test_highly_connected(self, call_graph):
        """Test finding highly connected symbols."""
        # Create hub node with many connections
        call_graph.graph.add_node("hub")
        for i in range(10):
            call_graph.graph.add_node(f"node_{i}")
            call_graph.graph.add_edge("hub", f"node_{i}")
            call_graph.graph.add_edge(f"node_{i}", "hub")
        
        # Hub should have degree 20 (10 in + 10 out)
        connected = call_graph.get_highly_connected(min_degree=10)
        
        assert len(connected) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
