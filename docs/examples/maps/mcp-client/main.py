from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
import asyncio
import yaml

async def main():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    servers = []
    for server_config in config['mcpServers']:
        server = MCPServerStdio(server_config['command'], server_config['args'])
        servers.append(server)
    
    agent = Agent('openai:gpt-4o-mini', mcp_servers=servers)
    async with agent.run_mcp_servers():
        await agent.run('What is this webpage about? https://www.bbc.co.uk/news/videos/c7898myzxvpo')

if __name__ == "__main__":
    asyncio.run(main())