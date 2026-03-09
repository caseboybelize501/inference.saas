"""Context packager - ranks and assembles context for LLM."""

from typing import List, Dict, Any, Optional
import numpy as np

from contracts.models.context_request import ContextQuery, ContextResult, ContextChunk
from contracts.models.index_entry import ChunkEntry
from stage2.embedding_index import EmbeddingIndex
from stage2.call_graph import CallGraph
from stage2.embedder import Embedder


class ContextPackager:
    """Assembles ranked context chunks for LLM prompts."""
    
    def __init__(self, embedding_index: EmbeddingIndex, call_graph: CallGraph):
        """
        Initialize context packager.
        
        Args:
            embedding_index: Vector index for semantic search
            call_graph: Call graph for code relationships
        """
        self.embedding_index = embedding_index
        self.call_graph = call_graph
        self.embedder = Embedder()
        
        # Ranking weights
        self.semantic_weight = 0.6
        self.callgraph_weight = 0.3
        self.proximity_weight = 0.1
    
    async def rank(
        self,
        query: ContextQuery
    ) -> ContextResult:
        """
        Rank and return context chunks for query.
        
        Args:
            query: Context query parameters
        
        Returns:
            ContextResult with ranked chunks
        """
        # Get embeddings for query
        query_embedding = await self.embedder.embed(query.query)
        
        if not query_embedding:
            return ContextResult(chunks=[], total_tokens_est=0)
        
        # Semantic search
        semantic_results = self.embedding_index.search(
            query_embedding,
            k=query.max_chunks * 2  # Get more for reranking
        )
        
        # Call graph results (if cursor position provided)
        callgraph_results = []
        if query.cursor_file and query.strategy in ("callgraph", "hybrid"):
            callgraph_results = self._get_callgraph_context(
                query.cursor_file,
                query.cursor_line
            )
        
        # Combine and rank
        ranked_chunks = self._combine_and_rank(
            query=query,
            semantic_results=semantic_results,
            callgraph_results=callgraph_results
        )
        
        # Calculate estimated tokens
        total_tokens = sum(self._estimate_tokens(chunk.content) for chunk in ranked_chunks)
        
        return ContextResult(
            chunks=ranked_chunks,
            total_tokens_est=total_tokens
        )
    
    def _get_callgraph_context(
        self,
        file: str,
        line: int,
        depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get context from call graph.
        
        Args:
            file: Current file
            line: Current line
            depth: Call graph search depth
        
        Returns:
            List of related chunks with scores
        """
        # Find symbol at cursor position (simplified)
        # In production, would use AST indexer to find exact symbol
        
        results = []
        
        # Get callers and callees
        # This is simplified - would need symbol resolution in production
        return results
    
    def _combine_and_rank(
        self,
        query: ContextQuery,
        semantic_results: List[tuple],
        callgraph_results: List[Dict]
    ) -> List[ContextChunk]:
        """
        Combine and rank results from multiple sources.
        
        Args:
            query: Original query
            semantic_results: Semantic search results
            callgraph_results: Call graph results
        
        Returns:
            Ranked list of ContextChunk objects
        """
        chunk_scores: Dict[str, Dict[str, float]] = {}
        
        # Score semantic results
        for chunk_id, distance in semantic_results:
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = {'semantic': 0, 'callgraph': 0, 'proximity': 0}
            # Convert distance to similarity (lower distance = higher similarity)
            chunk_scores[chunk_id]['semantic'] = 1 - distance
        
        # Score call graph results
        for result in callgraph_results:
            chunk_id = result.get('chunk_id')
            if chunk_id and chunk_id in chunk_scores:
                chunk_scores[chunk_id]['callgraph'] = result.get('score', 0.5)
            elif chunk_id:
                chunk_scores[chunk_id] = {'semantic': 0, 'callgraph': result.get('score', 0.5), 'proximity': 0}
        
        # Calculate combined scores
        combined = []
        for chunk_id, scores in chunk_scores.items():
            combined_score = (
                scores['semantic'] * self.semantic_weight +
                scores['callgraph'] * self.callgraph_weight +
                scores['proximity'] * self.proximity_weight
            )
            combined.append((chunk_id, combined_score, scores))
        
        # Sort by combined score
        combined.sort(key=lambda x: x[1], reverse=True)
        
        # Build result chunks
        results = []
        for chunk_id, score, scores in combined[:query.max_chunks]:
            metadata = self.embedding_index.get_chunk_metadata(chunk_id)
            if metadata:
                reason = self._build_reason(scores, query.strategy)
                results.append(ContextChunk(
                    file=metadata.get('file', 'unknown'),
                    start_line=metadata.get('line_start', 0),
                    end_line=metadata.get('line_end', 0),
                    content=metadata.get('content', ''),
                    score=score,
                    reason=reason
                ))
        
        return results
    
    def _build_reason(self, scores: Dict[str, float], strategy: str) -> str:
        """Build human-readable reason for inclusion."""
        reasons = []
        
        if scores['semantic'] > 0.5:
            reasons.append(f"semantic match ({scores['semantic']:.2f})")
        
        if scores['callgraph'] > 0.3:
            reasons.append(f"call graph related ({scores['callgraph']:.2f})")
        
        if scores['proximity'] > 0.3:
            reasons.append(f"near cursor ({scores['proximity']:.2f})")
        
        return "; ".join(reasons) if reasons else "fallback"
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimate: 1 token ≈ 4 characters for English code
        return len(text) // 4
    
    def assemble_prompt(
        self,
        chunks: List[ContextChunk],
        query: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Assemble ranked chunks into LLM prompt.
        
        Args:
            chunks: Ranked context chunks
            query: User query
            max_tokens: Maximum tokens for prompt
        
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        current_tokens = 0
        
        # Add query
        prompt_parts.append(f"Query: {query}\n")
        current_tokens += self._estimate_tokens(query) + 10
        
        # Add chunks
        for chunk in chunks:
            chunk_tokens = self._estimate_tokens(chunk.content) + 50
            
            if current_tokens + chunk_tokens > max_tokens:
                break
            
            prompt_parts.append(f"\n--- {chunk.file}:{chunk.start_line}-{chunk.end_line} ---\n")
            prompt_parts.append(chunk.content)
            prompt_parts.append("\n")
            current_tokens += chunk_tokens
        
        return "".join(prompt_parts)
