"""Agent functionality for the Augmenta package."""

from .base import BaseAgent, make_request_llm
from .agent import WebResearchAgent

__all__ = ['BaseAgent', 'make_request_llm', 'WebResearchAgent']