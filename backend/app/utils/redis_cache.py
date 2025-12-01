"""
Redis Cache Implementation
Distributed cache using Redis for multi-instance deployments
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.config import get_settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based distributed cache with TTL support and in-memory fallback"""

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize Redis cache
        
        Args:
            redis_client: Optional Redis client (will create new if not provided)
        """
        self.settings = get_settings()
        self._client: Optional[Redis] = None
        self._redis_client_provided = redis_client is not None
        self._fallback_cache = None  # SimpleCache fallback
        self._use_fallback = False
        
        if redis_client:
            self._client = redis_client
        else:
            # Will be initialized lazily
            self._redis_url = getattr(
                self.settings, "redis_url", "redis://localhost:6379/0"
            )

    def _get_fallback_cache(self):
        """Get or create in-memory fallback cache"""
        if self._fallback_cache is None:
            from app.utils.cache import SimpleCache
            self._fallback_cache = SimpleCache()
        return self._fallback_cache

    async def _get_client(self) -> Optional[Redis]:
        """Get or create Redis client, returns None if Redis unavailable"""
        if self._use_fallback:
            return None
            
        if self._client is None:
            try:
                self._client = await aioredis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    max_connections=50,  # Connection pool size
                )
                # Test connection
                await self._client.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}, falling back to in-memory cache")
                self._use_fallback = True
                return None
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis or fallback)"""
        try:
            client = await self._get_client()
            if client is None:
                # Use fallback cache
                return self._get_fallback_cache().get(key)
                
            value = await client.get(key)
            if value is None:
                return None

            # Deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, return as string
                return value

        except Exception as e:
            logger.warning(f"Redis get error for key {key}: {e}, using fallback")
            # Fallback to in-memory cache on error
            return self._get_fallback_cache().get(key)

    async def set(
        self, key: str, value: Any, ttl_seconds: int = 3600
    ) -> bool:
        """Set value in cache with TTL (Redis or fallback)"""
        try:
            client = await self._get_client()
            if client is None:
                # Use fallback cache
                self._get_fallback_cache().set(key, value, ttl_seconds)
                return True

            # Serialize to JSON
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError):
                # If can't serialize, convert to string
                serialized = str(value)

            await client.setex(key, ttl_seconds, serialized)
            return True

        except Exception as e:
            logger.warning(f"Redis set error for key {key}: {e}, using fallback")
            # Fallback to in-memory cache on error
            self._get_fallback_cache().set(key, value, ttl_seconds)
            return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache (Redis or fallback)"""
        try:
            client = await self._get_client()
            if client is None:
                # Use fallback cache
                self._get_fallback_cache().delete(key)
                return True

            result = await client.delete(key)
            return result > 0

        except Exception as e:
            logger.warning(f"Redis delete error for key {key}: {e}, using fallback")
            # Fallback to in-memory cache on error
            self._get_fallback_cache().delete(key)
            return True

    async def clear(self) -> bool:
        """Clear all cache (use with caution!)"""
        try:
            client = await self._get_client()
            if client is None:
                return False

            await client.flushdb()
            logger.warning("⚠️ Redis cache cleared")
            return True

        except Exception as e:
            logger.warning(f"Redis clear error: {e}")
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            client = await self._get_client()
            if client is None:
                # Return fallback cache stats
                fallback_stats = self._get_fallback_cache().get_stats()
                return {
                    "type": "fallback",
                    "status": "redis_unavailable",
                    **fallback_stats,
                }

            info = await client.info("stats")
            db_size = await client.dbsize()

            return {
                "type": "redis",
                "status": "connected",
                "keys": db_size,
                "hits": int(info.get("keyspace_hits", 0)),
                "misses": int(info.get("keyspace_misses", 0)),
                "hit_rate": (
                    int(info.get("keyspace_hits", 0))
                    / (
                        int(info.get("keyspace_hits", 0))
                        + int(info.get("keyspace_misses", 1))
                    )
                    if (int(info.get("keyspace_hits", 0)) + int(info.get("keyspace_misses", 1))) > 0
                    else 0.0
                ),
            }

        except Exception as e:
            logger.warning(f"Redis stats error: {e}")
            # Return fallback cache stats on error
            fallback_stats = self._get_fallback_cache().get_stats()
            return {
                "type": "fallback",
                "status": "error",
                "error": str(e),
                **fallback_stats,
            }

    async def close(self):
        """Close Redis connection"""
        if self._client and not self._redis_client_provided:
            await self._client.close()
            self._client = None
            logger.info("Redis cache connection closed")


# Global cache instance (will be initialized on first use)
_cache: Optional[RedisCache] = None


async def get_redis_cache() -> RedisCache:
    """Get global Redis cache instance"""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


async def close_redis_cache():
    """Close Redis cache connection"""
    global _cache
    if _cache:
        await _cache.close()
        _cache = None

