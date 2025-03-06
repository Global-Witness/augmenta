from typing import List, Optional, Tuple, Type, Union, Any
import logging
from pydantic_ai import RunContext
from pydantic import BaseModel
from ..search import search_web as search_web_impl
from ..extractors import visit_webpages as visit_webpages_impl
from .base import BaseAgent

logger = logging.getLogger(__name__)

class WebResearchAgent(BaseAgent):
    """An autonomous agent capable of web research through tools."""
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        rate_limit: Optional[float] = None,
        max_tokens: Optional[int] = None,
        verbose: bool = False,
        system_prompt: str = "You are a web research assistant. Use the provided tools to search for information and analyze web pages.",
        search_config: Optional[dict] = None
    ):
        """Initialize the web research agent.
        
        Args:
            model: The LLM model identifier
            temperature: Temperature setting for the model
            rate_limit: Optional rate limit between requests
            max_tokens: Optional maximum tokens for response
            verbose: Whether to enable verbose logging with logfire
            system_prompt: Default system prompt for the agent
        """
        super().__init__(
            model=model,
            temperature=temperature,
            rate_limit=rate_limit,
            max_tokens=max_tokens,
            verbose=verbose
        )
        self.system_prompt = system_prompt
        self.search_config = search_config or {}
        self.register_tools()
        
    def register_tools(self):
        """Register the web search and page extraction tools."""
        
        @self.agent.tool_plain
        async def search_web(query: str) -> str:
            """Search the web for information.
            
            Uses a search engine to find relevant web pages about a topic.
            
            Args:
                query: The search query to execute
                
            Returns:
                Markdown formatted search results with titles and descriptions
            """
            engine = self.search_config.get('engine')
            return await search_web_impl(query, engine=engine)
            
        @self.agent.tool_plain
        async def visit_webpages(urls: List[str]) -> List[Tuple[str, Optional[str]]]:
            """Visit web pages and extract their main content.
            
            Downloads web pages and extracts their main text content,
            filtering out navigation, ads, etc.
            
            Args:
                urls: List of URLs to visit and extract content from
                
            Returns:
                List of (url, content) tuples. Content may be None if extraction fails.
            """
            return await visit_webpages_impl(urls)
            
    async def run(self, prompt: str, response_format: Optional[Type[BaseModel]] = None) -> Union[str, dict[str, Any], BaseModel]:
        """Run the agent to perform web research.
        
        Args:
            prompt: The research query or task
            response_format: Optional Pydantic model for structured output
            
        Returns:
            The agent's response after researching, either as string, dict or Pydantic model
        """
        return await self.complete(
            prompt_system=self.system_prompt,
            prompt_user=prompt,
            response_format=response_format
        )