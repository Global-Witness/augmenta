"""Validation utilities for the cache system."""

from typing import Any, Pattern
from datetime import datetime
import re
from urllib.parse import urlparse
from .exceptions import ValidationError

# Common URL validation pattern
URL_PATTERN: Pattern = re.compile(
    r'^https?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

def is_valid_url(url: str) -> bool:
    """Validate URL format and basic structure."""
    if not url or not isinstance(url, str):
        return False
        
    url = url.strip()
    if not URL_PATTERN.match(url):
        return False
        
    try:
        result = urlparse(url)
        return all([
            result.scheme in ('http', 'https'),
            result.netloc,
            len(url) < 2048
        ])
    except Exception:
        return False

def validate_string(value: str, name: str) -> None:
    """Validate string is non-empty."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be a non-empty string")

def validate_int(value: int, name: str, min_value: int = 0) -> None:
    """Validate integer is within range."""
    if not isinstance(value, int) or value < min_value:
        raise ValidationError(f"{name} must be an integer >= {min_value}")

def validate_datetime(value: Any, name: str) -> None:
    """Validate datetime object."""
    if not isinstance(value, datetime):
        raise ValidationError(f"{name} must be a datetime object")