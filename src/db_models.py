"""SQLAlchemy database models for industry news agent."""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class InviteCode(Base):
    """Invite code model."""
    __tablename__ = "invite_codes"
    
    code = Column(String(50), primary_key=True, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    used_by = Column(String(100), nullable=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    username = Column(String(100), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    invite_code_used = Column(String(50), nullable=True)


class ScheduledTask(Base):
    """Scheduled task table."""
    __tablename__ = "scheduled_tasks"
    
    id = Column(String(50), primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    user_name = Column(String(100), nullable=False, index=True)
    companies = Column(Text, nullable=False)  # JSON string of company names
    max_articles = Column(Integer, nullable=False, default=5)
    
    # Schedule configuration
    schedule_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    schedule_time = Column(String(10), nullable=False)  # HH:MM format
    schedule_day = Column(String(20), nullable=True)  # day of week or day of month
    
    # Task status
    is_active = Column(Boolean, default=True, nullable=False)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    
    # Task execution results (for both manual and scheduled tasks)
    last_execution_status = Column(String(20), nullable=True)  # success, error, processing
    last_execution_result = Column(Text, nullable=True)  # JSON string of execution results
    last_report_paths = Column(Text, nullable=True)  # JSON string of report paths
    last_execution_time = Column(DateTime, nullable=True)
    last_execution_duration = Column(Integer, nullable=True)  # duration in seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TaskExecutionHistory(Base):
    """Task execution history table for detailed tracking."""
    __tablename__ = "task_execution_history"
    
    id = Column(String(50), primary_key=True, index=True)
    task_id = Column(String(50), nullable=False, index=True)  # Reference to scheduled_tasks.id
    task_group_id = Column(String(50), nullable=True, index=True)  # Reference to task group
    task_name = Column(String(255), nullable=False)
    user_name = Column(String(100), nullable=False, index=True)
    execution_type = Column(String(20), nullable=False)  # manual, scheduled
    
    # Execution details
    status = Column(String(20), nullable=False)  # success, error, processing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # duration in seconds
    
    # Results
    total_articles = Column(Integer, nullable=True)
    total_urls = Column(Integer, nullable=True)
    report_paths = Column(Text, nullable=True)  # JSON string of report paths
    errors = Column(Text, nullable=True)  # JSON string of errors
    logs = Column(Text, nullable=True)  # JSON string of logs
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserSettings(Base):
    """User settings table for storing user preferences."""
    __tablename__ = "user_settings"
    
    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(100), nullable=False, index=True, unique=True)
    email_notifications = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
