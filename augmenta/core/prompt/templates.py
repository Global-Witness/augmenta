"""Template handling for prompt creation."""

from typing import Any, Dict

class PromptTemplates:
    """Manages prompt templates and their rendering."""
    
    @staticmethod
    def render_prompt(template: str, **kwargs: Any) -> str:
        """
        Render a prompt template with given variables.
        
        Args:
            template: Template string with {variable} placeholders
            **kwargs: Variables to substitute in the template
            
        Returns:
            str: Rendered template with variables replaced
            
        Raises:
            KeyError: If a required template variable is missing
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Missing required template variable: {e}")