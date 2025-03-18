from typing import List, Optional, Type, Union, Any, Tuple
from pydantic import BaseModel

from ..tools.search_web import search_web
from ..tools.visit_webpages import visit_webpages
from ..utils.prompt_formatter import format_docs
from .base import BaseAgent, make_request_llm

class FixedAgent(BaseAgent):
    """An agent that implements a fixed for web research.
    
    Unlike the AutonomousAgent which makes its own decisions, this agent
    follows a predetermined workflow:
    1. Search for relevant web pages
    2. Extract content from those pages
    3. Format the documents
    4. Process with LLM
    """
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        rate_limit: Optional[float] = None,
        max_tokens: Optional[int] = None,
        verbose: bool = False,
        system_prompt: str = "You are a web research assistant analyzing search results."
    ):
        """Initialize the workflow agent.
        
        Args:
            model: The LLM model identifier
            temperature: Temperature setting for the model
            rate_limit: Optional rate limit between requests
            max_tokens: Optional maximum tokens for response
            verbose: Whether to enable verbose logging
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

    async def run(
        self,
        prompt: str,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Union[str, dict[str, Any], BaseModel]:
        """Run the fixed workflow to research and analyze.
        
        Args:
            prompt: The research query or task
            response_format: Optional Pydantic model for structured output
            
        Returns:
            The agent's response after following the workflow, either as:
            - string if no response_format
            - dict if response_format but response not valid
            - Pydantic model instance if response_format and valid
        """
        # 1. Execute search
        search_results = await search_web(prompt)
        urls = [result['url'] for result in search_results]
        
        # 2. Extract content
        raw_results = await visit_webpages(urls)
        
        # 3. Filter valid results and create sources summary
        valid_results = [result for result in raw_results if result["content"].strip()]
        sources_summary = [result["url"] for result in valid_results]
        
        # 4. Format documents and combine with prompt
        prompt_with_docs = f"{prompt}\n\n## Documents\n\n{format_docs(valid_results)}"
        
        # 5. Process with LLM
        response = await make_request_llm(
            prompt_system=self.system_prompt,
            prompt_user=prompt_with_docs,
            model=self.model,
            response_format=response_format,
            verbose=self.verbose,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            rate_limit=self.rate_limit
        )
        
        # Add sources to response if it's a dict
        if isinstance(response, dict):
            response['augmenta_sources'] = "\n".join(sources_summary)
            
        return response