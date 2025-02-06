import os
from typing import Dict, Set
from dotenv import load_dotenv

class CredentialsManager:
    """Manages API credentials and keys"""
    
    def __init__(self):
        load_dotenv()
        
    def get_required_keys(self, config: dict) -> Set[str]:
        """Determine required API keys based on configuration"""
        required_keys = set()
        
        # Search engine requirements
        search_engine = config.get("search", {}).get("engine", "").lower()
        if search_engine == "brave":
            required_keys.add("BRAVE_API_KEY")
        elif search_engine in ["oxylabs_google", "oxylabs_bing"]:
            required_keys.add("OXYLABS_USERNAME")
            required_keys.add("OXYLABS_PASSWORD")
            
        # LLM provider requirements
        model = config.get("model", "").lower()
        if model.startswith("openai"):
            required_keys.add("OPENAI_API_KEY")
            
        return required_keys
        
    def get_credentials(self, config: dict) -> Dict[str, str]:
        """Get and validate credentials from environment or config"""
        required_keys = self.get_required_keys(config)
        
        credentials = {
            key: os.getenv(key) or config.get("api_keys", {}).get(key)
            for key in required_keys
        }
        
        missing_keys = [k for k, v in credentials.items() if not v]
        if missing_keys:
            raise ValueError(
                f"Missing required API keys: {missing_keys}. "
                "Provide via environment variables or config file."
            )
            
        return credentials