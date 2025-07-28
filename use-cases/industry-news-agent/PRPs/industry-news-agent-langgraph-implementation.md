# Industry News Agent - LangGraph Production Implementation PRP

## 🎯 Project Requirements Analysis

Based on INITIAL.md analysis, this PRP specifies a **complete production-ready industry news aggregation agent** using LangGraph that performs:

1. **Web scraping** from company blog URLs with platform detection
2. **AI-powered content analysis** using OpenAI GPT models
3. **Report generation** in Markdown and PDF formats
4. **Email delivery** with secure SMTP integration
5. **Web interface** via FastAPI for user interaction

## 🔍 Research Summary & External Context

### LangGraph Best Practices (2025)
- **Async Patterns**: LangGraph 0.2.x supports native async workflows - critical for web scraping performance
- **State Management**: TypedDict with pydantic validation recommended for type safety
- **Tool Integration**: Use `@tool` decorator with asyncio support for concurrent HTTP requests
- **Error Handling**: Implement circuit breakers and exponential backoff for external API calls

### Web Scraping Patterns
- **Rate Limiting**: Between 1-3 seconds delay with jitter to avoid detection
- **User Agent Rotation**: Using realistic browser user agents
- **Response Caching**: 6-hour cache TTL to avoid re-scraping recently processed articles
- **Platform Detection**: Auto-detect WordPress, Medium, RSS feeds, or custom CMS

### External API Integration
- **OpenAI Integration**: gpt-4-turbo optimized for content analysis, 16k context window
- **SMTP Email**: TLS encryption required, retry logic with exponential backoff
- **Report Generation**: ReportLab 4.x for PDF, Jinja2 templates for dynamic content

## 🏗️ Architecture Design

### LangGraph Workflow Structure

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌────────────┐    ┌────────────────┐
│   Start     │    │   Scraping   │    │   Analysis    │    │   Report   │    │    Email       │
│   State     │───>│     Node     │───>│     Node      │───>│ Generation │───>│   Delivery     │
│   Init      │    │   (async)    │    │   (OpenAI)    │    │  (PDF/MD)  │    │   (SMTP)       │
└─────────────┘    └──────────────┘    └───────────────┘    └────────────┘    └────────────────┘
```

### TypedDict State Design

```python
from typing import List, Dict, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime

class Article(BaseModel):
    """Individual article data model"""
    url: str
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    company: str  # Extracted from URL domain
    summary: Optional[str] = None
    key_insights: List[str] = Field(default_factory=list)
    word_count: int = 0

class CompanyInsights(BaseModel):
    """Aggregated insights per company"""
    company_name: str
    article_count: int
    insights: List[str]
    trend_score: float  # 0-1 based on recency and relevance

class AgentState(TypedDict):
    """Main LangGraph workflow state"""
    urls: List[str]
    articles: List[Article]
    company_insights: Dict[str, CompanyInsights]
    weekly_summary: str
    report_path_md: Optional[str]
    report_path_pdf: Optional[str]
    email_recipients: List[str]
    task_id: str  # For async tracking
    processing_status: str  # 'pending', 'scraping', 'analyzing', 'generating', 'sending', 'completed', 'failed'
    progress: Dict[str, int]  # {'total': 10, 'scraped': 5, 'analyzed': 3}
    errors: List[str]
    total_tokens_used: int
```

## 📁 File Structure & Module Design

### Core Modules (Production-Ready)

```
src/
├── agent.py              # Main LangGraph workflow definition
├── tools.py              # Web scraping and analysis tools
├── models.py             # Pydantic models and state definitions
├── web_scraper.py        # Async web scraping utilities
├── report_generator.py   # PDF/Markdown report generation
├── email_service.py      # SMTP email functionality
├── settings.py           # Configuration management with pydantic-settings
├── web_interface.py      # FastAPI application
└── utils/
    ├── __init__.py
    ├── validators.py     # URL and email validation
    ├── cache.py         # In-memory caching for responses
    └── logger.py        # Structured logging
```

### Testing Structure

```
tests/
├── test_agent.py              # LangGraph workflow tests with mocks
├── test_web_scraper.py        # Web scraping with mock responses
├── test_report_generator.py   # Report generation validation
├── test_email_service.py      # SMTP mocking and email tests
├── test_models.py             # Pydantic model validation
├── test_web_interface.py      # FastAPI route testing
└── fixtures/
    ├── sample_articles.json   # Mock article data
    ├── sample_blogs/
    │   ├── wordpress_html.html
    │   ├── medium_html.html
    │   └── rss_feed.xml
    └── email_test_data.py
```

## 🔧 Implementation Blueprint

### Phase 1: Core Infrastructure (Priority 1)

#### Task 1.1: Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

#### Task 1.2: Settings Module
```python
# src/settings.py - Production-ready configuration
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os

class Settings(BaseSettings):
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    # LLM Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for content analysis")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    max_tokens_per_article: int = Field(default=2000, description="Max tokens for summarization")
    
    # SMTP Configuration
    smtp_server: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    email_username: str
    email_password: str
    email_from_name: str = Field(default="Industry News Agent")
    
    # Web Scraping
    request_delay: float = Field(default=2.0, description="Delay between requests (seconds)")
    max_concurrent_requests: int = Field(default=5, description="Max concurrent HTTP requests")
    user_agents: List[str] = Field(
        default = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
        ]
    )
    
    # Cache
    cache_ttl_minutes: int = Field(default=360, description="Cache TTL in minutes")
    
    # Reporting
    output_dir: str = Field(default="reports", description="Report output directory")
    max_report_size_mb: int = Field(default=10, description="Maximum report size in MB")
```

#### Task 1.3: Web Scraper Implementation
```python
# src/web_scraper.py - Async web scraping with rate limiting
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Optional
import time
import random
from urllib.parse import urlparse
import feedparser

class AsyncWebScraper:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": random.choice(self.settings.user_agents)}
        )
        return self
    
    async def scrape_blog_articles(self, url: str, max_articles: int = 10) -> List[Article]:
        """Detect platform and scrape articles accordingly"""
        delay = self.settings.request_delay * random.uniform(0.8, 1.2)
        await asyncio.sleep(delay)
        
        # Platform detection logic
        if "medium.com" in url.lower():
            return await self._scrape_medium(url, max_articles)
        elif any(rss_path in url.lower() for rss_path in ["/rss", "/feed", ".xml"]):
            return await self._scrape_rss(url, max_articles)
        else:
            return await self._scrape_generic_blog(url, max_articles)
    
    async def _scrape_medium(self, url: str, max_articles: int) -> List[Article]:
        """Medium.com specific scraping with beautiful soup"""
        # Implementation with async behavior
        pass
        
    async def _scrape_generic_blog(self, url: str, max_articles: int) -> List[Article]:
        """Generic blog scraping with article detection"""
        # Detect WordPress, custom CMS, etc.
        pass
```

### Phase 2: LangGraph Agent Implementation

#### Task 2.1: State Management
```python
# src/models.py - Complete state and model definitions
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Optional, Any

class WebScrapeConfig(BaseModel):
    max_articles_per_blog: int = Field(default=5, ge=1, le=50)
    min_word_count: int = Field(default=100, ge=10)
    include_images: bool = Field(default=False)
    
class AnalysisConfig(BaseModel):
    summary_length: str = Field(default="medium", pattern="^(short|medium|verbose)$")
    extract_quotes: bool = Field(default=True)
    trend_analysis: bool = Field(default=True)

class ProcessingState(TypedDict, total=False):
    """Detailed LangGraph workflow state with provenance tracking"""
    # Input
    raw_urls: List[str]
    validated_urls: List[str]
    processing_config: Dict[str, Any]
    
    # Processing
    scraping_results: List[Dict[str, Any]]
    analysis_results: List[Dict[str, Any]]
    error_log: List[Dict[str, str]]
    
    # Outputs
    reports_generated: List[str]
    emails_sent: List[str]
    final_status: Dict[str, Any]
```

#### Task 2.2: LangGraph Agent Definition
```python
# src/agent.py - Production LangGraph agent
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import asyncio

class IndustryNewsAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.graph = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """Define the complete LangGraph workflow"""
        
        def validate_urls(state: ProcessingState) -> ProcessingState:
            # URL validation and deduplication
            pass
            
        def scrape_articles(state: ProcessingState) -> ProcessingState:
            # Async web scraping with progress updates
            pass
            
        def analyze_content(state: ProcessingState) -> ProcessingState:
            # AI-powered content analysis
            pass
            
        def generate_reports(state: ProcessingState) -> ProcessingState:
            # Report generation in multiple formats
            pass
            
        def deliver_reports(state: ProcessingState) -> ProcessingState:
            # Email delivery with retry logic
            pass
            
        workflow = StateGraph(ProcessingState)
        
        # Add nodes with proper async handling
        workflow.add_node("validate", validate_urls)
        workflow.add_node("scrape", scrape_articles)
        workflow.add_node("analyze", analyze_content)
        workflow.add_node("report", generate_reports)
        workflow.add_node("deliver", deliver_reports)
        
        # Add conditional edges for error handling
        workflow.add_edge("validate", "scrape")
        workflow.add_edge("scrape", "analyze")
        workflow.add_edge("analyze", "report")
        workflow.add_edge("report", "deliver")
        workflow.add_edge("deliver", END)
        
        workflow.set_entry_point("validate")
        return workflow.compile()
```

### Phase 3: Report Generation

#### Task 3.1: Markdown & PDF Generation
```python
# src/report_generator.py - Professional report generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import markdown

class ReportGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings
        
    def generate_markdown_report(self, articles: List[Article], filename: str) -> str:
        """Generate comprehensive Markdown report"""
        template = """# Weekly Industry News Report
        
## Executive Summary
{executive_summary}

## Company Analysis
{company_sections}

## Industry Trends
{trend_analysis}

## Key Insights
{key_insights}

## Detailed Articles
{detailed_articles}
        """
        
    def generate_pdf_report(self, articles: List[Article], filename: str) -> str:
        """Generate professional PDF report with styling"""
        # ReportLab implementation with custom styling
        pass
```

### Phase 4: Web Interface Implementation

#### Task 4.1: FastAPI Application
```python
# src/web_interface.py - Production FastAPI application
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio
from typing import List

app = FastAPI(title="Industry News Agent API")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/generate-report")
async def generate_report(
    urls: List[str] = Form(...),
    email: str = Form(...),
    max_articles: int = Form(default=5)
):
    """Endpoint for report generation with validation"""
    # URL and email validation
    # Async task submission
    # Response with task ID for polling
    pass

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Real-time progress tracking"""
    # Task monitoring with Redis or in-memory storage
    pass
```

#### Task 4.2: Email Service Integration
```python
# src/email_service.py - Production email service
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import jinja2

class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates')
        )
        
    async def send_report_email(self, to_email: str, report_paths: List[str]) -> bool:
        """Send report with attachments and retry logic"""
        try:
            # Initialize SMTP connection
            smtp = aiosmtplib.SMTP(
                hostname=self.settings.smtp_server,
                port=self.settings.smtp_port,
                use_tls=True
            )
            
            async with smtp:
                await smtp.starttls()
                await smtp.login(
                    self.settings.email_username,
                    self.settings.email_password
                )
                
                # Build email with attachments
                message = await self._build_email_message(
                    to_email, report_paths
                )
                
                await smtp.send_message(message)
                return True
                
        except Exception as e:
            # Retry logic with exponential backoff
            return False
```

## ✅ Validation Gates (Production Ready)

### Gate 1: Syntax and Style Validation
```bash
#!/bin/bash
# Before running any tests, ensure code quality

# Code formatting and linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

### Gate 2: Unit Testing Suite
```bash
# Comprehensive test suite execution
pytest tests/ -v --cov=src --cov-report=html
pytest tests/test_agent.py -v -k "test_workflow_execution"
pytest tests/test_web_scraper.py -v -k "test_rate_limiting"
pytest tests/test_report_generator.py -v -k "test_pdf_generation"
pytest tests/test_email_service.py -v -k "test_smtp_integration"
```

### Gate 3: Integration Testing
```bash
#!/bin/bash
# Integration testing with external services

# Test web interface locally
uvicorn src.web_interface:app --reload --port 8001 &
sleep 3
curl -X POST http://localhost:8001/generate-report \
  -F "urls[]=https://blog.openai.com" \
  -F "email=test@example.com" \
  -F "max_articles=2"
pkill -f uvicorn

# Test workflow execution
python -c "
from src.agent import create_agent
agent = create_agent()
result = agent.invoke({
    'urls': ['https://blog.openai.com'],
    'email': 'test@example.com',
    'max_articles': 1
})
print(f'Workflow completed: {result[\"final_status\"]}')
"
```

### Gate 4: Performance Testing
```bash
#!/bin/bash
# Performance validation

# Memory usage testing
python -c "
import psutil, time
from src.agent import create_agent
import asyncio

process = psutil.Process()
start_memory = process.memory_info().rss / 1024 / 1024  # MB

async def test_performance():
    agent = create_agent()
    await agent.ainvoke({
        'urls': ['https://blog.openai.com'] * 10,
        'email': 'test@example.com' * 10,
        'max_articles': 5
    })

asyncio.run(test_performance())
end_memory = process.memory_info().rss / 1024 / 1024  # MB
print(f'Memory usage: {end_memory - start_memory:.1f} MB')
"

# Rate limiting validation
time python -c "
import asyncio
from src.web_scraper import AsyncWebScraper
from src.settings import load_settings

async def test_rate_limiting():
    settings = load_settings()
    async with AsyncWebScraper(settings) as scraper:
        await asyncio.gather(*[
            scraper.scrape_blog_articles('https://medium.com/example', 1)
            for _ in range(5)
        ])

asyncio.run(test_rate_limiting())
"
```

## ⚡ Error Handling & Resilience Patterns

### Web Scraping Resilience
```python
class ResilientWebScraper:
    def __init__(self, max_retries=3, backoff_factor=2):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def fetch_with_retry(self, url: str) -> str:
        # httpx with exponential backoff
        pass
```

### LLM Error Recovery
```python
class LLMErrorHandler:
    def __init__(self, primary_model: str, fallback_models: List[str]):
        self.current_model = primary_model
        self.fallback_models = fallback_models
    
    async def analyze_with_fallback(self, content: str) -> dict:
        try:
            return await self._openai_analyze(content, self.current_model)
        except Exception as e:
            for fallback_model in self.fallback_models:
                try:
                    self.current_model = fallback_model
                    return await self._openai_analyze(content, fallback_model)
                except Exception:
                    continue
            raise AggregationError("All LLM models failed")
```

## 📊 Monitoring & Logging

### Structured Logging
```python
import structlog
from datetime import datetime

logger = structlog.get_logger()

class WorkflowLogger:
    def log_workflow_start(self, urls: List[str], email: str):
        logger.info(
            "workflow_started",
            urls_count=len(urls),
            recipient=email,
            timestamp=datetime.utcnow()
        )
    
    def log_scraping_result(self, url: str, articles: int, duration: float):
        logger.info(
            "blog_scraped",
            url=url,
            articles_found=articles,
            duration_seconds=duration
        )
```

## 🗓️ Implementation Timeline

### Week 1: Foundation
- [ ] Create virtual environment and install dependencies
- [ ] Implement settings.py with pydantic-settings
- [ ] Create AsyncWebScraper with rate limiting
- [ ] Write comprehensive tests for web scraping

### Week 2: LangGraph & AI Integration
- [ ] Implement ProcessingState typedict
- [ ] Create LangGraph workflow structure
- [ ] Integrate OpenAI for content analysis
- [ ] Add error handling and retry logic

### Week 3: Report Generation & Email
- [ ] Implement ReportGenerator with PDF/Markdown
- [ ] Create EmailService with SMTP integration
- [ ] Add email templates with Jinja2
- [ ] Implement attachment handling

### Week 4: Web Interface & Testing
- [ ] Create FastAPI application
- [ ] Add form handling and validation
- [ ] Implement progress tracking
- [ ] Complete integration testing

### Week 5: Production Hardening
- [ ] Performance optimization
- [ ] Security review
- [ ] Comprehensive testing
- [ ] Deployment preparation

## 🎯 Success Criteria & Metrics

### Functional Metrics
- ✅ Successfully process 50+ blog URLs concurrently
- ✅ Generate 10MB+ reports with images
- ✅ 99.9% email delivery rate to valid addresses
- ✅ Sub-1-minute report generation for 10 articles

### Performance Metrics
- ⏱️ Under 256MB RAM usage for 10 URL processing
- 🔄 0-2% error rate for web scraping operations
- 📧 Sub-5-second email delivery
- 📊 Sub-30-second total workflow time for 5 URLs

### Security Metrics
- 🔒 All API keys encrypted in transit and at rest
- 🛡️ No hardcoded credentials
- ✅ Input validation preventing injection attacks
- 📝 Complete audit trail for all operations

## 🔍 Quality Assurance Checklist

**Pre-deployment Checklist:**
- [ ] All environment variables documented
- [ ] Rate limiting tested with real-world scenarios
- [ ] Email delivery tested with multiple providers
- [ ] PDF generation tested with large content
- [ ] Error handling tested for all failure modes
- [ ] Performance benchmarks documented
- [ ] Security scan passed (bandit -r src/)
- [ ] Documentation complete and updated
- [ ] Docker container tested (if applicable)
- [ ] Deployment scripts validated

**Confidence Score: 9.5/10** - This PRP provides comprehensive implementation guidance with production-ready patterns, extensive testing, and monitoring capabilities.

## 📚 Additional Resources

### External Documentation Links
- LangGraph Concepts: https://langchain-ai.github.io/langgraph/concepts/
- Python asyncio best practices: https://docs.python.org/3/library/asyncio.html
- ReportLab documentation: https://docs.reportlab.com/reportlab/userguide/ch1_intro/
- FastAPI async testing: https://fastapi.tiangolo.com/tutorial/dependencies/testing/

### Code Examples Repository
- Sample blog data: https://github.com/python-feedparser/feedparser
- Test URLs provided in tests/fixtures/
- Mock OpenAI responses in tests/mocks/
- Sample reports for reference in examples/