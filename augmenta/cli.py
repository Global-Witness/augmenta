import click
import os
from augmenta.core.augmenta import process_augmenta
from augmenta.core.cache import CacheManager

def prompt_for_api_keys():
    """Prompt user for API keys if they're not set"""
    keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")
    }
    
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
@click.argument('config_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--interactive', '-i', is_flag=True, 
              help='Enable interactive mode for entering API keys')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--resume', help='Resume a previous process using its ID')
@click.option('--clean-cache', is_flag=True, help='Clean up old cache entries')
def main(config_path, verbose, interactive, no_cache, resume, clean_cache):
    """
    Augmenta CLI tool for processing data using LLMs.
    
    CONFIG_PATH: Path to the YAML configuration file
    """
    try:
        if interactive:
            prompt_for_api_keys()
        
        if clean_cache:
            cache_manager = CacheManager()
            cache_manager.cleanup_old_processes()
            click.echo("Cache cleaned successfully!")
            return

        if verbose:
            click.echo(f"Processing config file: {config_path}")

        current_query = ""
        with click.progressbar(
            length=100,
            label='Processing',
            show_pos=True,
            item_show_func=lambda _: current_query if current_query else None
        ) as bar:
            def progress_callback(current: int, total: int, query: str):
                nonlocal current_query
                current_query = f"Current query: {query}"
                bar.update(current / total * 100 - bar.pos)

            _, process_id = process_augmenta(
                config_path,
                cache_enabled=not no_cache,
                process_id=resume,
                progress_callback=progress_callback
            )

        if verbose:
            click.echo("\nProcessing completed successfully!")
            if process_id:
                click.echo(f"Process ID: {process_id}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()
