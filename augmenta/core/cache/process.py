"""
Process-specific caching operations and utilities.
"""

from datetime import datetime
import click
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from .manager import CacheManager
from augmenta.core.utils import get_hash

def handle_process_resumption(
    config_data: Dict[str, Any],
    config_path: Path,
    csv_path: Path,
    no_cache: bool = False,
    resume: Optional[str] = None,
    no_auto_resume: bool = False
) -> Optional[str]:
    """
    Handle process resumption logic including user interaction.
    
    Args:
        config_data: Configuration dictionary
        config_path: Path to config file
        csv_path: Path to input CSV file
        no_cache: Whether caching is disabled
        resume: Optional process ID to resume
        no_auto_resume: Whether to disable automatic resumption
        
    Returns:
        Optional[str]: Process ID if resuming, None otherwise
    """
    process_id = resume
    if not resume and not no_cache and not no_auto_resume:
        cache_manager = CacheManager()
        # Generate combined hash of both config and CSV
        config_hash = get_hash(config_data)
        csv_hash = get_hash(csv_path)
        combined_hash = get_hash({'config': config_hash, 'csv': csv_hash})
        
        if unfinished_process := cache_manager.find_unfinished_process(combined_hash):
            summary = cache_manager.get_process_summary(unfinished_process)
            click.echo(summary)
            if click.confirm("Would you like to resume this process?"):
                process_id = unfinished_process.process_id
                
    return process_id

def handle_cache_cleanup() -> None:
    """Clean up old cache entries."""
    CacheManager().cleanup_old_processes()
    click.echo("Cache cleaned successfully!")

def apply_cached_results(
    df: pd.DataFrame,
    process_id: str,
    cache_manager: CacheManager
) -> pd.DataFrame:
    """
    Apply cached results to a DataFrame.
    
    Args:
        df: Input DataFrame
        process_id: Process ID to retrieve cache for
        cache_manager: Cache manager instance
        
    Returns:
        pd.DataFrame: DataFrame with cached results applied
    """
    cached_results = cache_manager.get_cached_results(process_id)
    
    # Apply cached results
    for row_index, result in cached_results.items():
        for key, value in result.items():
            df.at[row_index, key] = value
            
    return df

def setup_caching(
    config_data: Dict[str, Any],
    csv_path: Path,
    cache_enabled: bool,
    df_length: int,
    process_id: Optional[str] = None
) -> Tuple[Optional[CacheManager], Optional[str], Dict]:
    """
    Set up caching for a process.
    
    Args:
        config_data: Configuration dictionary
        csv_path: Path to input CSV file
        cache_enabled: Whether caching is enabled
        df_length: Length of the DataFrame
        process_id: Optional process ID to use
        
    Returns:
        Tuple containing:
        - Optional[CacheManager]: Cache manager instance if enabled
        - Optional[str]: Process ID if caching enabled
        - Dict: Cached results dictionary
    """
    cache_manager = None
    cached_results = {}
    
    if cache_enabled:
        cache_manager = CacheManager()
        config_hash = get_hash(config_data)
        csv_hash = get_hash(csv_path)
        combined_hash = get_hash({'config': config_hash, 'csv': csv_hash})
        
        if not process_id:
            process_id = cache_manager.start_process(combined_hash, df_length)
        else:
            # If resuming, ensure the process is still marked as running
            with cache_manager.db.get_connection() as conn:
                conn.execute(
                    """UPDATE processes 
                       SET status = 'running',
                           last_updated = ?
                       WHERE process_id = ?""",
                    (datetime.now(), process_id)
                )
            
        cached_results = cache_manager.get_cached_results(process_id)
    
    return cache_manager, process_id, cached_results