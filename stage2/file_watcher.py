"""File watcher - watches filesystem for changes and re-indexes."""

import os
import hashlib
from typing import Dict, Optional, Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent, FileMovedEvent

from stage2.ast_indexer import ASTIndexer


class IndexHandler(FileSystemEventHandler):
    """Handles file system events for incremental re-indexing."""
    
    def __init__(
        self,
        indexer: ASTIndexer,
        workspace_root: str,
        on_indexed: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize handler.
        
        Args:
            indexer: AST indexer instance
            workspace_root: Workspace root directory
            on_indexed: Optional callback when file is indexed
        """
        self.indexer = indexer
        self.workspace_root = workspace_root
        self.on_indexed = on_indexed
        self.pending_changes: Dict[str, bool] = {}
    
    def on_modified(self, event):
        """Handle file modification."""
        if event.is_directory:
            return
        self._queue_reindex(event.src_path)
    
    def on_created(self, event):
        """Handle file creation."""
        if event.is_directory:
            return
        self._queue_reindex(event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion."""
        if event.is_directory:
            return
        self._handle_delete(event.src_path)
    
    def on_moved(self, event):
        """Handle file move."""
        if event.is_directory:
            return
        self._handle_delete(event.src_path)
        self._queue_reindex(event.dest_path)
    
    def _queue_reindex(self, filepath: str) -> None:
        """Queue file for re-indexing."""
        # Check if file is a supported language
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in self.indexer.LANGUAGE_MAP:
            return
        
        self.pending_changes[filepath] = True
    
    def _handle_delete(self, filepath: str) -> None:
        """Handle file deletion."""
        # Remove from pending changes
        if filepath in self.pending_changes:
            del self.pending_changes[filepath]
        
        # TODO: Remove from index database
    
    def process_pending(self) -> List[str]:
        """
        Process all pending changes.
        
        Returns:
            List of re-indexed file paths
        """
        reindexed = []
        
        for filepath in list(self.pending_changes.keys()):
            try:
                result = self.indexer.reindex(filepath, self.workspace_root)
                if result:
                    reindexed.append(filepath)
                    if self.on_indexed:
                        self.on_indexed(filepath)
            except Exception as e:
                print(f"Error re-indexing {filepath}: {e}")
            
            del self.pending_changes[filepath]
        
        return reindexed


class FileWatcher:
    """Watches workspace for file changes."""
    
    def __init__(
        self,
        indexer: ASTIndexer,
        workspace_root: str,
        on_indexed: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize file watcher.
        
        Args:
            indexer: AST indexer instance
            workspace_root: Workspace root directory
            on_indexed: Optional callback when file is indexed
        """
        self.indexer = indexer
        self.workspace_root = workspace_root
        self.on_indexed = on_indexed
        self.observer: Optional[Observer] = None
        self.handler: Optional[IndexHandler] = None
        self.watching = False
    
    def start(self) -> None:
        """Start watching."""
        if self.watching:
            return
        
        self.handler = IndexHandler(
            self.indexer,
            self.workspace_root,
            self.on_indexed
        )
        
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            self.workspace_root,
            recursive=True
        )
        self.observer.start()
        self.watching = True
    
    def stop(self) -> None:
        """Stop watching."""
        if not self.watching:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        self.watching = False
    
    def process_changes(self) -> List[str]:
        """
        Process pending changes.
        
        Returns:
            List of re-indexed files
        """
        if self.handler:
            return self.handler.process_pending()
        return []
    
    def get_status(self) -> Dict:
        """Get watcher status."""
        return {
            'watching': self.watching,
            'workspace_root': self.workspace_root,
            'pending_changes': len(self.handler.pending_changes) if self.handler else 0
        }
