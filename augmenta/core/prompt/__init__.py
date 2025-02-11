"""Prompt handling and formatting functionality for Augmenta."""

from .formatter_docs import DocumentFormatter
from .formatter_examples import ExampleFormatter
from .templates import PromptTemplates

def format_docs(scraped_content):
    """Prepare documents for prompt creation"""
    return DocumentFormatter.format_docs(scraped_content)

def format_examples(examples_yaml):
    """Format examples for prompt creation"""
    return ExampleFormatter.format_examples(examples_yaml)

__all__ = [
    'DocumentFormatter',
    'ExampleFormatter',
    'PromptTemplates',
    'format_docs',
    'format_examples'
]