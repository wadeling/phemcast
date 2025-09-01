"""Configuration management for industry news agent."""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
from pathlib import Path

# Import logging configuration
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback for direct execution
    import logging
    logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    # Database Configuration
    database_url: str = Field(
        default="mysql://root:password@mysql:3306/phemcast",
        description="Database connection URL"
    )
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_file: Optional[str] = Field(default=None, description="Log file path (optional, console only if not set)")
    show_file_line: bool = Field(default=False, description="Show file name and line number in log messages")
    show_function: bool = Field(default=False, description="Show function name in log messages")
    uvicorn_log_level: str = Field(default="INFO", description="Uvicorn server log level (WARNING, INFO, ERROR)")
    
    @validator("uvicorn_log_level")
    def validate_uvicorn_log_level(cls, v):
        """Validate uvicorn log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid uvicorn log level: {v}. Valid levels: {', '.join(valid_levels)}")
        return v.upper()

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
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from_name: str = "Industry News Agent"
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None

    # Tencent Cloud SES Configuration
    tencent_cloud_secret_id: str = Field(..., description="Tencent Cloud API Secret ID")
    tencent_cloud_secret_key: str = Field(..., description="Tencent Cloud API Secret Key")
    tencent_cloud_region: str = Field(
        default="ap-guangzhou",
        description="Tencent Cloud service region for SES"
    )
    tencent_from_email: str = Field(..., description="Tencent Cloud SES sender email address")
    tencent_template_id: Optional[int] = Field(default=None, description="Tencent Cloud SES template ID")
    tencent_use_template: bool = Field(default=True, description="Whether to use template for sending emails")
    
    @validator("tencent_cloud_region")
    def validate_tencent_region(cls, v):
        """Validate Tencent Cloud region."""
        valid_regions = [
            "ap-guangzhou",    # 广州
            "ap-shanghai",     # 上海
            "ap-beijing",      # 北京
            "ap-hongkong",     # 香港
            "ap-singapore",    # 新加坡
            "ap-seoul",        # 首尔
            "ap-tokyo",        # 东京
            "ap-mumbai",       # 孟买
            "eu-frankfurt",    # 法兰克福
            "na-ashburn",      # 弗吉尼亚
            "na-siliconvalley" # 硅谷
        ]
        if v not in valid_regions:
            raise ValueError(f"Invalid Tencent Cloud region: {v}. Valid regions: {', '.join(valid_regions)}")
        return v

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
    
    # TTS Configuration
    minimaxi_api_key: Optional[str] = Field(default=None, description="Minimaxi API key for text-to-speech")
    minimaxi_group_id: Optional[str] = Field(default=None, description="Minimaxi Group ID for API access")
    base_url: str = Field(default="http://localhost:8000", description="Base URL for the application")
    enable_tts: bool = Field(default=True, description="Enable text-to-speech functionality")
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
        if "tencent_cloud_secret" in str(e).lower():
            error_msg += "\nMake sure to set TENCENT_CLOUD_SECRET_ID and TENCENT_CLOUD_SECRET_KEY in your .env file"
        if "tencent_from_email" in str(e).lower():
            error_msg += "\nMake sure to set TENCENT_FROM_EMAIL in your .env file"
        if "email" in str(e).lower() and "tencent" not in str(e).lower():
            error_msg += "\nMake sure to set EMAIL_USERNAME and EMAIL_PASSWORD in your .env file"
        
        logger.error(error_msg)
        raise ValueError(error_msg) from e