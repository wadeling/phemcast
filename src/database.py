"""Database connection manager for industry news agent."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
import os
from typing import Optional
from datetime import datetime


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
    
    def init_database(self, database_url: str):
        """Initialize database connection."""
        # Sync engine for migrations - use PyMySQL
        if database_url.startswith('mysql://'):
            sync_url = database_url.replace('mysql://', 'mysql+pymysql://')
        else:
            sync_url = database_url
            
        self.engine = create_engine(sync_url)
        
        # Async engine for operations
        if database_url.startswith('mysql://'):
            async_url = database_url.replace('mysql://', 'mysql+aiomysql://')
        else:
            async_url = database_url.replace('mysql+pymysql://', 'mysql+aiomysql://')
            
        self.async_engine = create_async_engine(
            async_url,
            pool_size=20,          # 连接池大小
            max_overflow=30,       # 最大溢出连接数
            pool_timeout=30,       # 获取连接超时时间
            pool_recycle=3600,     # 连接回收时间（1小时）
            pool_pre_ping=True     # 连接前ping检查
        )
        
        # Create tables
        # Import all models to ensure they're registered with Base
        from db_models import Base
        Base.metadata.create_all(bind=self.engine)
        
        # Session factories
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )
    
    def get_session(self):
        """Get database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    async def get_async_session(self):
        """Get async database session."""
        if not self.AsyncSessionLocal:
            raise RuntimeError("Database not initialized")
        return self.AsyncSessionLocal()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
        if self.async_engine:
            self.async_engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


def init_db(database_url: str):
    """Initialize database with retry mechanism."""
    import time
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
            db_manager.init_database(database_url)
            print("Database connection established successfully!")
            return
        except Exception as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Database initialization failed.")
                raise


def get_db():
    """Get database session."""
    return db_manager.get_session()


async def get_async_db():
    """Get async database session."""
    if not db_manager.AsyncSessionLocal:
        raise RuntimeError("Database not initialized")
    return db_manager.AsyncSessionLocal()


def serialize_for_json(obj):
    """Custom JSON serializer that handles Pydantic models and datetime objects."""
    import json
    from datetime import datetime
    from models import Article, CompanyInsights
    
    if isinstance(obj, (Article, CompanyInsights)):
        return obj.dict()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

async def get_user_email_settings(user_name: str) -> tuple[str, bool]:
    """
    Get user email and notification settings.
    
    Args:
        user_name: Username to check
        
    Returns:
        Tuple of (user_email, email_notifications_enabled)
    """
    from sqlalchemy import text
    from logging_config import get_logger
    
    logger = get_logger(__name__)
    
    try:
        db = await get_async_db()
        async with db as session:
            # Get user email and notification settings
            result = await session.execute(
                text("""
                    SELECT u.email, us.email_notifications 
                    FROM users u 
                    LEFT JOIN user_settings us ON u.username = us.username 
                    WHERE u.username = :username
                """),
                {"username": user_name}
            )
            row = result.fetchone()
            
            if row:
                user_email = row.email
                email_notifications = row.email_notifications if row.email_notifications is not None else True
                return user_email, email_notifications
            else:
                logger.warning(f"User {user_name} not found or no email settings")
                return None, False
    except Exception as e:
        logger.error(f"Failed to get user settings: {e}")
        return None, False


async def get_user_feishu_settings(user_name: str) -> tuple[str, bool]:
    """
    Get user Feishu webhook and notification settings.
    
    Args:
        user_name: Username to check
        
    Returns:
        Tuple of (feishu_webhook_url, feishu_notifications_enabled)
    """
    from sqlalchemy import text
    from logging_config import get_logger
    
    logger = get_logger(__name__)
    
    try:
        db = await get_async_db()
        async with db as session:
            # Get user Feishu settings
            result = await session.execute(
                text("""
                    SELECT feishu_webhook_url, feishu_notifications_enabled 
                    FROM user_settings 
                    WHERE username = :username
                """),
                {"username": user_name}
            )
            row = result.fetchone()
            
            if row:
                feishu_webhook_url = row.feishu_webhook_url
                feishu_notifications_enabled = row.feishu_notifications_enabled if row.feishu_notifications_enabled is not None else False
                return feishu_webhook_url, feishu_notifications_enabled
            else:
                logger.warning(f"User {user_name} not found or no Feishu settings")
                return None, False
    except Exception as e:
        logger.error(f"Failed to get user Feishu settings: {e}")
        return None, False

async def record_task_execution(
    task_id: str,
    task_name: str,
    user_name: str,
    execution_type: str,  # "manual" or "scheduled"
    status: str,  # "success", "error", "processing"
    started_at: datetime,
    task_group_id: str = None,
    completed_at: datetime = None,
    duration: int = None,
    total_articles: int = None,
    total_urls: int = None,
    report_paths: dict = None,
    errors: list = None,
    logs: list = None,
    result: dict = None
):
    """Record task execution results to database."""
    import json
    import uuid
    from sqlalchemy import text
    
    try:
        db = await get_async_db()
        async with db as session:
            # Generate unique execution history ID
            execution_id = str(uuid.uuid4())
            
            # Insert into task_execution_history
            await session.execute(
                text("""
                    INSERT INTO task_execution_history 
                    (id, task_id, task_group_id, task_name, user_name, execution_type, status, started_at, 
                     completed_at, duration, total_articles, total_urls, report_paths, 
                     errors, logs, created_at)
                    VALUES 
                    (:id, :task_id, :task_group_id, :task_name, :user_name, :execution_type, :status, :started_at,
                     :completed_at, :duration, :total_articles, :total_urls, :report_paths,
                     :errors, :logs, :created_at)
                """),
                {
                    "id": execution_id,
                    "task_id": task_id,
                    "task_group_id": task_group_id,
                    "task_name": task_name,
                    "user_name": user_name,
                    "execution_type": execution_type,
                    "status": status,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "duration": duration,
                    "total_articles": total_articles,
                    "total_urls": total_urls,
                    "report_paths": json.dumps(serialize_for_json(report_paths)) if report_paths else None,
                    "errors": json.dumps(serialize_for_json(errors)) if errors else None,
                    "logs": json.dumps(serialize_for_json(logs)) if logs else None,
                    "created_at": datetime.utcnow()
                }
            )
            
            # Update scheduled_tasks table with last execution info
            await session.execute(
                text("""
                    UPDATE scheduled_tasks 
                    SET last_execution_status = :status,
                        last_execution_result = :result,
                        last_report_paths = :report_paths,
                        last_execution_time = :execution_time,
                        last_execution_duration = :duration,
                        updated_at = :updated_at
                    WHERE id = :task_id
                """),
                {
                    "status": status,
                    "result": json.dumps(serialize_for_json(result)) if result else None,
                    "report_paths": json.dumps(serialize_for_json(report_paths)) if report_paths else None,
                    "execution_time": completed_at or started_at,
                    "duration": duration,
                    "updated_at": datetime.utcnow(),
                    "task_id": task_id
                }
            )
            
            await session.commit()
            return execution_id
            
    except Exception as e:
        print(f"Failed to record task execution: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

