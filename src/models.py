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
    analysis_data: Optional[Dict[str, Any]] = Field(default=None, description="AI analysis results with enhanced structure")
    
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
    max_tokens_per_summary: int = Field(default=10000, ge=50, le=20000)


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
    report_path_md: str = ""  # Path to markdown report
    report_path_pdf: str = ""  # Path to PDF report
    
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
    
    # Input configuration
    task_id: str
    urls: List[str]
    max_articles: int
    email_recipients: List[str]
    company_configs: List[Dict]
    
    # Processing state
    articles: List[Article]
    company_insights: Dict[str, CompanyInsights]
    weekly_summary: str
    report_path_md: Optional[str]
    report_path_pdf: Optional[str]
    report_path_audio: Optional[str]
    task_id: str
    processing_status: str
    progress: Dict[str, int]
    errors: List[str]
    total_tokens_used: int
    
    # Additional fields that may be set during workflow
    logs: List[str]
    total_urls: int
    total_articles: int
    email_sent: bool
    processing_time: float


class ScheduledTask(BaseModel):
    """Scheduled task model for automated report generation."""
    
    id: Optional[str] = None
    task_name: str = Field(..., description="Task name for identification")
    user_name: str = Field(..., description="User who created the task")
    urls: List[str] = Field(..., description="Company blog URLs to analyze")
    email_recipients: List[str] = Field(default_factory=list, description="Email addresses for report delivery")
    max_articles: int = Field(default=5, ge=1, le=20, description="Articles per blog to analyze")
    
    # Schedule configuration
    schedule_type: str = Field(..., pattern="^(daily|weekly|monthly)$", description="Schedule frequency")
    schedule_time: str = Field(..., description="Time of day (HH:MM format)")
    schedule_time_utc: str = Field(..., description="UTC Time of day (HH:MM format)")
    schedule_day: Optional[str] = Field(None, description="Day of week (for weekly) or day of month (for monthly)")
    
    # Task status
    is_active: bool = Field(default=True, description="Whether the task is currently active")
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    next_run: Optional[datetime] = Field(None, description="Next scheduled execution time")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('schedule_time')
    def validate_schedule_time(cls, v):
        """Validate time format HH:MM."""
        try:
            from datetime import datetime
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError('Time must be in HH:MM format (e.g., 09:30)')
    
    @validator('schedule_day')
    def validate_schedule_day(cls, v, values):
        """Validate schedule day based on schedule type."""
        if 'schedule_type' in values:
            if values['schedule_type'] == 'weekly' and v:
                valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                if v.lower() not in valid_days:
                    raise ValueError('Weekly schedule day must be a valid day of week')
            elif values['schedule_type'] == 'monthly' and v:
                try:
                    day = int(v)
                    if day < 1 or day > 31:
                        raise ValueError('Monthly schedule day must be between 1 and 31')
                except ValueError:
                    raise ValueError('Monthly schedule day must be a number')
        return v


class ScheduledTaskCreate(BaseModel):
    """Model for creating a new scheduled task."""
    
    task_name: str = Field(..., description="Task name for identification")
    urls: List[str] = Field(..., description="Company blog URLs to analyze")
    email_recipients: List[str] = Field(default_factory=list, description="Email addresses for report delivery")
    max_articles: int = Field(default=5, ge=1, le=20, description="Articles per blog to analyze")
    
    # Schedule configuration
    schedule_type: str = Field(..., pattern="^(daily|weekly|monthly)$", description="Schedule frequency")
    schedule_time: str = Field(..., description="Time of day (HH:MM format)")
    schedule_day: Optional[str] = Field(None, description="Day of week (for weekly) or day of month (for monthly)")


class ScheduledTaskUpdate(BaseModel):
    """Model for updating an existing scheduled task."""
    
    task_name: Optional[str] = Field(None, description="Task name for identification")
    urls: Optional[List[str]] = Field(None, description="Company blog URLs to analyze")
    email_recipients: Optional[List[str]] = Field(None, description="Email addresses for report delivery")
    max_articles: Optional[int] = Field(None, ge=1, le=20, description="Articles per blog to analyze")
    
    # Schedule configuration
    schedule_type: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$", description="Schedule frequency")
    schedule_time: Optional[str] = Field(None, description="Time of day (HH:MM format)")
    schedule_day: Optional[str] = Field(None, description="Day of week (for weekly) or day of month (for monthly)")
    
    # Task status
    is_active: Optional[bool] = Field(None, description="Whether the task is currently active")