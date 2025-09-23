#!/usr/bin/env python3
"""Task manager service for handling scheduled task operations."""
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import text
from database import get_async_db
from models import ScheduledTask, ScheduledTaskCreate, ScheduledTaskUpdate
from logging_config import get_logger

logger = get_logger(__name__)


class TaskManager:
    """Manages scheduled task operations."""
    
    def __init__(self):
        """Initialize the task manager."""
        # 东八区时区 (UTC+8)
        self.east_eight_timezone = timezone(timedelta(hours=8))
    
    def convert_east_eight_to_utc(self, time_str: str) -> str:
        """
        将东八区时间字符串转换为UTC时间字符串
        
        Args:
            time_str: 东八区时间字符串，格式为 "HH:MM"
            
        Returns:
            UTC时间字符串，格式为 "HH:MM"
        """
        try:
            # 解析东八区时间
            hour, minute = map(int, time_str.split(':'))
            
            # 创建今天的东八区时间
            today = datetime.now(self.east_eight_timezone).date()
            east_eight_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            east_eight_time = east_eight_time.replace(tzinfo=self.east_eight_timezone)
            
            # 转换为UTC时间
            utc_time = east_eight_time.astimezone(timezone.utc)
            
            # 返回UTC时间字符串
            return utc_time.strftime('%H:%M')
            
        except Exception as e:
            logger.error(f"Failed to convert time {time_str} from East Eight to UTC: {e}")
            # 如果转换失败，返回原时间（假设已经是UTC时间）
            return time_str
    
    async def create_task(self, task_data: Dict[str, Any], username: str) -> str:
        """Create a new scheduled task."""
        try:
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            
            # Log incoming task data for debugging
            logger.debug(f"Creating task with data: {task_data}")
            logger.debug(f"Companies from request: {task_data.get('companies', [])}")
            
            # Prepare task data
            task_data['id'] = task_id
            task_data['user_name'] = username
            task_data['created_at'] = datetime.utcnow()
            task_data['updated_at'] = datetime.utcnow()
            
            # Convert companies list to JSON string for database storage
            companies_json = json.dumps(task_data.get('companies', []))
            
            logger.debug(f"Companies JSON: {companies_json}")
            
            # Convert East Eight time to UTC time before saving to database
            schedule_time_utc = self.convert_east_eight_to_utc(task_data['schedule_time'])
            logger.info(f"Converting schedule time from East Eight {task_data['schedule_time']} to UTC {schedule_time_utc}")
            
            db = await get_async_db()
            async with db as session:
                # Insert new task
                await session.execute(
                    text("""
                        INSERT INTO scheduled_tasks (
                            id, task_name, user_name, companies, max_articles,
                            schedule_type, schedule_time, schedule_day, is_active,
                            created_at, updated_at
                        ) VALUES (
                            :id, :task_name, :user_name, :companies, :max_articles,
                            :schedule_type, :schedule_time, :schedule_day, :is_active,
                            :created_at, :updated_at
                        )
                    """),
                    {
                        'id': task_id,
                        'task_name': task_data['task_name'],
                        'user_name': username,
                        'companies': companies_json,
                        'max_articles': str(task_data.get('max_articles', 5)),
                        'schedule_type': task_data['schedule_type'],
                        'schedule_time': schedule_time_utc,  # 使用转换后的UTC时间
                        'schedule_day': task_data.get('schedule_day'),
                        'is_active': True,
                        'created_at': task_data['created_at'],
                        'updated_at': task_data['updated_at']
                    }
                )
                await session.commit()
                
            logger.info(f"Created scheduled task {task_id} for user {username}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create scheduled task: {e}")
            raise
    
    async def get_user_tasks(self, username: str) -> List[Dict[str, Any]]:
        """Get all scheduled tasks for a user."""
        try:
            logger.debug(f"Attempting to get tasks for user: {username}")
            db = await get_async_db()
            logger.debug("Got database session, executing query...")
            
            async with db as session:
                # Query user's tasks
                result = await session.execute(
                    text("SELECT * FROM scheduled_tasks WHERE user_name = :username ORDER BY created_at DESC"),
                    {'username': username}
                )
                rows = result.fetchall()
                logger.debug(f"Query returned {len(rows)} rows")
                
                tasks = []
                for row in rows:
                    try:
                        task_data = {
                            'id': row.id,
                            'task_name': row.task_name,
                            'user_name': row.user_name,
                            'companies': json.loads(row.companies) if row.companies else [],
                            'max_articles': int(row.max_articles) if row.max_articles else 5,
                            'schedule_type': row.schedule_type,
                            'schedule_time': row.schedule_time,
                            'schedule_day': row.schedule_day,
                            'is_active': bool(row.is_active),
                            'last_run': row.last_run,
                            'next_run': row.next_run,
                            'created_at': row.created_at,
                            'updated_at': row.updated_at
                        }
                        tasks.append(task_data)
                        logger.debug(f"Processed task: {task_data['task_name']}")
                    except Exception as row_error:
                        logger.error(f"Failed to process task row {getattr(row, 'id', 'unknown')}: {row_error}")
                        continue
                
            logger.info(f"Retrieved {len(tasks)} tasks for user {username}")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get user tasks: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def update_task(self, task_id: str, username: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing scheduled task."""
        try:
            # Verify task ownership
            db = await get_async_db()
            async with db as session:
                # Check if task exists and belongs to user
                result = await session.execute(
                    text("SELECT id FROM scheduled_tasks WHERE id = :task_id AND user_name = :username"),
                    {'task_id': task_id, 'username': username}
                )
                if not result.fetchone():
                    logger.warning(f"Task {task_id} not found or not owned by user {username}")
                    return False
                
                # Prepare update data
                update_fields = []
                params = {'task_id': task_id, 'username': username}
                
                if 'task_name' in update_data:
                    update_fields.append("task_name = :task_name")
                    params['task_name'] = update_data['task_name']
                
                if 'companies' in update_data:
                    update_fields.append("companies = :companies")
                    params['companies'] = json.dumps(update_data['companies'])
                
                if 'max_articles' in update_data:
                    update_fields.append("max_articles = :max_articles")
                    params['max_articles'] = str(update_data['max_articles'])
                
                if 'schedule_type' in update_data:
                    update_fields.append("schedule_type = :schedule_type")
                    params['schedule_type'] = update_data['schedule_type']
                
                if 'schedule_time' in update_data:
                    update_fields.append("schedule_time = :schedule_time")
                    # Convert East Eight time to UTC time
                    schedule_time_utc = self.convert_east_eight_to_utc(update_data['schedule_time'])
                    logger.info(f"Converting schedule time from East Eight {update_data['schedule_time']} to UTC {schedule_time_utc}")
                    params['schedule_time'] = schedule_time_utc
                
                if 'schedule_day' in update_data:
                    update_fields.append("schedule_day = :schedule_day")
                    params['schedule_day'] = update_data['schedule_day']
                
                if 'is_active' in update_data:
                    update_fields.append("is_active = :is_active")
                    params['is_active'] = update_data['is_active']
                
                # Always update the updated_at timestamp
                update_fields.append("updated_at = :updated_at")
                params['updated_at'] = datetime.utcnow()
                
                if update_fields:
                    # Build and execute update query
                    update_query = f"UPDATE scheduled_tasks SET {', '.join(update_fields)} WHERE id = :task_id AND user_name = :username"
                    await session.execute(text(update_query), params)
                    await session.commit()
                    
                    logger.info(f"Updated scheduled task {task_id} for user {username}")
                    return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to update scheduled task: {e}")
            raise
    
    async def delete_task(self, task_id: str, username: str) -> bool:
        """Delete a scheduled task."""
        try:
            db = await get_async_db()
            async with db as session:
                # Check if task exists and belongs to user
                result = await session.execute(
                    text("SELECT id FROM scheduled_tasks WHERE id = :task_id AND user_name = :username"),
                    {'task_id': task_id, 'username': username}
                )
                if not result.fetchone():
                    logger.warning(f"Task {task_id} not found or not owned by user {username}")
                    return False
                
                # Delete the task
                await session.execute(
                    text("DELETE FROM scheduled_tasks WHERE id = :task_id AND user_name = :username"),
                    {'task_id': task_id, 'username': username}
                )
                await session.commit()
                
                logger.info(f"Deleted scheduled task {task_id} for user {username}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete scheduled task: {e}")
            raise
    
    async def toggle_task_status(self, task_id: str, username: str) -> bool:
        """Toggle the active status of a scheduled task."""
        try:
            db = await get_async_db()
            async with db as session:
                # Check if task exists and belongs to user
                result = await session.execute(
                    text("SELECT id, is_active FROM scheduled_tasks WHERE id = :task_id AND user_name = :username"),
                    {'task_id': task_id, 'username': username}
                )
                row = result.fetchone()
                if not row:
                    logger.warning(f"Task {task_id} not found or not owned by user {username}")
                    return False
                
                # Toggle the status
                new_status = not row.is_active
                await session.execute(
                    text("UPDATE scheduled_tasks SET is_active = :is_active, updated_at = :updated_at WHERE id = :task_id AND user_name = :username"),
                    {
                        'is_active': new_status,
                        'updated_at': datetime.utcnow(),
                        'task_id': task_id,
                        'username': username
                    }
                )
                await session.commit()
                
                logger.info(f"Toggled scheduled task {task_id} status to {new_status} for user {username}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to toggle scheduled task status: {e}")
            raise


# Global task manager instance
task_manager = TaskManager()
