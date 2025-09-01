"""Text-to-Speech service using Minimaxi API."""
import os
import json
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import secrets

from settings import Settings
from logging_config import get_logger

logger = get_logger(__name__)


class TTSVoiceConfig:
    """Voice configuration for TTS."""
    
    def __init__(self):
        # 成熟女性语音配置 - 使用Minimaxi支持的语音ID
        self.voice_id = "female-chengshu"  # 默认使用成熟女声
        self.speed = 1     # 语速 (Minimaxi期望整数)
        self.vol = 1       # 音量 (Minimaxi期望整数)
        self.pitch = 0     # 音调 (Minimaxi期望整数)
        self.emotion = "happy"  # 情感 (Minimaxi特有参数)


class MinimaxiTTSService:
    """Text-to-Speech service using Minimaxi API."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_url = "https://api.minimaxi.com/v1/t2a_v2"
        self.api_key = getattr(settings, 'minimaxi_api_key', None)
        self.group_id = getattr(settings, 'minimaxi_group_id', None)  # 添加GroupId支持
        self.voice_config = TTSVoiceConfig()
        
        # 创建语音文件存储目录
        self.audio_dir = Path(settings.output_dir) / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建临时访问目录
        self.temp_audio_dir = Path(settings.output_dir) / "temp_audio"
        self.temp_audio_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TTS service initialized. Audio directory: {self.audio_dir}")
    
    def _generate_filename(self, text: str, report_id: str) -> str:
        """Generate unique filename for audio file."""
        # 使用文本内容的hash和报告ID生成文件名
        text_hash = hashlib.md5(text[:100].encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"report_{report_id}_{text_hash}_{timestamp}.mp3"
    
    def _generate_access_token(self) -> str:
        """Generate secure access token for audio files."""
        return secrets.token_urlsafe(32)
    
    def _load_audio_prompt(self) -> str:
        """Load audio prompt from local file."""
        try:
            prompt_file = Path(__file__).parent.parent / "audio_prompt.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                logger.warning(f"Audio prompt file not found: {prompt_file}")
                return self._get_default_prompt()
        except Exception as e:
            logger.error(f"Error loading audio prompt: {e}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default audio prompt if file not found."""
        return """你是一个专业的行业分析师，请根据以下博客文章内容，生成一个简洁、清晰的语音播报中文摘要。

要求：
1. 总结文章的核心观点和关键信息
2. 使用简洁明了的语言，适合语音播报
3. 保持逻辑清晰，结构完整
4. 长度控制在600-700字之间
5. 语言风格要专业但不失亲和力

请基于以下文章内容生成中文摘要：

`{articles_content}`

请直接返回摘要内容，不要添加任何额外的说明或格式。"""
    
    def _format_articles_for_summary(self, articles: List[Dict[str, Any]]) -> str:
        """Format articles list into text for summary generation."""
        if not articles:
            return "暂无文章内容"
        
        formatted_articles = []
        for i, article in enumerate(articles, 1):
            title = article.get('title', '无标题')
            content = article.get('content', '无内容')
            
            # 清理内容，移除多余的空白字符
            content = ' '.join(content.split())
            
            # 限制内容长度，避免过长
            if len(content) > 16000:
                content = content[:16000] + "..."
            
            formatted_articles.append(f"文章{i}：{title}\n内容：{content}")
        
        return "\n\n".join(formatted_articles)
    
    async def generate_summary_from_articles(
        self, 
        articles: List[Dict[str, Any]], 
        report_id: str
    ) -> Dict[str, Any]:
        """
        Generate summary from articles using AI model, then convert to speech.
        
        Args:
            articles: List of article dictionaries with 'title' and 'content'
            report_id: Unique identifier for the report
            
        Returns:
            Dictionary containing summary text, audio info, and success status
        """
        try:
            logger.info(f"Generating summary from {len(articles)} articles for report {report_id}")
            
            # 1. 格式化文章内容
            articles_text = self._format_articles_for_summary(articles)
            logger.debug(f"Formatted articles text length: {len(articles_text)}")
            
            # 2. 加载提示词
            prompt_template = self._load_audio_prompt()
            prompt = prompt_template.format(articles_content=articles_text)
            
            # 3. 调用大模型生成摘要
            summary = await self._call_ai_model_for_summary(prompt)
            if not summary:
                raise Exception("Failed to generate summary from AI model")
            
            logger.info(f"Generated summary length: {len(summary)} characters")
            logger.debug(f"Summary content: {summary[:200]}...")
            
            # 4. 将摘要转换为语音
            audio_result = await self.generate_speech(summary, report_id)
            
            if audio_result.get('success'):
                # 添加摘要信息到结果
                audio_result['summary'] = summary
                audio_result['articles_count'] = len(articles)
                audio_result['summary_length'] = len(summary)
                
                logger.info(f"Successfully generated audio summary for report {report_id}")
                return audio_result
            else:
                logger.error(f"Failed to generate audio for summary: {audio_result.get('error')}")
                return {
                    'success': False,
                    'error': f"Audio generation failed: {audio_result.get('error')}",
                    'summary': summary,
                    'articles_count': len(articles)
                }
                
        except Exception as e:
            logger.error(f"Failed to generate summary from articles: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'articles_count': len(articles) if 'articles' in locals() else 0
            }
    
    async def _call_ai_model_for_summary(self, prompt: str) -> Optional[str]:
        """
        Call AI model to generate summary from prompt.
        
        Args:
            prompt: Formatted prompt with articles content
            
        Returns:
            Generated summary text or None if failed
        """
        try:
            # 使用 OpenAI API 生成摘要
            if hasattr(self.settings, 'openai_api_key') and self.settings.openai_api_key:
                return await self._call_openai_api(prompt)
            
            # 如果没有配置 OpenAI API，使用简单的文本处理（fallback）
            else:
                logger.warning("OpenAI API not configured, using fallback text processing")
                return self._fallback_text_summary(prompt)
                
        except Exception as e:
            logger.error(f"Error calling AI model: {e}")
            return None
    
    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for summary generation using new 1.0.0+ interface."""
        try:
            import openai
            
            # 创建 OpenAI 客户端（新版本）
            client = openai.OpenAI(api_key=self.settings.openai_api_key)
            
            # 调用API（新版本）
            response = client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的行业分析师，擅长生成简洁的语音播报摘要。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=15000,  # 增加token数量以支持600-700字的摘要
                #temperature=0.6
                temperature=1.3
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"OpenAI API summary generated successfully.response: {response}")
            return summary
            
        except ImportError:
            logger.error("OpenAI library not installed")
            return None
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def _fallback_text_summary(self, prompt: str) -> str:
        """Fallback text processing when AI model is not available."""
        try:
            # 简单的文本处理：提取关键信息
            articles_text = prompt.split("`{articles_content}`")[1] if "`{articles_content}`" in prompt else prompt
            
            # 提取标题和内容
            lines = articles_text.split('\n')
            titles = []
            contents = []
            
            for line in lines:
                if line.startswith('文章'):
                    titles.append(line)
                elif line.startswith('内容：'):
                    contents.append(line[3:])  # 移除"内容："前缀
            
            # 生成简单摘要
            if titles and contents:
                summary = f"本次报告分析了{len(titles)}篇文章。"
                summary += " ".join([f"文章《{title.split('：')[1]}》主要讨论了{content[:100]}等内容。" 
                                   for title, content in zip(titles, contents)])
                summary += "这些文章反映了当前行业的发展趋势和重要动态。"
            else:
                summary = "本次报告分析了多篇行业相关文章，涵盖了技术发展、市场趋势等多个方面。"
            
            logger.info("Generated fallback summary using text processing")
            return summary
            
        except Exception as e:
            logger.error(f"Fallback summary generation error: {e}")
            return "本次报告分析了多篇行业相关文章，内容涵盖技术发展、市场趋势等多个方面。"
    
    def _create_temp_access(self, audio_path: Path, token: str) -> Path:
        """Create temporary access file with token."""
        temp_file = self.temp_audio_dir / f"{token}.mp3"
        if audio_path.exists():
            # 创建符号链接或复制文件
            try:
                if temp_file.exists():
                    temp_file.unlink()
                temp_file.symlink_to(audio_path)
            except OSError:
                # 如果符号链接失败，复制文件
                import shutil
                shutil.copy2(audio_path, temp_file)
        return temp_file
    
    async def generate_speech(
        self, 
        text: str, 
        report_id: str,
        voice_config: Optional[TTSVoiceConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate speech from text using Minimaxi API.
        
        Args:
            text: Text to convert to speech
            report_id: Unique identifier for the report
            voice_config: Voice configuration (optional)
            
        Returns:
            Dictionary containing file path, access token, and expiry info
        """
        try:
            if not self.api_key:
                raise ValueError("Minimaxi API key not configured")
            
            if not self.group_id:
                raise ValueError("Minimaxi Group ID not configured")
            
            # 使用提供的语音配置或默认配置
            config = voice_config or self.voice_config
            
            # 准备API请求 - 根据Minimaxi API规范
            payload = {
                "model": "speech-2.5-hd-preview",  # 使用高清预览模型
                "text": text,
                "stream": False,  # 非流式
                "voice_setting": {
                    "voice_id": config.voice_id,
                    "speed": int(config.speed),      # 确保是整数
                    "vol": int(config.vol),          # 确保是整数
                    "pitch": int(config.pitch),      # 确保是整数
                    "emotion": config.emotion
                },
                "audio_setting": {
                    "sample_rate": 32000,
                    "bitrate": 128000,
                    "format": "mp3",
                    "channel": 1
                },
                "output_format": "hex"  # 返回hex格式的音频数据
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建完整的URL，包含GroupId
            api_url = f"{self.api_url}?GroupId={self.group_id}"
            
            logger.info(f"Generating speech for report {report_id}, text length: {len(text)}")
            logger.debug(f"API URL: {api_url}")
            logger.debug(f"Request payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            # 调用Minimaxi API
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Minimaxi API error: {response.status_code} - {response.text}")
                raise Exception(f"TTS API error: {response.status_code}")
            
            # 解析响应数据
            response_data = response.json()
            
            # 检查API响应状态
            if response_data.get('base_resp', {}).get('status_code') != 0:
                error_msg = response_data.get('base_resp', {}).get('status_msg', 'Unknown error')
                logger.error(f"Minimaxi API business error: {error_msg}")
                raise Exception(f"TTS business error: {error_msg}")
            
            # 获取音频数据 - Minimaxi返回hex格式
            audio_hex = response_data.get('data', {}).get('audio')
            if not audio_hex:
                logger.error("No audio data in response")
                raise Exception("No audio data received from API")
            
            # 将hex字符串转换为二进制数据
            try:
                audio_data = bytes.fromhex(audio_hex)
            except ValueError as e:
                logger.error(f"Invalid hex audio data: {e}")
                raise Exception("Invalid audio data format")
            
            # 生成文件名和保存路径
            filename = self._generate_filename(text, report_id)
            audio_path = self.audio_dir / filename
            
            # 保存音频文件
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # 生成访问token和临时访问文件
            access_token = self._generate_access_token()
            temp_file = self._create_temp_access(audio_path, access_token)
            
            # 设置24小时过期时间
            expiry_time = datetime.now() + timedelta(hours=24)
            
            # 保存token信息到数据库或文件（这里简化处理）
            token_info = {
                "token": access_token,
                "audio_path": str(audio_path),
                "temp_path": str(temp_file),
                "expires_at": expiry_time.isoformat(),
                "report_id": report_id
            }
            
            # 保存token信息到临时文件（生产环境建议使用数据库）
            token_file = self.temp_audio_dir / f"{access_token}.json"
            with open(token_file, 'w', encoding='utf-8') as f:
                json.dump(token_info, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Speech generated successfully: {filename}")
            
            return {
                "success": True,
                "audio_path": str(audio_path),
                "access_token": access_token,
                "expires_at": expiry_time.isoformat(),
                "file_size": len(audio_data),
                "duration_estimate": len(text) // 10  # 粗略估计时长（每10个字符约1秒）
            }
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_audio_access_url(self, token: str) -> Optional[str]:
        """Get audio access URL for a given token."""
        token_file = self.temp_audio_dir / f"{token}.json"
        
        if not token_file.exists():
            return None
        
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                token_info = json.load(f)
            
            # 检查是否过期
            expiry_time = datetime.fromisoformat(token_info["expires_at"])
            if datetime.now() > expiry_time:
                # 清理过期文件
                self._cleanup_expired_token(token)
                return None
            
            # 返回访问URL
            base_url = getattr(self.settings, 'base_url', 'http://localhost:8000')
            return f"{base_url}/audio/{token}"
            
        except Exception as e:
            logger.error(f"Error reading token info: {str(e)}")
            return None
    
    def _cleanup_expired_token(self, token: str):
        """Clean up expired token and associated files."""
        try:
            token_file = self.temp_audio_dir / f"{token}.json"
            temp_audio_file = self.temp_audio_dir / f"{token}.mp3"
            
            if token_file.exists():
                token_file.unlink()
            if temp_audio_file.exists():
                temp_audio_file.unlink()
                
            logger.info(f"Cleaned up expired token: {token}")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired token {token}: {str(e)}")
    
    def cleanup_expired_tokens(self):
        """Clean up all expired tokens."""
        try:
            for token_file in self.temp_audio_dir.glob("*.json"):
                try:
                    with open(token_file, 'r', encoding='utf-8') as f:
                        token_info = json.load(f)
                    
                    expiry_time = datetime.fromisoformat(token_info["expires_at"])
                    if datetime.now() > expiry_time:
                        token = token_info["token"]
                        self._cleanup_expired_token(token)
                        
                except Exception as e:
                    logger.error(f"Error processing token file {token_file}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error during token cleanup: {str(e)}")


# 便捷函数
def create_tts_service(settings: Settings) -> MinimaxiTTSService:
    """Create TTS service instance."""
    return MinimaxiTTSService(settings)
