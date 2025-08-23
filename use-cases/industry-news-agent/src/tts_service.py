"""Text-to-Speech service using Minimaxi API."""
import os
import json
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets

from .settings import Settings
from .logging_config import get_logger

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
