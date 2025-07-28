## FEATURE:

Weekly Industry News Aggregation Agent using LangGraph

A comprehensive agent system that:
1. Crawls latest articles from specified company blog URLs
2. Extracts and summarizes article content using AI
3. Generates weekly reports in Markdown and PDF formats
4. Provides a web interface for users to input company blog URLs (multi-line support)
5. Sends generated reports to user-specified email addresses
6. Uses LangGraph for workflow orchestration and state management

## EXAMPLES:

In the `examples/` folder, there will be:
- `examples/basic_agent/` - Simple LangGraph agent with web scraping and summarization
- `examples/web_interface/` - FastAPI web application with form handling
- `examples/email_service/` - Email sending functionality with report attachments
- `examples/report_generator/` - Markdown and PDF report generation

Use these examples to understand:
- LangGraph workflow patterns and state management
- Web scraping with proper error handling and rate limiting
- AI-powered content summarization and analysis
- Web interface development with FastAPI
- Email service integration with file attachments
- Report generation in multiple formats

## DOCUMENTATION:

- LangGraph documentation: https://langchain-ai.github.io/langgraph/concepts/why-langgraph/
- LangChain documentation: https://python.langchain.com/
- FastAPI documentation: https://fastapi.tiangolo.com/
- BeautifulSoup documentation: https://www.crummy.com/software/BeautifulSoup/
- ReportLab documentation: https://www.reportlab.com/docs/reportlab-userguide.pdf

## OTHER CONSIDERATIONS:

- Include proper rate limiting for web scraping to avoid being blocked
- Implement robust error handling for network failures and parsing errors
- Use async/await patterns for better performance with multiple blog scraping
- Include content deduplication to avoid processing the same articles multiple times
- Implement proper logging for debugging and monitoring
- Use environment variables for API keys and configuration
- Include comprehensive unit tests for all components
- Consider implementing a database to store processed articles and avoid re-processing
- Add support for different blog platforms (WordPress, Medium, custom CMS)
- Include content filtering to focus on relevant industry topics
- Implement proper email formatting with HTML and plain text alternatives
- Consider adding user authentication for the web interface
- Include progress tracking for long-running report generation tasks 