#!/usr/bin/env python3
"""Background task processor using apscheduler for cron-like functionality."""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import traceback

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy import text

from settings import load_settings
from logging_config import setup_logging, get_logger
from database import get_async_db, init_db, record_task_execution
from models import ScheduledTask
from db_models import ScheduledTask as DBScheduledTask
from report_generator import ReportGenerator
from email_service import EmailService
from agent import create_agent

class TaskProcessor:
    """Background task processor that reads tasks from database and schedules them."""
    
    def __init__(self):
        """Initialize the task processor."""
        # Load settings
        self.settings = load_settings()
        
        # Setup logging
        setup_logging(
            log_level=self.settings.log_level,
            log_file=self.settings.log_file,
            show_file_line=self.settings.show_file_line,
            show_function=self.settings.show_function
        )
        
        self.logger = get_logger(__name__)
        
        # Initialize database
        try:
            self.logger.info("Initializing database connection...")
            self.logger.debug(f"Database URL: {self.settings.database_url}")
            init_db(self.settings.database_url)
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            import traceback
            self.logger.error(f"Database initialization traceback: {traceback.format_exc()}")
            raise
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor()},
            job_defaults={
                'coalesce': False,
                'max_instances': 1,
                'misfire_grace_time': 300  # 5 minutes grace time
            }
        )
        
        # Initialize services
        self.report_generator = None
        self.email_service = None
        self.agent = None
        
        # 东八区时区 (UTC+8)
        self.east_eight_timezone = timezone(timedelta(hours=8))
        
        self.logger.info("TaskProcessor initialized")
    
    def convert_utc_to_east_eight(self, time_str: str) -> str:
        """
        将UTC时间字符串转换为东八区时间字符串
        
        Args:
            time_str: UTC时间字符串，格式为 "HH:MM"
            
        Returns:
            东八区时间字符串，格式为 "HH:MM"
        """
        try:
            # 解析UTC时间
            hour, minute = map(int, time_str.split(':'))
            
            # 创建今天的UTC时间
            today = datetime.now(timezone.utc).date()
            utc_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            utc_time = utc_time.replace(tzinfo=timezone.utc)
            
            # 转换为东八区时间
            east_eight_time = utc_time.astimezone(self.east_eight_timezone)
            
            # 返回东八区时间字符串
            return east_eight_time.strftime('%H:%M')
            
        except Exception as e:
            self.logger.error(f"Failed to convert time {time_str} from UTC to East Eight: {e}")
            # 如果转换失败，返回原时间
            return time_str
    
    async def initialize_services(self):
        """Initialize required services."""
        try:
            # Initialize report generator
            self.report_generator = ReportGenerator(self.settings)
            
            # Initialize email service
            self.email_service = EmailService(self.settings)
            
            # Initialize agent
            self.agent = create_agent(self.settings)
            
            self.logger.info("All services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    async def load_tasks_from_database(self) -> List[ScheduledTask]:
        """Load all active scheduled tasks from database."""
        try:
            self.logger.debug("Attempting to get async database session...")
            db = await get_async_db()
            self.logger.debug("Got async database session, creating context...")
            
            async with db as session:
                self.logger.debug("Executing query for active tasks...")
                # Query active tasks
                result = await session.execute(
                    text("SELECT * FROM scheduled_tasks WHERE is_active = 1")
                )
                rows = result.fetchall()
                self.logger.debug(f"Query returned {len(rows)} rows")
                
                tasks = []
                for row in rows:
                    try:
                        # Convert database row to Pydantic model
                        # Convert UTC time back to East Eight time for display
                        schedule_time_east_eight = self.convert_utc_to_east_eight(row.schedule_time)
                        
                        task_data = {
                            'id': row.id,
                            'task_name': row.task_name,
                            'user_id': row.user_id,
                            'urls': json.loads(row.urls) if row.urls else [],
                            'email_recipients': json.loads(row.email_recipients) if row.email_recipients else [],
                            'max_articles': int(row.max_articles) if row.max_articles else 5,
                            'schedule_type': row.schedule_type,
                            'schedule_time': schedule_time_east_eight,  # 显示东八区时间
                            'schedule_time_utc': row.schedule_time,    # 保留UTC时间用于调度
                            'schedule_day': row.schedule_day,
                            'is_active': bool(row.is_active),
                            'last_run': row.last_run,
                            'next_run': row.next_run,
                            'created_at': row.created_at,
                            'updated_at': row.updated_at
                        }
                        task = ScheduledTask(**task_data)
                        tasks.append(task)
                        self.logger.debug(f"Created task object for: {task.task_name}")
                    except Exception as row_error:
                        self.logger.error(f"Failed to process row {row.id}: {row_error}")
                        continue
                
                self.logger.info(f"Loaded {len(tasks)} active tasks from database")
                return tasks
                
        except Exception as e:
            self.logger.error(f"Failed to load tasks from database: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def create_cron_trigger(self, task: ScheduledTask) -> CronTrigger:
        """Create a cron trigger based on task schedule configuration."""
        # Use UTC time if available, otherwise fall back to schedule_time
        schedule_time = getattr(task, 'schedule_time_utc', task.schedule_time_utc)
        time_parts = schedule_time.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if task.schedule_type == 'daily':
            return CronTrigger(hour=hour, minute=minute)
        elif task.schedule_type == 'weekly':
            day_map = {
                'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
                'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
            }
            day = day_map.get(task.schedule_day.lower(), 'mon')
            return CronTrigger(day_of_week=day, hour=hour, minute=minute)
        elif task.schedule_type == 'monthly':
            day = int(task.schedule_day) if task.schedule_day else 1
            return CronTrigger(day=day, hour=hour, minute=minute)
        else:
            # Default to daily
            return CronTrigger(hour=hour, minute=minute)
    
    async def schedule_task(self, task: ScheduledTask):
        """Schedule a single task using apscheduler."""
        try:
            # Use UTC time for scheduling (stored in schedule_time_utc if available)
            schedule_time_utc = getattr(task, 'schedule_time_utc', task.schedule_time_utc)
            self.logger.debug(f"Scheduling task '{task.task_name}' with time: {schedule_time_utc} (UTC)")
            
            # Create cron trigger
            trigger = self.create_cron_trigger(task)
            
            # Add job to scheduler
            job = self.scheduler.add_job(
                func=self.execute_task,
                trigger=trigger,
                args=[task],
                id=f"task_{task.id}",
                name=task.task_name,
                replace_existing=True
            )
            
            self.logger.info(f"Scheduled task '{task.task_name}' (ID: {task.id}) with trigger: {trigger}")
            
            # Update next_run in database
            await self.update_task_next_run(task.id, job.next_run_time)
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task {task.id}: {e}")
    
    async def execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        self.logger.info(f"Executing task: {task.task_name} (ID: {task.id})")
        started_at = datetime.utcnow()
        
        try:
            # Update last_run timestamp
            await self.update_task_last_run(task.id, started_at)
            
            # Record task start in database
            try:
                await record_task_execution(
                    task_id=task.id,
                    task_name=task.task_name,
                    user_id=task.user_id,
                    execution_type="scheduled",
                    status="processing",
                    started_at=started_at
                )
            except Exception as db_error:
                self.logger.warning(f"Failed to record task start in database: {db_error}")
            
            # Generate report using agent workflow
            if task.urls:
                try:
                    self.logger.info(f"Starting report generation for task {task.id}")
                    
                    # Create agent and run workflow
                    if self.agent:
                        result = await self.agent.run_workflow(
                            urls=task.urls,
                            email_recipients=task.email_recipients,
                            max_articles=task.max_articles
                        )
                        
                        self.logger.info(f"Report generation completed for task {task.id}: {result.get('status', 'unknown')}")
                        
                        # Send email if recipients specified and email service available
                        if task.email_recipients and self.email_service and result.get('report_paths'):
                            try:
                                # Try to send email with available report paths
                                report_path = result.get('report_paths', {}).get('pdf') or result.get('report_paths', {}).get('markdown')
                                if report_path:
                                    await self.email_service.send_report_email(
                                        recipients=task.email_recipients,
                                        report_path=report_path,
                                        task_name=task.task_name
                                    )
                                    self.logger.info(f"Email sent successfully for task {task.id}")
                                else:
                                    self.logger.warning(f"No report path available for email in task {task.id}")
                            except Exception as email_error:
                                self.logger.error(f"Failed to send email for task {task.id}: {email_error}")
                        
                        # Calculate completion time and duration
                        completed_at = datetime.utcnow()
                        duration = int((completed_at - started_at).total_seconds())
                        
                        # Record task completion in database
                        try:
                            await record_task_execution(
                                task_id=task.id,
                                task_name=task.task_name,
                                user_id=task.user_id,
                                execution_type="scheduled",
                                status=result.get("status", "completed"),
                                started_at=started_at,
                                completed_at=completed_at,
                                duration=duration,
                                total_articles=result.get("total_articles", 0),
                                total_urls=result.get("total_urls", 0),
                                report_paths=result.get("report_paths", {}),
                                errors=result.get("errors", []),
                                logs=result.get("logs", []),
                                result=result
                            )
                        except Exception as db_error:
                            self.logger.warning(f"Failed to record task completion in database: {db_error}")
                        
                        self.logger.info(f"Task {task.id} completed successfully")
                    else:
                        self.logger.error(f"Agent not available for task {task.id}")
                        
                        # Record task error in database
                        completed_at = datetime.utcnow()
                        duration = int((completed_at - started_at).total_seconds())
                        try:
                            await record_task_execution(
                                task_id=task.id,
                                task_name=task.task_name,
                                user_id=task.user_id,
                                execution_type="scheduled",
                                status="error",
                                started_at=started_at,
                                completed_at=completed_at,
                                duration=duration,
                                errors=["Agent not available"],
                                logs=["Agent not available for task execution"]
                            )
                        except Exception as db_error:
                            self.logger.warning(f"Failed to record task error in database: {db_error}")
                        
                except Exception as report_error:
                    self.logger.error(f"Failed to generate report for task {task.id}: {report_error}")
                    
                    # Record task error in database
                    completed_at = datetime.utcnow()
                    duration = int((completed_at - started_at).total_seconds())
                    try:
                        await record_task_execution(
                            task_id=task.id,
                            task_name=task.task_name,
                            user_id=task.user_id,
                            execution_type="scheduled",
                            status="error",
                            started_at=started_at,
                            completed_at=completed_at,
                            duration=duration,
                            errors=[str(report_error)],
                            logs=[f"Failed to generate report: {str(report_error)}"]
                        )
                    except Exception as db_error:
                        self.logger.warning(f"Failed to record task error in database: {db_error}")
                    
                    # Continue execution even if report generation fails
            else:
                self.logger.warning(f"Task {task.id} has no URLs")
                
                # Record task error in database
                completed_at = datetime.utcnow()
                duration = int((completed_at - started_at).total_seconds())
                try:
                    await record_task_execution(
                        task_id=task.id,
                        task_name=task.task_name,
                        user_id=task.user_id,
                        execution_type="scheduled",
                        status="error",
                        started_at=started_at,
                        completed_at=completed_at,
                        duration=duration,
                        errors=["No URLs provided"],
                        logs=["Task has no URLs to process"]
                    )
                except Exception as db_error:
                    self.logger.warning(f"Failed to record task error in database: {db_error}")
                
        except Exception as e:
            self.logger.error(f"Failed to execute task {task.id}: {e}")
            traceback.print_exc()
            
            # Record task error in database
            completed_at = datetime.utcnow()
            duration = int((completed_at - started_at).total_seconds())
            try:
                await record_task_execution(
                    task_id=task.id,
                    task_name=task.task_name,
                    user_id=task.user_id,
                    execution_type="scheduled",
                    status="error",
                    started_at=started_at,
                    completed_at=completed_at,
                    duration=duration,
                    errors=[str(e)],
                    logs=[f"Task execution failed: {str(e)}"]
                )
            except Exception as db_error:
                self.logger.warning(f"Failed to record task error in database: {db_error}")
    
    async def update_task_last_run(self, task_id: str, last_run: datetime):
        """Update the last_run timestamp for a task."""
        try:
            db = await get_async_db()
            async with db as session:
                await session.execute(
                    text("UPDATE scheduled_tasks SET last_run = :last_run WHERE id = :task_id"),
                    {"last_run": last_run, "task_id": task_id}
                )
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to update last_run for task {task_id}: {e}")
    
    async def update_task_next_run(self, task_id: str, next_run: Optional[datetime]):
        """Update the next_run timestamp for a task."""
        try:
            db = await get_async_db()
            async with db as session:
                await session.execute(
                    text("UPDATE scheduled_tasks SET next_run = :next_run WHERE id = :task_id"),
                    {"next_run": next_run, "task_id": task_id}
                )
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to update next_run for task {task_id}: {e}")
    
    async def schedule_all_tasks(self):
        """Load and schedule all active tasks from database."""
        try:
            tasks = await self.load_tasks_from_database()
            
            for task in tasks:
                await self.schedule_task(task)
            
            self.logger.info(f"Scheduled {len(tasks)} tasks")
            
        except Exception as e:
            self.logger.error(f"Failed to schedule tasks: {e}")
    
    async def refresh_tasks(self):
        """Refresh task schedule from database (called periodically)."""
        try:
            self.logger.debug("Starting task refresh...")
            
            # Get current job IDs to identify business tasks (not system tasks)
            current_jobs = self.scheduler.get_jobs()
            self.logger.debug(f"Current jobs before refresh: {[job.id for job in current_jobs]}")
            
            business_task_ids = [job.id for job in current_jobs if not job.id.startswith('system_')]
            self.logger.debug(f"Business task IDs to remove: {business_task_ids}")
            
            # Remove only business tasks, not system tasks
            for job_id in business_task_ids:
                try:
                    self.scheduler.remove_job(job_id)
                    self.logger.debug(f"Removed business task job: {job_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove job {job_id}: {e}")
            
            # Reload and reschedule business tasks
            await self.schedule_all_tasks()
            
            # Log final job count
            final_jobs = self.scheduler.get_jobs()
            self.logger.debug(f"Jobs after refresh: {[job.id for job in final_jobs]}")
            
            self.logger.info("Task schedule refreshed from database")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh tasks: {e}")
            import traceback
            self.logger.error(f"Refresh tasks error traceback: {traceback.format_exc()}")
    
    async def run(self):
        """Start the task processor."""
        try:
            self.logger.info("Starting task processor...")
            
            # Initialize services
            await self.initialize_services()
            
            # Start scheduler
            self.scheduler.start()
            self.logger.info("Scheduler started")
            
            # Schedule initial tasks
            await self.schedule_all_tasks()
            
            # Add periodic task refresh (every 5 minutes)
            self.scheduler.add_job(
                func=self.refresh_tasks,
                trigger=IntervalTrigger(minutes=5),
                id="system_refresh_tasks",
                name="Refresh tasks from database"
            )
            
            self.logger.info("Task processor running. Press Ctrl+C to stop.")
            self.logger.info("System refresh task scheduled with ID: system_refresh_tasks")
            
            # Keep the processor running
            try:
                # Wait indefinitely instead of trying to run the event loop
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
            finally:
                self.scheduler.shutdown()
                self.logger.info("Task processor stopped")
                
        except Exception as e:
            self.logger.error(f"Task processor failed: {e}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    processor = TaskProcessor()
    asyncio.run(processor.run())
