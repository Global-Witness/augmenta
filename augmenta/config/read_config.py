"""Configuration handling for the Augmenta package."""

import yaml
from typing import Dict, Any, Set, Union
from pathlib import Path

# Store loaded config
_config_data: Dict[str, Any] = {}

REQUIRED_CONFIG_FIELDS: Set[str] = {
    "input_csv",
    "query_col",
    "prompt",
    "model",
    "search"
}

def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration data structure and required fields."""
    missing_fields = REQUIRED_CONFIG_FIELDS - set(config.keys())
    if missing_fields:
        raise ValueError(f"Missing required config fields: {missing_fields}")
    
    if not isinstance(config.get("search"), dict):
        raise ValueError("'search' must be a dictionary")
    if not isinstance(config.get("prompt"), dict):
        raise ValueError("'prompt' must be a dictionary")

def get_config_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract commonly used config values."""
    return {
        "model_id": f"{config['model']['provider']}:{config['model']['name']}",
        "temperature": config.get("model", {}).get("temperature", 0.0),
        "max_tokens": config.get("model", {}).get("max_tokens"),
        "rate_limit": config.get("model", {}).get("rate_limit"),
        "search_engine": config["search"]["engine"],
        "search_results": config["search"]["results"]
    }

def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and validate configuration from a YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Validated configuration dictionary
    """
    global _config_data
    
    if not _config_data:
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            _config_data = yaml.safe_load(f)
            _config_data["config_path"] = str(config_path)
            
        validate_config(_config_data)
    
    return _config_data

def get_config() -> Dict[str, Any]:
    """Get the current configuration.
    
    Returns:
        Currently loaded configuration dictionary
    
    Raises:
        RuntimeError: If configuration hasn't been loaded yet
    """
    if not _config_data:
        raise RuntimeError("Configuration not loaded. Call load_config first.")
    return _config_data