# Industry News Aggregation Agent

A comprehensive AI-powered system that automatically crawls company blogs, analyzes content, and generates weekly industry reports using LangGraph for workflow orchestration.

## 🚀 Features

- **Intelligent Web Scraping**: Crawls multiple company blog URLs with rate limiting and error handling
- **AI-Powered Content Analysis**: Uses OpenAI to summarize and analyze article content
- **Multi-Format Report Generation**: Creates reports in both Markdown and PDF formats
- **Web Interface**: User-friendly web application for inputting blog URLs and email addresses
- **Email Delivery**: Automatically sends generated reports to specified email addresses
- **Multiple Email Services**: Supports both Tencent Cloud SES and traditional SMTP
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

# Email Configuration - Choose one option:

# Option 1: Tencent Cloud SES (Recommended)
TENCENT_CLOUD_SECRET_ID=your_tencent_cloud_secret_id
TENCENT_CLOUD_SECRET_KEY=your_tencent_cloud_secret_key
TENCENT_CLOUD_REGION=ap-guangzhou
TENCENT_FROM_EMAIL=your_verified_email@yourdomain.com

# Option 2: Traditional SMTP
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

### Email Service Configuration

The system automatically detects and uses the best available email service:

1. **Tencent Cloud SES** (Recommended): More reliable, secure, and cost-effective
   - Set `TENCENT_CLOUD_SECRET_ID` and `TENCENT_CLOUD_SECRET_KEY`
   - Configure `TENCENT_FROM_EMAIL` with your verified sender address
   - Choose `TENCENT_CLOUD_REGION` based on your location (default: ap-guangzhou)
   - **Template Support**: Set `TENCENT_TEMPLATE_ID` for template-based emails
   - **Content Mode**: Set `TENCENT_USE_TEMPLATE=false` for direct HTML/text content
   - See [Tencent Cloud Setup Guide](TENCENT_CLOUD_SETUP.md) for detailed instructions

2. **SMTP Fallback**: Traditional email service
   - Set SMTP server details and credentials
   - Used when Tencent Cloud SES is not configured

**Tencent Cloud Email Modes:**
- **Template Mode** (Default): Uses pre-configured email templates with dynamic content
- **Direct Content Mode**: Sends custom HTML and text content directly

**Region Selection Tips:**
- `ap-guangzhou` (Guangzhou): Recommended for Mainland China users
- `ap-hongkong` (Hong Kong): Good for Hong Kong/Taiwan users
- `ap-singapore` (Singapore): Good for Southeast Asia users
- `eu-frankfurt` (Frankfurt): Good for European users
- `na-ashburn` (Virginia): Good for US East Coast users

For detailed Tencent Cloud SES setup instructions, see [TENCENT_CLOUD_SETUP.md](TENCENT_CLOUD_SETUP.md).

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

### Quick Setup

1. **Run the setup script:**
   ```bash
   python setup_tencent_email.py
   ```

2. **Get help with region selection:**
   ```bash
   python select_region.py
   ```

3. **Validate your configuration:**
   ```bash
   python validate_email_config.py
   ```

4. **Test the email service:**
   ```bash
   python test_tencent_email.py
   ```

5. **Start the web interface:**
   ```bash
   python -m src.web_interface
   ```

### Logging Configuration

The application includes advanced logging with file line numbers and function names:

```bash
# Test logging configuration
python test_logging.py

# Configure logging in .env file
LOG_LEVEL=DEBUG                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log             # Optional: log to file
SHOW_FILE_LINE=true               # Show file:line in logs
SHOW_FUNCTION=true                # Show function name in logs
```

**Log Format Examples:**
- **Full format**: `2024-01-15 10:30:45 - module_name - INFO - filename.py:123 - function_name - Message`
- **File line only**: `2024-01-15 10:30:45 - module_name - INFO - filename.py:123 - Message`
- **Simple format**: `2024-01-15 10:30:45 - module_name - INFO - Message`

### Configuration Migration

If you have an existing configuration with the old format, you can migrate it:

```bash
# 迁移旧格式配置到新格式
python migrate_config.py
```

**Old format:** `TENCENTCLOUD_SECRET_ID`, `TENCENTCLOUD_SECRET_KEY`  
**New format:** `TENCENT_CLOUD_SECRET_ID`, `TENCENT_CLOUD_SECRET_KEY`

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