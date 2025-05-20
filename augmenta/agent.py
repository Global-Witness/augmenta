"""Unified agent module for Augmenta."""

from typing import Type, Optional, Union, Any, Dict, ClassVar, Literal, List
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, create_model
from pydantic_ai import Agent, BinaryContent
import logfire
from .tools.mcp import load_mcp_servers
from .tools.search_web import search_web
from .tools.visit_webpages import visit_webpages

Agent.instrument_all()

class AugmentaAgent:
    """Agent that provides LLM functionality with web research capabilities."""
    
    TYPE_MAPPING: ClassVar[Dict[str, type]] = {
        'str': str, 'bool': bool, 'int': int,
        'float': float, 'dict': dict, 'list': list
    }
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        rate_limit: Optional[float] = None,
        max_tokens: Optional[int] = None,
        verbose: bool = False,
        system_prompt: str = "You are a web research assistant. Use the provided tools to search for information and analyse web pages."
    ):
        """Initialize the agent.
        
        Args:
            model: The LLM model identifier
            temperature: Temperature setting for the model
            rate_limit: Optional rate limit between requests
            max_tokens: Optional maximum tokens for response
            verbose: Whether to enable verbose logging with logfire
            system_prompt: Default system prompt for the agent
        """
        # Store parameters for reuse
        self.model = model
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.max_tokens = max_tokens
        self.verbose = verbose
        self.system_prompt = system_prompt
        
        # Create model settings
        model_settings = self._create_model_settings(temperature)
            
        # Load MCP servers from config
        try:
            mcp_servers = load_mcp_servers()
        except RuntimeError:
            # Config not loaded yet, proceed without MCP servers
            mcp_servers = []
            
        self.agent = Agent(
            model,
            model_settings=model_settings,
            tools=[search_web, visit_webpages],
            mcp_servers=mcp_servers
        )

    def _create_model_settings(self, temperature: float) -> Dict[str, Any]:
        """Create model settings dictionary with proper parameters.
        
        Args:
            temperature: Temperature setting for the model
            
        Returns:
            Dictionary with model settings
        """
        model_settings = {'temperature': temperature}
        if self.rate_limit is not None:
            model_settings['rate_limit'] = self.rate_limit
        if self.max_tokens is not None:
            model_settings['max_tokens'] = self.max_tokens
        return model_settings
    
    @staticmethod
    def create_structure_class(yaml_file_path: Union[str, Path]) -> Type[BaseModel]:
        """Creates a Pydantic model from YAML structure definition.
        
        Args:
            yaml_file_path: Path to YAML file containing structure definition
            
        Returns:
            A Pydantic model class based on the YAML structure
        """
        yaml_file_path = Path(yaml_file_path)
        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
                
            if not isinstance(yaml_content, dict) or 'structure' not in yaml_content:
                raise ValueError("YAML must contain a 'structure' dictionary")
                
            fields: Dict[str, tuple] = {}
            for field_name, field_info in yaml_content['structure'].items():
                if not isinstance(field_info, dict):
                    raise ValueError(f"Invalid field definition for {field_name}")
                
                # Determine field type based on options or type specification
                if 'options' in field_info:
                    field_type = Literal[tuple(str(opt) for opt in field_info['options'])]
                else:
                    type_str = field_info.get('type', 'str')
                    field_type = AugmentaAgent.TYPE_MAPPING.get(type_str, str)
                
                fields[field_name] = (
                    field_type,
                    Field(description=field_info.get('description', ''))
                )
            
            return create_model('Structure', **fields, __base__=BaseModel)
                
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Failed to parse YAML: {e}")
    
    def get_mcp_servers_context(self):
        """Get the MCP servers context manager from the underlying agent.
        
        Returns:
            Context manager for running MCP servers
        """
        return self.agent.run_mcp_servers()
      
    async def run(
        self,
        prompt: Union[str, List[Union[str, BinaryContent]]],
        response_format: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> Union[str, dict[str, Any], BaseModel]:
        """Run the agent to perform web research.
        
        Args:
            prompt: The research query/task as a string or a list containing text and binary content
            response_format: Optional Pydantic model for structured output
            temperature: Optional override for model temperature
            system_prompt: Optional override for system prompt (defaults to self.system_prompt)
            
        Returns:
            The agent's response after researching, either as string, dict or Pydantic model
        """
        try:
            # Set the system prompt
            self.agent.system_prompt = system_prompt or self.system_prompt
            
            # Prepare model settings only if temperature override is provided
            model_settings = None
            if temperature is not None and temperature != self.temperature:
                model_settings = self._create_model_settings(temperature)
            
            # Note: MCP servers context should be managed at a higher level now
            result = await self.agent.run(
                prompt,
                output_type=response_format,
                model_settings=model_settings
            )

            # Return the appropriate result format
            return result.data.model_dump() if response_format else result.data
        except Exception as e:
            logfire.error(f"LLM request failed: {e}")
            raise RuntimeError(f"LLM request failed: {e}")
