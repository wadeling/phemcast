# Web Interface Example

This example demonstrates a FastAPI web application for the industry news agent.

## Features

- User-friendly web form for inputting blog URLs
- Multi-line URL support
- Email address input
- Progress tracking for long-running tasks
- File upload support for URL lists

## Usage

```bash
# Start the web server
uvicorn web_interface:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - Main form page
- `POST /generate-report` - Submit URLs and generate report
- `GET /status/{task_id}` - Check report generation status
- `GET /download/{report_id}` - Download generated report

## Structure

- `app.py` - FastAPI application with routes
- `templates/` - HTML templates for the web interface
- `static/` - CSS, JavaScript, and static assets
- `forms.py` - Form validation and processing

## Key Concepts

1. **Async Processing**: Background task processing with Celery or asyncio
2. **Form Handling**: Multi-part form processing with validation
3. **File Uploads**: Support for uploading URL files
4. **Progress Tracking**: Real-time progress updates via WebSockets 