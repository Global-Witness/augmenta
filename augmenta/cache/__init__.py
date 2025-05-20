"""
Cache management system for Augmenta.
Provides functionality for caching and retrieving process results.
"""

from .exceptions import CacheError, DatabaseError, ValidationError
from .models import ProcessStatus
from .process import (
    get_cache_manager,
    handle_cache_cleanup,
    setup_cache_handling,
    apply_cached_results
)
from .manager import CacheManager

__all__ = [
    # Core cache management
    'CacheManager',
    'get_cache_manager',
      # Process handling
    'handle_cache_cleanup',
    'setup_cache_handling',
    'apply_cached_results',
    
    # Models and exceptions
    'ProcessStatus',
    'CacheError',
    'DatabaseError',
    'ValidationError'
]