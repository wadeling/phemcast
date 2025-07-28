# Industry News Agent PRP Template

## 🎯 Project Overview

This PRP (Product Requirements Prompt) defines the implementation plan for a Weekly Industry News Aggregation Agent using LangGraph. The agent will crawl company blogs, analyze content using AI, generate reports, and deliver them via email.

## 📋 Core Requirements

### 1. Web Scraping & Content Extraction
- **Multi-blog crawling**: Support for multiple company blog URLs
- **Rate limiting**: Configurable delays to avoid being blocked
- **Error handling**: Robust error handling for network failures
- **Content parsing**: Extract article titles, content, dates, and metadata
- **Platform support**: WordPress, Medium, custom CMS, RSS feeds

### 2. AI-Powered Content Analysis
- **Content summarization**: Generate concise summaries of articles
- **Trend analysis**: Identify industry trends and patterns
- **Key insights extraction**: Extract important takeaways
- **Content categorization**: Categorize articles by topic/theme

### 3. Report Generation
- **Multi-format output**: Markdown and PDF formats
- **Structured content**: Executive summary, company analysis, trends
- **Professional formatting**: Clean, readable report layout
- **Customizable templates**: Configurable report templates

### 4. Web Interface
- **User-friendly form**: Multi-line URL input
- **Email integration**: Email address input and validation
- **Progress tracking**: Real-time progress updates
- **File upload support**: Upload URL lists as files

### 5. Email Delivery
- **SMTP integration**: Secure email sending
- **File attachments**: PDF and Markdown report attachments
- **HTML email templates**: Professional email formatting
- **Error handling**: Retry logic for failed sends

### 6. LangGraph Workflow
- **State management**: TypedDict for workflow state
- **Node transitions**: Clear workflow progression
- **Error recovery**: Graceful error handling
- **Async processing**: Non-blocking operations

## 🏗️ Technical Architecture

### LangGraph Workflow Design
```
URL Input → Validation → Scraping → Analysis → Report Generation → Email Delivery
```

### State Management
```python
class AgentState(TypedDict):
    urls: List[str]
    articles: List[Article]
    summaries: List[Summary]
    report_path: str
    email_sent: bool
    errors: List[str]
```

### Component Structure
- `agent.py`: Main LangGraph agent with workflow definition
- `tools.py`: Web scraping, analysis, and report generation tools
- `models.py`: Pydantic models for data validation
- `web_interface.py`: FastAPI web application
- `email_service.py`: Email sending functionality
- `report_generator.py`: Report generation utilities

## 🔧 Implementation Plan

### Phase 1: Core Infrastructure
1. **Environment Setup**
   - Virtual environment creation
   - Dependency installation
   - Environment variable configuration

2. **Basic LangGraph Agent**
   - State definition with TypedDict
   - Basic workflow nodes
   - Tool integration patterns

3. **Web Scraping Foundation**
   - HTTP client with rate limiting
   - Content parsing utilities
   - Error handling patterns

### Phase 2: Content Processing
1. **AI Integration**
   - OpenAI API integration
   - Content summarization tools
   - Trend analysis algorithms

2. **Report Generation**
   - Markdown template system
   - PDF generation with ReportLab
   - Report formatting utilities

### Phase 3: User Interface
1. **Web Application**
   - FastAPI application setup
   - Form handling and validation
   - File upload functionality

2. **Email Service**
   - SMTP configuration
   - Email template system
   - File attachment handling

### Phase 4: Testing & Optimization
1. **Unit Testing**
   - Component-level tests
   - Mock responses for web scraping
   - Email service testing

2. **Integration Testing**
   - End-to-end workflow testing
   - Performance optimization
   - Error scenario testing

## 🧪 Testing Strategy

### Unit Tests
- **Web scraping**: Mock HTTP responses, error scenarios
- **AI analysis**: Mock OpenAI responses, content validation
- **Report generation**: Template rendering, format validation
- **Email service**: SMTP mocking, attachment testing

### Integration Tests
- **Complete workflow**: End-to-end report generation
- **Error handling**: Network failures, API limits
- **Performance**: Large URL lists, multiple blogs

### Test Data
- Sample blog URLs for different platforms
- Mock article content and metadata
- Test email configurations

## 📚 Documentation Requirements

### Code Documentation
- **Function docstrings**: Google style for all functions
- **Class documentation**: Comprehensive class descriptions
- **Workflow documentation**: LangGraph node explanations
- **Configuration guide**: Environment setup instructions

### User Documentation
- **Installation guide**: Step-by-step setup instructions
- **Usage examples**: Command-line and web interface usage
- **Configuration reference**: All environment variables
- **Troubleshooting guide**: Common issues and solutions

## 🔒 Security & Best Practices

### Security Considerations
- **API key management**: Secure environment variable handling
- **Email security**: SMTP authentication and encryption
- **Input validation**: URL and email validation
- **Rate limiting**: Respectful web scraping practices

### Performance Optimization
- **Async processing**: Non-blocking operations
- **Caching**: Avoid re-processing articles
- **Batch processing**: Efficient handling of multiple URLs
- **Memory management**: Large report handling

## 📊 Success Metrics

### Functional Requirements
- ✅ Successfully scrape articles from multiple blog platforms
- ✅ Generate accurate AI summaries and analysis
- ✅ Create professional reports in multiple formats
- ✅ Deliver reports via email with attachments
- ✅ Handle errors gracefully with proper logging

### Performance Requirements
- ⏱️ Process 10+ blog URLs within 30 minutes
- 📧 Email delivery within 5 minutes of report generation
- 💾 Memory usage under 1GB for large reports
- 🔄 Support concurrent processing of multiple requests

## 🚀 Deployment Considerations

### Environment Setup
- **Production server**: FastAPI with uvicorn
- **Background tasks**: Celery or asyncio for long-running tasks
- **Database**: Optional SQLite for caching and state persistence
- **Monitoring**: Logging and health check endpoints

### Scalability
- **Horizontal scaling**: Multiple worker processes
- **Queue management**: Background task queues
- **Resource monitoring**: Memory and CPU usage tracking
- **Error tracking**: Comprehensive error logging

## 📝 Next Steps

1. **Review and validate** this PRP with stakeholders
2. **Set up development environment** with all dependencies
3. **Implement Phase 1** components with basic functionality
4. **Add comprehensive testing** for each component
5. **Iterate and refine** based on testing results
6. **Deploy and monitor** in production environment 