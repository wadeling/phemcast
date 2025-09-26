"""
Post-action services for sending notifications after task completion.
This module provides an abstraction for different notification channels like email, Feishu, Slack, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PostActionResult:
    """Result of a post-action execution."""
    
    def __init__(self, success: bool, message: str = "", error: Optional[str] = None):
        self.success = success
        self.message = message
        self.error = error


class PostAction(ABC):
    """Abstract base class for post-actions."""
    
    @abstractmethod
    async def execute(self, task_group_id: str, task_results: List[Dict], user_name: str) -> PostActionResult:
        """
        Execute the post-action.
        
        Args:
            task_group_id: ID of the task group
            task_results: List of task results
            user_name: Username
            
        Returns:
            PostActionResult: Result of the execution
        """
        pass


class PostActionManager:
    """Manager for executing multiple post-actions."""
    
    def __init__(self):
        self.actions: List[PostAction] = []
    
    def add_action(self, action: PostAction):
        """Add a post-action to the manager."""
        self.actions.append(action)
    
    async def execute_all(self, task_group_id: str, task_results: List[Dict], user_name: str) -> List[PostActionResult]:
        """
        Execute all registered post-actions.
        
        Args:
            task_group_id: ID of the task group
            task_results: List of task results
            user_name: Username
            
        Returns:
            List of PostActionResult objects
        """
        results = []
        
        for action in self.actions:
            try:
                result = await action.execute(task_group_id, task_results, user_name)
                results.append(result)
                
                if result.success:
                    logger.info(f"Post-action {action.__class__.__name__} executed successfully: {result.message}")
                else:
                    logger.warning(f"Post-action {action.__class__.__name__} failed: {result.error}")
                    
            except Exception as e:
                logger.error(f"Post-action {action.__class__.__name__} raised an exception: {str(e)}")
                results.append(PostActionResult(
                    success=False,
                    error=f"Exception: {str(e)}"
                ))
        
        return results
