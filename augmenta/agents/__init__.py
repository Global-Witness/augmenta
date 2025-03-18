"""Agent functionality for the Augmenta package."""

from .base import BaseAgent, make_request_llm
from .autonomous_agent import AutonomousAgent

__all__ = ['BaseAgent', 'make_request_llm', 'AutonomousAgent']