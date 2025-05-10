"""Manages API credentials and authentication for various services."""

import os
from typing import Dict, Set, List, Any
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import logging

class CredentialsManager:
    """Manages API credentials and keys for various services."""
    
    def __init__(self) -> None:
        """Initialize the credentials manager."""
        # Try to load from current directory first, then search upwards
        env_path = Path(os.getcwd()) / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logging.info(f"Loaded .env from: {env_path}")
        else:
            # Try to find any .env file in parent directories
            dotenv_path = find_dotenv()
            if dotenv_path:
                load_dotenv(dotenv_path)
                logging.info(f"Loaded .env from: {dotenv_path}")
            else:
                logging.warning(f"No .env file found in {env_path.parent} or parent directories")

    def get_credentials(self, required_keys: Set[str]) -> Dict[str, str]:
        """Get and validate credentials from environment or config.
        
        Args:
            required_keys: Set of required credential key names
            
        Returns:
            Dictionary of credential key-value pairs
            
        Raises:
            ValueError: If any required credentials are missing
        """
        credentials = {
            key: os.getenv(key)
            for key in required_keys
        }
        
        missing_keys = [key for key, value in credentials.items() if not value]
        
        if missing_keys:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing_keys)}. "
                "Please create a .env file in your project root with the required keys. "
                "For example: BRAVE_API_KEY=your_key, OPENAI_API_KEY=your_key, etc."
            )
            
        return {k: v for k, v in credentials.items() if v}
        
    def get_required_keys(self, config_data: Dict[str, Any]) -> Set[str]:
        """Determine which API keys are required based on the configuration.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            Set of required API key names
        """
        required_keys = set()
        
        # Check model provider
        model_provider = config_data.get("model", {}).get("provider", "").lower()
        if model_provider == "openai":
            required_keys.add("OPENAI_API_KEY")
        elif model_provider == "anthropic":
            required_keys.add("ANTHROPIC_API_KEY")
            
        # Check search engine
        search_engine = config_data.get("search", {}).get("engine", "").lower()
        if search_engine == "brave":
            required_keys.add("BRAVE_API_KEY")
        elif search_engine == "brightdata":
            required_keys.add("BRIGHTDATA_API_KEY")
            required_keys.add("BRIGHTDATA_ZONE")
        elif search_engine == "google":
            required_keys.add("GOOGLE_API_KEY")
            required_keys.add("GOOGLE_SEARCH_ENGINE_ID")
        elif search_engine == "oxylabs":
            required_keys.add("OXYLABS_USERNAME")
            required_keys.add("OXYLABS_PASSWORD")
            
        return required_keys
