#!/usr/bin/env python3
"""Scheduler service singleton for managing background tasks."""
import asyncio
from task_processor import TaskProcessor

class SchedulerService:
    """Singleton scheduler service."""
    
    def __init__(self):
        self.task_processor = None
        self._running = False
    
    async def start(self):
        """Start the scheduler service."""
        if self._running:
            return
        
        try:
            self.task_processor = TaskProcessor()
            await self.task_processor.run()
            self._running = True
        except Exception as e:
            raise e
    
    async def stop(self):
        """Stop the scheduler service."""
        if self.task_processor:
            # The task processor handles its own shutdown
            pass
        self._running = False

# Global scheduler service instance
task_scheduler = SchedulerService()
