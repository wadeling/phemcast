# PHEMCAST 

> **AI-Powered Industry Voice Aggregation & Podcast Generation Platform**

PHEMCAST is an intelligent system that automatically aggregates enterprise "public voices" (blogs) and "summons" them into compelling podcast narratives. The name combines ancient Greek roots: **Φήμη (Phēmē)** - "public voice, reputation" and **κᾰλέω (Kaleō)** - "to call, summon, gather", representing AI's ability to automatically collect information and summon audiences through voice.

## 🎯 Core Concept

- **Φήμη (Phēmē)**: "What is spoken" → "reputation, public voice" (perfectly matches enterprise blogs' public information and podcast voice transmission)
- **κᾰλέω (Kaleō)**: "to call, summon, gather" (symbolizes AI automatically "summoning" information and "calling" audiences)
- **Meaning**: AI system automatically aggregates enterprise "public voices" (blogs) and "summons" them into new podcast formats for dissemination, emphasizing information aggregation and voice summoning

## 🚀 Key Features

### 🎙️ **Voice-First Design**
- **AI-Generated Podcasts**: Automatically converts industry reports into engaging audio content
- **Voice Cloning Technology**: Supports custom voice synthesis for personalized podcast experiences
- **Multi-Format Audio**: Generates MP3, WAV, and other audio formats
- **Real-time Audio Streaming**: WebSocket-based audio delivery for instant playback

### 🧠 **Intelligent Content Processing**
- **Advanced Web Scraping**: Crawls multiple company blogs with intelligent rate limiting
- **AI-Powered Analysis**: Uses state-of-the-art language models for content summarization
- **Multi-Language Support**: Processes content in multiple languages with translation
- **Content Deduplication**: Smart filtering to avoid repetitive content

### 📊 **Comprehensive Reporting**
- **Multi-Format Reports**: Generates Markdown, PDF, and audio reports
- **Interactive Web Interface**: Modern, responsive UI for content management
- **Real-time Task Monitoring**: Live task status updates via WebSocket
- **Scheduled Automation**: Automated report generation and delivery

### 🔄 **Robust Architecture**
- **LangGraph Workflow**: Advanced workflow orchestration with state management
- **Async-First Design**: Non-blocking architecture for high performance
- **Database Integration**: Persistent storage for task history and user management
- **Email Integration**: Multi-provider email delivery (Tencent Cloud SES, SMTP)

## 🏗️ Project Structure

```
phemcast/
├── src/                          # Core application code
│   ├── agent.py                  # LangGraph workflow orchestration
│   ├── tools.py                  # AI content analysis tools
│   ├── web_interface.py          # FastAPI web application
│   ├── tts_service.py            # Text-to-Speech & voice synthesis
│   ├── report_generator.py       # Multi-format report generation
│   ├── web_scraper.py            # Intelligent web scraping
│   ├── email_service.py          # Email delivery service
│   ├── database.py               # Database connection management
│   ├── db_models.py              # SQLAlchemy data models
│   ├── task_processor.py         # Background task processing
│   ├── session_manager.py        # User session management
│   ├── wechat_auth.py            # WeChat authentication
│   ├── settings.py               # Configuration management
│   └── util/
│       ├── voice_clone.py        # Voice cloning utilities
│       └── README_voice_clone.md # Voice cloning documentation
├── html/                         # Frontend web interface
│   ├── index.html                # Main web application
│   ├── static/
│   │   ├── css/style.css         # Styling and responsive design
│   │   └── js/app.js             # Frontend JavaScript logic
│   └── nginx.conf                # Nginx configuration
├── build/                        # Docker build configurations
│   ├── backend/Dockerfile        # Backend container setup
│   ├── frontend/Dockerfile       # Frontend container setup
│   └── requirements.txt          # Python dependencies
├── deploy/                       # Deployment configurations
│   ├── docker-compose.yml        # Multi-container orchestration
│   ├── deploy.sh                 # Deployment script
│   └── mysql/init/               # Database initialization
├── tests/                        # Test suite
│   ├── conftest.py               # Test configuration
│   ├── test_models.py            # Model tests
│   ├── test_settings.py          # Settings tests
│   └── test_web_interface.py     # Web interface tests
├── requirements.txt              # Python dependencies
├── prompt.txt                    # AI analysis prompts
├── audio_prompt.txt              # Voice generation prompts
└── README.md                     # This documentation
```

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.8+**
- **Docker & Docker Compose** (for containerized deployment)
- **OpenAI API Key** (for AI content analysis)
- **Email Service** (Tencent Cloud SES recommended)

### Quick Start

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd phemcast
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Using Docker (Recommended):**
   ```bash
   # Start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

4. **Using Python directly:**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start the application
   python src/main.py
   ```

### Configuration

Create a `.env` file with the following variables:

```env
# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=deepseek-reasoner
OPENAI_BASE_URL=https://api.deepseek.com/v1

# Voice Synthesis (Optional)
MINIMAXI_GROUP_ID=your_group_id
MINIMAXI_CLONE_API_KEY=your_api_key

# Email Configuration
TENCENT_CLOUD_SECRET_ID=your_tencent_secret_id
TENCENT_CLOUD_SECRET_KEY=your_tencent_secret_key
TENCENT_CLOUD_REGION=ap-guangzhou
TENCENT_FROM_EMAIL=your_verified_email@domain.com

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Database Configuration
DATABASE_URL=mysql://user:password@localhost:3306/phemcast

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

## 🎯 Usage

### Web Interface

1. **Access the application:**
   ```
   http://localhost:8000
   ```

2. **Submit content sources:**
   - Enter company blog URLs (one per line)
   - Specify email for report delivery
   - Set maximum articles per source

3. **Monitor progress:**
   - Real-time task status updates
   - Live progress indicators
   - Task history and management

4. **Access generated content:**
   - Download reports (PDF, Markdown)
   - Play generated audio podcasts
   - View task execution history

### API Endpoints

- `POST /api/generate-report-form` - Submit new content generation request
- `GET /api/task-status-list` - Get recent task status
- `GET /api/recent-tasks` - Get completed tasks with audio
- `GET /download/{task_id}/{format}` - Download generated content
- `GET /api/status` - System health check

## 🔄 Workflow Architecture

### LangGraph Processing Pipeline

1. **URL Validation** → Validates and normalizes input URLs
2. **Content Scraping** → Intelligently crawls articles with rate limiting
3. **AI Analysis** → Processes content using advanced language models
4. **Report Generation** → Creates multi-format reports (MD, PDF)
5. **Voice Synthesis** → Generates audio podcasts from content
6. **Email Delivery** → Sends reports and notifications

### Async-First Design

- **Non-blocking Architecture**: All operations run asynchronously
- **Concurrent Processing**: Multiple tasks can run simultaneously
- **Real-time Updates**: WebSocket-based status broadcasting
- **Scalable Performance**: Thread pool execution for CPU-intensive tasks

## 🎙️ Voice Features

### Text-to-Speech Capabilities

- **Multiple TTS Providers**: OpenAI, Tencent Cloud, and custom voice cloning
- **Voice Cloning**: Create personalized voice models
- **Audio Format Support**: MP3, WAV, M4A formats
- **Quality Control**: Configurable audio quality and speed

### Voice Cloning Setup

1. **Prepare voice samples** (M4A format recommended)
2. **Configure voice cloning service**:
   ```python
   # See src/util/voice_clone.py for detailed setup
   VOICE_CLONE_GROUP_ID=your_group_id
   VOICE_CLONE_API_KEY=your_api_key
   ```
3. **Upload voice samples** and get voice IDs
4. **Configure TTS service** to use cloned voices

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov-report=html
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# Scale specific services
docker-compose up -d --scale web=3

# View service status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Production Considerations

- **Database**: Use MySQL or PostgreSQL for production
- **Caching**: Implement Redis for session and task caching
- **Load Balancing**: Use Nginx for load balancing
- **Monitoring**: Set up application monitoring and logging
- **Security**: Configure HTTPS and secure authentication

## 🔒 Security & Best Practices

- **Rate Limiting**: Intelligent request throttling to avoid blocking
- **User Authentication**: Secure session management
- **Data Privacy**: Encrypted data storage and transmission
- **Error Handling**: Comprehensive error handling and logging
- **Input Validation**: Robust input sanitization and validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues

1. **Audio Generation Fails**: Check voice cloning configuration and API keys
2. **Web Scraping Blocked**: Adjust rate limiting and user agent settings
3. **Email Delivery Issues**: Verify email service configuration
4. **Database Connection**: Ensure database is running and accessible

### Getting Help

- Check the logs for detailed error messages
- Verify your environment variables are set correctly
- Test individual components using the provided examples
- Open an issue for bug reports or feature requests

---

**PHEMCAST** - Where enterprise voices become compelling podcast narratives through the power of AI. 🎙️✨