"""FastAPI web interface for industry news agent."""
import asyncio
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from .settings import Settings, load_settings
from .logging_config import setup_logging, get_logger

# Load settings first to get log level
settings = load_settings()

# Setup logging with file line numbers enabled
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    show_file_line=settings.show_file_line,
    show_function=settings.show_function
)

from fastapi import FastAPI, HTTPException, Form, BackgroundTasks, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn

from .agent import create_agent
from .models import TaskStatus
from .database import init_db, get_async_db, User
from .auth import (
    authenticate_user, create_user, verify_invite_code,
    create_access_token, get_current_user
)


logger = get_logger(__name__)

# Global task storage (in production, use Redis or database)
running_tasks: Dict[str, Dict] = {}


class ReportRequest(BaseModel):
    """Report generation request."""
    urls: List[str] = Field(..., description="Company blog URLs")
    email: Optional[str] = Field(None, description="Email for report delivery")
    max_articles: int = Field(default=5, ge=1, le=20, description="Articles per blog to analyze")

    @field_validator('urls', mode='before')
    @classmethod
    def parse_urls(cls, v):
        """Parse URLs from string or list."""
        if isinstance(v, str):
            return [url.strip() for url in v.split('\n') if url.strip()]
        return v


class LoginRequest(BaseModel):
    """Login request."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class InviteVerifyRequest(BaseModel):
    """Invite code verification request."""
    invite_code: str = Field(..., description="Invite code")


class RegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email")
    password: str = Field(..., description="Password")
    invite_code: str = Field(..., description="Invite code")


# Initialize Python application
app = FastAPI(
    title="Industry News Agent API",
    description="AI-powered industry news aggregation and analysis",
    version="1.0.0"
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    from .settings import load_settings
    settings = load_settings()
    init_db(settings.database_url)

# Setup middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files - serve from html directory
html_dir = Path(__file__).parent.parent / "html"
if not html_dir.exists():
    html_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(html_dir)), name="static")

# Also mount individual directories for better organization
css_dir = html_dir / "css"
if css_dir.exists():
    app.mount("/static/css", StaticFiles(directory=str(css_dir)), name="css")

js_dir = html_dir / "js"
if js_dir.exists():
    app.mount("/static/js", StaticFiles(directory=str(js_dir)), name="js")

# Global settings
# settings = load_settings() # This line is now redundant as settings is loaded globally


@app.get("/")
async def home():
    """Serve the main web interface."""
    html_file = html_dir / "index.html"
    if not html_file.exists():
        return JSONResponse(
            {"error": "HTML interface not found. Please ensure html/index.html exists."},
            status_code=500
        )
    return FileResponse(html_file, media_type="text/html")


@app.get("/login")
async def login_page():
    """Serve the login page."""
    html_file = html_dir / "login.html"
    if not html_file.exists():
        return JSONResponse(
            {"error": "Login page not found."},
            status_code=500
        )
    return FileResponse(html_file, media_type="text/html")


@app.get("/error")
async def error_page():
    """Serve the error page."""
    html_file = html_dir / "error.html"
    if not html_file.exists():
        return JSONResponse(
            {"error": "Error page not found."},
            status_code=500
        )
    return FileResponse(html_file, media_type="text/html")


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/status")
async def get_system_status(current_user: User = Depends(get_current_user)):
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
        "active_tasks": len(running_tasks),
        "user": current_user.username
    }


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """User login with username and password."""
    user = await authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username
    }


@app.post("/api/auth/verify-invite")
async def verify_invite(request: InviteVerifyRequest):
    """Verify invite code."""
    invite_code = await verify_invite_code(request.invite_code)
    if not invite_code:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired invite code"
        )
    
    return {"message": "Invite code is valid"}


@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register new user with invite code."""
    try:
        user = await create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            invite_code=request.invite_code
        )
        
        return {
            "message": "User created successfully",
            "username": user.username
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


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
    logger.info("=== FORM SUBMISSION RECEIVED ===")
    logger.info(f"Generating report for {urls} with email {email} and max_articles {max_articles}")
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
        
        # Update task with enhanced results
        running_tasks[task_id].update({
            "status": result["status"],
            "completed_at": datetime.now().isoformat(),
            "result": result,
            "report_paths": result.get("report_paths", {}),
            "report_path_md": result.get("report_paths", {}).get("markdown", ""),
            "report_path_pdf": result.get("report_paths", {}).get("pdf", ""),
            "total_articles": result.get("total_articles", 0),
            "total_urls": result.get("total_urls", 0),
            "processing_time": result.get("processing_time", 0),
            "logs": result.get("logs", []),
            "errors": result.get("errors", [])
        })
        
        logger.info(f"Task {task_id} completed: {result['status']}")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        running_tasks[task_id].update({
            "status": "error",
            "error": str(e),
            "logs": [f"❌ Processing failed: {str(e)}", "📋 See error details above"],
            "completed_at": datetime.now().isoformat()
        })




@app.get("/api/docs")
async def api_docs():
    """API documentation redirect."""
    return {"message": "API documentation available at /docs", "endpoints": {
        "POST /api/generate-report": "Generate reports (JSON)",
        "POST /api/generate-report-form": "Generate reports (form)",
        "GET /api/task/{task_id}": "Check task status",
        "GET /api/status": "System status"
    }}


if __name__ == "__main__":
    uvicorn.run("src.web_interface:app", host="0.0.0.0", port=8000, reload=True)