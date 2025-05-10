"""Core processing logic for the Augmenta package."""

import json
import asyncio
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable, Type, Union
from dataclasses import dataclass

from augmenta.utils.prompt_formatter import format_examples, format_prompt
from augmenta.agent import AugmentaAgent
from augmenta.cache import CacheManager
from augmenta.cache.process import handle_process_resumption, setup_caching, apply_cached_results
from augmenta.config.read_config import load_config, get_config_values
import logfire

@dataclass
class ProcessingResult:
    """Container for processing results."""
    index: int
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None

class AugmentaError(Exception):
    """Base exception for Augmenta-related errors."""
    pass


def setup_agent(config_data: Dict[str, Any]) -> AugmentaAgent:
    """Set up the agent with configuration values.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        Configured AugmentaAgent instance
    """
    # Initialize agent with all necessary parameters
    config_values = get_config_values(config_data)
    
    agent_settings = {
        "model": config_values["model_id"],
        "temperature": config_values["temperature"],
        "max_tokens": config_values["max_tokens"],
        "rate_limit": config_values["rate_limit"],
        "system_prompt": config_data["prompt"]["system"]
    }
    
    # Create and return agent instance
    return AugmentaAgent(**agent_settings)


def load_input_data(config_data: Dict[str, Any]) -> pd.DataFrame:
    """Load and validate input data.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        Loaded DataFrame
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        pd.errors.ParserError: If the CSV is malformed
    """
    input_csv = config_data.get("input_csv")
    if not input_csv:
        raise ValueError("Input CSV path not specified in configuration")
        
    try:
        return pd.read_csv(input_csv)
    except Exception as e:
        raise ValueError(f"Failed to read input CSV file '{input_csv}': {str(e)}")


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
        
    # Handle process resumption
    process_id = handle_process_resumption(
        config_data=config_data,
        config_path=config_path,
        csv_path=config_data["input_csv"],
        no_cache=not cache_enabled,
        resume=process_id,
        no_auto_resume=not auto_resume
    )

    # Set up caching
    cache_manager, process_id, cached_results = setup_caching(
        config_data=config_data,
        csv_path=config_data["input_csv"],
        cache_enabled=cache_enabled,
        df_length=len(df),
        process_id=process_id
    )
    
    return process_id, cache_manager, cached_results


async def process_augmenta(
    config_path: Union[str, Path],
    cache_enabled: bool = True,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    auto_resume: bool = True
) -> Tuple[pd.DataFrame, Optional[str]]:
    """Process data using the Augmenta pipeline.
    
    Args:
        config_path: Path to configuration file
        cache_enabled: Whether to enable caching
        process_id: Optional process ID for resuming
        progress_callback: Optional callback for progress updates
        auto_resume: Whether to auto-resume previous processes
        
    Returns:
        Tuple of (processed DataFrame, process ID if caching enabled)
        
    Raises:
        AugmentaError: For Augmenta-specific errors
        ValueError: For configuration or validation errors
        IOError: For file I/O errors
    """
    # Load and validate configuration
    config_path = Path(config_path)
    if not config_path.exists():
        raise AugmentaError(f"Config file not found: {config_path}")
    
    config_data = load_config(config_path)
    
    # Set up agent
    agent = setup_agent(config_data)
    
    # Load input data
    df = load_input_data(config_data)

    # Handle caching setup
    process_id, cache_manager, cached_results = setup_cache_handling(
        config_data=config_data,
        config_path=config_path,
        cache_enabled=cache_enabled,
        process_id=process_id,
        auto_resume=auto_resume,
        df=df
    )
    
    if cache_enabled:
        df = apply_cached_results(df, process_id, cache_manager)
    
    # Prepare rows for processing with cache awareness
    rows_to_process = [
        {'index': index, 'data': row}
        for index, row in df.iterrows()
        if not cache_enabled or index not in cached_results
    ]
    
    # Setup progress tracking
    processed = 0
    total = len(rows_to_process)
    
    def update_progress(row_index: str) -> None:
        """Update progress counter and invoke callback if provided."""
        nonlocal processed
        processed += 1
        if progress_callback:
            progress_callback(processed, total, row_index)
    
    # Process rows concurrently with rate limiting
    workers = config_data.get("workers", 10)
    semaphore = asyncio.Semaphore(workers)
    
    async def process_with_limit(row: Dict[str, Any]) -> ProcessingResult:
        """Process a row with rate limiting via semaphore.
        
        Args:
            row: Row data to process
            
        Returns:
            Processing result
        """
        async with semaphore:
            return await process_row(
                row_data=row,
                config=config_data,
                agent=agent,
                response_format=AugmentaAgent.create_structure_class(config_data["config_path"]),
                cache_manager=cache_manager,
                process_id=process_id,
                progress_callback=update_progress
            )
    
    tasks = [process_with_limit(row) for row in rows_to_process]
    results = await asyncio.gather(*tasks)

    # Update DataFrame with results
    successful_results, error_count = update_dataframe_with_results(df, results)

    save_and_finalize(
        df=df,
        config_data=config_data,
        cache_enabled=cache_enabled,
        cache_manager=cache_manager,
        process_id=process_id
    )
    
    return df, process_id if cache_enabled else None


async def process_row(
    row_data: Dict[str, Any],
    config: Dict[str, Any],
    agent: AugmentaAgent,
    response_format: Type,
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> ProcessingResult:
    """Process a single data row asynchronously.
    
    Args:
        row_data: Dictionary containing 'index' and 'data' keys
        config: Configuration dictionary
        agent: Agent instance to use for processing
        response_format: Response format specification
        cache_manager: Optional cache manager for caching results
        process_id: Optional process ID for cache management
        progress_callback: Optional callback for progress updates
        
    Returns:
        ProcessingResult containing processing result or error
    """
    try:
        index = row_data['index']
        row = row_data['data']
        
        # Create prompt with data from row
        prompt_user = create_formatted_prompt(config, row)
        
        # Run prompt using the agent
        response = await agent.run(prompt_user, response_format=response_format)
        
        # Handle caching and progress tracking
        handle_result_tracking(
            cache_manager=cache_manager,
            process_id=process_id, 
            index=index, 
            response=response,
            progress_callback=progress_callback
        )
            
        return ProcessingResult(index=index, data=response)
        
    except Exception as e:
        logfire.error(f"Error processing row {index}: {str(e)}", row_index=index, error=str(e))
        return ProcessingResult(index=index, data=None, error=str(e))


def create_formatted_prompt(config: Dict[str, Any], row: Dict[str, Any]) -> str:
    """Create a formatted prompt using row data and examples.
    
    Args:
        config: Configuration dictionary
        row: Row data
        
    Returns:
        Formatted prompt string
    """
    # Format the prompt with row data using string templating
    prompt_user = format_prompt(config["prompt"]["user"], row)
        
    # Format examples if present
    if examples_yaml := config.get("examples"):
        if examples_text := format_examples(examples_yaml):
            prompt_user = f'{prompt_user}\n\n{examples_text}'
            
    return prompt_user


def handle_result_tracking(
    cache_manager: Optional[CacheManager],
    process_id: Optional[str],
    index: int, 
    response: Dict[str, Any],
    progress_callback: Optional[Callable[[str], None]] = None
) -> None:
    """Handle caching and progress tracking.
    
    Args:
        cache_manager: Optional cache manager
        process_id: Optional process ID
        index: Row index
        response: Response data
        progress_callback: Optional progress callback
    """
    # Handle caching if enabled
    if cache_manager and process_id:
        cache_manager.cache_result(
            process_id=process_id,
            row_index=index,
            query=str(index),  # Use row index as query identifier
            result=json.dumps(response)
        )
    
    # Update progress if callback provided
    if progress_callback:
        progress_callback(str(index))  # Use row index for progress tracking


def update_dataframe_with_results(
    df: pd.DataFrame, 
    results: list[ProcessingResult]
) -> Tuple[int, int]:
    """Update DataFrame with processing results.
    
    Args:
        df: DataFrame to update
        results: List of processing results
        
    Returns:
        Tuple of (successful_count, error_count)
    """
    successful_results = 0
    error_count = 0
    
    for result in results:
        if result.data:
            for key, value in result.data.items():
                df.at[result.index, key] = value
            successful_results += 1
        elif result.error:
            error_count += 1
            df.at[result.index, "_error"] = result.error
    
    # Log error summary
    if error_count > 0 and error_count == len(results):
        logfire.warning(f"All {error_count} processing tasks failed. Check logs for details.")
    elif error_count > 0:
        logfire.warning(f"{error_count} of {len(results)} processing tasks failed.")
            
    return successful_results, error_count


def save_and_finalize(
    df: pd.DataFrame,
    config_data: Dict[str, Any],
    cache_enabled: bool,
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None
) -> None:
    """Save output and finalize processing.
    
    Args:
        df: DataFrame to save
        config_data: Configuration dictionary
        cache_enabled: Whether caching is enabled
        cache_manager: Optional cache manager
        process_id: Optional process ID
    """
    # Save CSV output if configured
    if output_csv := config_data.get("output_csv"):
        try:
            df.to_csv(output_csv, index=False)
            logfire.info(f"Saved output to {output_csv}")
        except Exception as e:
            logfire.error(f"Failed to save output CSV: {str(e)}")
    
    # Mark process as completed in cache if applicable
    if cache_enabled and cache_manager and process_id:
        try:
            cache_manager.mark_process_completed(process_id)
            logfire.info(f"Marked process {process_id} as completed")
        except Exception as e:
            logfire.error(f"Failed to mark process as completed: {str(e)}")
