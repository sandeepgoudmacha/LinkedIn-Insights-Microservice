"""
Caching utilities with Redis
"""
import json
import redis
import logging
import os
from typing import Any, Optional
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.ttl = int(os.getenv('CACHE_TTL_SECONDS', '300'))
        self.client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Caching disabled.")
            self.client = None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a cache value
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (uses default if not specified)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            ttl = ttl or self.ttl
            json_value = json.dumps(value)
            self.client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key '{key}': {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a cache value
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache key '{key}': {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a cache key"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key '{key}': {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern
        
        Args:
            pattern: Key pattern (e.g., 'page:*')
        
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern '{pattern}': {str(e)}")
            return 0
    
    def flush_all(self) -> bool:
        """Flush all cache (use with caution)"""
        if not self.client:
            return False
        
        try:
            self.client.flushdb()
            logger.warning("Cache flushed completely")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {str(e)}")
            return False


# Global cache instance
cache_manager = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)


def cached(ttl: Optional[int] = None):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
    
    Usage:
        @cached(ttl=600)
        def get_page_details(page_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__module__}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


def async_cached(ttl: Optional[int] = None):
    """
    Decorator to cache async function results
    
    Usage:
        @async_cached(ttl=600)
        async def get_page_details_async(page_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__module__}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate cache for a pattern
    
    Usage:
        @invalidate_cache("page:*")
        def update_page(page_id: str, **kwargs):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache_manager.clear_pattern(pattern)
            return result
        
        return wrapper
    return decorator
