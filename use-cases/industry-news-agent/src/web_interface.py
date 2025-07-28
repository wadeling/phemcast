"""FastAPI web interface for industry news agent."""
import asyncio
import logging
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from pathlib import Path
import uvicorn

from .settings import Settings, load_settings
from .agent import create_agent
from .models import TaskStatus


logger = logging.getLogger(__name__)

# Global task storage (in production, use Redis or database)
running_tasks: Dict[str, Dict] = {}


class ReportRequest(BaseModel):
    """Report generation request."""
    urls: List[str] = Field(..., description="Company blog URLs")
    email: Optional[str] = Field(None, description="Email for report delivery")
    max_articles: int = Field(default=5, ge=1, le=20, description="Articles per blog to analyze")

    @validator('urls', pre=True)
    def parse_urls(cls, v):
        """Parse URLs from string or list."""
        if isinstance(v, str):
            return [url.strip() for url in v.split('\n') if url.strip()]
        return v


# Initialize Python application
app = FastAPI(
    title="Industry News Agent API",
    description="AI-powered industry news aggregation and analysis",
    version="1.0.0"
)

# Setup middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global settings
settings = load_settings()


@app.get("/")
async def home():
    """Serve the main web interface with simple HTML."""
    html_content = """
    <html>
    <head>
        <title>Industry News Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c5aa0; text-align: center; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
            textarea, input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
            textarea { height: 150px; resize: vertical; }
            button { background: #2c5aa0; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; }
            button:hover { background: #1e3d6f; }
            .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .status { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            #loading { display: none; text-align: center; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏢 Industry News Agent</h1>
            <form id="reportForm" onsubmit="handleSubmit(event)">
                <div class="form-group">
                    <label for="urls">Company Blog URLs (one per line):</label>
                    <textarea id="urls" name="urls" placeholder="https://blog.openai.com&#10;https://blog.microsoft.com&#10;https://engineering.linkedin.com" required></textarea>
                </div>
                
                <div class="form-group">
                    <label for="email">Email for Report Delivery (optional):</label>
                    <input type="email" id="email" name="email" placeholder="your.email@company.com">
                </div>
                
                <div class="form-group">
                    <label for="max_articles">Maximum Articles per Blog:</label>
                    <select id="max_articles" name="max_articles">
                        <option value="3">3 articles</option>
                        <option value="5" selected>5 articles</option>
                        <option value="10">10 articles</option>
                        <option value="20">20 articles</option>
                    </select>
                </div>
                
                <button type="submit">Generate Report</button>
                
                <div id="loading">
                    <strong>Processing...</strong><br>
                    This may take a few minutes...<br>
                    <small>Scraping articles and analyzing content...</small>
                </div>
                
                <div id="result"></div>
            </form>
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 14px;">
                <strong>Features:</strong> AI-powered analysis • Smart insights • PDF & Markdown reports • Rate-limited scraping<br>
                <strong>API:</strong> POST to /api/generate-report for programmatic access
            </div>
            
            <script>
                async function handleSubmit(event) {
                    event.preventDefault();
                    
                    const formData = new FormData();
                    formData.append('urls', document.getElementById('urls').value);
                    const email = document.getElementById('email').value;
                    if (email) formData.append('email', email);
                    formData.append('max_articles', document.getElementById('max_articles').value);
                    
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('result').innerHTML = '';
                    
                    try {
                        const response = await fetch('/api/generate-report-form', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        
                        if (result.task_id) {
                            document.getElementById('loading').style.display = 'none';
                            document.getElementById('result').innerHTML = \`
                                <div class="result success">
                                    <strong>✅ Report Generation Started</strong><br>
                                    Task ID: \${result.task_id}<br><br>
                                    <div id="status"></div>
                                    <button onclick="checkStatus('\${result.task_id}')" 
                                            style="background: #28a745; margin-top: 10px;">
                                        Check Status
                                    </button>
                                </div>
                            \`;
                        }
                    } catch (error) {
                        document.getElementById('loading').style.display = 'none';
                        document.getElementById('result').innerHTML = \`
                            <div class="result error">
                                <strong>❌ Error:</strong> \${error.message}
                            </div>
                        \`;
                    }
                }
                
                async function checkStatus(taskId) {
                    try {
                        const response = await fetch(\`/api/task/\${taskId}\`);
                        const status = await response.json();
                        
                        const statusDiv = document.getElementById('status');
                        
                        if (status.status === 'completed') {
                            statusDiv.innerHTML = \`
                                <strong>✅ Completed!</strong><br>
                                Analyzed: \${status.total_articles || 0} articles<br>
                                \${status.report_paths ? Object.keys(status.report_paths).map(k => \`
                                    <a href="/api/download/\${taskId}/\${k}" 
                                       target="_blank" style="color: blue;">Download \${k.toUpperCase()} Report</a><br>
                                \`).join('') : ''}
                                \${status.email_sent ? '<br>📧 Sent to email' : ''}
                            \`;
                        } else if (status.status === 'error') {
                            statusDiv.innerHTML = \`<div style="color: red;"><strong>Error:</strong> \${status.error || 'Processing failed'}</div>\`;
                        } else {
                            statusDiv.innerHTML = \`
                                <div class="status">
                                    <strong>⏳ Status: \${status.status}</strong><br>
                                    <small>Please refresh in 30 seconds...</small>
                                </div>
                            \`;
                            
                            if (status.status === 'processing') {
                                setTimeout(() => checkStatus(taskId), 10000); // Check every 10 seconds
                            }
                        }
                    } catch (error) {
                        document.getElementById('status').innerHTML = \`<div style="color: red;">Status check failed: \${error.message}</div>\`;
                    }
                }
            </script>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/status")
async def get_system_status():
    """Get system status and configuration."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "supported_formats": ["markdown", "pdf"],
        "max_urls_per_request": 50,
        "features": [
            "web_scraping",
            "ai_analysis",
            "report_generation",
            "email_delivery"
        ],
        "active_tasks": len(running_tasks)
    }


@app.post("/api/generate-report")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """
    Submit a report generation request via JSON API.
    
    Args:
        request: Report generation details
    
    Returns:
        Task ID for tracking progress
    """
    try:
        task_id = str(uuid.uuid4())
        
        # Validate URLs
        if not request.urls:
            raise HTTPException(status_code=400, detail="At least one URL is required")
        
        # Validate email if provided
        if request.email and '@' not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Start background processing
        background_tasks.add_task(
            _process_report_task,
            task_id,
            request.urls,
            request.email,
            request.max_articles
        )
        
        # Register task
        running_tasks[task_id] = {
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "urls": request.urls,
            "email": request.email,
            "max_articles": request.max_articles
        }
        
        return {"task_id": task_id, "status": "processing"}
        
    except Exception as e:
        logger.error(f"Failed to create report task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-report-form")
async def generate_report_form(
    urls: str = Form(...),
    email: str = Form(None),
    max_articles: int = Form(5)
):
    """
    Generate report from form data (with multi-line URL input).
    
    Args:
        urls: Multi-line string with URLs
        email: Email for delivery
        max_articles: Max articles per blog
    
    Returns:
        Task ID
    """
    try:
        # Parse URLs from form
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        
        if not url_list:
            raise HTTPException(status_code=400, detail="No valid URLs found")
        
        task_id = str(uuid.uuid4())
        
        # Use asyncio to run in background
        asyncio.create_task(
            _process_report_task(
                task_id, 
                url_list, 
                email, 
                max_articles
            )
        )
        
        running_tasks[task_id] = {
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "urls": url_list,
            "email": email,
            "max_articles": max_articles
        }
        
        return {"task_id": task_id, "status": "processing"}
        
    except Exception as e:
        logger.error(f"Failed to process form submission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """Check task status and progress."""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return running_tasks[task_id]


@app.get("/api/tasks")
async def list_tasks():
    """List all active tasks with basic info."""
    return [
        {
            "task_id": tid,
            "status": info.get("status"),
            "created_at": info.get("created_at"),
            "urls_count": len(info.get("urls", []))
        }
        for tid, info in running_tasks.items()
    ]


@app.get("/download/{task_id}/{format_type}")
async def download_report(task_id: str, format_type: str):
    """Download generated report by format type (simple endpoint)."""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = running_tasks[task_id]
    
    if task_info.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    report_paths = task_info.get("result", {}).get("report_paths", {})
    
    if format_type not in report_paths:
        raise HTTPException(status_code=404, detail=f"{format_type} report not available")
    
    file_path = Path(report_paths[format_type])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    media_type_map = {
        "markdown": "text/markdown",
        "pdf": "application/pdf"
    }
    
    return FileResponse(
        str(file_path),
        media_type=media_type_map.get(format_type, "application/octet-stream"),
        filename=file_path.name
    )


@app.delete("/api/task/{task_id}")
async def cancel_task(task_id: str):
    """Cancel an active task."""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = running_tasks[task_id]
    
    if task_info.get("status") == "processing":
        task_info.update({
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat()
        })
    
    return {"status": "cancelled"}


async def _process_report_task(
    task_id: str, 
    urls: List[str], 
    email: Optional[str], 
    max_articles: int
):
    """Background task for processing reports."""
    try:
        running_tasks[task_id]["status"] = "processing"
        running_tasks[task_id]["started_at"] = datetime.now().isoformat()
        
        # Create and run agent
        agent = create_agent()
        result = await agent.run_workflow(urls, [email] if email else None, max_articles)
        
        # Update task with results
        running_tasks[task_id].update({
            "status": result["status"],
            "completed_at": datetime.now().isoformat(),
            "result": result,
            "report_paths": result.get("report_paths", {}),
            "total_articles": result.get("total_articles", 0),
            "errors": result.get("errors", [])
        })
        
        logger.info(f"Task {task_id} completed: {result['status']}")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        running_tasks[task_id].update({
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })


# Add HTMLResponse for the home page
from fastapi.responses import HTMLResponse


# Let's make home redirect to the API
@app.get("/")
async def root():
    return {"message": "Industry News Agent API", "docs": "/docs", "web_ui": "/", "health": "/api/health"}


@app.get("/")
async def home_html():
    """Serve enhanced HTML interface."""
    return app.routes[0].endpoint() if hasattr(app, 'routes') and app.routes else {"message": "Configure web interface"}


# Reassign the root route to serve HTML
from fastapi import Request
from fastapi.responses import Response


@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """API endpoint that gives options."""
    return HTMLResponse(content="""
    <html>
    <head><title>Industry News Agent API</title></head>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px;">
            <h1 style="color: #2c5aa0;">🏢 Industry News Agent</h1>
            
            <h2>API Endpoints</h2>
            <ul>
                <li><strong><a href="/docs">/docs</a></strong> - Interactive API documentation</li>
                <li><strong>POST /api/generate-report</strong> - Generate reports (JSON)</li>
                <li><strong>POST /api/generate-report-form</strong> - Generate reports (form)</li>
                <li><strong>GET /api/task/{task_id}</strong> - Check task status</li>
                <li><strong>GET /api/health</strong> - Health check</li>
            </ul>
            
            <h2>Example Usage</h2>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
POST /api/generate-report
{
    "urls": ["https://blog.openai.com", "https://engineering.linkedin.com"],
    "email": "user@company.com",
    "max_articles": 5
}
            </pre>
            
            <h2>Report Form</h2>
            <form action="/api/generate-report-form" method="post" style="background: #fafafa; padding: 20px; border-radius: 5px;">
                <div style="margin-bottom: 15px;">
                    <label>URLs (one per line):</label><br>
                    <textarea name="urls" rows="4" style="width: 100%;" required>
https://blog.openai.com
https://news.microsoft.com
https://engineering.linkedin.com
                    </textarea>
                </div>
                <div style="margin-bottom: 15px;">
                    <label>Email:</label><br>
                    <input type="email" name="email" style="width: 100%;" placeholder="your.email@company.com">
                </div>
                <div style="margin-bottom: 15px;">
                    <label>Max Articles per Blog:</label><br>
                    <select name="max_articles">
                        <option value="3">3</option>
                        <option value="5" selected>5</option>
                        <option value="10">10</option>
                    </select>
                </div>
                <button type="submit" style="background: #2c5aa0; color: white; padding: 10px 20px; border: none; border-radius: 5px;">
                    Generate Report
                </button>
            </form>
        </div>
    </body>
    </html>
    """)


if __name__ == "__main__":
    uvicorn.run("src.web_interface:app", host="0.0.0.0", port=8000, reload=True)