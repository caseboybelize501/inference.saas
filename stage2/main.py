"""Stage 2 main entry point - orchestrates startup."""

import asyncio
import uvicorn
import os

from stage2.ast_indexer import ASTIndexer
from stage2.call_graph import CallGraph
from stage2.embedding_index import EmbeddingIndex
from stage2.embedder import Embedder
from stage2.context_packager import ContextPackager
from stage2.file_watcher import FileWatcher
from stage2.intelligence_server import app, indexer, call_graph, embedding_index, context_packager, embedder, file_watcher, workspace_root, last_indexed


# Configuration
DEFAULT_WORKSPACE = os.getenv("APEX_WORKSPACE", os.getcwd())


async def startup():
    """Initialize Stage 2 components."""
    global workspace_root
    
    print("Stage 2: Starting up...")
    
    # Initialize components
    print("Initializing components...")
    
    # Index workspace
    workspace = DEFAULT_WORKSPACE
    print(f"Workspace: {workspace}")
    
    # Start indexing
    print("Scanning workspace...")
    if indexer:
        count = indexer.scan(workspace)
        print(f"  Indexed {count} files")
    
    # Build call graph
    print("Building call graph...")
    if call_graph:
        edges = call_graph.build()
        print(f"  Built call graph with {edges} edges")
    
    # Embed chunks
    print("Generating embeddings...")
    if indexer and embedder and embedding_index:
        chunks = indexer.get_all_chunks()
        print(f"  Found {len(chunks)} chunks to embed")
        
        # Batch embed
        from stage2.embedder import BATCH_SIZE
        embeddings = {}
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_embeddings = embedder.embed_chunks(batch)
            embeddings.update(batch_embeddings)
            print(f"  Embedded {len(embeddings)}/{len(chunks)} chunks...")
        
        # Build index
        if embeddings:
            embedding_index.build(embeddings)
            embedding_index.save()
            print(f"  Built embedding index with {len(embeddings)} vectors")
    
    # Start file watcher
    print("Starting file watcher...")
    if indexer:
        file_watcher = FileWatcher(indexer, workspace)
        file_watcher.start()
        print("  File watcher started")
    
    last_indexed = __import__('time').strftime("%Y-%m-%dT%H:%M:%SZ")
    
    print("\nStage 2 ready on http://0.0.0.0:3001")


def main():
    """Main entry point."""
    # Run startup
    asyncio.run(startup())
    
    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=3001)


if __name__ == "__main__":
    main()
