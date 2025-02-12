"""
Cache management system for Augmenta.
Provides functionality for caching and retrieving process results.
"""

from .manager import CacheManager
from .models import ProcessStatus, CacheError, DatabaseError
from .process import (
    handle_process_resumption,
    handle_cache_cleanup,
    setup_caching,
    apply_cached_results
)

__all__ = [
    # Core cache management
    'CacheManager',
    
    # Process handling
    'handle_process_resumption',
    'handle_cache_cleanup',
    'setup_caching',
    'apply_cached_results',
    
    # Models and exceptions
    'ProcessStatus',
    'CacheError',
    'DatabaseError'
]