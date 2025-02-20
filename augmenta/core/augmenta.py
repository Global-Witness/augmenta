"""Core processing logic for the Augmenta package."""

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
from augmenta.core.llm import make_request_llm, LLMClient
from augmenta.core.cache import CacheManager
from augmenta.core.cache.process import handle_process_resumption, setup_caching, apply_cached_results
from augmenta.core.config.credentials import CredentialsManager

logger = logging.getLogger(__name__)

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

async def process_row(
    row_data: Dict[str, Any],
    config: Dict[str, Any],
    credentials: Dict[str, str],
    cache_manager: Optional[CacheManager] = None,
    process_id: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> ProcessingResult:
    """Process a single data row asynchronously."""
    try:
        index = row_data['index']
        row = row_data['data']
        query = row[config['query_col']]
        
        urls = await search_web(
            query=query,
            results=config["search"]["results"],
            engine=config["search"]["engine"],
            rate_limit=config["search"].get("rate_limit"),
            credentials=credentials,
            search_config=config["search"]  # Pass the entire search config
        )
        
        # Track URL processing results
        urls_with_content = await extract_urls(urls)
        
        # Categorize URLs
        used_urls = []
        no_content_urls = []
        attempted_urls = set(urls)
        
        for url, content in urls_with_content:
            if content and content.strip():
                used_urls.append(url)
                attempted_urls.remove(url)
            elif content is not None:  # Empty string content
                no_content_urls.append(url)
                attempted_urls.remove(url)
        
        # Format the sources summary
        sources_summary = []
        if used_urls:
            sources_summary.append("Used:")
            sources_summary.extend(used_urls)
        if no_content_urls:
            if sources_summary:
                sources_summary.append("")
            sources_summary.append("No content:")
            sources_summary.extend(no_content_urls)
        if attempted_urls:
            if sources_summary:
                sources_summary.append("")
            sources_summary.append("Attempted:")
            sources_summary.extend(attempted_urls)
        
        # Filter out URLs with no content for the prompt
        valid_urls = [(url, content) for url, content in urls_with_content if content and content.strip()]
        
        prompt_user = config["prompt"]["user"]
        
        for column, value in row.items():
            prompt_user = prompt_user.replace(f"{{{{{column}}}}}", str(value))
        
        if examples_yaml := config.get("examples"):
            if examples_text := format_examples(examples_yaml):
                prompt_user = f'{prompt_user}\n\n{examples_text}'
        
        prompt_user = f'{prompt_user}\n\n## Documents\n\n{format_docs(valid_urls)}'

        Structure = LLMClient.create_structure_class(config["config_path"])
        response = await make_request_llm(
            prompt_system=config["prompt"]["system"],
            prompt_user=prompt_user,
            model=config["model"]["name"],
            response_format=Structure,
            rate_limit=config["model"].get("rate_limit"),
            max_tokens=config.get("model", {}).get("max_tokens")
        )
        
        if cache_manager and process_id:
            cache_manager.cache_result(
                process_id=process_id,
                row_index=index,
                query=query,
                result=json.dumps(response)
            )
        
        if progress_callback:
            progress_callback(query)
        
        # Add sources summary to response
        if isinstance(response, dict):
            response['augmenta_sources'] = "\n".join(sources_summary)
            
        return ProcessingResult(index=index, data=response)
        
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
    """Process data using the Augmenta pipeline."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise AugmentaError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
        config_data["config_path"] = str(config_path)
    
    validate_config(config_data)
    
    credentials_manager = CredentialsManager()
    credentials = credentials_manager.get_credentials(config_data)
    
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

    for result in results:
        if result.data:
            for key, value in result.data.items():
                df.at[result.index, key] = value

    if output_csv := config_data.get("output_csv"):
        df.to_csv(output_csv, index=False)
        
    if cache_enabled and cache_manager and process_id:
        cache_manager.mark_process_completed(process_id)
        
    return df, process_id if cache_enabled else None