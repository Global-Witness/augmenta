"""
Core processing logic for the Augmenta package.
"""

import yaml
import json
import logging
import asyncio
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable, Set
from dataclasses import dataclass

from augmenta.core.search import search_web
from augmenta.core.extractors import extract_urls
from augmenta.core.prompt import format_docs, format_examples
from augmenta.core.llm import make_request_llm, InstructorHandler
from augmenta.core.cache import CacheManager
from augmenta.core.cache.process import setup_caching, apply_cached_results
from augmenta.core.config.credentials import CredentialsManager

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases
ConfigDict = Dict[str, Any]
RowData = Dict[str, Any]
ProgressCallback = Callable[[int, int, str], None]

# Required configuration fields
REQUIRED_CONFIG_FIELDS: Set[str] = {
    "input_csv",
    "query_col",
    "prompt",
    "model",
    "search"
}

@dataclass
class ProcessingResult:
    """Container for processing results."""
    index: int
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None

class AugmentaError(Exception):
    """Base exception for Augmenta-related errors."""
    pass

class ConfigurationError(AugmentaError):
    """Configuration-related errors."""
    pass

def validate_config(config: ConfigDict) -> None:
    """
    Validate configuration data structure and required fields.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    missing_fields = REQUIRED_CONFIG_FIELDS - set(config.keys())
    if missing_fields:
        raise ConfigurationError(f"Missing required config fields: {missing_fields}")
    
    if not isinstance(config.get("search"), dict):
        raise ConfigurationError("'search' must be a dictionary")
    if not isinstance(config.get("prompt"), dict):
        raise ConfigurationError("'prompt' must be a dictionary")

async def process_row(
    row_data: RowData,
    config: ConfigDict,
    credentials: Dict[str, str],
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> ProcessingResult:
    """
    Process a single data row asynchronously.
    
    Args:
        row_data: Dictionary containing row index and data
        config: Configuration dictionary
        credentials: API credentials
        cache_manager: Optional cache manager instance
        process_id: Optional process ID for caching
        progress_callback: Optional callback for progress updates
        
    Returns:
        ProcessingResult containing processed data or error information
    """
    index = row_data['index']
    row = row_data['data']
    
    try:
        query = row[config['query_col']]
        
        # Search and extract
        urls = await search_web(
            query=query,
            results=config["search"]["results"],
            engine=config["search"]["engine"],
            rate_limit=config["search"].get("rate_limit"),
            credentials=credentials
        )
        
        urls_text = await extract_urls(urls)
        urls_docs = format_docs(urls_text)
        
        # Format prompt
        prompt_user = config["prompt"]["user"]
        for column, value in row.items():
            placeholder = f"{{{{{column}}}}}"
            if placeholder in prompt_user:
                prompt_user = prompt_user.replace(placeholder, str(value))
        
        # Add examples if present
        if examples_yaml := config["prompt"].get("examples"):
            if examples_text := format_examples(examples_yaml):
                prompt_user = f'{prompt_user}\n\n{examples_text}'
        
        prompt_user = f'{prompt_user}\n\n## Documents\n\n{urls_docs}'
        
        # Process with LLM
        Structure = InstructorHandler.create_structure_class(config["config_path"])
        response = await make_request_llm(
            prompt_system=config["prompt"]["system"],
            prompt_user=prompt_user,
            model=config["model"]["name"],
            response_format=Structure,
            rate_limit=config["model"].get("rate_limit"),
            max_tokens=config.get("model", {}).get("max_tokens")
        )
        
        # Cache result if enabled
        if cache_manager and process_id:
            cache_manager.cache_result(
                process_id=process_id,
                row_index=index,
                query=query,
                result=json.dumps(response)
            )
        
        if progress_callback:
            progress_callback(query)
            
        return ProcessingResult(index=index, data=response)
        
    except Exception as e:
        logger.error(f"Error processing row {index}: {str(e)}", exc_info=True)
        return ProcessingResult(index=index, data=None, error=str(e))

async def process_augmenta(
    config_path: str | Path,
    cache_enabled: bool = True,
    process_id: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
    auto_resume: bool = True
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Process data using the Augmenta pipeline.
    
    Args:
        config_path: Path to configuration file
        cache_enabled: Whether to enable caching
        process_id: Optional process ID for resuming
        progress_callback: Optional callback for progress updates
        auto_resume: Whether to automatically resume unfinished processes
        
    Returns:
        Tuple of processed DataFrame and process ID (if caching enabled)
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")
    
    # Load and validate configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            config_data["config_path"] = str(config_path)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML config: {e}")
    
    validate_config(config_data)
    
    # Setup credentials and load data
    credentials_manager = CredentialsManager()
    credentials = credentials_manager.get_credentials(config_data)
    
    try:
        df = pd.read_csv(config_data["input_csv"])
        if config_data["query_col"] not in df.columns:
            raise ConfigurationError(
                f"Query column '{config_data['query_col']}' not found in CSV"
            )
    except Exception as e:
        raise ConfigurationError(f"Error loading input CSV: {e}")

    # Handle caching setup
    cache_manager, process_id, cached_results = setup_caching(
        config_data,
        cache_enabled,
        len(df),
        process_id
    )
    
    if cache_enabled:
        df = apply_cached_results(df, process_id, cache_manager)

    # Process remaining rows
    rows_to_process = [
        {'index': index, 'data': row}
        for index, row in df.iterrows()
        if not cache_enabled or index not in cached_results
    ]


    processed = 0
    def update_progress(query: str) -> None:
        nonlocal processed
        processed += 1
        if progress_callback:
            progress_callback(processed, len(rows_to_process), query)

    # Process rows concurrently
    tasks = [
        process_row(
            row_data=row,
            config=config_data,
            credentials=credentials,
            cache_manager=cache_manager,
            process_id=process_id,
            progress_callback=update_progress
        ) for row in rows_to_process
    ]
    
    results = await asyncio.gather(*tasks)

    # Update DataFrame with results
    for result in results:
        if result.data:
            for key, value in result.data.items():
                df.at[result.index, key] = value
        elif result.error:
            logger.error(f"Row {result.index} failed: {result.error}")

    # Save results if output path specified
    if output_csv := config_data.get("output_csv"):
        df.to_csv(output_csv, index=False)
    
    return df, process_id if cache_enabled else None