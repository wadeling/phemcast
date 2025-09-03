"""FastAPI web interface for industry news agent."""
import asyncio
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from settings import Settings, load_settings
from logging_config import setup_logging, get_logger

# Load settings first to get log level
settings = load_settings()

# Setup logging with file line numbers enabled
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    show_file_line=settings.show_file_line,
    show_function=settings.show_function
)

from fastapi import FastAPI, HTTPException, Form, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn
import json
from typing import List

from agent import create_agent
from models import TaskStatus
from database import init_db, get_async_db
from db_models import User
from task_manager import task_manager
from auth import (
    authenticate_user, create_user, verify_invite_code,
    create_access_token, get_current_user
)
from tts_service import create_tts_service

# Import scheduled task models
from models import ScheduledTaskCreate, ScheduledTaskUpdate


logger = get_logger(__name__)

# Global task storage (in production, use Redis or database)
running_tasks: Dict[str, Dict] = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                    logger.debug(f"Message broadcasted successfully to client")
                except Exception as e:
                    logger.error(f"Failed to send message to WebSocket: {e}")
                    # Mark for removal
                    disconnected_connections.append(connection)
            
            # Remove broken connections
            for connection in disconnected_connections:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)
                    logger.info(f"Removed broken WebSocket connection. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

manager = ConnectionManager()


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
    try:
        from settings import load_settings
        settings = load_settings()
        logger.info("Initializing database on startup...")
        logger.debug(f"Database URL: {settings.database_url}")
        init_db(settings.database_url)
        logger.info("Database initialized successfully on startup")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")
        import traceback
        logger.error(f"Startup database error traceback: {traceback.format_exc()}")
        raise

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


@app.get("/scheduled-tasks")
async def scheduled_tasks_page():
    """Serve the scheduled tasks management page."""
    html_file = html_dir / "scheduled-tasks.html"
    if not html_file.exists():
        return JSONResponse(
            {"error": "Scheduled tasks page not found."},
            status_code=500
        )
    return FileResponse(html_file, media_type="text/html")


@app.get("/scheduled-tasks-test")
async def scheduled_tasks_test_page():
    """Serve the scheduled tasks test page (no auth required)."""
    html_file = html_dir / "scheduled-tasks-test.html"
    if not html_file.exists():
        return JSONResponse(
            {"error": "Scheduled tasks test page not found."},
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
        "pdf": "application/pdf",
        "audio": "audio/mpeg"
    }
    
    # 获取文件扩展名
    file_ext = file_path.suffix.lower()
    
    # 关键修改：根据文件类型设置不同的响应头
    if format_type == "audio" or file_ext in [".mp3", ".wav", ".ogg", ".m4a", ".aac"]:
        # 对于音频文件，设置内联播放的响应头
        return FileResponse(
            str(file_path),
            media_type=media_type_map.get(format_type, "audio/mpeg"),
            filename=file_path.name,
            headers={
                "Content-Disposition": f"inline; filename=\"{file_path.name}\"",
                "Accept-Ranges": "bytes"
            }
        )
    else:
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
        # Update status to processing
        running_tasks[task_id]["status"] = "processing"
        running_tasks[task_id]["started_at"] = datetime.now().isoformat()
        
        # Broadcast processing status
        await manager.broadcast({
            "type": "task_update",
            "task_id": task_id,
            "status": "processing",
            "message": "Task started processing"
        })
        
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
            "report_path_audio": result.get("report_paths", {}).get("audio", ""),
            "total_articles": result.get("total_articles", 0),
            "total_urls": result.get("total_urls", 0),
            "processing_time": result.get("processing_time", 0),
            "logs": result.get("logs", []),
            "errors": result.get("errors", [])
        })
        
        logger.info(f"Task {task_id} completed: {result['status']}")
        
        # Broadcast completion status
        await manager.broadcast({
            "type": "task_update",
            "task_id": task_id,
            "status": result["status"],
            "message": "Task completed successfully",
            "data": {
                "total_articles": result.get("total_articles", 0),
                "report_paths": result.get("report_paths", {}),
                "email_sent": bool(email)
            }
        })
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        running_tasks[task_id].update({
            "status": "error",
            "error": str(e),
            "logs": [f"❌ Processing failed: {str(e)}", "📋 See error details above"],
            "completed_at": datetime.now().isoformat()
        })
        
        # Broadcast error status
        await manager.broadcast({
            "type": "task_update",
            "task_id": task_id,
            "status": "error",
            "message": "Task failed",
            "error": str(e)
        })




@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    try:
        await manager.connect(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(manager.active_connections)}")
        
        while True:
            try:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_personal_message({"type": "pong"}, websocket)
                        logger.debug(f"Ping received from client, sent pong")
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received from WebSocket")
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(manager.active_connections)}")


@app.get("/api/docs")
async def api_docs():
    """API documentation redirect."""
    return {"message": "API documentation available at /docs", "endpoints": {
        "POST /api/generate-report": "Generate reports (JSON)",
        "POST /api/generate-report-form": "Generate reports (form)",
        "GET /api/task/{task_id}": "Check task status",
        "GET /api/status": "System status",
        "GET /audio/{token}": "Access audio file with token",
        "WS /ws": "WebSocket for real-time updates"
    }}


@app.get("/audio/{token}")
async def get_audio_file(token: str):
    """Get audio file using access token."""
    try:
        from settings import load_settings
        settings = load_settings()
        
        # 创建TTS服务实例来验证token
        tts_service = create_tts_service(settings)
        
        # 获取音频访问URL
        audio_url = tts_service.get_audio_access_url(token)
        if not audio_url:
            raise HTTPException(status_code=404, detail="Audio file not found or token expired")
        
        # 获取token信息
        token_file = tts_service.temp_audio_dir / f"{token}.json"
        if not token_file.exists():
            raise HTTPException(status_code=404, detail="Invalid token")
        
        import json
        with open(token_file, 'r', encoding='utf-8') as f:
            token_info = json.load(f)
        
        # 检查是否过期
        from datetime import datetime
        expiry_time = datetime.fromisoformat(token_info["expires_at"])
        if datetime.now() > expiry_time:
            # 清理过期文件
            tts_service._cleanup_expired_token(token)
            raise HTTPException(status_code=410, detail="Audio file access expired")
        
        # 返回音频文件
        audio_path = Path(token_info["temp_path"])
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            str(audio_path),
            media_type="audio/mpeg",
            filename=f"report_audio_{token[:8]}.mp3"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing audio file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/scheduled-tasks")
async def create_scheduled_task(
    request: ScheduledTaskCreate, 
    current_user: User = Depends(get_current_user)
):
    """Create a new scheduled task."""
    try:
        logger.debug(f"Received scheduled task creation request: {request.dict()}")
        logger.debug(f"URLs in request: {request.urls}")
        logger.debug(f"Email recipients in request: {request.email_recipients}")
        
        task_id = await task_manager.create_task(request.dict(), current_user.username)
        return {"task_id": task_id, "message": "Scheduled task created successfully"}
    except Exception as e:
        logger.error(f"Failed to create scheduled task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduled-tasks")
async def get_scheduled_tasks(current_user: User = Depends(get_current_user)):
    """Get all scheduled tasks for the current user."""
    try:
        logger.debug(f"Fetching scheduled tasks for user: {current_user.username}")
        tasks = await task_manager.get_user_tasks(current_user.username)
        logger.debug(f"Successfully fetched {len(tasks)} tasks")
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Failed to fetch scheduled tasks: {str(e)}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch scheduled tasks: {str(e)}")


@app.put("/api/scheduled-tasks/{task_id}")
async def update_scheduled_task(
    task_id: str,
    request: ScheduledTaskUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an existing scheduled task."""
    try:
        success = await task_manager.update_task(task_id, current_user.username, request.dict(exclude_unset=True))
        if success:
            return {"message": "Scheduled task updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found or update failed")
    except Exception as e:
        logger.error(f"Failed to update scheduled task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/scheduled-tasks/{task_id}")
async def delete_scheduled_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a scheduled task."""
    try:
        success = await task_manager.delete_task(task_id, current_user.username)
        if success:
            return {"message": "Scheduled task deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found or delete failed")
    except Exception as e:
        logger.error(f"Failed to delete scheduled task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduled-tasks/{task_id}/toggle")
async def toggle_scheduled_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Toggle the active status of a scheduled task."""
    try:
        success = await task_manager.toggle_task_status(task_id, current_user.username)
        if success:
            return {"message": "Task status toggled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found or toggle failed")
    except Exception as e:
        logger.error(f"Failed to toggle scheduled task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: Task scheduler is now managed by the background TaskProcessor process
# No API endpoints are needed for start/stop operations


# Note: This file is now imported by main.py
# Use 'python main.py' to start the application