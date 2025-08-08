# Industry News Aggregation Agent

A comprehensive AI-powered system that automatically crawls company blogs, analyzes content, and generates weekly industry reports using LangGraph for workflow orchestration.

## 🚀 Features

- **Intelligent Web Scraping**: Crawls multiple company blog URLs with rate limiting and error handling
- **AI-Powered Content Analysis**: Uses OpenAI to summarize and analyze article content
- **Multi-Format Report Generation**: Creates reports in both Markdown and PDF formats
- **Web Interface**: User-friendly web application for inputting blog URLs and email addresses
- **Email Delivery**: Automatically sends generated reports to specified email addresses
- **LangGraph Workflow**: Robust state management and workflow orchestration

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- SMTP email credentials
- Virtual environment (recommended)

## 🛠️ Installation

1. **Clone the repository and navigate to the project:**
   ```bash
   cd use-cases/industry-news-agent
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and email settings
   ```

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: for OpenAI-compatible endpoints

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Web Scraping Configuration
REQUEST_DELAY=1.0
MAX_RETRIES=3
TIMEOUT=30

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

## 🏗️ Project Structure

```
industry-news-agent/
├── src/
│   ├── agent.py              # Main LangGraph agent definition
│   ├── tools.py              # Web scraping and analysis tools
│   ├── models.py             # Pydantic models and state management
│   ├── web_interface.py      # FastAPI web application
│   ├── email_service.py      # Email sending functionality
│   └── report_generator.py   # Report generation (Markdown/PDF)
├── examples/
│   ├── basic_agent/          # Simple LangGraph agent example
│   ├── web_interface/        # FastAPI web app example
│   ├── email_service/        # Email service example
│   └── report_generator/     # Report generation example
├── tests/
│   ├── unit/                 # Unit tests for each component
│   └── integration/          # Integration tests
├── PRPs/                     # Product Requirements Prompts
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🚀 Usage

### Web Interface

1. **Start the web server:**
   ```bash
   python -m src.web_interface
   ```

2. **Open your browser** and navigate to `http://localhost:8000`

3. **Enter company blog URLs** (one per line) and your email address

4. **Submit the form** to start the report generation process

### Command Line Interface

```bash
# Generate a report for specific URLs
python -m src.cli --urls "https://blog.company1.com,https://blog.company2.com" --email user@example.com

# Generate a report from a file containing URLs
python -m src.cli --url-file urls.txt --email user@example.com
```

## 🔄 LangGraph Workflow

The agent uses LangGraph for workflow orchestration with the following nodes:

1. **URL Validation**: Validates and normalizes blog URLs
2. **Content Scraping**: Crawls articles from each blog with rate limiting
3. **Content Analysis**: Uses AI to summarize and analyze articles
4. **Report Generation**: Creates Markdown and PDF reports
5. **Email Delivery**: Sends reports to specified email addresses

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src
```

## 📊 Supported Blog Platforms

- **WordPress**: Standard WordPress blogs with RSS feeds
- **Medium**: Medium publications and personal blogs
- **Custom CMS**: Generic HTML parsing for custom platforms
- **RSS Feeds**: Direct RSS feed processing

## 🔒 Security & Best Practices

- **Rate Limiting**: Configurable delays between requests to avoid being blocked
- **User Agent Rotation**: Rotates user agents to avoid detection
- **Error Handling**: Robust error handling for network failures and parsing errors
- **Content Deduplication**: Avoids processing the same articles multiple times
- **Environment Variables**: Secure configuration management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Rate Limiting**: If you're getting blocked, increase the `REQUEST_DELAY` in your `.env` file
2. **Email Issues**: Make sure to use an app password for Gmail, not your regular password
3. **API Limits**: Monitor your OpenAI API usage to avoid hitting rate limits
4. **Memory Issues**: For large reports, consider processing URLs in batches

### Getting Help

- Check the logs for detailed error messages
- Verify your environment variables are set correctly
- Test individual components using the examples in the `examples/` directory 