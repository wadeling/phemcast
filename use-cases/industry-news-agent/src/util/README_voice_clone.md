# 音声复刻工具使用说明

## 概述

`voice_clone.py` 提供了音声复刻功能，支持将音频文件上传到 MiniMax API 进行声音克隆。

## 功能特性

- 支持音频文件上传到 MiniMax API
- 提供多种使用方式（服务类、便捷函数）
- 完整的错误处理和日志记录
- 支持获取文件状态

## 使用方法

### 1. 基本配置

首先需要获取 MiniMax API 的配置信息：
- `group_id`: 你的 Group ID
- `api_key`: 你的 API Key

### 2. 使用服务类

```python
from util.voice_clone import VoiceCloneService

# 初始化服务
service = VoiceCloneService("your_group_id", "your_api_key")

# 上传音频文件
file_id = service.upload_voice_file("path/to/audio.m4a")
if file_id:
    print(f"文件ID: {file_id}")
    
    # 获取文件状态
    status = service.get_voice_clone_status(file_id)
    print(f"状态: {status}")
```

### 3. 使用便捷函数

#### 方法1：直接指定文件路径
```python
from util.voice_clone import clone_voice_from_file

file_id = clone_voice_from_file("src/data/siyu2.m4a", "your_group_id", "your_api_key")
```

#### 方法2：使用数据目录
```python
from util.voice_clone import clone_voice_from_data_dir

file_id = clone_voice_from_data_dir("siyu2.m4a", "your_group_id", "your_api_key")
```

### 4. 在项目中使用

```python
# 在你的模块中导入
from util.voice_clone import VoiceCloneService

# 从配置文件或环境变量获取配置
GROUP_ID = os.getenv("MINIMAX_GROUP_ID")
API_KEY = os.getenv("MINIMAX_API_KEY")

# 创建服务实例
voice_service = VoiceCloneService(GROUP_ID, API_KEY)

# 使用音声复刻功能
def process_voice_clone():
    file_id = voice_service.upload_voice_file("src/data/siyu2.m4a")
    if file_id:
        # 处理成功的情况
        return {"success": True, "file_id": file_id}
    else:
        # 处理失败的情况
        return {"success": False, "error": "上传失败"}
```

## 错误处理

工具包含完整的错误处理机制：

- 文件不存在检查
- 网络请求错误处理
- API 响应错误处理
- 详细的日志记录

## 测试

运行测试脚本：
```bash
python test_voice_clone.py
```

## 注意事项

1. 确保音频文件格式正确（支持 .m4a, .mp3 等格式）
2. 需要有效的 MiniMax API 配置
3. 网络连接正常
4. 文件大小符合 API 限制

## API 参考

### VoiceCloneService 类

#### `__init__(group_id: str, api_key: str)`
初始化音声复刻服务

#### `upload_voice_file(file_path: str, purpose: str = "voice_clone") -> Optional[str]`
上传音频文件进行音声复刻

#### `get_voice_clone_status(file_id: str) -> Optional[Dict[str, Any]]`
获取音声复刻状态

### 便捷函数

#### `clone_voice_from_file(file_path: str, group_id: str, api_key: str) -> Optional[str]`
从文件进行音声复刻

#### `clone_voice_from_data_dir(filename: str, group_id: str, api_key: str, data_dir: str = None) -> Optional[str]`
从数据目录进行音声复刻

#### `clone_voice_with_file_id(file_id: int, voice_id: str, group_id: str, api_key: str, **kwargs) -> Optional[Dict[str, Any]]`
使用已上传的文件ID进行音声复刻

## 新增功能

### 完整的参数支持

现在支持所有官方API参数：

- `file_id`: 文件ID（必须是int64类型）
- `voice_id`: 音色ID（8-256字符，首字符必须为英文字母）
- `clone_prompt`: 音色复刻参数
- `text`: 复刻试听文本（最多2000字符）
- `model`: 试听模型（speech-01-turbo, speech-01-hd等）
- `need_noise_reduction`: 是否开启降噪
- `need_volume_normalization`: 是否开启音量归一化
- `aigc_watermark`: 是否添加音频节奏标识

### 参数验证

- 自动验证 `file_id` 类型（必须是整数）
- 自动验证 `voice_id` 格式
- 自动检查 `text` 和 `model` 参数的关联性
- 自动检查文本长度限制

### 使用示例

```python
# 基本用法
service = VoiceCloneService(GROUP_ID, API_KEY)
result = service.clone_voice(
    file_id=307887913775171,
    voice_id="phemcastvoice"
)

# 带试听功能
result = service.clone_voice(
    file_id=307887913775171,
    voice_id="phemcastvoice",
    text="你好，这是音声复刻测试。",
    model="speech-01-turbo",
    need_noise_reduction=True,
    need_volume_normalization=True
)

# 使用便捷函数
result = clone_voice_with_file_id(
    file_id=307887913775171,
    voice_id="phemcastvoice",
    group_id=GROUP_ID,
    api_key=API_KEY,
    text="测试文本",
    model="speech-01-turbo"
)
```
