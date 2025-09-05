"""
音声复刻工具模块

该模块提供音声复刻功能，支持将音频文件上传到 MiniMax API 进行声音克隆。
"""

import json
import os
import logging
from typing import Optional, Dict, Any
import requests
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)


class VoiceCloneService:
    """音声复刻服务类"""
    
    def __init__(self, group_id: str, api_key: str):
        """
        初始化音声复刻服务
        
        Args:
            group_id: MiniMax API 的 Group ID
            api_key: MiniMax API 的 API Key
        """
        self.group_id = group_id
        self.api_key = api_key
        self.base_url = "https://api.minimaxi.com/v1"
        
    def upload_voice_file(self, file_path: str, purpose: str = "voice_clone") -> Optional[str]:
        """
        上传音频文件进行音声复刻
        
        Args:
            file_path: 音频文件路径
            purpose: 文件用途，默认为 "voice_clone"
            
        Returns:
            文件ID，如果上传失败返回 None
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"音频文件不存在: {file_path}")
                return None
                
            # 构建上传URL
            url = f"{self.base_url}/files/upload?GroupId={self.group_id}"
            
            # 设置请求头
            headers = {
                'authority': 'api.minimaxi.com',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # 设置请求数据
            data = {
                'purpose': purpose
            }
            
            # 打开并上传文件
            with open(file_path, 'rb') as file:
                files = {
                    'file': file
                }
                
                logger.info(f"开始上传音频文件: {file_path}")
                response = requests.post(url, headers=headers, data=data, files=files)
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    file_id = result.get("file", {}).get("file_id")
                    if file_id:
                        logger.info(f"音频文件上传成功，文件ID: {file_id}")
                        return file_id
                    else:
                        logger.error(f"响应中未找到文件ID: {result}")
                        return None
                else:
                    logger.error(f"上传失败，状态码: {response.status_code}, 响应: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"上传音频文件时发生错误: {str(e)}")
            return None
    
    def clone_voice(self, file_id: int, voice_id: str = "phemcastvoice", 
                   clone_prompt: Optional[Dict[str, str]] = None,
                   text: Optional[str] = None, 
                   model: Optional[str] = None,
                   need_noise_reduction: bool = False,
                   need_volume_normalization: bool = False,
                   aigc_watermark: bool = False) -> Optional[Dict[str, Any]]:
        """
        调用音频复刻接口，生成复刻音色

        Args:
            file_id: 已上传音频的文件ID (int64)
            voice_id: 复刻音色的ID（可自定义，长度8-256，首字符必须为英文字母）
            clone_prompt: 音色复刻参数，包含text字段的字典
            text: 复刻试听参数，模型将使用复刻后的音色念诵本段文本内容
            model: 复刻试听参数，指定试听使用的语音模型（传text时必传）
            need_noise_reduction: 是否开启降噪
            need_volume_normalization: 是否开启音量归一化
            aigc_watermark: 是否在合成试听音频末尾添加音频节奏标识

        Returns:
            接口返回的结果字典，如果失败返回 None
        """
        try:
            # 参数验证
            if not isinstance(file_id, int):
                logger.error(f"file_id 必须是整数类型，当前类型: {type(file_id)}")
                return None
                
            if not self._validate_voice_id(voice_id):
                logger.error(f"voice_id 格式不正确: {voice_id}")
                return None
                
            if text and not model:
                logger.error("传入text参数时必须同时传入model参数")
                return None
                
            if text and len(text) > 2000:
                logger.error("text参数长度不能超过2000字符")
                return None

            url = f"{self.base_url}/voice_clone?GroupId={self.group_id}"
            
            # 构建请求体
            payload_data = {
                "file_id": file_id,
                "voice_id": voice_id,
                "need_noise_reduction": need_noise_reduction,
                "need_volume_normalization": need_volume_normalization,
                "aigc_watermark": aigc_watermark
            }
            
            # 添加可选参数
            if clone_prompt:
                payload_data["clone_prompt"] = clone_prompt
                
            if text:
                payload_data["text"] = text
                
            if model:
                payload_data["model"] = model
            
            payload = json.dumps(payload_data)
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'content-type': 'application/json'
            }
            
            logger.info(f"请求音频复刻: file_id={file_id}, voice_id={voice_id}")
            response = requests.post(url, headers=headers, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                logger.info("音频复刻请求成功")
                
                # 检查业务状态码
                base_resp = result.get('base_resp', {})
                status_code = base_resp.get('status_code')
                if status_code == 0:
                    logger.info("音频复刻成功")
                else:
                    logger.warning(f"音频复刻业务状态异常: {base_resp.get('status_msg', '未知错误')}")
                
                return result
            else:
                logger.error(f"音频复刻失败，状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"音频复刻请求异常: {str(e)}")
            return None
    
    def _validate_voice_id(self, voice_id: str) -> bool:
        """
        验证voice_id格式
        
        Args:
            voice_id: 要验证的voice_id
            
        Returns:
            验证是否通过
        """
        if not voice_id or not isinstance(voice_id, str):
            return False
            
        # 长度检查
        if len(voice_id) < 8 or len(voice_id) > 256:
            return False
            
        # 首字符必须是英文字母
        if not voice_id[0].isalpha():
            return False
            
        # 末位字符不能是-、_
        if voice_id[-1] in ['-', '_']:
            return False
            
        # 只允许数字、字母、-、_
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(c in allowed_chars for c in voice_id):
            return False
            
        return True

    def get_voice_clone_status(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取音声复刻状态
        
        Args:
            file_id: 文件ID
            
        Returns:
            状态信息字典，如果获取失败返回 None
        """
        try:
            url = f"{self.base_url}/files/{file_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取文件状态失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取音声复刻状态时发生错误: {str(e)}")
            return None


def clone_voice_from_file(file_path: str, group_id: str, api_key: str) -> Optional[str]:
    """
    便捷函数：从文件进行音声复刻
    
    Args:
        file_path: 音频文件路径
        group_id: MiniMax API 的 Group ID
        api_key: MiniMax API 的 API Key
        
    Returns:
        文件ID，如果失败返回 None
    """
    service = VoiceCloneService(group_id, api_key)
    return service.upload_voice_file(file_path)


def clone_voice_from_data_dir(filename: str, group_id: str, api_key: str, 
                             data_dir: str = None) -> Optional[str]:
    """
    便捷函数：从数据目录进行音声复刻
    
    Args:
        filename: 音频文件名（如 "siyu2.m4a"）
        group_id: MiniMax API 的 Group ID
        api_key: MiniMax API 的 API Key
        data_dir: 数据目录路径，默认为当前模块的父目录下的 data 目录
        
    Returns:
        文件ID，如果失败返回 None
    """
    if data_dir is None:
        # 默认使用 src/data 目录
        current_dir = Path(__file__).parent
        data_dir = current_dir.parent / "data"
    
    file_path = os.path.join(data_dir, filename)
    return clone_voice_from_file(file_path, group_id, api_key)


def clone_voice_with_file_id(file_id: int, voice_id: str, group_id: str, api_key: str,
                            **kwargs) -> Optional[Dict[str, Any]]:
    """
    便捷函数：使用已上传的文件ID进行音声复刻
    
    Args:
        file_id: 已上传音频的文件ID (int64)
        voice_id: 复刻音色的ID
        group_id: MiniMax API 的 Group ID
        api_key: MiniMax API 的 API Key
        **kwargs: 其他可选参数（text, model, need_noise_reduction 等）
        
    Returns:
        接口返回的结果字典，如果失败返回 None
    """
    service = VoiceCloneService(group_id, api_key)
    return service.clone_voice(file_id, voice_id, **kwargs)


# 示例用法
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 示例配置（请替换为实际的配置）
    GROUP_ID = "your group id"
    API_KEY = "your api key"
    
    # 方法1：直接指定文件路径
    file_id = clone_voice_from_file("src/data/siyu2.m4a", GROUP_ID, API_KEY)
    if file_id:
        print(f"音声复刻文件ID: {file_id}")
    else:
        print("音声复刻失败")
    
    # 方法2：使用数据目录
    file_id = clone_voice_from_data_dir("siyu2.m4a", GROUP_ID, API_KEY)
    if file_id:
        print(f"音声复刻文件ID: {file_id}")
    else:
        print("音声复刻失败")
    
    # 方法3：使用服务类
    service = VoiceCloneService(GROUP_ID, API_KEY)
    file_id = service.upload_voice_file("src/data/siyu2.m4a")
    if file_id:
        print(f"音声复刻文件ID: {file_id}")
        # 获取状态
        status = service.get_voice_clone_status(file_id)
        if status:
            print(f"文件状态: {status}")
    else:
        print("音声复刻失败")
