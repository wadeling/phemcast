"""Configuration management for industry news agent."""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

    # LLM Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for content analysis")
    openai_model: str = Field(
        default="gpt-4-turbo-preview", description="OpenAI model to use"
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API base URL for compatible endpoints"
    )
    max_tokens_per_article: int = Field(
        default=2000, description="Max tokens for summarization"
    )

    # SMTP Configuration
    smtp_server: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    email_username: str = Field(..., description="Email username")
    email_password: str = Field(..., description="Email password or app password")
    email_from_name: str = Field(default="Industry News Agent", description="Email sender name")

    # Web Scraping
    request_delay: float = Field(default=2.0, description="Delay between requests (seconds)")
    max_concurrent_requests: int = Field(
        default=5, description="Max concurrent HTTP requests"
    )
    user_agents: List[str] = Field(
        default=[
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")

    # Cache
    cache_ttl_minutes: int = Field(default=360, description="Cache TTL in minutes")

    # Reporting
    output_dir: str = Field(default="reports", description="Report output directory")
    max_report_size_mb: int = Field(default=10, description="Maximum report size in MB")

    @validator("output_dir")
    def validate_output_dir(cls, v):
        """Ensure output directory exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @validator("request_delay")
    def validate_delay(cls, v):
        """Ensure delay is reasonable."""
        if v < 0.1 or v > 10:
            raise ValueError("request_delay must be between 0.1 and 10 seconds")
        return v


def load_settings() -> Settings:
    """Load settings with proper error handling."""
    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "api_key" in str(e).lower():
            error_msg += "\nMake sure to set OPENAI_API_KEY in your .env file"
        if "email" in str(e).lower():
            error_msg += "\nMake sure to set EMAIL_USERNAME and EMAIL_PASSWORD in your .env file"
        raise ValueError(error_msg) from e