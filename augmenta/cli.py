"""Command-line interface for the Augmenta tool."""

import click
import os
import asyncio
import yaml
import logging
from typing import Dict, Any, Optional
from colorama import Fore, Style, init

from augmenta.core.augmenta import process_augmenta
from augmenta.core.cache.process import handle_cache_cleanup
from augmenta.core.config.credentials import CredentialsManager

# Initialize colorama
init()

class ScrapeFilter(logging.Filter):
    """Filter out common scraping-related errors unless in verbose mode."""
    
    FILTERED_MESSAGES = [
        'net::ERR_ABORTED',
        'Target page, context or browser has been closed',
        'TimeoutError',
        'Navigation timeout',
        'net::ERR_CONNECTION_TIMED_OUT',
        'net::ERR_CONNECTION_REFUSED',
        'Playwright timeout',
        'Target closed',
        'ERR_NAME_NOT_RESOLVED',
    ]
    
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.verbose = verbose
    
    def filter(self, record: logging.LogRecord) -> bool:
        if self.verbose:
            return True
        
        # Check if message contains any of the filtered phrases
        return not any(msg in str(record.msg) for msg in self.FILTERED_MESSAGES)

def configure_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.addFilter(ScrapeFilter(verbose))
    
    # Set format
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if verbose else logging.WARNING)
    
    # Remove existing handlers and add our configured one
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    loggers = [
        'trafilatura',
        'trafilatura.core',
        'augmenta.core.extractors',
        'augmenta.core.extractors.trafilatura',
        'playwright._impl._api_types',
        'playwright._impl.connection',
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO if verbose else logging.CRITICAL)
        # Prevent log propagation to avoid duplicate messages
        logger.propagate = False
        logger.handlers.clear()
        logger.addHandler(console_handler)

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
        
        # Read version from pyproject.toml
        import os
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pyproject_path = os.path.join(package_dir, 'pyproject.toml')
        
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('version'):
                    version = line.split('=')[1].strip().strip('"').strip("'")
                    break
                    
        print(f"{Fore.CYAN}{Style.BRIGHT}{banner}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}v. {version}{Style.RESET_ALL}\n")
    
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
        configure_logging(verbose)

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