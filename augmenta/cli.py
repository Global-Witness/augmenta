"""Command-line interface for the Augmenta tool."""

import click
import os
import asyncio
import yaml
from typing import Dict, Any, Optional, Tuple
from colorama import Fore, Style, init
import pandas as pd

# Configure logfire to suppress warnings unless in verbose mode
os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"

from augmenta.augmenta import process_augmenta
from augmenta.cache.process import handle_cache_cleanup
from augmenta.config.get_credentials import CredentialsManager
import logfire
import logfire

# Initialize colorama
init()

class ConsolePrinter:
    """Handles console output for Augmenta CLI."""
    
    def __init__(self):
        """Initialize the console printer."""
        self.current_file = None
        
    def print_banner(self):
        """Print the Augmenta banner."""
        banner = r"""
    ___                                    __       
   /   | __  ______ _____ ___  ___  ____  / /_____ _
  / /| |/ / / / __ `/ __ `__ \/ _ \/ __ \/ __/ __ `/
/ ___ / /_/ / /_/ / / / / / /  __/ / / / /_/ /_/ / 
/_/  |_\__,_/\__, /_/ /_/ /_/\___/_/ /_/\__/\__,_/  
            /____/                                  
"""
        
        print(f"{Fore.CYAN}{Style.BRIGHT}{banner}{Style.RESET_ALL}")
    
    def update_progress(self, current: int, total: int, row_index: str):
        """Update progress display.
        
        Args:
            current: Current number of processed items
            total: Total number of items to process
            row_index: Index of the current row being processed
        """
        # Move cursor up one line and clear the line
        print(f"\033[A\033[K{Fore.CYAN}Processing: {Style.BRIGHT}Row {row_index} of {total}{Style.RESET_ALL}")

def get_api_keys(config_data: Dict[str, Any], interactive: bool = False) -> Dict[str, str]:
    """Get required API keys from environment or user input."""
    credentials_manager = CredentialsManager()
    required_keys = credentials_manager.get_required_keys(config_data)
    keys = {key: os.getenv(key) for key in required_keys}
    
    if interactive:
        for key_name, value in keys.items():
            if not value:
                value = click.prompt(f"Enter your {key_name}", hide_input=True, type=str)
                os.environ[key_name] = value
    
    return keys

def configure_logging(config_data: Dict[str, Any], verbose: bool) -> None:
    """Configure logging based on verbosity and config.
    
    Args:
        config_data: Configuration dictionary
        verbose: Whether verbose logging is enabled
    """
    if verbose:
        # Only send to logfire if explicitly enabled in config
        send_to_logfire = config_data.get('logfire', False)
        logfire.configure(
            scrubbing=False,
            send_to_logfire='if-token-present' if not send_to_logfire else True
        )
        
        logfire.instrument_httpx(capture_all=True)
        # Uncomment if needed: logfire.instrument_pydantic()

def run_processing(
    config_path: str, 
    cache_enabled: bool, 
    process_id: Optional[str], 
    auto_resume: bool,
    console: ConsolePrinter
) -> Tuple[pd.DataFrame, Optional[str]]:
    """Run the Augmenta processing pipeline with progress tracking.
    
    Args:
        config_path: Path to configuration file
        cache_enabled: Whether caching is enabled
        process_id: Optional process ID for resuming
        auto_resume: Whether to auto-resume previous processes
        console: Console printer for output
        
    Returns:
        Tuple of (processed DataFrame, process ID if caching enabled)
    """
    with click.progressbar(
        length=100,
        label=f'{Fore.GREEN}Progress{Style.RESET_ALL}',
        fill_char='█',
        empty_char='░',
        show_percent=True,
        show_eta=True,
        item_show_func=lambda _: None
    ) as progress:
        def update_progress(current: int, total: int, query: str):
            # Update CLI progress bar
            progress.update(round((current / total * 100) - progress.pos))
            # Update console display
            console.update_progress(current, total, query)
        
        # Run the main processing function
        return asyncio.run(process_augmenta(
            config_path,
            cache_enabled=cache_enabled,
            process_id=process_id,
            progress_callback=update_progress,
            auto_resume=auto_resume
        ))

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
    """Augmenta CLI tool for processing data using LLMs.
    
    Args:
        config_path: Path to configuration file
        verbose: Whether to enable verbose output
        interactive: Whether to enable interactive mode for API keys
        no_cache: Whether to disable caching
        resume: Optional process ID to resume
        clean_cache: Whether to clean up old cache entries
        no_auto_resume: Whether to disable automatic process resumption
    """
    try:
        console = ConsolePrinter()
        console.print_banner()
        
        # Handle the clean cache option separately
        if clean_cache:
            handle_cache_cleanup()
            return
            
        # Require config path for all other operations
        if not config_path:
            raise click.UsageError("Config path is required unless using --clean-cache")

        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Configure logging
        configure_logging(config_data, verbose)
            
        # Handle API keys in interactive mode
        if interactive:
            get_api_keys(config_data, interactive=True)

        if verbose:
            click.echo(f"Processing config file: {config_path}")

        # Run the main processing
        _, process_id = run_processing(
            config_path, 
            not no_cache, 
            resume, 
            not no_auto_resume, 
            console
        )

        if verbose and process_id:
            click.echo(f"\n{Fore.GREEN}Process completed successfully! ID: {Style.BRIGHT}{process_id}{Style.RESET_ALL}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", err=True)
        raise click.Abort()