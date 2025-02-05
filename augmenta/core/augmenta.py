import yaml
import json
import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, Callable, List
import pandas as pd
import hashlib
import asyncio

from augmenta.core.search import search_web
from augmenta.core.extract_text import extract_urls
from augmenta.core.prompt import prepare_docs
from augmenta.core.llm import create_structure_class, make_request_llm
from augmenta.core.cache import CacheManager

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_API_KEYS = {"OPENAI_API_KEY", "BRAVE_API_KEY"}
REQUIRED_CONFIG_FIELDS = {"input_csv", "query_col", "prompt", "model", "search"}
DEFAULT_MAX_CONCURRENT = 3

class AugmentaError(Exception):
    """Base exception for Augmenta-related errors"""
    pass

class ConfigurationError(AugmentaError):
    """Raised when there are configuration-related errors"""
    pass

@dataclass
class ProcessingResult:
    """Container for processing results"""
    index: int
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None

def validate_config(config_data: Dict[str, Any]) -> None:
    """Validate configuration data"""
    missing_fields = REQUIRED_CONFIG_FIELDS - set(config_data.keys())
    if missing_fields:
        raise ConfigurationError(f"Missing required config fields: {missing_fields}")

def get_api_keys(config_data: Dict[str, Any]) -> Dict[str, str]:
    """Get and validate API keys from environment or config"""
    keys = {
        key: os.getenv(key) or config_data.get("api_keys", {}).get(key)
        for key in REQUIRED_API_KEYS
    }
    
    missing_keys = [k for k, v in keys.items() if not v]
    if missing_keys:
        raise ConfigurationError(
            f"Missing required API keys: {missing_keys}. "
            "Provide via environment variables or config file."
        )
    
    return keys

def get_config_hash(config_data: Dict[str, Any]) -> str:
    """Generate deterministic hash of config data"""
    return hashlib.sha256(
        json.dumps(config_data, sort_keys=True).encode()
    ).hexdigest()

async def process_row(
    row_data: Dict[str, Any],
    config_data: Dict[str, Any],
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> ProcessingResult:
    """Process a single data row asynchronously"""
    index = row_data['index']
    row = row_data['data']
    
    try:
        query = row[config_data['query_col']]
        
        # Fetch and process search results
        urls = await search_web(
            query=query,
            results=config_data["search"]["results"],
            engine=config_data["search"]["engine"]
        )
        
        urls_text = await extract_urls(urls)
        urls_docs = prepare_docs(urls_text)
        
        # Prepare prompt and structure
        prompt_user = (
            f'{urls_docs}\n\n'
            f'{config_data["prompt"]["user"].replace("{{research_keyword}}", query)}'
        )
        
        Structure = create_structure_class(config_data["config_path"])
        
        # Get LLM response
        response = await make_request_llm(
            prompt_system=config_data["prompt"]["system"],
            prompt_user=prompt_user,
            model=config_data["model"],
            response_format=Structure
        )
        
        response_dict = json.loads(response)
        
        # Cache result if enabled
        if cache_manager and process_id:
            cache_manager.cache_result(
                process_id=process_id,
                row_index=index,
                query=query,
                result=json.dumps(response_dict)
            )
        
        if progress_callback:
            progress_callback(query)
            
        return ProcessingResult(index=index, data=response_dict)
        
    except Exception as e:
        logger.error(f"Error processing row {index}: {str(e)}", exc_info=True)
        return ProcessingResult(index=index, data=None, error=str(e))

async def process_augmenta(
    config_path: str | Path,
    cache_enabled: bool = True,
    process_id: Optional[str] = None,
    max_concurrent: int = DEFAULT_MAX_CONCURRENT,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Process data using the Augmenta pipeline.
    
    Args:
        config_path: Path to YAML config file
        cache_enabled: Whether to enable result caching
        process_id: Optional ID for resuming previous run
        max_concurrent: Maximum concurrent tasks
        progress_callback: Optional progress reporting callback
    
    Returns:
        Processed DataFrame and process ID (if caching enabled)
    
    Raises:
        ConfigurationError: If configuration is invalid
        AugmentaError: For other processing errors
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")
    
    # Load and validate configuration
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            config_data["config_path"] = str(config_path)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML config: {e}")
    
    validate_config(config_data)
    
    # Setup API keys
    api_keys = get_api_keys(config_data)
    os.environ.update(api_keys)
    
    # Load input data
    try:
        df = pd.read_csv(config_data["input_csv"])
        if config_data["query_col"] not in df.columns:
            raise ConfigurationError(
                f"Query column '{config_data['query_col']}' not found in CSV"
            )
    except Exception as e:
        raise ConfigurationError(f"Error loading input CSV: {e}")

    # Setup caching
    cache_manager = None
    cached_results = {}
    
    if cache_enabled:
        cache_manager = CacheManager()
        config_hash = get_config_hash(config_data)
        
        if not process_id:
            process_id = cache_manager.start_process(config_hash, len(df))
        
        cached_results = cache_manager.get_cached_results(process_id)
        
        # Apply cached results
        for row_index, result in cached_results.items():
            for key, value in result.items():
                df.at[row_index, key] = value

    # Prepare rows for processing
    rows_to_process = [
        {'index': index, 'data': row}
        for index, row in df.iterrows()
        if not cache_enabled or index not in cached_results
    ]

    processed = 0
    def update_progress(query: str):
        nonlocal processed
        processed += 1
        if progress_callback:
            progress_callback(processed, len(rows_to_process), query)

    # Process in batches
    results: List[ProcessingResult] = []
    for i in range(0, len(rows_to_process), max_concurrent):
        batch = rows_to_process[i:i + max_concurrent]
        batch_tasks = [
            process_row(
                row_data=row,
                config_data=config_data,
                cache_manager=cache_manager,
                process_id=process_id,
                progress_callback=update_progress
            ) for row in batch
        ]
        
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)

    # Update DataFrame with results
    for result in results:
        if result.data:
            for key, value in result.data.items():
                df.at[result.index, key] = value
        elif result.error:
            logger.error(f"Row {result.index} failed: {result.error}")

    # Save results
    if output_csv := config_data.get("output_csv"):
        df.to_csv(output_csv, index=False)
    
    return df, process_id if cache_enabled else None