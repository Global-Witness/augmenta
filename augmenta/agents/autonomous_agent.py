from typing import Optional, Type, Union, Any
from pydantic import BaseModel
from ..tools.search_web import search_web
from ..tools.visit_webpages import visit_webpages
from .base import BaseAgent

class AutonomousAgent(BaseAgent):
    """An autonomous agent capable of web research through tools."""
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        rate_limit: Optional[float] = None,
        max_tokens: Optional[int] = None,
        verbose: bool = False,
        system_prompt: str = "You are a web research assistant. Use the provided tools to search for information and analyze web pages."
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
            verbose=verbose,
            tools=[search_web, visit_webpages]
        )
        self.system_prompt = system_prompt
            
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