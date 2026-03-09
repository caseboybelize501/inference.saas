"""Embedding index - hnswlib vector index for semantic search."""

import os
import pickle
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from contracts.models.index_entry import ChunkEntry


class EmbeddingIndex:
    """HNSW index for semantic search over code chunks."""
    
    def __init__(self, index_dir: str = "stage2/data/embeddings"):
        """
        Initialize embedding index.
        
        Args:
            index_dir: Directory to store index files
        """
        self.index_dir = index_dir
        self.index_path = os.path.join(index_dir, "hnsw_index.pkl")
        self.metadata_path = os.path.join(index_dir, "metadata.pkl")
        
        self.index: Optional[Any] = None
        self.id_map: Dict[int, str] = {}  # HNSW index -> chunk ID
        self.chunk_map: Dict[str, Dict] = {}  # chunk ID -> metadata
        self.dimension: int = 384  # Default for all-MiniLM-L6-v2
        
        os.makedirs(index_dir, exist_ok=True)
        self._load_or_create_index()
    
    def _load_or_create_index(self) -> None:
        """Load existing index or create new one."""
        if os.path.exists(self.index_path):
            self._load_index()
        else:
            self._create_index()
    
    def _create_index(self) -> None:
        """Create new HNSW index."""
        try:
            import hnswlib
            self.index = hnswlib.Index(space='cosine', dim=self.dimension)
        except ImportError:
            # Fallback to simple numpy array if hnswlib not available
            self.index = None
            self._vectors: List[np.ndarray] = []
    
    def _load_index(self) -> None:
        """Load index from disk."""
        try:
            with open(self.index_path, 'rb') as f:
                data = pickle.load(f)
                self.id_map = data.get('id_map', {})
                self.chunk_map = data.get('chunk_map', {})
                self.dimension = data.get('dimension', 384)
            
            # Load hnswlib index
            import hnswlib
            self.index = hnswlib.Index(space='cosine', dim=self.dimension)
            self.index.load_index(self.index_path + ".bin")
            
        except Exception as e:
            print(f"Failed to load index: {e}")
            self._create_index()
    
    def build(self, embeddings: Dict[str, List[float]], metadata: Optional[Dict[str, Dict]] = None) -> int:
        """
        Build index from embeddings.
        
        Args:
            embeddings: Dictionary mapping chunk ID to embedding vector
            metadata: Optional metadata for each chunk
        
        Returns:
            Number of vectors indexed
        """
        if not embeddings:
            return 0
        
        # Get dimension from first embedding
        first_emb = next(iter(embeddings.values()))
        self.dimension = len(first_emb)
        
        # Reinitialize index with correct dimension
        try:
            import hnswlib
            self.index = hnswlib.Index(space='cosine', dim=self.dimension)
            
            # Prepare data
            chunk_ids = list(embeddings.keys())
            vectors = np.array([embeddings[cid] for cid in chunk_ids]).astype('float32')
            
            # Initialize index
            self.index.init_index(
                max_elements=len(chunk_ids),
                ef_construction=200,
                M=16
            )
            
            # Add vectors
            int_ids = list(range(len(chunk_ids)))
            self.index.add_items(vectors, int_ids)
            
            # Build mapping
            self.id_map = {i: cid for i, cid in enumerate(chunk_ids)}
            self.chunk_map = metadata or {cid: {} for cid in chunk_ids}
            
            # Set search efficiency
            self.index.set_ef(50)
            
        except ImportError:
            # Fallback without hnswlib
            self._vectors = [np.array(embeddings[cid]) for cid in embeddings.keys()]
            self.id_map = {i: cid for i, cid in enumerate(embeddings.keys())}
            self.chunk_map = metadata or {cid: {} for cid in embeddings.keys()}
        
        return len(embeddings)
    
    def search(self, query_embedding: List[float], k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
        
        Returns:
            List of (chunk_id, distance) tuples
        """
        if self.index is None:
            # Fallback: brute force search
            return self._brute_force_search(query_embedding, k)
        
        try:
            import hnswlib
            
            query_vector = np.array([query_embedding]).astype('float32')
            labels, distances = self.index.knn_query(query_vector, k=k)
            
            results = []
            for i, (label, distance) in enumerate(zip(labels[0], distances[0])):
                chunk_id = self.id_map.get(int(label))
                if chunk_id:
                    results.append((chunk_id, float(distance)))
            
            return results
            
        except ImportError:
            return self._brute_force_search(query_embedding, k)
    
    def _brute_force_search(self, query_embedding: List[float], k: int) -> List[Tuple[str, float]]:
        """Brute force similarity search fallback."""
        if not hasattr(self, '_vectors') or not self._vectors:
            return []
        
        query = np.array(query_embedding)
        query = query / np.linalg.norm(query)
        
        distances = []
        for i, vector in enumerate(self._vectors):
            vector = vector / np.linalg.norm(vector)
            distance = 1 - np.dot(query, vector)  # Cosine distance
            chunk_id = self.id_map.get(i)
            if chunk_id:
                distances.append((chunk_id, float(distance)))
        
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def add(self, chunk_id: str, embedding: List[float], metadata: Optional[Dict] = None) -> None:
        """
        Add single embedding to index.
        
        Args:
            chunk_id: Chunk identifier
            embedding: Embedding vector
            metadata: Optional metadata
        """
        # Get next index
        next_idx = len(self.id_map)
        
        # Add to mapping
        self.id_map[next_idx] = chunk_id
        self.chunk_map[chunk_id] = metadata or {}
        
        # Add to index
        if self.index is not None:
            try:
                import hnswlib
                vector = np.array([embedding]).astype('float32')
                self.index.add_items(vector, [next_idx])
            except ImportError:
                pass
        else:
            if not hasattr(self, '_vectors'):
                self._vectors = []
            self._vectors.append(np.array(embedding))
    
    def remove(self, chunk_id: str) -> bool:
        """
        Remove embedding from index.
        
        Args:
            chunk_id: Chunk identifier
        
        Returns:
            True if removed
        """
        # Find index for chunk
        idx_to_remove = None
        for idx, cid in self.id_map.items():
            if cid == chunk_id:
                idx_to_remove = idx
                break
        
        if idx_to_remove is None:
            return False
        
        # Remove from mappings
        del self.id_map[idx_to_remove]
        if chunk_id in self.chunk_map:
            del self.chunk_map[chunk_id]
        
        # Note: HNSW doesn't support deletion, would need rebuild
        # For now, just remove from mapping (will be filtered in search)
        
        return True
    
    def save(self) -> None:
        """Save index to disk."""
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Save metadata
        data = {
            'id_map': self.id_map,
            'chunk_map': self.chunk_map,
            'dimension': self.dimension
        }
        
        with open(self.index_path, 'wb') as f:
            pickle.dump(data, f)
        
        # Save hnswlib index
        if self.index is not None:
            try:
                self.index.save_index(self.index_path + ".bin")
            except Exception as e:
                print(f"Failed to save hnswlib index: {e}")
    
    def get_chunk_metadata(self, chunk_id: str) -> Optional[Dict]:
        """Get metadata for chunk."""
        return self.chunk_map.get(chunk_id)
    
    def size(self) -> int:
        """Get number of vectors in index."""
        return len(self.id_map)
    
    def clear(self) -> None:
        """Clear index."""
        self.id_map = {}
        self.chunk_map = {}
        self._create_index()
