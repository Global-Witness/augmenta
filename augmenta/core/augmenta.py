import yaml
import json
import logging
import asyncio
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass

from augmenta.core.search import search_web
from augmenta.core.extractors import extract_urls
from augmenta.core.prompt import prepare_docs
from augmenta.core.llm import make_request_llm, InstructorHandler
from augmenta.core.cache import CacheManager
from augmenta.core.config.credentials import CredentialsManager
from augmenta.core.utils import get_config_hash

# Configure module logger
logger = logging.getLogger(__name__)

# Type aliases
ConfigDict = Dict[str, Any]
RowData = Dict[str, Any]

# Constants
REQUIRED_CONFIG_FIELDS = {"input_csv", "query_col", "prompt", "model", "search"}

@dataclass
class ProcessingResult:
    """Container for processing results"""
    index: int
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None

class AugmentaError(Exception):
    """Base exception for Augmenta-related errors"""
    pass

class ConfigurationError(AugmentaError):
    """Configuration-related errors"""
    pass

def validate_config(config: ConfigDict) -> None:
    """Validate configuration data"""
    missing_fields = REQUIRED_CONFIG_FIELDS - set(config.keys())
    if missing_fields:
        raise ConfigurationError(f"Missing required config fields: {missing_fields}")
    
    if not isinstance(config.get("search", {}), dict):
        raise ConfigurationError("'search' must be a dictionary")
    if not isinstance(config.get("prompt", {}), dict):
        raise ConfigurationError("'prompt' must be a dictionary")

async def process_row(
    row_data: RowData,
    config: ConfigDict,
    credentials: Dict[str, str],
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> ProcessingResult:
    """Process a single data row asynchronously"""
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
        urls_docs = prepare_docs(urls_text)
        
        # Prepare prompt by replacing all {{column}} placeholders with values from the row
        prompt_user = config["prompt"]["user"]
        for column in row.index:
            placeholder = f"{{{{{column}}}}}"
            if placeholder in prompt_user:
                prompt_user = prompt_user.replace(placeholder, str(row[column]))
        
        prompt_user = f'{urls_docs}\n\n{prompt_user}'
        
        # # Add structure format to prompt if structure is defined
        # if "structure" in config:
        #     prompt_user = append_structure(prompt_user, config["structure"])
        
        # Create structure class using InstructorHandler
        Structure = InstructorHandler.create_structure_class(config["config_path"])
        
        # Get LLM response
        response = await make_request_llm(
            prompt_system=config["prompt"]["system"],
            prompt_user=prompt_user,
            model=config["model"]["name"],
            response_format=Structure,
            rate_limit=config["model"].get("rate_limit")
        )
        
        # Response is already a dict, no need to parse JSON
        response_dict = response
        
        # Cache if enabled
        if cache_manager and process_id:
            cache_manager.cache_result(
                process_id=process_id,
                row_index=index,
                query=query,
                result=json.dumps(response_dict)  # Convert to JSON for caching
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
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    auto_resume: bool = True
) -> Tuple[pd.DataFrame, Optional[str]]:
    """Process data using the Augmenta pipeline"""
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
    
    # Setup credentials
    credentials_manager = CredentialsManager()
    credentials = credentials_manager.get_credentials(config_data)
    
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
        
        if not process_id and auto_resume:
            unfinished_process = cache_manager.find_unfinished_process(config_hash)
            if unfinished_process:
                process_id = unfinished_process.process_id
                
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

    # Save results
    if output_csv := config_data.get("output_csv"):
        df.to_csv(output_csv, index=False)
    
    return df, process_id if cache_enabled else None