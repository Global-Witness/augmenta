"""
Command-line interface for the Augmenta tool.
"""

import click
import os
import asyncio
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from augmenta.core.augmenta import process_augmenta
from augmenta.core.cache import CacheManager
from augmenta.core.utils import get_config_hash
from augmenta.core.config.credentials import CredentialsManager

# Configure logging
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger('trafilatura').setLevel(logging.CRITICAL)

def prompt_for_api_keys(config_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Prompt user for missing API keys required by the configuration.
    
    Args:
        config_data: The loaded configuration dictionary
        
    Returns:
        Dict[str, str]: Dictionary of API key names and values
    """
    credentials_manager = CredentialsManager()
    required_keys = credentials_manager.get_required_keys(config_data)
    keys = {key: os.getenv(key) for key in required_keys}
    
    for key_name, value in keys.items():
        if not value:
            value = click.prompt(
                f"Please enter your {key_name}", 
                hide_input=True,
                type=str
            )
            os.environ[key_name] = value
    
    return keys

class ProcessContext:
    """Context manager for process progress display."""
    
    def __init__(self, length: int = 100):
        self.length = length
        self.current_query = ""
        self.progress_bar = None
        
    def __enter__(self):
        self.progress_bar = click.progressbar(
            length=self.length,
            label='Processing',
            show_pos=True,
            item_show_func=lambda _: self.current_query if self.current_query else None
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress_bar:
            self.progress_bar.finish()
            
    def update_progress(self, current: int, total: int, query: str):
        """Update progress bar with current status."""
        self.current_query = f"Processing: {query}"
        if self.progress_bar:
            self.progress_bar.update(round(current / total * 100 - self.progress_bar.pos, 1))

@click.command()
@click.argument('config_path', type=click.Path(exists=True), required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--interactive', '-i', is_flag=True, help='Enable interactive mode for API keys')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--resume', help='Resume a previous process using its ID')
@click.option('--clean-cache', is_flag=True, help='Clean up old cache entries')
@click.option('--no-auto-resume', is_flag=True, help='Disable automatic process resumption')
def main(
    config_path: Optional[str],
    verbose: bool = False,
    interactive: bool = False,
    no_cache: bool = False,
    resume: Optional[str] = None,
    clean_cache: bool = False,
    no_auto_resume: bool = False
) -> None:
    """
    Augmenta CLI tool for processing data using LLMs.
    
    CONFIG_PATH: Path to the YAML configuration file (required unless using --clean-cache)
    """
    try:
        if clean_cache:
            CacheManager().cleanup_old_processes()
            click.echo("Cache cleaned successfully!")
            return

        if not config_path:
            raise click.UsageError("Config path is required unless using --clean-cache")

        config_path = Path(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        if interactive:
            prompt_for_api_keys(config_data)

        if verbose:
            click.echo(f"Processing config file: {config_path}")

        # Handle process resumption
        process_id = resume
        if not resume and not no_cache and not no_auto_resume:
            cache_manager = CacheManager()
            config_hash = get_config_hash(config_data)
            if unfinished_process := cache_manager.find_unfinished_process(config_hash):
                summary = cache_manager.get_process_summary(unfinished_process)
                click.echo(summary)
                if click.confirm("Would you like to resume this process?"):
                    process_id = unfinished_process.process_id

        # Process with progress tracking
        with ProcessContext() as ctx:
            _, final_process_id = asyncio.run(process_augmenta(
                config_path,
                cache_enabled=not no_cache,
                process_id=process_id,
                progress_callback=ctx.update_progress,
                auto_resume=not no_auto_resume
            ))

        if verbose:
            click.echo("\nProcessing completed successfully!")
            if final_process_id:
                click.echo(f"Process ID: {final_process_id}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()