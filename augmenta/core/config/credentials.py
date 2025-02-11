"""Manages API credentials and authentication for various services."""

import os
from typing import Dict, Set, Optional
from dotenv import load_dotenv

class CredentialsManager:
    """
    Manages API credentials and keys for various services.
    
    This class handles loading credentials from environment variables or config files,
    validating required keys, and providing a centralized credential management system.
    """
    
    # Mapping of services to their required credentials
    CREDENTIAL_REQUIREMENTS = {
        'brave': {'BRAVE_API_KEY'},
        'oxylabs_google': {'OXYLABS_USERNAME', 'OXYLABS_PASSWORD'},
        'oxylabs_bing': {'OXYLABS_USERNAME', 'OXYLABS_PASSWORD'}
    }
    
    def __init__(self, load_env: bool = True):
        """
        Initialize the credentials manager.
        
        Args:
            load_env: Whether to automatically load .env file on initialization
        """
        if load_env:
            load_dotenv()
            
    def get_required_keys(self, config: Dict) -> Set[str]:
        """
        Determine required API keys based on configuration.
        
        Args:
            config: Configuration dictionary containing service settings
            
        Returns:
            Set of required credential key names
        """
        required_keys: Set[str] = set()
        
        # Get search engine from config, defaulting to empty string
        search_config = config.get('search', {})
        search_engine = search_config.get('engine', '').lower()
        
        # Add required keys based on search engine
        if search_engine in self.CREDENTIAL_REQUIREMENTS:
            required_keys.update(self.CREDENTIAL_REQUIREMENTS[search_engine])
            
        return required_keys
        
    def get_credentials(self, config: Dict) -> Dict[str, str]:
        """
        Get and validate credentials from environment or config.
        
        Args:
            config: Configuration dictionary that may contain API keys
            
        Returns:
            Dictionary of credential key-value pairs
            
        Raises:
            ValueError: If any required credentials are missing
        """
        required_keys = self.get_required_keys(config)
        api_keys = config.get('api_keys', {})
        
        credentials = {}
        missing_keys = []
        
        for key in required_keys:
            value = os.getenv(key) or api_keys.get(key)
            if value:
                credentials[key] = value
            else:
                missing_keys.append(key)
                
        if missing_keys:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing_keys)}. "
                "Provide via environment variables or config file."
            )
            
        return credentials
        
    def validate_credential(self, key: str, value: Optional[str]) -> bool:
        """
        Validate a single credential value.
        
        Args:
            key: The credential key name
            value: The credential value to validate
            
        Returns:
            True if credential is valid, False otherwise
        """
        if not value:
            return False
            
        # Add specific validation rules for different credential types
        if key == 'BRAVE_API_KEY':
            return len(value) >= 32  # Brave API keys are typically 32+ characters
        
        return True