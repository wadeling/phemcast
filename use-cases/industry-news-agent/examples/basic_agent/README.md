# Basic Industry News Agent Example

This example demonstrates a simple LangGraph agent that can scrape blog articles and generate summaries.

## Features

- Web scraping with rate limiting and error handling
- AI-powered content summarization
- LangGraph workflow orchestration
- State management with TypedDict

## Usage

```bash
# Run the basic agent
python basic_agent.py --urls "https://blog.example.com" --output reports/
```

## Structure

- `agent.py` - Main LangGraph agent definition
- `tools.py` - Web scraping and analysis tools
- `models.py` - Pydantic models and state management
- `settings.py` - Configuration management

## Key Concepts

1. **LangGraph State Management**: Using TypedDict for state definition
2. **Tool Integration**: Decorating functions with @tool for LangGraph integration
3. **Error Handling**: Robust error handling for web scraping operations
4. **Rate Limiting**: Configurable delays to avoid being blocked 