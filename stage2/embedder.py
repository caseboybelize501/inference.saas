"""Embedder - generates embeddings via Stage 1 InferenceAPI."""

import asyncio
from typing import List, Dict, Any, Optional
import httpx

from contracts.models.index_entry import ChunkEntry


INFERENCE_API_URL = "http://localhost:3000"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Small dedicated embedder
BATCH_SIZE = 32


class Embedder:
    """Generates embeddings by calling Stage 1 InferenceAPI."""
    
    def __init__(self, base_url: str = INFERENCE_API_URL):
        """
        Initialize embedder.
        
        Args:
            base_url: Stage 1 InferenceAPI base URL
        """
        self.base_url = base_url
        self.model = EMBEDDING_MODEL
    
    async def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector or None if failed
        """
        result = await self.embed_batch([text])
        return result[0] if result else None
    
    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for batch of texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors (None for failures)
        """
        embeddings = [None] * len(texts)
        
        # Process in batches
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            batch_embeddings = await self._request_embeddings(batch)
            
            if batch_embeddings:
                for j, emb in enumerate(batch_embeddings):
                    embeddings[i + j] = emb
        
        return embeddings
    
    async def _request_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Request embeddings from InferenceAPI.
        
        Args:
            texts: Texts to embed
        
        Returns:
            List of embedding vectors or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/embeddings",
                    json={
                        "model": self.model,
                        "input": texts
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Sort by index to maintain order
                sorted_embeddings = sorted(data.get("data", []), key=lambda x: x["index"])
                return [item["embedding"] for item in sorted_embeddings]
                
        except httpx.HTTPError as e:
            print(f"Embedding request failed: {e}")
            return None
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def embed_sync(self, text: str) -> Optional[List[float]]:
        """
        Synchronous embedding for single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector or None
        """
        return asyncio.run(self.embed(text))
    
    def embed_batch_sync(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Synchronous batch embedding.
        
        Args:
            texts: Texts to embed
        
        Returns:
            List of embedding vectors
        """
        return asyncio.run(self.embed_batch(texts))
    
    def embed_chunks(self, chunks: List[ChunkEntry]) -> Dict[str, List[float]]:
        """
        Embed list of chunks.
        
        Args:
            chunks: ChunkEntry objects to embed
        
        Returns:
            Dictionary mapping chunk ID to embedding
        """
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_batch_sync(texts)
        
        result = {}
        for chunk, embedding in zip(chunks, embeddings):
            if embedding:
                result[chunk.id] = embedding
        
        return result


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Convenience function to embed texts synchronously.
    
    Args:
        texts: Texts to embed
    
    Returns:
        List of embedding vectors
    """
    embedder = Embedder()
    results = embedder.embed_batch_sync(texts)
    return [r for r in results if r is not None]
