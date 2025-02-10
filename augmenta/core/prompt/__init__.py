from .formatter import DocumentFormatter
from .templates import PromptTemplates
from .structure import StructureFormatter

def prepare_docs(scraped_content):
    """Prepare documents for prompt creation"""
    return DocumentFormatter.format_docs(scraped_content)

def append_structure(prompt: str, structure: dict) -> str:
    """Append structure format to prompt"""
    return StructureFormatter.append_structure_to_prompt(prompt, structure)

__all__ = [
    'DocumentFormatter',
    'PromptTemplates',
    'StructureFormatter',
    'prepare_docs',
    'append_structure'
]