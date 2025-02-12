"""Manages API credentials and authentication for various services."""

import os
from typing import Dict, Set
from dotenv import load_dotenv

class CredentialsManager:
    """Manages API credentials and keys for various services."""
    
    CREDENTIAL_REQUIREMENTS: Dict[str, Set[str]] = {
        'brave': {'BRAVE_API_KEY'},
        'oxylabs_google': {'OXYLABS_USERNAME', 'OXYLABS_PASSWORD'},
        'oxylabs_bing': {'OXYLABS_USERNAME', 'OXYLABS_PASSWORD'}
    }
    
    def __init__(self, load_env: bool = True) -> None:
        """Initialize the credentials manager.
        
        Args:
            load_env: Whether to automatically load .env file
        """
        if load_env:
            load_dotenv()
            
    def get_required_keys(self, config: Dict) -> Set[str]:
        """Get required API keys based on configuration.
        
        Args:
            config: Configuration dictionary containing service settings
            
        Returns:
            Set of required credential key names
        """
        search_engine = config.get('search', {}).get('engine', '').lower()
        return self.CREDENTIAL_REQUIREMENTS.get(search_engine, set())
        
    def get_credentials(self, config: Dict) -> Dict[str, str]:
        """Get and validate credentials from environment or config.
        
        Args:
            config: Configuration dictionary that may contain API keys
            
        Returns:
            Dictionary of credential key-value pairs
            
        Raises:
            ValueError: If any required credentials are missing
        """
        required_keys = self.get_required_keys(config)
        api_keys = config.get('api_keys', {})
        
        credentials = {
            key: os.getenv(key) or api_keys.get(key)
            for key in required_keys
        }
        
        missing_keys = [key for key, value in credentials.items() if not value]
        
        if missing_keys:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing_keys)}. "
                "Provide via environment variables or config file."
            )
            
        return {k: v for k, v in credentials.items() if v}