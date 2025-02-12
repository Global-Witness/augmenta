"""
Cache management system for Augmenta.
Provides functionality for caching and retrieving process results.
"""

from augmenta.utils.exceptions import CacheError, DatabaseError, ValidationError
from .models import ProcessStatus
from .process import (
    handle_process_resumption,
    handle_cache_cleanup,
    setup_caching,
    apply_cached_results
)
from .manager import CacheManager

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
    'DatabaseError',
    'ValidationError'
]