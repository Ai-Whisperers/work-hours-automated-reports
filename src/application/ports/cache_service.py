"""Cache service port."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheService(ABC):
    """Port for caching service.
    
    This interface abstracts caching functionality and can be
    implemented using different backends (memory, Redis, file, etc.).
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
            
        Returns:
            True if successfully cached
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cached values.
        
        Returns:
            True if cache was cleared
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and is not expired
        """
        pass