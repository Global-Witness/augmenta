"""Manages API credentials and authentication for various services."""

import os
from typing import Dict, Set, Optional
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import logging

class CredentialsManager:
    """Manages API credentials and keys for various services."""
    
    def __init__(self) -> None:
        """Initialize the credentials manager."""
        env_path = Path(os.getcwd()) / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logging.info(f"Loaded .env from: {env_path}")
        else:
            logging.warning(f"No .env file found in {env_path.parent}")

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
