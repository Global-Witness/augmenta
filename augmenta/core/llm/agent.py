from typing import List, Optional, Tuple
import logging
from pydantic_ai import RunContext
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
        system_prompt: str = "You are a web research assistant. Use the provided tools to search for information and analyze web pages."
    ):
        """Initialize the web research agent.
        
        Args:
            model: The LLM model identifier
            temperature: Temperature setting for the model
            rate_limit: Optional rate limit between requests
            max_tokens: Optional maximum tokens for response
            system_prompt: Default system prompt for the agent
        """
        super().__init__(
            model=model,
            temperature=temperature,
            rate_limit=rate_limit,
            max_tokens=max_tokens
        )
        self.system_prompt = system_prompt
        self.register_tools()
        
    def register_tools(self):
        """Register the web search and page extraction tools."""
        
        @self.agent.tool_plain
        async def search_web(query: str) -> List[str]:
            """Search the web for information.
            
            Uses a search engine to find relevant web pages about a topic.
            
            Args:
                query: The search query to execute
                
            Returns:
                A list of relevant URLs
            """
            return await search_web_impl(query)
            
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
            
    async def run(self, prompt: str) -> str:
        """Run the agent to perform web research.
        
        This method uses the agent's tools to:
        1. Search the web for relevant information
        2. Visit and extract content from web pages
        3. Synthesize the information into a response
        
        Args:
            prompt: The research query or task
            
        Returns:
            The agent's response after researching
        """
        return await self.complete(
            prompt_system=self.system_prompt,
            prompt_user=prompt
        )