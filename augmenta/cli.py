"""Command-line interface for the Augmenta tool."""

import click
import os
import asyncio
import yaml
from typing import Dict, Any, Optional
from colorama import Fore, Style, init

from augmenta.core.augmenta import process_augmenta
from augmenta.core.cache.process import handle_cache_cleanup
from augmenta.core.config.credentials import CredentialsManager
import logfire

# Initialize colorama
init()

class ConsolePrinter:
    def __init__(self):
        self.current_file = None
        
    def print_banner(self):
        banner = r"""
    ___                                    __       
   /   | __  ______ _____ ___  ___  ____  / /_____ _
  / /| |/ / / / __ `/ __ `__ \/ _ \/ __ \/ __/ __ `/
 / ___ / /_/ / /_/ / / / / / /  __/ / / / /_/ /_/ / 
/_/  |_\__,_/\__, /_/ /_/ /_/\___/_/ /_/\__/\__,_/  
            /____/                                  """
        
        print(f"{Fore.CYAN}{Style.BRIGHT}{banner}{Style.RESET_ALL}")
    
    def update_progress(self, current: int, total: int, query: str):
        self.current_file = query
        # Move cursor up one line and clear the line
        print(f"\033[A\033[K{Fore.CYAN}Processing: {Style.BRIGHT}{query}{Style.RESET_ALL}")

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
    """Augmenta CLI tool for processing data using LLMs."""
    try:
        console = ConsolePrinter()
        console.print_banner()
        
        # Configure logging based on verbosity
        if verbose:
            logfire.configure(scrubbing=False)
            logfire.instrument_httpx(capture_all=True)

        if clean_cache:
            handle_cache_cleanup()
            return

        if not config_path:
            raise click.UsageError("Config path is required unless using --clean-cache")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        if interactive:
            get_api_keys(config_data, interactive=True)

        if verbose:
            click.echo(f"Processing config file: {config_path}")

        # Print an initial empty line for the processing status
        print(f"{Fore.CYAN}Processing: Starting...{Style.RESET_ALL}")
            
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
                progress.update(round((current / total * 100) - progress.pos))
                console.update_progress(current, total, query)
                
            _, process_id = asyncio.run(process_augmenta(
                config_path,
                cache_enabled=not no_cache,
                process_id=resume,
                progress_callback=update_progress,
                auto_resume=not no_auto_resume
            ))

        if verbose and process_id:
            click.echo(f"\n{Fore.GREEN}Process completed successfully! ID: {Style.BRIGHT}{process_id}{Style.RESET_ALL}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", err=True)
        raise click.Abort()