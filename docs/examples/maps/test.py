import os
import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

# Load environment variables from .env file
load_dotenv()

# Debug logging
print(f"OPENAI_API_KEY present: {'OPENAI_API_KEY' in os.environ}")
print(f"OPENAI_API_KEY value: {os.environ.get('OPENAI_API_KEY', '')[:8]}...")

server = MCPServerStdio('npx', ['-y', '@modelcontextprotocol/server-google-maps', 'stdio'], env=os.environ)
agent = Agent('openai:gpt-4o-mini', mcp_servers=[server])

print("Agent initialized.")
async def main():
    print("Starting MCP server...")
    async with agent.run_mcp_servers():
        print("Asking...")
        result = await agent.run('What\'s a good Japanese restaurant in Chisinau?')
    print(result.data)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.

if __name__ == "__main__":
    asyncio.run(main())