"""Cache adapter implementations."""

import pickle
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib
import logging

from ...application.ports import CacheService

logger = logging.getLogger(__name__)


class LocalCacheService(CacheService):
    """Local file-based cache implementation."""

    def __init__(self, cache_dir: Path):
        """Initialize local cache service.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Hash the key to create a safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "rb") as f:
                data = pickle.load(f)

            # Check expiration
            if "expires_at" in data:
                if datetime.now() > data["expires_at"]:
                    # Expired, delete file
                    cache_file.unlink()
                    return None

            return data.get("value")

        except Exception as e:
            logger.error(f"Failed to read cache for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successfully cached
        """
        cache_file = self._get_cache_file(key)

        try:
            data = {"value": value}

            if ttl:
                data["expires_at"] = datetime.now() + timedelta(seconds=ttl)

            with open(cache_file, "wb") as f:
                pickle.dump(data, f)

            return True

        except Exception as e:
            logger.error(f"Failed to cache value for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        cache_file = self._get_cache_file(key)

        if cache_file.exists():
            try:
                cache_file.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed to delete cache for key {key}: {e}")

        return False

    async def clear(self) -> bool:
        """Clear all cached values.

        Returns:
            True if cache was cleared
        """
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired
        """
        value = await self.get(key)
        return value is not None


class RedisCacheService(CacheService):
    """Redis-based cache implementation."""

    def __init__(self, redis_url: str, key_prefix: str = ""):
        """Initialize Redis cache service.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all keys
        """
        import redis.asyncio as redis

        self.redis = redis.from_url(redis_url)
        self.key_prefix = key_prefix

    def _make_key(self, key: str) -> str:
        """Create full key with prefix.

        Args:
            key: Cache key

        Returns:
            Full key with prefix
        """
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        full_key = self._make_key(key)

        try:
            value = await self.redis.get(full_key)
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Failed to get from Redis: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successfully cached
        """
        full_key = self._make_key(key)

        try:
            serialized = pickle.dumps(value)

            if ttl:
                await self.redis.setex(full_key, ttl, serialized)
            else:
                await self.redis.set(full_key, serialized)

            return True

        except Exception as e:
            logger.error(f"Failed to set in Redis: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        full_key = self._make_key(key)

        try:
            result = await self.redis.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete from Redis: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cached values.

        Returns:
            True if cache was cleared
        """
        try:
            if self.key_prefix:
                # Clear only keys with our prefix
                pattern = f"{self.key_prefix}*"
                cursor = 0

                while True:
                    cursor, keys = await self.redis.scan(
                        cursor, match=pattern, count=100
                    )

                    if keys:
                        await self.redis.delete(*keys)

                    if cursor == 0:
                        break
            else:
                # Clear entire database (use with caution)
                await self.redis.flushdb()

            return True

        except Exception as e:
            logger.error(f"Failed to clear Redis cache: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        full_key = self._make_key(key)

        try:
            return await self.redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Failed to check existence in Redis: {e}")
            return False
