"""Configuration handling for the Augmenta package."""

import yaml
from typing import Dict, Any, Set, Union
from pathlib import Path

# Store loaded config
_config_data: Dict[str, Any] = {}

REQUIRED_CONFIG_FIELDS: Set[str] = {
    "input_csv",
    "prompt",
    "model",
    "search"
}

def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration data structure and required fields.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid or missing required fields
    """
    # Check for required top-level fields
    missing_fields = REQUIRED_CONFIG_FIELDS - set(config.keys())
    if missing_fields:
        raise ValueError(f"Missing required config fields: {', '.join(missing_fields)}")
    
    # Validate search configuration
    if not isinstance(config.get("search"), dict):
        raise ValueError("'search' must be a dictionary with 'engine' and 'results' fields")
    
    search_config = config.get("search", {})
    if "engine" not in search_config:
        raise ValueError("'search' configuration must include 'engine' field")
    
    # Validate prompt configuration  
    if not isinstance(config.get("prompt"), dict):
        raise ValueError("'prompt' must be a dictionary with 'system' and 'user' fields")
        
    prompt_config = config.get("prompt", {})
    if "system" not in prompt_config or "user" not in prompt_config:
        raise ValueError("'prompt' configuration must include 'system' and 'user' fields")
        
    # Validate model configuration
    model_config = config.get("model", {})
    if not isinstance(model_config, dict):
        raise ValueError("'model' must be a dictionary")
    
    if "provider" not in model_config or "name" not in model_config:
        raise ValueError("'model' configuration must include 'provider' and 'name' fields")
            
    # Validate MCP servers configuration if present
    if "mcpServers" in config:
        if not isinstance(config["mcpServers"], list):
            raise ValueError("'mcpServers' must be a list of server configurations")
            
        for idx, server in enumerate(config["mcpServers"]):
            if not isinstance(server, dict):
                raise ValueError(f"MCP server #{idx+1} must be a dictionary")
            
            if not all(k in server for k in ("name", "command", "args")):
                raise ValueError(f"MCP server #{idx+1} must have 'name', 'command' and 'args' fields")
                
            if not isinstance(server.get("args"), list):
                raise ValueError(f"MCP server #{idx+1} 'args' must be a list")

def get_config_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract commonly used config values with proper defaults.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with extracted and normalized config values
        
    Raises:
        KeyError: If required keys are missing
    """
    # Ensure required nested structures exist
    if "model" not in config:
        raise KeyError("Configuration missing 'model' section")
    
    model_config = config["model"]
    search_config = config.get("search", {})
    
    # Check for required model fields
    if "provider" not in model_config or "name" not in model_config:
        raise KeyError("Model configuration must include 'provider' and 'name'")
        
    # Construct model ID with provider
    model_id = f"{model_config['provider']}:{model_config['name']}"
      # Extract commonly used values with defaults
    return {
        "model_id": model_id,
        "temperature": model_config.get("temperature", 0.0),
        "max_tokens": model_config.get("max_tokens"),
        "rate_limit": model_config.get("rate_limit"),
        "search_engine": search_config.get("engine"),
        "search_results": search_config.get("results", 3),
        "file_col": config.get("file_col")
    }

def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and validate configuration from a YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config has validation errors
        yaml.YAMLError: If the YAML is malformed
    """
    global _config_data
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Always reload the configuration when explicitly requested
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        if not config:
            raise ValueError(f"Empty or invalid configuration file: {config_path}")
            
        config["config_path"] = str(config_path.resolve())
        
    # Validate the configuration
    validate_config(config)
    
    # Store for later global access
    _config_data = config
    
    return config

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