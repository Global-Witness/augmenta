"""Core processing logic for the Augmenta package."""

import json
import asyncio
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass

from augmenta.utils.prompt_formatter import format_examples
from augmenta.agents.base import BaseAgent
from augmenta.agents.autonomous_agent import AutonomousAgent
from augmenta.agents.fixed_agent import FixedAgent
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

async def process_row(
    row_data: Dict[str, Any],
    config: Dict[str, Any],
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
        agent_settings = {
            "model": config_values["model_id"],
            "temperature": config_values["temperature"],
            "max_tokens": config_values["max_tokens"],
            "rate_limit": config_values["rate_limit"],
            "verbose": verbose,
            "system_prompt": config["prompt"]["system"]
        }
        
        # Get agent mode and initialize appropriate agent
        agent_mode = config.get("agent", "fixed")
        
        # Format prompt with row data
        prompt_user = config["prompt"]["user"]
        for column, value in row.items():
            prompt_user = prompt_user.replace(f"{{{{{column}}}}}", str(value))
            
        # Format examples and structure
        if examples_yaml := config.get("examples"):
            if examples_text := format_examples(examples_yaml):
                prompt_user = f'{prompt_user}\n\n{examples_text}'
        
        Structure = BaseAgent.create_structure_class(config["config_path"])

        # Initialize agent based on mode
        if agent_mode == "autonomous":
            agent = AutonomousAgent(**agent_settings)
        elif agent_mode == "fixed":
            agent = FixedAgent(**agent_settings)
        else:
            raise AugmentaError(f"Invalid agent mode: {agent_mode}")
        
        # Run the agent with the prepared prompt
        response = await agent.run(prompt_user, response_format=Structure)
        
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
    
    config_data = load_config(config_path)
    
    # Extract common config values
    config_values = get_config_values(config_data)
    
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