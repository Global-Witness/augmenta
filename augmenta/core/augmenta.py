import yaml
import json
import os
import pandas as pd
import hashlib
from typing import Optional, Tuple, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from augmenta.core.search import search_web
from augmenta.core.extract_text import extract_urls
from augmenta.core.prompt import prepare_docs
from augmenta.core.llm import create_structure_class, make_request_llm
from augmenta.core.cache import CacheManager

def get_api_keys(config_data):
    """
    Get API keys using the following priority:
    1. Environment variables
    2. Config file
    """
    keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY"),
    }
    
    # If keys exist in config, use them as fallback
    if "api_keys" in config_data:
        for key_name, value in keys.items():
            if value is None:
                keys[key_name] = config_data["api_keys"].get(key_name)
    
    return keys

def validate_api_keys(keys):
    """Validate that required API keys are present"""
    missing_keys = [k for k, v in keys.items() if v is None]
    if missing_keys:
        raise ValueError(
            f"Missing required API keys: {', '.join(missing_keys)}. "
            "Please provide them either through environment variables "
            "or in the config file under the 'api_keys' section."
        )

def get_config_hash(config_data: dict) -> str:
    """
    Generate a hash of the config data to uniquely identify the configuration.
    
    Args:
        config_data (dict): The configuration dictionary
        
    Returns:
        str: A hex digest of the configuration hash
    """
    return hashlib.sha256(
        json.dumps(config_data, sort_keys=True).encode()
    ).hexdigest()

def process_row(
    row_data: Dict[str, Any],
    config_data: dict,
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None,
    cache_lock: Optional[Lock] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Tuple[int, Optional[Dict[str, Any]]]:
    """
    Process a single row of data.
    
    Args:
        # ... existing args ...
        progress_callback: Optional callback function to report progress
    """
    index = row_data['index']
    row = row_data['data']
    
    try:
        query = row[config_data['query_col']]
        if progress_callback:
            progress_callback(query)
        prompt_user = config_data["prompt"]["user"].replace("{{research_keyword}}", query)
        
        # Get search results
        urls = search_web(
            query, 
            results=config_data["search"]["results"], 
            engine=config_data["search"]["engine"]
        )
        
        # Extract text from URLs
        urls_text = extract_urls(urls)
        
        # Prepare documents for processing
        urls_docs = prepare_docs(urls_text)
        
        prompt_user = f'{urls_docs}\n\n{prompt_user}'
        
        # Create a Pydantic class for the structured output
        Structure = create_structure_class(config_data["config_path"])
        
        # Make the LLM request
        response = make_request_llm(
            prompt_system=config_data["prompt"]["system"], 
            prompt_user=prompt_user, 
            model=config_data["model"],
            response_format=Structure
        )
        
        # Convert JSON string to dictionary
        response_dict = json.loads(response)
        
        # Cache the result if enabled
        if cache_manager and process_id:
            with cache_lock:
                cache_manager.cache_result(
                    process_id,
                    index,
                    query,
                    json.dumps(response_dict)
                )
        
        return index, response_dict
        
    except Exception as e:
        print(f"Error processing row {index}: {e}")
        return index, None

def process_augmenta(
    config_path: str, 
    cache_enabled: bool = True, 
    process_id: Optional[str] = None,
    max_workers: int = 1,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Args:
        config_path (str): Path to the YAML config file
        cache_enabled (bool): Whether to enable caching
        process_id (str, optional): Process ID for resuming a previous run
        max_workers (int): Maximum number of worker threads
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple[pd.DataFrame, Optional[str]]: The processed DataFrame and process ID (if caching enabled)
    """
    # Import config values
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
        config_data["config_path"] = config_path  # Add config path to config data
        
    # Get and validate API keys
    api_keys = get_api_keys(config_data)
    validate_api_keys(api_keys)
    
    # Set API keys in environment for library usage
    for key_name, value in api_keys.items():
        os.environ[key_name] = value
    
    input_csv = config_data.get("input_csv")
    output_csv = config_data.get("output_csv")
    query_col = config_data.get("query_col")
    max_workers = config_data.get("max_workers", 1)
    
    if not input_csv or not query_col:
        raise ValueError("input_csv and query_col must be specified in the config file")

    # Read the CSV file
    df = pd.read_csv(input_csv)

    if query_col not in df.columns:
        raise ValueError(f"Column '{query_col}' not found in the CSV file")

    # Initialize cache and get cached results if enabled
    cache_manager = None
    cached_results = {}
    cache_lock = Lock()
    
    if cache_enabled:
        cache_manager = CacheManager()
        config_hash = get_config_hash(config_data)
        
        if process_id is None:
            # Start new process
            process_id = cache_manager.start_process(config_hash, len(df))
        
        # Get cached results
        cached_results = cache_manager.get_cached_results(process_id)
        
        # Apply cached results to DataFrame
        for row_index, result in cached_results.items():
            for key, value in result.items():
                df.at[row_index, key] = value

    # Prepare rows for processing
    rows_to_process = []
    for index, row in df.iterrows():
        if not cache_enabled or index not in cached_results:
            rows_to_process.append({
                'index': index,
                'data': row
            })


    total_rows = len(rows_to_process)
    processed_rows = 0

    def update_progress(query: str):
        nonlocal processed_rows
        processed_rows += 1
        if progress_callback:
            progress_callback(processed_rows, total_rows, query)

    # Process rows in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_row = {
            executor.submit(
                process_row,
                row_data=row,
                config_data=config_data,
                cache_manager=cache_manager,
                process_id=process_id,
                cache_lock=cache_lock,
                progress_callback=update_progress
            ): row for row in rows_to_process
        }
        
        for future in as_completed(future_to_row):
            try:
                index, result = future.result()
                if result:
                    for key, value in result.items():
                        df.at[index, key] = value
            except Exception as e:
                print(f"Error processing future: {e}")

    # Save the results back to a CSV
    if output_csv:
        df.to_csv(output_csv, index=False)
    
    return df, process_id if cache_enabled else None