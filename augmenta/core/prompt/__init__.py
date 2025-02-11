from .formatter_docs import DocumentFormatter
from .templates import PromptTemplates

def prepare_docs(scraped_content):
    """Prepare documents for prompt creation"""
    return DocumentFormatter.format_docs(scraped_content)

__all__ = [
    'DocumentFormatter',
    'PromptTemplates',
    'prepare_docs'
]