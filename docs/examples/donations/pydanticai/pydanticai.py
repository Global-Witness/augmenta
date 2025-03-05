from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits
# from pydanticai.tools.search import web_search_ddg
# from pydanticai.tools.extract import visit_webpage
from augmenta.core.search import search_web
from augmenta.core.extractors import visit_webpages
import logfire

logfire.configure()
logfire.instrument_httpx(capture_all=True)

# Create the agent with the tools
agent = Agent(
    model="openai:gpt-4o-mini",
    # Register the tools with tool_plain since they don't need context
    tools=[search_web, visit_webpages]
    # tools=[web_search_ddg, visit_webpage]
)

result = agent.run_sync(
    "Perform a web search for Mitsubishi Research Institute and identify whether they have any ties to the fossil fuels industry. Don't make your search terms too specific, at least not in the beginning.",
    usage_limits=UsageLimits()
)

print(result.data)

with open("pydanticai/messages.txt", "w") as f:
    messages = result.all_messages()
    string_messages = [str(message) for message in messages]
    f.write("\n".join(string_messages))



result = agent.run_sync('Where does "hello world" come from?')





import asyncio
from augmenta.core.search import search_web
from augmenta.core.extractors import visit_webpages

# this works
async def main():
    results = await visit_webpages(["http://nicu.md"])
    print(results)

if __name__ == "__main__":
    asyncio.run(main())


# this works
async def main():
    results = await search_web("Nicu Calcea")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())