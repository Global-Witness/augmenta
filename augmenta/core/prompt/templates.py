class PromptTemplates:
    """Manages prompt templates and their rendering"""
    
    @staticmethod
    def render_prompt(template: str, **kwargs) -> str:
        """Render a prompt template with given variables"""
        return template.format(**kwargs)