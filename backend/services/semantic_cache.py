"""
Semantic prompt cache using Redis and embeddings.
Checks FIRST before any RAG pipeline execution.
"""
import time
from typing import Optional
from datetime import datetime
from database.redis_client import redis_client
from services.embedding_service import embedding_service
from models.schemas import CachedAnswer
from config.settings import settings


class SemanticCache:
    """
    Semantic cache for storing and retrieving similar queries.
    Uses embedding similarity with configurable threshold.
    """
    
    CACHE_KEY_PREFIX = "semantic_cache"
    STATS_KEY = "cache_stats"
    
    async def get_similar_answer(self, query: str) -> Optional[CachedAnswer]:
        """
        Check cache for semantically similar query.
        Returns cached answer if similarity exceeds threshold.
        """
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = embedding_service.embed_text(query)
        
        # Get all cached queries (in production, use more efficient indexing)
        cache_keys = await self._get_all_cache_keys()
        
        best_match = None
        best_similarity = 0.0
        
        for cache_key in cache_keys:
            cached_data = await redis_client.get_json(cache_key)
            if not cached_data:
                continue
            
            cached_embedding = cached_data["query_embedding"]
            similarity = embedding_service.cosine_similarity(
                query_embedding,
                cached_embedding
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached_data
        
        # Check if similarity exceeds threshold
        if best_similarity >= settings.CACHE_SIMILARITY_THRESHOLD:
            await self._update_stats("hit", best_similarity)
            return CachedAnswer(**best_match)
        
        await self._update_stats("miss", 0.0)
        return None
    
    async def store_answer(
        self,
        query: str,
        answer: str,
        confidence: float,
        metadata: dict
    ):
        """Store a new answer in the cache with TTL."""
        query_embedding = embedding_service.embed_text(query)
        
        cached_answer = CachedAnswer(
            query=query,
            query_embedding=query_embedding,
            answer=answer,
            confidence=confidence,
            metadata=metadata,
            cached_at=datetime.now(),
            ttl_seconds=settings.CACHE_TTL_SECONDS
        )
        
        # Use query hash as key
        cache_key = self._get_cache_key(query)
        
        await redis_client.set_json(
            cache_key,
            cached_answer.model_dump(mode='json'),
            ttl=settings.CACHE_TTL_SECONDS
        )
        
        # Track this cache key
        await self._add_cache_key_to_tracking(cache_key)
    
    async def get_stats(self) -> dict:
        """Get cache statistics using atomic Redis counters."""
        # Read from atomic counters - no race conditions
        total_queries = int(
            await redis_client.client.get(f"{self.STATS_KEY}:total_queries") or 0
        )
        cache_hits = int(
            await redis_client.client.get(f"{self.STATS_KEY}:cache_hits") or 0
        )
        cache_misses = int(
            await redis_client.client.get(f"{self.STATS_KEY}:cache_misses") or 0
        )
        total_similarity = float(
            await redis_client.client.get(f"{self.STATS_KEY}:total_similarity") or 0.0
        )
        
        hit_rate = (
            cache_hits / total_queries
            if total_queries > 0 else 0.0
        )
        
        avg_similarity = (
            total_similarity / cache_hits
            if cache_hits > 0 else 0.0
        )
        
        return {
            "total_queries": total_queries,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate": hit_rate,
            "avg_similarity": avg_similarity
        }
    
    async def _update_stats(self, result: str, similarity: float):
        """Update cache statistics using atomic Redis operations."""
        # All operations are atomic - no read-modify-write race conditions
        await redis_client.client.incr(f"{self.STATS_KEY}:total_queries")
        
        if result == "hit":
            await redis_client.client.incr(f"{self.STATS_KEY}:cache_hits")
            try:
                await redis_client.client.incrbyfloat(
                    f"{self.STATS_KEY}:total_similarity",
                    similarity
                )
            except:
                # Fallback if incrbyfloat not available
                current = float(
                    await redis_client.client.get(f"{self.STATS_KEY}:total_similarity") or 0.0
                )
                await redis_client.client.set(
                    f"{self.STATS_KEY}:total_similarity",
                    current + similarity
                )
        else:
            await redis_client.client.incr(f"{self.STATS_KEY}:cache_misses")
    
    async def _get_all_cache_keys(self) -> list:
        """Get all cache keys from atomic set (no race conditions)."""
        tracking_key = f"{self.CACHE_KEY_PREFIX}:keys"
        # SMEMBERS returns all members atomically
        keys = await redis_client.client.smembers(tracking_key)
        return list(keys)
    
    async def clear_all(self) -> int:
        """Clear all cached queries. Returns number of keys deleted."""
        keys = await self._get_all_cache_keys()
        deleted = 0
        
        for key in keys:
            try:
                # Delete the cache entry
                await redis_client.delete(key)
                deleted += 1
            except:
                pass
        
        # Clear tracking set
        tracking_key = f"{self.CACHE_KEY_PREFIX}:keys"
        await redis_client.client.delete(tracking_key)
        
        # Reset atomic stat counters
        await redis_client.client.delete(f"{self.STATS_KEY}:total_queries")
        await redis_client.client.delete(f"{self.STATS_KEY}:cache_hits")
        await redis_client.client.delete(f"{self.STATS_KEY}:cache_misses")
        await redis_client.client.delete(f"{self.STATS_KEY}:total_similarity")
        
        return deleted
    
    async def delete_query(self, query: str) -> bool:
        """Delete a specific cached query. Returns True if found and deleted."""
        cache_key = self._get_cache_key(query)
        
        # Check if exists
        cached = await redis_client.get_json(cache_key)
        if not cached:
            return False
        
        # Delete it
        await redis_client.delete(cache_key)
        
        # Remove from tracking set atomically
        tracking_key = f"{self.CACHE_KEY_PREFIX}:keys"
        await redis_client.client.srem(tracking_key, cache_key)
        
        return True
    
    async def get_all_cached_queries(self, limit: int = 100) -> list:
        """Get all cached queries with metadata."""
        keys = await self._get_all_cache_keys()
        cached_items = []
        
        for key in keys[:limit]:
            cached = await redis_client.get_json(key)
            if cached:
                cached_items.append({
                    'query': cached.get('query'),
                    'answer_preview': cached.get('answer', '')[:100],
                    'confidence': cached.get('confidence'),
                    'cached_at': cached.get('timestamp')
                })
        
        return cached_items
    
    async def search_cache(self, keyword: str, limit: int = 20) -> list:
        """Search cached queries by keyword."""
        all_cached = await self.get_all_cached_queries(limit=500)
        keyword_lower = keyword.lower()
        
        matches = [
            item for item in all_cached
            if keyword_lower in item['query'].lower()
        ]
        
        return matches[:limit]
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        query_hash = hash(query) & 0xFFFFFFFF  # Positive 32-bit hash
        return f"{self.CACHE_KEY_PREFIX}:{query_hash}"
    
    async def _add_cache_key_to_tracking(self, cache_key: str):
        """Add cache key to tracking set atomically."""
        tracking_key = f"{self.CACHE_KEY_PREFIX}:keys"
        # SADD is atomic - automatically handles duplicates
        await redis_client.client.sadd(tracking_key, cache_key)
        # Set expiration on the set
        await redis_client.client.expire(tracking_key, settings.CACHE_TTL_SECONDS)


# Global semantic cache instance
semantic_cache = SemanticCache()
