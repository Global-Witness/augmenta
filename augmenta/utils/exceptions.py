"""Exceptions for the cache system."""

class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass

class DatabaseError(CacheError):
    """Exception for database operation failures."""
    pass

class ValidationError(CacheError):
    """Exception for data validation failures."""
    pass