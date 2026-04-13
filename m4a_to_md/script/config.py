#!/usr/bin/env python3
"""
配置文件
"""

import os
from pathlib import Path

# 工具根目录
TOOL_ROOT = Path(__file__).parent.parent

# 默认路径配置
DEFAULT_PATHS = {
    'input_dir': TOOL_ROOT / 'input',
    'output_dir': TOOL_ROOT / 'output',
    'script_dir': TOOL_ROOT / 'script',
    'log_dir': TOOL_ROOT / 'logs',
    'temp_dir': TOOL_ROOT / 'temp',
}

# 确保目录存在
for path in DEFAULT_PATHS.values():
    path.mkdir(exist_ok=True)

# 音频处理配置
AUDIO_CONFIG = {
    'target_sample_rate': 16000,      # 目标采样率（Hz）
    'target_channels': 1,             # 目标声道数（1=单声道）
    'chunk_duration': 30,             # 音频分片时长（秒）
    'max_file_size_mb': 500,          # 最大文件大小（MB）
    'supported_formats': ['.m4a', '.mp3', '.wav', '.flac', '.aac'],
}

# 语音识别配置
RECOGNITION_CONFIG = {
    'default_language': 'zh-CN',      # 默认识别语言
    'engine': 'google',               # 识别引擎：google, google_cloud, vosk, whisper
    'api_key': None,                  # API密钥（如果需要）
    'alternative_languages': ['en-US', 'ja-JP', 'ko-KR'],  # 备选语言
    'confidence_threshold': 0.6,      # 置信度阈值
}

# Google Cloud Speech API配置（如果使用）
GOOGLE_CLOUD_CONFIG = {
    'credentials_file': None,         # 服务账号密钥文件路径
    'project_id': None,               # Google Cloud项目ID
    'enable_automatic_punctuation': True,
    'enable_word_time_offsets': True,
}

# Vosk离线识别配置（如果使用）
VOSK_CONFIG = {
    'model_dir': TOOL_ROOT / 'models' / 'vosk',
    'model_name': 'vosk-model-small-zh-cn-0.22',  # 中文模型
    'model_url': 'https://alphacephei.com/vosk/models/vosk-model-small-zh-cn-0.22.zip',
}

# Whisper配置（如果使用）
WHISPER_CONFIG = {
    'model_size': 'small',            # tiny, base, small, medium, large
    'device': 'cpu',                  # cpu or cuda
    'compute_type': 'float32',        # float32, float16, int8
    'language': 'zh',                 # 自动检测或指定
}

# 文本处理配置
TEXT_CONFIG = {
    'clean_text': True,               # 是否清理文本
    'add_timestamps': True,           # 是否添加时间戳
    'generate_summary': True,         # 是否生成摘要
    'extract_keywords': True,         # 是否提取关键词
    'max_summary_sentences': 5,       # 摘要最大句子数
    'keyword_count': 10,              # 关键词数量
}

# 输出配置
OUTPUT_CONFIG = {
    'format': 'markdown',             # 输出格式：markdown, txt, json, html
    'include_metadata': True,         # 是否包含元数据
    'include_statistics': True,       # 是否包含统计信息
    'timestamp_format': '%Y-%m-%d %H:%M:%S',  # 时间戳格式
    'auto_open_output': False,        # 是否自动打开输出文件
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',                  # 日志级别：DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_file_size_mb': 10,           # 日志文件最大大小
    'backup_count': 5,                # 保留的日志文件数量
}

# 性能配置
PERFORMANCE_CONFIG = {
    'max_workers': 2,                 # 最大工作线程数
    'timeout_seconds': 300,           # 单文件处理超时时间
    'batch_size': 5,                  # 批量处理大小
    'use_cache': True,                # 是否使用缓存
}

# 用户界面配置
UI_CONFIG = {
    'show_progress': True,            # 显示进度条
    'show_estimated_time': True,      # 显示预计剩余时间
    'verbose_mode': False,            # 详细模式
    'color_output': True,             # 彩色输出
}

def get_config():
    """
    获取完整配置
    """
    return {
        'paths': DEFAULT_PATHS,
        'audio': AUDIO_CONFIG,
        'recognition': RECOGNITION_CONFIG,
        'google_cloud': GOOGLE_CLOUD_CONFIG,
        'vosk': VOSK_CONFIG,
        'whisper': WHISPER_CONFIG,
        'text': TEXT_CONFIG,
        'output': OUTPUT_CONFIG,
        'log': LOG_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'ui': UI_CONFIG,
    }


def update_config(new_config):
    """
    更新配置
    """
    global AUDIO_CONFIG, RECOGNITION_CONFIG, TEXT_CONFIG, OUTPUT_CONFIG

    for section, values in new_config.items():
        if section == 'audio' and isinstance(values, dict):
            AUDIO_CONFIG.update(values)
        elif section == 'recognition' and isinstance(values, dict):
            RECOGNITION_CONFIG.update(values)
        elif section == 'text' and isinstance(values, dict):
            TEXT_CONFIG.update(values)
        elif section == 'output' and isinstance(values, dict):
            OUTPUT_CONFIG.update(values)


def save_config_to_file(file_path=None):
    """
    保存配置到文件
    """
    import json

    if file_path is None:
        file_path = TOOL_ROOT / 'config.json'

    config = get_config()

    # 将Path对象转换为字符串
    def convert_paths(obj):
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_paths(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_paths(item) for item in obj]
        else:
            return obj

    config = convert_paths(config)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"配置已保存到: {file_path}")


def load_config_from_file(file_path=None):
    """
    从文件加载配置
    """
    import json

    if file_path is None:
        file_path = TOOL_ROOT / 'config.json'

    if not os.path.exists(file_path):
        print(f"配置文件不存在: {file_path}，使用默认配置")
        return get_config()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 将字符串路径转换为Path对象
        def restore_paths(obj):
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    if k.endswith('_dir') or k.endswith('_file') or 'path' in k.lower():
                        if isinstance(v, str):
                            result[k] = Path(v)
                        else:
                            result[k] = v
                    else:
                        result[k] = restore_paths(v)
                return result
            elif isinstance(obj, list):
                return [restore_paths(item) for item in obj]
            else:
                return obj

        config = restore_paths(config)
        update_config(config)

        print(f"配置已从文件加载: {file_path}")
        return config

    except Exception as e:
        print(f"加载配置文件失败: {e}，使用默认配置")
        return get_config()


def print_config_summary():
    """
    打印配置摘要
    """
    config = get_config()

    print("=" * 60)
    print("工具配置摘要")
    print("=" * 60)

    print("\n📁 路径配置:")
    for name, path in config['paths'].items():
        print(f"  {name}: {path}")

    print("\n🎵 音频配置:")
    for key, value in config['audio'].items():
        print(f"  {key}: {value}")

    print("\n🗣️  识别配置:")
    for key, value in config['recognition'].items():
        if key != 'api_key' or value is None:
            print(f"  {key}: {value}")

    print("\n📝 文本配置:")
    for key, value in config['text'].items():
        print(f"  {key}: {value}")

    print("\n💾 输出配置:")
    for key, value in config['output'].items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 测试配置
    print_config_summary()
    save_config_to_file()