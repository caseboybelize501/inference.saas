"""Call graph builder - networkx graph from AST output."""

import sqlite3
from typing import Dict, List, Set, Optional, Any
import networkx as nx

from contracts.models.index_entry import SymbolEntry, CallEntry


class CallGraph:
    """Builds and queries call graph from AST indexer output."""
    
    def __init__(self, db_path: str = "stage2/data/index.db"):
        """
        Initialize call graph.
        
        Args:
            db_path: Path to SQLite index database
        """
        self.db_path = db_path
        self.graph: nx.DiGraph = nx.DiGraph()
        self.symbol_map: Dict[str, SymbolEntry] = {}
    
    def build(self) -> int:
        """
        Build call graph from indexed symbols.
        
        Returns:
            Number of call relationships found
        """
        # Load all symbols
        self._load_symbols()
        
        # Build edges from call relationships in database
        self._load_calls()
        
        # Infer additional calls from symbol references
        self._infer_calls()
        
        return self.graph.number_of_edges()
    
    def _load_symbols(self) -> None:
        """Load all symbols from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM symbols")
        
        for row in cursor.fetchall():
            symbol = SymbolEntry(
                id=row[0],
                file_id=row[1],
                name=row[2],
                kind=row[3],
                line_start=row[4],
                line_end=row[5],
                col_start=row[6],
                col_end=row[7],
                docstring=row[8],
                signature=row[9]
            )
            self.symbol_map[symbol.id] = symbol
            self.graph.add_node(symbol.id, symbol=symbol)
        
        conn.close()
    
    def _load_calls(self) -> None:
        """Load existing call relationships from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM calls")
        
        for row in cursor.fetchall():
            caller_id = row[1]
            callee_id = row[2]
            
            if caller_id in self.symbol_map and callee_id in self.symbol_map:
                self.graph.add_edge(caller_id, callee_id, call_site_line=row[3])
        
        conn.close()
    
    def _infer_calls(self) -> None:
        """Infer call relationships from symbol signatures."""
        # Simple inference: if a function's signature references another symbol name,
        # assume it might call it
        # This is a placeholder - real implementation would use tree-sitter call sites
        
        for symbol_id, symbol in self.symbol_map.items():
            if symbol.kind != 'function':
                continue
            
            # Look for function calls in signature (very simplified)
            if symbol.signature:
                for other_id, other_symbol in self.symbol_map.items():
                    if other_id == symbol_id:
                        continue
                    if other_symbol.kind == 'function' and other_symbol.name in symbol.signature:
                        # Potential call relationship
                        if not self.graph.has_edge(symbol_id, other_id):
                            self.graph.add_edge(symbol_id, other_id, inferred=True)
    
    def get_callers(self, symbol_id: str, depth: int = 1) -> List[SymbolEntry]:
        """
        Get symbols that call this symbol.
        
        Args:
            symbol_id: Symbol to find callers for
            depth: How many levels up to search
        
        Returns:
            List of caller symbols
        """
        callers = set()
        to_visit = [(symbol_id, 0)]
        
        while to_visit:
            current, current_depth = to_visit.pop(0)
            if current_depth > depth:
                continue
            
            for predecessor in self.graph.predecessors(current):
                if predecessor not in callers:
                    callers.add(predecessor)
                    if current_depth < depth:
                        to_visit.append((predecessor, current_depth + 1))
        
        return [self.symbol_map[sid] for sid in callers if sid in self.symbol_map]
    
    def get_callees(self, symbol_id: str, depth: int = 1) -> List[SymbolEntry]:
        """
        Get symbols that this symbol calls.
        
        Args:
            symbol_id: Symbol to find callees for
            depth: How many levels down to search
        
        Returns:
            List of callee symbols
        """
        callees = set()
        to_visit = [(symbol_id, 0)]
        
        while to_visit:
            current, current_depth = to_visit.pop(0)
            if current_depth > depth:
                continue
            
            for successor in self.graph.successors(current):
                if successor not in callees:
                    callees.add(successor)
                    if current_depth < depth:
                        to_visit.append((successor, current_depth + 1))
        
        return [self.symbol_map[sid] for sid in callees if sid in self.symbol_map]
    
    def get_call_graph(self, symbol_id: str, depth: int = 3) -> Dict[str, Any]:
        """
        Get full call graph for a symbol.
        
        Args:
            symbol_id: Symbol to analyze
            depth: Search depth
        
        Returns:
            Dictionary with callers, callees, and depth searched
        """
        callers = self.get_callers(symbol_id, depth)
        callees = self.get_callees(symbol_id, depth)
        
        return {
            'symbol': self.symbol_map.get(symbol_id),
            'callers': callers,
            'callees': callees,
            'depth_searched': depth
        }
    
    def get_symbol_path(self, from_id: str, to_id: str) -> Optional[List[str]]:
        """
        Find call path between two symbols.
        
        Args:
            from_id: Starting symbol
            to_id: Target symbol
        
        Returns:
            List of symbol IDs in path, or None if no path
        """
        try:
            path = nx.shortest_path(self.graph, from_id, to_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_highly_connected(self, min_degree: int = 5) -> List[SymbolEntry]:
        """
        Get symbols with many connections (potential hotspots).
        
        Args:
            min_degree: Minimum total degree (in + out)
        
        Returns:
            List of highly connected symbols
        """
        connected = []
        for node in self.graph.nodes():
            degree = self.graph.degree(node)
            if degree >= min_degree:
                if node in self.symbol_map:
                    connected.append(self.symbol_map[node])
        return connected
    
    def save_calls(self, calls: List[CallEntry]) -> None:
        """
        Save call relationships to database.
        
        Args:
            calls: List of CallEntry objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for call in calls:
            cursor.execute("""
                INSERT OR REPLACE INTO calls (id, caller_symbol_id, callee_symbol_id, 
                                             call_site_line, call_site_col)
                VALUES (?, ?, ?, ?, ?)
            """, (call.id, call.caller_symbol_id, call.callee_symbol_id,
                  call.call_site_line, call.call_site_col))
        
        conn.commit()
        conn.close()
