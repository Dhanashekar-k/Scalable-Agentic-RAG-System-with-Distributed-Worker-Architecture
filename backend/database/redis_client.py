"""
Redis client for semantic caching and short-lived agent state.
Handles connection pooling and async operations.
"""
import json
import asyncio
import socket
from typing import Optional, Any, List
from redis.asyncio import Redis, ConnectionPool
from config.settings import settings


class RedisClient:
    """Async Redis client wrapper."""
    
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
    
    async def connect(self):
        """Initialize Redis connection pool with optimized settings."""
        # Use named socket constants for cross-version compatibility
        # (raw ints 1/2/3 worked in redis-py 4.x but are unreliable in 5.x)
        keepalive_opts = {}
        try:
            keepalive_opts = {
                socket.TCP_KEEPIDLE: 3,   # seconds idle before probes
                socket.TCP_KEEPINTVL: 3,  # seconds between probes
                socket.TCP_KEEPCNT: 3,    # number of probes before giving up
            }
        except AttributeError:
            # TCP_KEEPIDLE not available on all platforms (e.g. macOS < 10.8)
            pass

        self.pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=False,  # Handle binary for embeddings
            max_connections=50,      # Handle concurrent load
            socket_connect_timeout=10,
            socket_keepalive=True,
            socket_keepalive_options=keepalive_opts,
        )
        self.client = Redis(connection_pool=self.pool)
    
    async def disconnect(self):
        """Close Redis connections (compatible with redis-py 4.x and 5.x)."""
        if self.client:
            # redis-py 5.x uses aclose(); fall back to close() for 4.x
            if hasattr(self.client, 'aclose'):
                await self.client.aclose()
            else:
                await self.client.close()
        if self.pool:
            await self.pool.disconnect()
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get value by key."""
        return await self.client.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value with optional TTL (seconds)."""
        await self.client.set(key, value, ex=ttl)
    
    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set JSON-serializable value."""
        await self.set(key, json.dumps(value), ttl)
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get and deserialize JSON value."""
        value = await self.get(key)
        return json.loads(value) if value else None
    
    async def delete(self, key: str):
        """Delete key."""
        await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0
    
    async def increment(self, key: str) -> int:
        """Increment counter."""
        return await self.client.incr(key)
    
    async def lpush(self, key: str, value: str):
        """Push value to left of Redis list."""
        await self.client.lpush(key, value)
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range of values from Redis list."""
        result = await self.client.lrange(key, start, end)
        # Decode bytes to strings if needed
        return [item.decode('utf-8') if isinstance(item, bytes) else item for item in result]
    
    async def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


# Global Redis client instance
redis_client = RedisClient()
