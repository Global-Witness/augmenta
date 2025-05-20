"""Process-specific caching operations."""

from datetime import datetime
import click
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from augmenta.utils.get_hash import get_hash
from .manager import CacheManager

def get_cache_manager() -> CacheManager:
    """Get the singleton cache manager instance."""
    return CacheManager()

def setup_cache_handling(
    config_data: Dict[str, Any],
    config_path: Path,
    cache_enabled: bool,
    process_id: Optional[str],
    auto_resume: bool,
    df: pd.DataFrame
) -> Tuple[Optional[str], Optional[CacheManager], Dict[int, Any]]:
    """Set up caching configuration.
    
    Args:
        config_data: Configuration dictionary
        config_path: Path to configuration file
        cache_enabled: Whether caching is enabled
        process_id: Optional process ID for resuming
        auto_resume: Whether to auto-resume previous processes
        df: Loaded DataFrame
        
    Returns:
        Tuple of (process ID, cache manager, cached results)
    """
    if not cache_enabled:
        return None, None, {}
        
    # Initialize cache manager once
    cache_manager = get_cache_manager()
    
    # Skip resumption if explicitly provided or disabled
    if not process_id and auto_resume:
        # Generate hash for config and input data
        config_hash = get_hash(config_data)
        csv_hash = get_hash(config_data["input_csv"])
        combined_hash = get_hash({'config': config_hash, 'csv': csv_hash})
        
        # Check for unfinished process
        if unfinished_process := cache_manager.find_unfinished_process(combined_hash):
            summary = cache_manager.get_process_summary(unfinished_process)
            click.echo(summary)
            if click.confirm("Would you like to resume this process?"):
                process_id = unfinished_process.process_id
    
    # Set up or resume process
    if not process_id:
        # Start new process
        config_hash = get_hash(config_data)
        csv_hash = get_hash(config_data["input_csv"])
        combined_hash = get_hash({'config': config_hash, 'csv': csv_hash})
        process_id = cache_manager.start_process(combined_hash, len(df))
    else:
        # Update existing process
        with cache_manager.db.get_connection() as conn:
            conn.execute(
                "UPDATE processes SET status = 'running', last_updated = ? WHERE process_id = ?",
                (datetime.now(), process_id)
            )
    
    # Get cached results
    cached_results = cache_manager.get_cached_results(process_id)
    
    return process_id, cache_manager, cached_results

def apply_cached_results(
    df: pd.DataFrame,
    process_id: str,
    cache_manager: Optional[CacheManager] = None
) -> pd.DataFrame:
    """Apply cached results to a DataFrame."""
    if cache_manager is None:
        cache_manager = get_cache_manager()
        
    cached_results = cache_manager.get_cached_results(process_id)
    for row_index, result in cached_results.items():
        for key, value in result.items():
            df.at[row_index, key] = value
    return df

def handle_cache_cleanup(cache_manager: Optional[Any] = None) -> None:
    """Clean up cache by removing the cache database file."""
    if cache_manager is None:
        cache_manager = get_cache_manager()
    
    try:
        # Ensure all pending writes are processed
        cache_manager.cleanup()
        
        # Get the database path
        db_path = cache_manager.db_path
        
        # Close any existing connections
        cache_manager.close_connections()
        
        # Delete the database file if it exists
        if db_path.exists():
            db_path.unlink()
            click.echo("Cache database deleted successfully!")
        else:
            click.echo("No cache database found.")
            
    except Exception as e:
        click.echo(f"Error cleaning cache: {e}", err=True)