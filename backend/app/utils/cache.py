import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check if expired
        if datetime.utcnow() > entry["expires_at"]:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set value in cache with TTL"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        # Count expired entries
        now = datetime.utcnow()
        expired = sum(1 for entry in self._cache.values() if now > entry["expires_at"])

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "expired_entries": expired,
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries, return count of removed entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self._cache.items() if now > entry["expires_at"]
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


# Global cache instance
_cache = SimpleCache()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl_seconds: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results

    Args:
        ttl_seconds: Time to live in seconds
        key_prefix: Prefix for cache key
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = _cache.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache MISS for {func.__name__}")
            result = await func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_key_str, result, ttl_seconds)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = _cache.get(cache_key_str)
            if cached_value is not None:
                logger.debug(f"Cache HIT for {func.__name__}")
                return cached_value

            # Cache miss - execute function
            logger.debug(f"Cache MISS for {func.__name__}")
            result = func(*args, **kwargs)

            # Store in cache
            _cache.set(cache_key_str, result, ttl_seconds)

            return result

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_cache() -> SimpleCache:
    """Get global cache instance"""
    return _cache
