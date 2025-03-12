"""Centralized logging functionality for the Augmenta package."""

import logging
import contextlib
from typing import Any, Dict, Optional
from functools import wraps

try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

# Global state
_LOGGING_ENABLED = False
_LOGFIRE_ENABLED = False

def is_logging_enabled() -> bool:
    """Check if logging is enabled."""
    return _LOGGING_ENABLED

def is_logfire_enabled() -> bool:
    """Check if logfire is enabled and configured."""
    return _LOGFIRE_ENABLED and LOGFIRE_AVAILABLE

def configure_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    global _LOGGING_ENABLED, _LOGFIRE_ENABLED
    
    _LOGGING_ENABLED = verbose
    
    if not verbose:
        return
        
    if LOGFIRE_AVAILABLE:
        try:
            logfire.configure(scrubbing=False)
            logfire.instrument_httpx(capture_all=True)
            _LOGFIRE_ENABLED = True
        except Exception as e:
            print(f"Failed to configure logfire: {e}")
            _LOGFIRE_ENABLED = False
    else:
        print("Please install `pip install 'logfire[httpx]'` to see the logs in logfire.")

@contextlib.contextmanager
def create_row_span(query: str, **attributes):
    """Create a span for processing a single row.
    
    Args:
        query: The query being processed
        **attributes: Additional attributes to attach to the span
    """
    if not is_logging_enabled():
        yield None
        return
        
    if is_logfire_enabled():
        with logfire.span(f"Processing row: {query}", **attributes) as span:
            yield span
    else:
        logger = logging.getLogger(__name__)
        logger.info(f"Starting processing row: {query}")
        yield None
        logger.info(f"Finished processing row: {query}")

def get_current_span() -> Optional[Any]:
    """Get the current active span, if any."""
    if not is_logfire_enabled():
        return None
    
    return logfire.current_span()

def log_to_span(message: str, level: str = "info", **attributes):
    """Log a message to the current span.
    
    Args:
        message: The message to log
        level: The log level ('debug', 'info', 'warning', 'error')
        **attributes: Additional attributes to attach to the log entry
    """
    if not is_logging_enabled():
        return
        
    if is_logfire_enabled():
        log_func = getattr(logfire, level, logfire.info)
        log_func(message, **attributes)
    else:
        logger = logging.getLogger(__name__)
        log_func = getattr(logger, level, logger.info)
        log_func(message)

def trace(message: str, **attributes):
    """Log a trace message."""
    log_to_span(message, "trace", **attributes)

def debug(message: str, **attributes):
    """Log a debug message."""
    log_to_span(message, "debug", **attributes)

def info(message: str, **attributes):
    """Log an info message."""
    log_to_span(message, "info", **attributes)

def warning(message: str, **attributes):
    """Log a warning message."""
    log_to_span(message, "warning", **attributes)

def error(message: str, **attributes):
    """Log an error message."""
    log_to_span(message, "error", **attributes)

def fatal(message: str, **attributes):
    """Log a fatal message."""
    log_to_span(message, "fatal", **attributes)