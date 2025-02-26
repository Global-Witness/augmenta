# Rate Limiter Implementation Plan

## Problem
Current rate limiting implementation is not effectively preventing multiple concurrent requests to the Brave Search API, resulting in 429 Too Many Requests errors.

## Proposed Solution
Implement a new rate limiting solution using aiolimiter library to ensure consistent rate limiting across async processes.

### Key Components

1. New Rate Limiter Module (`augmenta/core/rate_limit/limiter.py`)
   - Create a global rate limiter instance using aiolimiter
   - Implement context manager for easy usage
   - Ensure thread-safe access to rate limiter

2. Integration with Search Providers
   - Modify base search provider to use new rate limiter
   - Remove old rate limiter implementation
   - Add rate limiter as a required component for API-based providers

### Implementation Details

1. Install aiolimiter:
```bash
pip install aiolimiter
```

2. Create new rate limiter module:
```python
from aiolimiter import AsyncLimiter
from contextlib import asynccontextmanager

class RateLimitManager:
    """Global rate limiter using aiolimiter."""
    _instances = {}
    
    @classmethod
    def get_limiter(cls, name: str, rate: float, time_period: float = 1.0):
        """Get or create a rate limiter for a specific service."""
        if name not in cls._instances:
            cls._instances[name] = AsyncLimiter(rate, time_period)
        return cls._instances[name]

    @classmethod
    @asynccontextmanager
    async def acquire(cls, name: str, rate: float, time_period: float = 1.0):
        """Context manager for rate limiting."""
        limiter = cls.get_limiter(name, rate, time_period)
        try:
            async with limiter:
                yield
        except Exception as e:
            # Log error but don't release limiter early
            raise
```

3. Modify base search provider:
```python
from ...rate_limit.limiter import RateLimitManager

class BaseSearchProvider:
    async def _make_request(self, url: str, **kwargs):
        async with RateLimitManager.acquire(
            self.__class__.__name__, 
            rate=0.5,  # 1 request per 2 seconds
            time_period=1.0
        ):
            # Make actual request
            async with self.client.stream(**kwargs) as response:
                # ... rest of the code
```

### Benefits
- Consistent rate limiting across all async processes
- Thread-safe implementation
- Simpler, more reliable code
- Better error handling and logging

### Testing Plan
1. Unit tests for rate limiter
   - Test singleton behavior
   - Test rate limiting accuracy
   - Test error handling

2. Integration tests
   - Test with multiple concurrent requests
   - Verify rate limit compliance
   - Test error scenarios

### Migration Plan
1. Create new rate limit module
2. Add aiolimiter to project dependencies
3. Modify search providers to use new rate limiter
4. Remove old rate limiter code
5. Run tests and verify rate limiting works
6. Deploy changes