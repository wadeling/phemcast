"""Pydantic models for data validation and state management."""
from datetime import datetime
from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class Article(BaseModel):
    """Individual article data model."""
    
    url: str
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Main article content")
    company_name: str = Field(..., description="Company extracted from domain")
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    summary: Optional[str] = None
    key_insights: List[str] = Field(default_factory=list)
    word_count: int = Field(default=0)
    language: str = Field(default="en")
    tags: List[str] = Field(default_factory=list)
    
    @validator("url")
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    @validator("word_count")
    def validate_word_count(cls, v):
        """Ensure word count is non-negative."""
        if v < 0:
            raise ValueError("Word count must be non-negative")
        return v
    
    def calculate_word_count(self) -> int:
        """Calculate word count from content."""
        return len(self.content.split()) if self.content else 0


class CompanyInsights(BaseModel):
    """Aggregated insights per company."""
    
    company_name: str
    domain: str
    article_count: int = Field(ge=0)
    insights: List[str] = Field(default_factory=list)
    trend_score: float = Field(default=0.0, ge=0.0, le=1.0, description="0-1 based on recency and relevance")
    key_topics: List[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    
    @validator("trend_score")
    def validate_trend_score(cls, v):
        """Ensure trend score is between 0 and 1."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Trend score must be between 0 and 1")
        return v


class WebScrapeConfig(BaseModel):
    """Configuration for web scraping."""
    
    max_articles_per_blog: int = Field(default=5, ge=1, le=50)
    min_word_count: int = Field(default=100, ge=10)
    include_images: bool = Field(default=False)
    filter_duplicates: bool = Field(default=True)
    timeout: int = Field(default=30, ge=5, le=120)
    

class AnalysisConfig(BaseModel):
    """Configuration for AI analysis."""
    
    summary_length: str = Field(default="medium", pattern="^(short|medium|verbose)$")
    extract_quotes: bool = Field(default=True)
    trend_analysis: bool = Field(default=True)
    generate_insights: bool = Field(default=True)
    max_tokens_per_summary: int = Field(default=500, ge=50, le=2000)


class ReportConfig(BaseModel):
    """Configuration for report generation."""
    
    output_dir: str = Field(default="reports")
    include_csv: bool = Field(default=False)
    include_json: bool = Field(default=False)
    include_markdown: bool = Field(default=True)
    include_pdf: bool = Field(default=True)
    template_name: str = Field(default="default")


class ProcessingState(TypedDict, total=False):
    """Complete LangGraph workflow state with detailed tracking."""
    
    # Input configuration
    raw_urls: List[str]
    validated_urls: List[str]
    email_recipients: List[str]
    task_id: str
    processing_config: Dict[str, Any]
    
    # Web scraping results
    scraped_articles: List[Article]
    scraping_errors: List[Dict[str, str]]
    
    # Analysis results
    articles_with_summary: List[Article]
    company_insights: Dict[str, CompanyInsights]
    industry_trends: List[str]
    key_insights: List[str]
    analysis_errors: List[Dict[str, str]]
    
    # Report addresses
    report_paths: Dict[str, str]  # {"markdown": "path/md", "pdf": "path/pdf"}
    
    # Email delivery
    email_sent: bool
    delivery_errors: List[str]
    
    # Execution tracking
    processing_status: str  # 'pending', 'scraping', 'analyzing', 'generating', 'sending', 'completed', 'failed'
    processing_started_at: datetime
    processing_completed_at: Optional[datetime]
    
    # Progress tracking
    total_urls: int
    total_articles: int
    articles_processed: int
    processing_errors: List[str]
    
    # Resource usage
    total_tokens_used: int
    execution_time_seconds: float


class TaskStatus(BaseModel):
    """Status tracking for async task processing."""
    
    task_id: UUID = Field(default_factory=uuid4)
    status: str = Field(default="pending", pattern="^(pending|processing|completed|failed)$")
    current_step: str = Field(default="starting")
    progress: Dict[str, int] = Field(default_factory=dict)
    error: Optional[str] = None
    result_url: Optional[str] = None
    
    @validator("progress")
    def validate_progress(cls, v):
        """Ensure progress has expected keys."""
        if v is None:
            return {"total": 0, "completed": 0, "failed": 0}
        return v


# LangGraph-specific state for workflow
class AgentState(TypedDict, total=False):
    """LangGraph workflow state - optimized for workflow execution."""
    
    urls: List[str]
    articles: List[Article]
    company_insights: Dict[str, CompanyInsights]
    weekly_summary: str
    report_path_md: Optional[str]
    report_path_pdf: Optional[str]
    email_recipients: List[str]
    task_id: str
    processing_status: str
    progress: Dict[str, int]
    errors: List[str]
    total_tokens_used: int