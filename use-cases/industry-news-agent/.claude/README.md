# Industry News Agent - Claude Commands

This directory contains Claude commands for the Industry News Agent development workflow.

## Available Commands

### `/generate-industry-news-prp INITIAL.md`
Generates a comprehensive Product Requirements Prompt (PRP) for industry news agent implementation. This command:

- Analyzes the INITIAL.md requirements
- Researches LangGraph patterns and best practices
- Investigates web scraping, AI analysis, and report generation techniques
- Creates a detailed implementation plan with validation gates
- Saves the PRP as `PRPs/{feature-name}.md`

### `/execute-industry-news-prp PRPs/filename.md`
Executes the implementation plan defined in the PRP. This command:

- Reads the specified PRP file
- Implements the LangGraph agent with proper state management
- Creates web scraping tools with rate limiting and error handling
- Integrates AI analysis for content summarization
- Builds report generation in Markdown and PDF formats
- Implements email service with SMTP integration
- Creates FastAPI web interface for user interaction
- Adds comprehensive testing for all components

## Usage Workflow

1. **Define Requirements**: Start with `INITIAL.md` containing your feature requirements
2. **Generate PRP**: Use `/generate-industry-news-prp INITIAL.md` to create implementation plan
3. **Execute Implementation**: Use `/execute-industry-news-prp PRPs/filename.md` to build the agent
4. **Validate**: Run tests and validate all components work correctly

## Key Features Supported

- **LangGraph Workflow**: State management with TypedDict
- **Web Scraping**: Rate limiting, error handling, content parsing
- **AI Analysis**: OpenAI integration for content summarization
- **Report Generation**: Markdown and PDF with professional templates
- **Email Service**: SMTP integration with file attachments
- **Web Interface**: FastAPI application with form handling
- **Testing**: Comprehensive unit and integration tests

## Development Guidelines

- Follow patterns established in `CLAUDE.md`
- Use LangGraph for workflow orchestration
- Implement proper error handling for all external services
- Add unit tests for all new functionality
- Document all code changes
- Use environment variables for configuration 