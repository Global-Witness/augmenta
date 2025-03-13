"""Core processing logic for the Augmenta package."""

import yaml
import json
import asyncio
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable, Set
from dataclasses import dataclass

from augmenta.core.search import _search_web_impl
from augmenta.core.extractors import _visit_webpages_impl
from augmenta.core.prompt import format_docs, format_examples
from augmenta.core.llm.base import BaseAgent, make_request_llm
from augmenta.core.llm.agent import WebResearchAgent
from augmenta.core.cache import CacheManager
from augmenta.core.cache.process import handle_process_resumption, setup_caching, apply_cached_results
from augmenta.core.config.credentials import CredentialsManager
import logfire

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

def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration data structure and required fields."""
    missing_fields = REQUIRED_CONFIG_FIELDS - set(config.keys())
    if missing_fields:
        raise AugmentaError(f"Missing required config fields: {missing_fields}")
    
    if not isinstance(config.get("search"), dict):
        raise AugmentaError("'search' must be a dictionary")
    if not isinstance(config.get("prompt"), dict):
        raise AugmentaError("'prompt' must be a dictionary")

def get_config_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract commonly used config values."""
    return {
        "model_id": f"{config['model']['provider']}:{config['model']['name']}",
        "temperature": config.get("model", {}).get("temperature", 0.0),
        "max_tokens": config.get("model", {}).get("max_tokens"),
        "rate_limit": config.get("model", {}).get("rate_limit"),
        "search_engine": config["search"]["engine"],
        "search_results": config["search"]["results"]
    }

async def process_row(
    row_data: Dict[str, Any],
    config: Dict[str, Any],
    credentials: Dict[str, str],
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    verbose: bool = False
) -> ProcessingResult:
    """Process a single data row asynchronously."""
    try:
        index = row_data['index']
        row = row_data['data']
        query = row[config['query_col']]
        
        # Get common config values
        config_values = get_config_values(config)
        model_settings = {
            "temperature": config_values["temperature"],
            "max_tokens": config_values["max_tokens"],
            "rate_limit": config_values["rate_limit"]
        }
        
        # Check if agent mode is enabled
        agent_config = config.get("agent", {})
        use_agent = agent_config.get("enabled", False)
        
        if use_agent:
            # Use WebResearchAgent for autonomous operation
            agent = WebResearchAgent(
                model=config_values["model_id"],
                verbose=verbose,
                search_config=config["search"],
                **model_settings
            )
            
            # Format prompt with row data
            prompt_user = config["prompt"]["user"]
            for column, value in row.items():
                prompt_user = prompt_user.replace(f"{{{{{column}}}}}", str(value))
                
            # Add examples if configured
            if examples_yaml := config.get("examples"):
                if examples_text := format_examples(examples_yaml):
                    prompt_user = f'{prompt_user}\n\n{examples_text}'
            
            Structure = BaseAgent.create_structure_class(config["config_path"])
            # Let the agent handle search and extraction
            response = await agent.run(prompt_user, response_format=Structure)
            
        else:
            # Use traditional approach with base agent functionality
            search_results = await _search_web_impl(
                query=query,
                results=config_values["search_results"],
                engine=config_values["search_engine"],
                rate_limit=config_values["rate_limit"],
                credentials=credentials,
                search_config=config["search"]
            )
            
            urls = [result['url'] for result in search_results]
            
            # Get extraction config options if provided
            extraction_config = config.get("extraction", {})
            raw_results = await _visit_webpages_impl(
                urls=urls,
                max_workers=extraction_config.get("max_workers", 10),
                timeout=extraction_config.get("timeout", 30)
            )
            
            # Filter valid URLs and create sources summary
            valid_urls = [(url, content) for url, content in raw_results if content and content.strip()]
            sources_summary = [url for url, _ in valid_urls]
            
            prompt_user = config["prompt"]["user"]
            
            for column, value in row.items():
                prompt_user = prompt_user.replace(f"{{{{{column}}}}}", str(value))
            
            if examples_yaml := config.get("examples"):
                if examples_text := format_examples(examples_yaml):
                    prompt_user = f'{prompt_user}\n\n{examples_text}'
            
            prompt_user = f'{prompt_user}\n\n## Documents\n\n{format_docs(valid_urls)}'

            Structure = BaseAgent.create_structure_class(config["config_path"])
            response = await make_request_llm(
                prompt_system=config["prompt"]["system"],
                prompt_user=prompt_user,
                model=config_values["model_id"],
                response_format=Structure,
                verbose=verbose,
                **model_settings
            )
            
            # Add sources summary to response if it's a dict
            if isinstance(response, dict):
                response['augmenta_sources'] = "\n".join(sources_summary)
        
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
        logfire.error(f"Error processing row {index}: {str(e)}", row_index=index, error=str(e))
        return ProcessingResult(index=index, data=None, error=str(e))

async def process_augmenta(
    config_path: str | Path,
    cache_enabled: bool = True,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    auto_resume: bool = True,
    verbose: bool = False
) -> Tuple[pd.DataFrame, Optional[str]]:
    """Process data using the Augmenta pipeline."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise AugmentaError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
        config_data["config_path"] = str(config_path)
    
    validate_config(config_data)
    
    # Extract common config values and get credentials
    config_values = get_config_values(config_data)
    credentials_manager = CredentialsManager()
    try:
        from augmenta.core.search.providers import PROVIDERS
        required_credentials = PROVIDERS[config_values["search_engine"]].required_credentials
        credentials = credentials_manager.get_credentials(required_credentials)
    except KeyError as e:
        raise AugmentaError(f"Unsupported search engine: {config_values['search_engine']}")
    except ValueError as e:
        raise AugmentaError(f"Credentials error: {str(e)}")
    
    df = pd.read_csv(config_data["input_csv"])
    if config_data["query_col"] not in df.columns:
        raise AugmentaError(f"Query column '{config_data['query_col']}' not found in CSV")

    process_id = handle_process_resumption(
        config_data=config_data,
        config_path=config_path,
        csv_path=config_data["input_csv"],
        no_cache=not cache_enabled,
        resume=process_id,
        no_auto_resume=not auto_resume
    )

    cache_manager, process_id, cached_results = setup_caching(
        config_data=config_data,
        csv_path=config_data["input_csv"],
        cache_enabled=cache_enabled,
        df_length=len(df),
        process_id=process_id
    )
    
    if cache_enabled:
        df = apply_cached_results(df, process_id, cache_manager)

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
    # Create a semaphore to limit concurrent tasks
    semaphore = asyncio.Semaphore(5)

    async def process_with_limit(row):
        async with semaphore:
            return await process_row(
                row_data=row,
                config=config_data,
                credentials=credentials,
                cache_manager=cache_manager,
                process_id=process_id,
                progress_callback=update_progress,
                verbose=verbose
            )

    tasks = [process_with_limit(row) for row in rows_to_process]
    results = await asyncio.gather(*tasks)

    for result in results:
        if result.data:
            for key, value in result.data.items():
                df.at[result.index, key] = value

    if output_csv := config_data.get("output_csv"):
        df.to_csv(output_csv, index=False)
        
    if cache_enabled and cache_manager and process_id:
        cache_manager.mark_process_completed(process_id)
        
    return df, process_id if cache_enabled else None