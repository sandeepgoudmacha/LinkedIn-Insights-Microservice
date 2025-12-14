"""
General utility functions
"""
import logging
import time
import hashlib
from typing import Optional, List
from functools import wraps
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed"""
        now = time.time()
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False


def retry(max_attempts: int = 3, delay: int = 1, backoff: float = 1.0):
    """
    Decorator for retrying function calls with exponential backoff
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay between attempts
    
    Usage:
        @retry(max_attempts=3, delay=2)
        def fetch_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(max_attempts: int = 3, delay: int = 1, backoff: float = 1.0):
    """Async version of retry decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


def generate_hash(text: str) -> str:
    """Generate SHA256 hash of text"""
    return hashlib.sha256(text.encode()).hexdigest()


def truncate_text(text: str, length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) > length:
        return text[:length - 3] + "..."
    return text


def calculate_engagement_rate(
    likes: int,
    comments: int,
    shares: int,
    views: int
) -> float:
    """
    Calculate engagement rate
    
    Formula: (likes + comments + shares) / views * 100
    """
    if views == 0:
        return 0.0
    return ((likes + comments + shares) / views) * 100


def format_large_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def paginate_query(query, page: int = 1, per_page: int = 20):
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Tuple of (items, total, pages)
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 20
    
    total = query.count()
    pages = (total + per_page - 1) // per_page
    
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return items, total, pages


def parse_follower_range(follower_str: str) -> Optional[tuple]:
    """
    Parse follower range string like "1k-10k" or "1m-5m"
    
    Returns:
        Tuple of (min_followers, max_followers) or None if invalid
    """
    try:
        if '-' not in follower_str:
            return None
        
        parts = follower_str.lower().split('-')
        if len(parts) != 2:
            return None
        
        def parse_number(s):
            s = s.strip()
            multipliers = {'k': 1000, 'm': 1_000_000, 'b': 1_000_000_000}
            for suffix, mult in multipliers.items():
                if s.endswith(suffix):
                    return int(float(s[:-1]) * mult)
            return int(float(s))
        
        min_val = parse_number(parts[0])
        max_val = parse_number(parts[1])
        
        return (min_val, max_val)
    except Exception as e:
        logger.error(f"Error parsing follower range '{follower_str}': {str(e)}")
        return None


class SearchHelper:
    """Helper functions for text search and filtering"""
    
    @staticmethod
    def similarity_score(text1: str, text2: str) -> float:
        """
        Calculate similarity between two strings (0-1)
        Uses simple character overlap method
        """
        text1 = text1.lower()
        text2 = text2.lower()
        
        # If exact match
        if text1 == text2:
            return 1.0
        
        # If one contains the other
        if text1 in text2 or text2 in text1:
            return 0.9
        
        # Character overlap
        common = len(set(text1) & set(text2))
        total = len(set(text1) | set(text2))
        
        if total == 0:
            return 0.0
        
        return common / total
    
    @staticmethod
    def similar_search(query: str, items: List[str], threshold: float = 0.6) -> List[str]:
        """Find similar strings from a list"""
        results = []
        for item in items:
            score = SearchHelper.similarity_score(query, item)
            if score >= threshold:
                results.append(item)
        return results


def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} executed in {elapsed:.2f}s")
        return result
    
    return wrapper


def async_log_execution_time(func):
    """Decorator to log async function execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} executed in {elapsed:.2f}s")
        return result
    
    return wrapper
