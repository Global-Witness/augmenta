# Augmenta Agent

Augmenta uses a unified agent architecture that handles web research through a streamlined interface.

The `AugmentaAgent` class provides built-in capabilities for web search, content extraction, and LLM-based analysis.

## Features

- Web search using various search providers
- Content extraction from web pages
- Integration with Model Context Protocol (MCP) servers
- Structured output formatting via Pydantic models
- Customizable system prompts and model parameters

## Usage

The agent is automatically configured when you run Augmenta with your configuration:

```yaml
# Basic configuration example
model: "openai/gpt-4o"
temperature: 0.2
max_tokens: 2048
rate_limit: 10  # Optional: Requests per minute
```

## Advanced Configuration

You can customize the agent's behavior through your configuration file:

```yaml
prompt:
  system: "You are a research assistant specialized in analyzing company donations data. Your task is to categorize each donation and provide reasoning."
  user: "Analyze this donation: {{amount}} from {{donor}} to {{recipient}}. Provide category and reasoning."
```

The agent integrates seamlessly with Augmenta's search and extraction tools to provide comprehensive research capabilities.
