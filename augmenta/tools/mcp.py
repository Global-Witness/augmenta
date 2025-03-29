"""MCP server configuration and loading utilities."""

from typing import List, Dict, Any
from pydantic_ai.mcp import MCPServerStdio
from ..config.read_config import get_config

def load_mcp_servers() -> List[MCPServerStdio]:
    """Load MCP server configurations from the main config.
    
    Returns:
        List of initialized MCPServerStdio instances
        
    Raises:
        RuntimeError: If configuration hasn't been loaded
        ValueError: If MCP configuration is malformed
    """
    config = get_config()
    
    if 'mcpServers' not in config:
        return []  # No MCP servers configured
        
    if not isinstance(config['mcpServers'], list):
        raise ValueError("'mcpServers' must be a list")
        
    servers = []
    for server_config in config['mcpServers']:
        if not all(k in server_config for k in ('name', 'command', 'args')):
            raise ValueError("Each server config must have 'name', 'command' and 'args' fields")
            
        server = MCPServerStdio(
            server_config['command'],
            server_config['args']
        )
        servers.append(server)
        
    print(f"Loaded {len(servers)} MCP servers from config.")
    return servers