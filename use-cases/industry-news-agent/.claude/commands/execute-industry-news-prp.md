# Execute Industry News Agent PRP

Implement an industry news agent using LangGraph and the PRP file.

## PRP File: $ARGUMENTS

## Execution Process

1. **Load PRP**
   - Read the specified industry news agent PRP file
   - Understand all agent requirements and research findings
   - Follow all instructions in the PRP and extend research if needed
   - Review LangGraph patterns for implementation guidance
   - Do more web searches and LangGraph documentation review as needed

2. **ULTRATHINK**
   - Think hard before executing the agent implementation plan
   - Break down agent development into smaller steps using your todos tools  
   - Use the TodoWrite tool to create and track your agent implementation plan
   - Follow LangGraph patterns for configuration and structure
   - Plan agent.py, tools.py, models.py, web_interface.py, and testing approach

3. **Execute the plan**
   - Implement the LangGraph agent following the PRP
   - Create agent with environment-based configuration (settings.py, providers.py)
   - Use TypedDict for state management and workflow orchestration
   - Implement tools with @tool decorators and proper error handling
   - Add comprehensive testing with web scraping mocks and email service tests

4. **Validate**
   - Test agent import and instantiation
   - Run LangGraph workflow validation for rapid development testing
   - Test tool registration and functionality
   - Test web scraping with mock responses
   - Test email service with test SMTP server
   - Run pytest test suite if created
   - Verify agent follows LangGraph patterns

5. **Complete**
   - Ensure all PRP checklist items done
   - Test agent with example blog URLs
   - Verify security patterns (environment variables, error handling, rate limiting)
   - Test web interface functionality
   - Test email delivery with attachments
   - Report completion status
   - Read the PRP again to ensure complete implementation

6. **Reference the PRP**
   - You can always reference the PRP again if needed

## Industry News Agent-Specific Patterns to Follow

- **LangGraph Workflow**: Use TypedDict for state management and clear node transitions
- **Web Scraping**: Implement rate limiting, user agent rotation, and error handling
- **AI Integration**: Use OpenAI for content summarization and trend analysis
- **Report Generation**: Create both Markdown and PDF formats with professional templates
- **Email Service**: Implement SMTP integration with file attachments
- **Web Interface**: Use FastAPI for user-friendly form handling
- **Testing**: Include web scraping mocks, email service tests, and workflow validation

## Key Components to Implement

### LangGraph Agent Structure
- `agent.py`: Main workflow definition with state management
- `tools.py`: Web scraping, AI analysis, and report generation tools
- `models.py`: Pydantic models for data validation and state management
- `web_interface.py`: FastAPI application with form handling
- `email_service.py`: SMTP email sending with attachments
- `report_generator.py`: Markdown and PDF report generation

### Critical Features
- **State Management**: TypedDict for workflow state tracking
- **Web Scraping**: Rate limiting, error handling, content parsing
- **AI Analysis**: Content summarization and trend analysis
- **Report Generation**: Professional formatting in multiple formats
- **Email Delivery**: Secure SMTP with file attachments
- **Web Interface**: User-friendly form for URL input

Note: If validation fails, use error patterns in PRP to fix and retry. Follow LangGraph best practices for workflow orchestration and state management. 