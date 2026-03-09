"""Search - BM25 keyword fallback when embedder unavailable."""

import os
import re
import math
from typing import List, Dict, Tuple, Optional
from collections import Counter


class BM25Search:
    """BM25 keyword search as fallback for semantic search."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 search.
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        
        self.documents: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0
        self.idf: Dict[str, float] = {}
        self.term_freq: Dict[str, Dict[str, int]] = {}
    
    def index(self, doc_id: str, content: str) -> None:
        """
        Index a document.
        
        Args:
            doc_id: Document identifier
            content: Document content
        """
        self.documents[doc_id] = content
        self.doc_lengths[doc_id] = len(self._tokenize(content))
        
        # Update average document length
        total_docs = len(self.documents)
        total_length = sum(self.doc_lengths.values())
        self.avg_doc_length = total_length / total_docs if total_docs > 0 else 0
        
        # Calculate term frequencies
        tokens = self._tokenize(content)
        self.term_freq[doc_id] = Counter(tokens)
        
        # Update IDF for all terms
        self._update_idf()
    
    def remove(self, doc_id: str) -> None:
        """
        Remove a document from index.
        
        Args:
            doc_id: Document identifier
        """
        if doc_id not in self.documents:
            return
        
        # Remove term frequencies
        if doc_id in self.term_freq:
            del self.term_freq[doc_id]
        
        # Remove document
        del self.documents[doc_id]
        del self.doc_lengths[doc_id]
        
        # Update average document length
        total_docs = len(self.documents)
        if total_docs > 0:
            total_length = sum(self.doc_lengths.values())
            self.avg_doc_length = total_length / total_docs
        
        # Update IDF
        self._update_idf()
    
    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for documents matching query.
        
        Args:
            query: Search query
            k: Number of results to return
        
        Returns:
            List of (doc_id, score) tuples
        """
        query_tokens = self._tokenize(query)
        
        scores: Dict[str, float] = {}
        
        for doc_id in self.documents:
            score = 0
            doc_len = self.doc_lengths.get(doc_id, 0)
            
            for token in query_tokens:
                if token not in self.idf:
                    continue
                
                tf = self.term_freq.get(doc_id, {}).get(token, 0)
                idf = self.idf[token]
                
                # BM25 scoring
                tf_component = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length))
                score += idf * tf_component
            
            if score > 0:
                scores[doc_id] = score
        
        # Sort by score
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def _update_idf(self) -> None:
        """Update IDF values for all terms."""
        term_doc_count: Dict[str, int] = Counter()
        
        for doc_id, freq in self.term_freq.items():
            for term in freq.keys():
                term_doc_count[term] += 1
        
        total_docs = len(self.documents)
        self.idf = {}
        
        for term, count in term_doc_count.items():
            # IDF with smoothing
            self.idf[term] = math.log((total_docs - count + 0.5) / (count + 0.5) + 1)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into terms.
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Split on non-alphanumeric, but keep underscores for code
        tokens = re.findall(r'[a-z0-9_]+', text)
        
        # Filter very short tokens
        tokens = [t for t in tokens if len(t) > 1]
        
        return tokens


class Search:
    """Unified search interface with BM25 fallback."""
    
    def __init__(self):
        """Initialize search."""
        self.bm25 = BM25Search()
        self.has_semantic = False
    
    def index(self, chunk_id: str, content: str, embedding: Optional[List[float]] = None) -> None:
        """
        Index a chunk.
        
        Args:
            chunk_id: Chunk identifier
            content: Chunk content
            embedding: Optional embedding vector
        """
        self.bm25.index(chunk_id, content)
    
    def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search for chunks.
        
        Args:
            query: Search query
            query_embedding: Optional query embedding for semantic search
            k: Number of results
        
        Returns:
            List of (chunk_id, score) tuples
        """
        # Use semantic search if available
        if self.has_semantic and query_embedding:
            # Would call embedding_index.search() here
            pass
        
        # Fall back to BM25
        return self.bm25.search(query, k)
