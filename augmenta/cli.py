import click
import os
import asyncio
import yaml
import logging
from augmenta.core.augmenta import process_augmenta
from augmenta.core.cache import CacheManager
from augmenta.core.utils import get_config_hash
from augmenta.core.config.credentials import CredentialsManager

# Configure root logger to WARNING level
logging.getLogger().setLevel(logging.WARNING)

# Disable INFO logs from specific noisy libraries
# logging.getLogger('httpx').setLevel(logging.WARNING)
# logging.getLogger('LiteLLM').setLevel(logging.WARNING)
logging.getLogger('trafilatura').setLevel(logging.CRITICAL)

def prompt_for_api_keys(config_data):
    """
    Prompt user for search engine API keys if they're not set
    
    Args:
        config_data: The loaded configuration dictionary
    """
    credentials_manager = CredentialsManager()
    required_keys = credentials_manager.get_required_keys(config_data)
    keys = {key: os.getenv(key) for key in required_keys}
    
    for key_name, value in keys.items():
        if value is None:
            value = click.prompt(
                f"Please enter your {key_name}", 
                hide_input=True,
                type=str
            )
            os.environ[key_name] = value
    
    return keys

@click.command()
@click.argument('config_path', type=click.Path(exists=True), required=False)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--interactive', '-i', is_flag=True, 
              help='Enable interactive mode for entering API keys')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--resume', help='Resume a previous process using its ID')
@click.option('--clean-cache', is_flag=True, help='Clean up old cache entries')
@click.option('--no-auto-resume', is_flag=True, help='Disable automatic process resumption')
def main(**kwargs):
    """
    Augmenta CLI tool for processing data using LLMs.
    
    CONFIG_PATH: Path to the YAML configuration file (required unless using --clean-cache)
    """
    config_path = kwargs.get('config_path')
    verbose = kwargs.get('verbose', False)
    interactive = kwargs.get('interactive', False)
    no_cache = kwargs.get('no_cache', False)
    resume = kwargs.get('resume')
    clean_cache = kwargs.get('clean_cache', False)
    no_auto_resume = kwargs.get('no_auto_resume', False)

    try:
        if clean_cache:
            cache_manager = CacheManager()
            cache_manager.cleanup_old_processes()
            click.echo("Cache cleaned successfully!")
            return

        if not config_path:
            raise click.UsageError("Config path is required unless using --clean-cache")

        # Load config first to determine required API keys
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if interactive:
            prompt_for_api_keys(config_data)

        if verbose:
            click.echo(f"Processing config file: {config_path}")

        # Check for unfinished process if not explicitly resuming
        if not resume and not no_cache and not no_auto_resume:
            cache_manager = CacheManager()
            config_hash = get_config_hash(config_data)
            unfinished_process = cache_manager.find_unfinished_process(config_hash)
            
            if unfinished_process:
                summary = cache_manager.get_process_summary(unfinished_process)
                click.echo(summary)
                if click.confirm("Would you like to resume this process?"):
                    resume = unfinished_process.process_id

        current_query = ""
        with click.progressbar(
            length=100,
            label='Processing',
            show_pos=True,
            item_show_func=lambda _: current_query if current_query else None
        ) as bar:
            def progress_callback(current: int, total: int, query: str):
                nonlocal current_query
                current_query = f"Processed query: {query}"
                bar.update(round(current / total * 100 - bar.pos, 1))

            # Run the async process
            _, process_id = asyncio.run(process_augmenta(
                config_path,
                cache_enabled=not no_cache,
                process_id=resume,
                progress_callback=progress_callback,
                auto_resume=not no_auto_resume
            ))

        if verbose:
            click.echo("\nProcessing completed successfully!")
            if process_id:
                click.echo(f"Process ID: {process_id}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()