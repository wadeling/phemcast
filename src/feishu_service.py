"""
Feishu notification service for sending task completion reports.
"""

import json
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from logging_config import get_logger
from post_actions import PostAction, PostActionResult
from database import get_user_feishu_settings

logger = get_logger(__name__)


class FeishuNotificationService(PostAction):
    """Feishu notification service."""
    
    def __init__(self):
        self.name = "FeishuNotification"
    
    async def execute(self, task_group_id: str, task_results: List[Dict], user_name: str) -> PostActionResult:
        """
        Send Feishu notification for task group completion.
        
        Args:
            task_group_id: ID of the task group
            task_results: List of task results
            user_name: Username
            
        Returns:
            PostActionResult: Result of the execution
        """
        try:
            # Get user Feishu settings
            webhook_url, notifications_enabled = await get_user_feishu_settings(user_name)
            
            if not notifications_enabled or not webhook_url:
                return PostActionResult(
                    success=True,
                    message="Feishu notifications disabled or no webhook URL configured"
                )
            
            # Build Feishu card
            card_data = self._build_feishu_card(task_group_id, task_results, user_name)
            
            # Send to Feishu
            success = await self._send_to_feishu(webhook_url, card_data)
            
            if success:
                return PostActionResult(
                    success=True,
                    message=f"Feishu notification sent successfully for task group {task_group_id}"
                )
            else:
                return PostActionResult(
                    success=False,
                    error="Failed to send Feishu notification"
                )
                
        except Exception as e:
            logger.error(f"Feishu notification failed: {str(e)}")
            return PostActionResult(
                success=False,
                error=f"Feishu notification failed: {str(e)}"
            )
    
    def _build_feishu_card(self, task_group_id: str, task_results: List[Dict], user_name: str, **kwargs) -> Dict[str, Any]:
        """
        Build Feishu card data for task group completion.
        
        Args:
            task_group_id: ID of the task group
            task_results: List of task results
            user_name: Username
            **kwargs: Additional keyword arguments (e.g., report_paths)
            
        Returns:
            Dict containing Feishu card data
        """
        successful_tasks = [result for result in task_results if result.get("status") != "error"]
        failed_tasks = [result for result in task_results if result.get("status") == "error"]
        
        # Build card elements
        elements = []
        
        # Task details - focus on audio content
        for i, task_result in enumerate(successful_tasks, 1):
            company_name = task_result.get("company_name", "Unknown")
            articles = task_result.get("articles", [])
            report_paths = task_result.get("report_paths", {})
            audio_content_text = task_result.get("audio_content_text", "")
            task_id = task_result.get("task_id", "N/A")
            
            # Build task content
            task_content = f"**🎯 {company_name} 语音播客**\n\n"
            
            # Add articles
            if articles:
                task_content += "**📰 抓取文章:**\n"
                for article in articles[:3]:  # Show first 3 articles
                    # Handle both dict and Article object
                    if hasattr(article, 'title'):
                        title = article.title
                    elif isinstance(article, dict):
                        title = article.get("title", "Unknown Title")
                    else:
                        title = "Unknown Title"
                    task_content += f"• {title}\n"
                if len(articles) > 3:
                    task_content += f"• ... 还有 {len(articles) - 3} 篇文章\n"
                task_content += "\n"
            
            # Add audio content text if available
            if audio_content_text:
                # Truncate content if too long (Feishu has content length limits)
                display_text = audio_content_text[:2000] + "..." if len(audio_content_text) > 2000 else audio_content_text
                task_content += f"**🎧 语音播客内容**:\n{display_text}\n\n"
            else:
                task_content += "⚠️ 无语音播客内容\n\n"
            
            elements.append({
                "tag": "markdown",
                "content": task_content,
                "text_align": "left",
                "text_size": "normal_v2"
            })
            
            # Add audio button if available
            audio_url = report_paths.get("audio", "")
            if audio_url:
                # Construct full URL for audio playback
                from settings import load_settings
                settings = load_settings()
                full_audio_url = f"{settings.base_url}/download/{task_id}/audio"
                
                elements.append({
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": f"🎧 播放 {company_name} 播客"
                    },
                    "type": "primary",
                    "width": "default",
                    "size": "medium",
                    "behaviors": [
                        {
                            "type": "open_url",
                            "default_url": full_audio_url,
                            "pc_url": "",
                            "ios_url": "",
                            "android_url": ""
                        }
                    ]
                })
            
            if i < len(successful_tasks):
                elements.append({"tag": "hr"})
        
        # Add failed tasks if any
        if failed_tasks:
            elements.append({
                "tag": "markdown",
                "content": f"**❌ 失败任务 ({len(failed_tasks)} 个):**\n" + 
                          "\n".join([f"• {task.get('company_name', 'Unknown')}" for task in failed_tasks]),
                "text_align": "left",
                "text_size": "normal_v2"
            })

        # tail section
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "markdown",
            "content": f"**🎧  播客由Phemcast智能体召唤而来**\n\n",
            "text_align": "left",
            "text_size": "normal_v2"
        })
        
        # Build the complete card
        card_data = {
            "msg_type": "interactive",
            "card": {
                "schema": "2.0",
                "config": {
                    "update_multi": True,
                    "style": {
                        "text_size": {
                            "normal_v2": {
                                "default": "normal",
                                "pc": "normal",
                                "mobile": "heading"
                            }
                        }
                    }
                },
                "body": {
                    "direction": "vertical",
                    "padding": "12px 12px 12px 12px",
                    "elements": elements
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "🎧 Phemcast 语音播客报告"
                    },
                    "template": "orange",
                    "padding": "12px 12px 12px 12px"
                }
            }
        }
        
        return card_data
    
    async def _send_to_feishu(self, webhook_url: str, card_data: Dict[str, Any]) -> bool:
        """
        Send card data to Feishu webhook.
        
        Args:
            webhook_url: Feishu webhook URL
            card_data: Card data to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=card_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == 0:
                            logger.info("Feishu notification sent successfully")
                            return True
                        else:
                            logger.error(f"Feishu API error: {result}")
                            return False
                    else:
                        logger.error(f"Feishu webhook failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Feishu notification: {str(e)}")
            return False
