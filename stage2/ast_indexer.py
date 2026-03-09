"""AST Indexer - tree-sitter based code parsing."""

import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import sqlite3

from contracts.models.index_entry import FileEntry, SymbolEntry, ChunkEntry


# Language mappings for tree-sitter
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "c_sharp",
    ".swift": "swift",
    ".kt": "kotlin",
}


class ASTIndexer:
    """Indexes code files using tree-sitter."""
    
    def __init__(self, db_path: str = "stage2/data/index.db"):
        """
        Initialize indexer.
        
        Args:
            db_path: Path to SQLite index database
        """
        self.db_path = db_path
        self.workspace_hash: Optional[str] = None
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                workspace_root TEXT NOT NULL,
                hash TEXT NOT NULL,
                language TEXT NOT NULL,
                indexed_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL REFERENCES files(id),
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                col_start INTEGER NOT NULL,
                col_end INTEGER NOT NULL,
                docstring TEXT,
                signature TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id TEXT PRIMARY KEY,
                caller_symbol_id TEXT REFERENCES symbols(id),
                callee_symbol_id TEXT REFERENCES symbols(id),
                call_site_line INTEGER NOT NULL,
                call_site_col INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL REFERENCES files(id),
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding_index TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def scan(self, workspace_root: str) -> int:
        """
        Scan workspace and index all files.
        
        Args:
            workspace_root: Root directory to scan
        
        Returns:
            Number of files indexed
        """
        self.workspace_hash = hashlib.sha256(workspace_root.encode()).hexdigest()[:16]
        
        files_indexed = 0
        for root, dirs, files in os.walk(workspace_root):
            # Skip hidden and common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                      ('node_modules', '__pycache__', 'venv', 'env', '.git', 'dist', 'build')]
            
            for filename in files:
                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in LANGUAGE_MAP:
                    try:
                        self.index_file(filepath, workspace_root)
                        files_indexed += 1
                    except Exception as e:
                        print(f"Error indexing {filepath}: {e}")
        
        return files_indexed
    
    def index_file(self, filepath: str, workspace_root: str) -> Optional[FileEntry]:
        """
        Index a single file.
        
        Args:
            filepath: Path to file
            workspace_root: Workspace root directory
        
        Returns:
            FileEntry if indexed, None if skipped
        """
        rel_path = os.path.relpath(filepath, workspace_root)
        file_id = f"{self.workspace_hash}:{rel_path}"
        
        # Check if file needs re-indexing
        existing = self._get_file(file_id)
        content_hash = self._hash_file(filepath)
        
        if existing and existing.hash == content_hash:
            return None  # No changes
        
        # Read file content
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Get language
        ext = os.path.splitext(filepath)[1].lower()
        language = LANGUAGE_MAP.get(ext, "text")
        
        # Parse AST and extract symbols
        symbols = self._parse_file(content, language, filepath)
        
        # Create chunks
        chunks = self._create_chunks(content, rel_path)
        
        # Save to database
        self._save_file(file_id, rel_path, workspace_root, content_hash, language)
        self._save_symbols(file_id, symbols)
        self._save_chunks(file_id, chunks)
        
        return FileEntry(
            id=file_id,
            path=rel_path,
            workspace_root=workspace_root,
            hash=content_hash,
            language=language,
            indexed_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def reindex(self, filepath: str, workspace_root: str) -> Optional[FileEntry]:
        """
        Re-index a single file (called by file watcher).
        
        Args:
            filepath: Path to changed file
            workspace_root: Workspace root directory
        
        Returns:
            FileEntry if re-indexed
        """
        return self.index_file(filepath, workspace_root)
    
    def get_symbols(self, file_id: str) -> List[SymbolEntry]:
        """
        Get symbols for a file.
        
        Args:
            file_id: File ID
        
        Returns:
            List of SymbolEntry objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM symbols WHERE file_id = ?",
            (file_id,)
        )
        
        symbols = []
        for row in cursor.fetchall():
            symbols.append(SymbolEntry(
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
            ))
        
        conn.close()
        return symbols
    
    def get_all_symbols(self, workspace_root: Optional[str] = None) -> List[SymbolEntry]:
        """
        Get all symbols across all files.
        
        Args:
            workspace_root: Optional workspace filter
        
        Returns:
            List of all SymbolEntry objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if workspace_root:
            workspace_hash = hashlib.sha256(workspace_root.encode()).hexdigest()[:16]
            cursor.execute(
                "SELECT s.* FROM symbols s JOIN files f ON s.file_id = f.id WHERE f.workspace_root = ?",
                (workspace_root,)
            )
        else:
            cursor.execute("SELECT * FROM symbols")
        
        symbols = []
        for row in cursor.fetchall():
            symbols.append(SymbolEntry(
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
            ))
        
        conn.close()
        return symbols
    
    def _get_file(self, file_id: str) -> Optional[FileEntry]:
        """Get file entry by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return FileEntry(
                id=row[0],
                path=row[1],
                workspace_root=row[2],
                hash=row[3],
                language=row[4],
                indexed_at=row[5],
                updated_at=row[6]
            )
        return None
    
    def _hash_file(self, filepath: str) -> str:
        """Compute content hash for file."""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            hasher.update(f.read())
        return hasher.hexdigest()
    
    def _parse_file(self, content: str, language: str, filepath: str) -> List[Dict[str, Any]]:
        """
        Parse file and extract symbols using tree-sitter.
        
        Args:
            content: File content
            language: Programming language
            filepath: File path
        
        Returns:
            List of symbol dictionaries
        """
        # Placeholder implementation - would use tree-sitter in production
        # For now, use simple regex-based extraction
        
        symbols = []
        lines = content.split('\n')
        
        if language == "python":
            symbols = self._parse_python(lines, filepath)
        elif language in ("javascript", "typescript"):
            symbols = self._parse_javascript(lines, filepath)
        else:
            # Generic fallback
            symbols = self._parse_generic(lines, filepath)
        
        return symbols
    
    def _parse_python(self, lines: List[str], filepath: str) -> List[Dict[str, Any]]:
        """Parse Python file for symbols."""
        symbols = []
        symbol_id = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Function definitions
            if stripped.startswith('def '):
                name = stripped.split('(')[0].replace('def ', '')
                symbols.append({
                    'id': f"{filepath}:func:{symbol_id}",
                    'name': name,
                    'kind': 'function',
                    'line_start': i,
                    'line_end': i,
                    'col_start': line.index('def'),
                    'col_end': len(line),
                    'docstring': self._extract_docstring(lines, i + 1),
                    'signature': stripped
                })
                symbol_id += 1
            
            # Class definitions
            elif stripped.startswith('class '):
                name = stripped.split('(')[0].replace('class ', '')
                symbols.append({
                    'id': f"{filepath}:class:{symbol_id}",
                    'name': name,
                    'kind': 'class',
                    'line_start': i,
                    'line_end': i,
                    'col_start': line.index('class'),
                    'col_end': len(line),
                    'docstring': self._extract_docstring(lines, i + 1),
                    'signature': stripped
                })
                symbol_id += 1
        
        return symbols
    
    def _parse_javascript(self, lines: List[str], filepath: str) -> List[Dict[str, Any]]:
        """Parse JavaScript/TypeScript file for symbols."""
        symbols = []
        symbol_id = 0
        
        import re
        
        for i, line in enumerate(lines):
            # Function declarations
            match = re.match(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', line)
            if match:
                symbols.append({
                    'id': f"{filepath}:func:{symbol_id}",
                    'name': match.group(1),
                    'kind': 'function',
                    'line_start': i,
                    'line_end': i,
                    'col_start': 0,
                    'col_end': len(line),
                    'signature': line.strip()
                })
                symbol_id += 1
            
            # Arrow functions assigned to const
            match = re.match(r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(', line)
            if match:
                symbols.append({
                    'id': f"{filepath}:func:{symbol_id}",
                    'name': match.group(1),
                    'kind': 'function',
                    'line_start': i,
                    'line_end': i,
                    'col_start': 0,
                    'col_end': len(line),
                    'signature': line.strip()
                })
                symbol_id += 1
            
            # Class declarations
            match = re.match(r'(?:export\s+)?class\s+(\w+)', line)
            if match:
                symbols.append({
                    'id': f"{filepath}:class:{symbol_id}",
                    'name': match.group(1),
                    'kind': 'class',
                    'line_start': i,
                    'line_end': i,
                    'col_start': 0,
                    'col_end': len(line),
                    'signature': line.strip()
                })
                symbol_id += 1
        
        return symbols
    
    def _parse_generic(self, lines: List[str], filepath: str) -> List[Dict[str, Any]]:
        """Generic symbol extraction fallback."""
        return []
    
    def _extract_docstring(self, lines: List[str], start_line: int) -> Optional[str]:
        """Extract docstring from lines after definition."""
        if start_line >= len(lines):
            return None
        
        line = lines[start_line].strip()
        if line.startswith('"""') or line.startswith("'''"):
            quote = line[:3]
            if line.count(quote) >= 2:
                return line[3:line.rfind(quote)]
            
            # Multi-line docstring
            docstring_lines = [line[3:]]
            for i in range(start_line + 1, min(start_line + 20, len(lines))):
                if quote in lines[i]:
                    docstring_lines.append(lines[i][:lines[i].index(quote)])
                    return '\n'.join(docstring_lines)
                docstring_lines.append(lines[i].strip())
        
        return None
    
    def _create_chunks(self, content: str, rel_path: str) -> List[Dict[str, Any]]:
        """
        Create text chunks for embedding.
        
        Args:
            content: File content
            rel_path: Relative file path
        
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        lines = content.split('\n')
        
        # Chunk by 50 lines with 10 line overlap
        chunk_size = 50
        overlap = 10
        
        for start in range(0, len(lines), chunk_size - overlap):
            end = min(start + chunk_size, len(lines))
            chunk_content = '\n'.join(lines[start:end])
            
            if chunk_content.strip():
                chunks.append({
                    'id': f"{rel_path}:chunk:{start}",
                    'line_start': start,
                    'line_end': end,
                    'content': chunk_content
                })
        
        return chunks
    
    def _save_file(self, file_id: str, path: str, workspace_root: str, 
                   file_hash: str, language: str) -> None:
        """Save file entry to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO files (id, path, workspace_root, hash, language, indexed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file_id, path, workspace_root, file_hash, language, now, now))
        
        conn.commit()
        conn.close()
    
    def _save_symbols(self, file_id: str, symbols: List[Dict[str, Any]]) -> None:
        """Save symbols to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing symbols for this file
        cursor.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        
        for sym in symbols:
            cursor.execute("""
                INSERT INTO symbols (id, file_id, name, kind, line_start, line_end, 
                                    col_start, col_end, docstring, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sym['id'], file_id, sym['name'], sym['kind'],
                sym['line_start'], sym['line_end'], sym['col_start'], sym['col_end'],
                sym.get('docstring'), sym.get('signature')
            ))
        
        conn.commit()
        conn.close()
    
    def _save_chunks(self, file_id: str, chunks: List[Dict[str, Any]]) -> None:
        """Save chunks to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing chunks for this file
        cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
        
        for chunk in chunks:
            cursor.execute("""
                INSERT INTO chunks (id, file_id, line_start, line_end, content, embedding_index)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chunk['id'], file_id, chunk['line_start'], chunk['line_end'], 
                  chunk['content'], None))
        
        conn.commit()
        conn.close()
    
    def get_chunks(self, file_id: str) -> List[ChunkEntry]:
        """Get chunks for a file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM chunks WHERE file_id = ?", (file_id,))
        
        chunks = []
        for row in cursor.fetchall():
            chunks.append(ChunkEntry(
                id=row[0],
                file_id=row[1],
                line_start=row[2],
                line_end=row[3],
                content=row[4],
                embedding_index=row[5]
            ))
        
        conn.close()
        return chunks
    
    def get_all_chunks(self) -> List[ChunkEntry]:
        """Get all chunks."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM chunks")
        
        chunks = []
        for row in cursor.fetchall():
            chunks.append(ChunkEntry(
                id=row[0],
                file_id=row[1],
                line_start=row[2],
                line_end=row[3],
                content=row[4],
                embedding_index=row[5]
            ))
        
        conn.close()
        return chunks
