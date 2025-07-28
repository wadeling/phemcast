# Industry News Agent Context Engineering - Global Rules for LangGraph Development

This file contains the global rules and principles that apply to ALL Industry News Agent development work. These rules are specialized for building production-grade AI agents with LangGraph, web scraping, content analysis, and report generation.

## 🔄 Industry News Agent Core Principles

**IMPORTANT: These principles apply to ALL Industry News Agent development:**

### Agent Development Workflow
- **Always start with INITIAL.md** - Define agent requirements before generating PRPs
- **Use the PRP pattern**: INITIAL.md → `/generate-industry-news-prp INITIAL.md` → `/execute-industry-news-prp PRPs/filename.md`
- **Follow validation loops** - Each PRP must include agent testing with comprehensive test cases
- **Context is King** - Include ALL necessary LangGraph patterns, examples, and documentation

### Research Methodology for Industry News Agents
- **Web scraping extensively** - Always research LangGraph patterns and best practices
- **Study official documentation** - langchain-ai.github.io/langgraph is the authoritative source
- **Pattern extraction** - Identify reusable agent architectures and workflow patterns
- **Gotcha documentation** - Document async patterns, rate limiting, and content processing issues

## 📚 Project Awareness & Context

- **Use a virtual environment** to run all code and tests. If one isn't already in the codebase when needed, create it
- **Use consistent LangGraph naming conventions** and agent structure patterns
- **Follow established agent directory organization** patterns (agent.py, tools.py, models.py, web_interface.py)
- **Leverage LangGraph examples extensively** - Study existing patterns before creating new agents

## 🧱 Agent Structure & Modularity

- **Never create files longer than 500 lines** - Split into modules when approaching limit
- **Organize agent code into clearly separated modules** grouped by responsibility:
  - `agent.py` - Main LangGraph agent definition and execution logic
  - `tools.py` - Tool functions for web scraping, content analysis, and report generation
  - `models.py` - Pydantic output models and state management classes
  - `web_interface.py` - FastAPI web application with form handling
  - `email_service.py` - Email sending functionality with attachments
  - `report_generator.py` - Markdown and PDF report generation
- **Use clear, consistent imports** - Import from langgraph and langchain packages appropriately
- **Use python-dotenv and load_dotenv()** for environment variables
- **Never hardcode sensitive information** - Always use .env files for API keys and configuration

## 🤖 LangGraph Development Standards

### Agent Creation Patterns
- **Use LangGraph for workflow orchestration** - Implement state management and node transitions
- **Implement proper state management** - Use TypedDict for state definition and validation
- **Define structured outputs** - Use Pydantic models for result validation
- **Include comprehensive system prompts** - Both static and dynamic instructions

### Tool Integration Standards
- **Use @tool decorator** for context-aware tools with proper error handling
- **Implement proper parameter validation** - Use Pydantic models for tool parameters
- **Handle tool errors gracefully** - Implement retry mechanisms and error recovery
- **Use async/await patterns** - For better performance with multiple operations

### Web Scraping Standards
- **Implement rate limiting** - Avoid being blocked by websites
- **Use proper user agents** - Rotate user agents to avoid detection
- **Handle different blog platforms** - WordPress, Medium, custom CMS support
- **Implement content deduplication** - Avoid processing the same articles multiple times
- **Use robust error handling** - Network failures, parsing errors, and timeouts

### Environment Variable Configuration with python-dotenv
```python
# Use python-dotenv and pydantic-settings for proper configuration management
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    
    # Email Configuration
    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP server")
    smtp_port: int = Field(default=587, description="SMTP port")
    email_username: str = Field(..., description="Email username")
    email_password: str = Field(..., description="Email password")
    
    # Web Scraping Configuration
    request_delay: float = Field(default=1.0, description="Delay between requests")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=30, description="Request timeout in seconds")

def load_settings() -> Settings:
    """Load settings with proper error handling and environment loading."""
    load_dotenv()
    
    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "api_key" in str(e).lower():
            error_msg += "\nMake sure to set OPENAI_API_KEY in your .env file"
        raise ValueError(error_msg) from e
```

## 🧪 Testing & Reliability

- **Always create comprehensive unit tests** for all components (functions, classes, routes, etc.)
- **Test web scraping with mock responses** - Use pytest-mock for HTTP responses
- **Test LangGraph workflows** - Validate state transitions and node execution
- **Test email functionality** - Use test SMTP servers or mock email sending
- **Test report generation** - Validate Markdown and PDF output formats
- **Tests should live in a `/tests` folder** mirroring the main app structure
- **Include integration tests** - Test the complete workflow from web scraping to email delivery

## ✅ Task Completion

- **Mark completed tasks in `TASK.md`** immediately after finishing them
- **Add new sub-tasks or TODOs** discovered during development to `TASK.md` under a "Discovered During Work" section
- **Update documentation** when new features are added or dependencies change

## 📎 Style & Conventions

- **Use Python** as the primary language
- **Follow PEP8**, use type hints, and format with `black`
- **Use `pydantic` for data validation** and state management
- **Use `FastAPI` for web interface** and `aiohttp` for async web scraping
- **Use `ReportLab` for PDF generation** and `markdown` for Markdown formatting
- **Write docstrings for every function** using the Google style:
  ```python
  def scrape_blog_articles(url: str, max_articles: int = 10) -> List[Article]:
      """
      Scrape articles from a blog URL.
      
      Args:
          url (str): The blog URL to scrape
          max_articles (int): Maximum number of articles to scrape
          
      Returns:
          List[Article]: List of scraped articles with metadata
      """
  ```

## 📚 Documentation & Explainability

- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer
- **Document web scraping patterns** - Include examples for different blog platforms
- **Document LangGraph workflow patterns** - Include state management and node transition examples
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what

## 🧠 AI Behavior Rules

- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages
- **Always confirm file paths and module names** exist before referencing them in code or tests
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`
- **Always implement proper error handling** for web scraping and external API calls
- **Always test rate limiting and user agent rotation** to avoid being blocked by websites 