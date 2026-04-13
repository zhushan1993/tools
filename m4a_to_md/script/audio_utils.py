#!/usr/bin/env python3
"""
音频处理工具函数
"""

import os
import subprocess
import tempfile
from pathlib import Path

def is_ffmpeg_available():
    """检查FFmpeg是否可用"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_audio_info(file_path):
    """
    获取音频文件信息
    返回字典包含：时长、采样率、声道数、比特率等
    """
    try:
        # 尝试使用pydub获取信息
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        return {
            'duration_ms': len(audio),
            'duration_sec': len(audio) / 1000,
            'channels': audio.channels,
            'frame_rate': audio.frame_rate,
            'sample_width': audio.sample_width,
            'frame_width': audio.frame_width,
            'format': Path(file_path).suffix.lower()[1:],
            'file_size': os.path.getsize(file_path)
        }
    except Exception:
        # 备用方案：使用ffprobe
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration,size,bit_rate',
                '-show_entries', 'stream=sample_rate,channels,codec_name',
                '-of', 'json',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # 这里简化处理，实际需要解析JSON
            return {'duration_sec': '未知', 'format': Path(file_path).suffix.lower()[1:]}
        except Exception:
            return {'duration_sec': '未知', 'format': Path(file_path).suffix.lower()[1:]}


def convert_audio_format(input_path, output_path, target_format='wav',
                        sample_rate=16000, channels=1):
    """
    转换音频格式
    """
    if not is_ffmpeg_available():
        raise RuntimeError("FFmpeg未安装，无法进行音频格式转换")

    try:
        # 使用ffmpeg进行转换
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ar', str(sample_rate),  # 采样率
            '-ac', str(channels),     # 声道数
            '-y',                     # 覆盖输出文件
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return True

    except subprocess.CalledProcessError as e:
        print(f"音频转换失败: {e}")
        return False


def normalize_audio(input_path, output_path=None):
    """
    音频标准化：调整音量到合适水平
    """
    try:
        from pydub import AudioSegment
        from pydub.effects import normalize

        audio = AudioSegment.from_file(input_path)
        normalized = normalize(audio)

        if output_path is None:
            output_path = Path(input_path).with_suffix('.normalized.wav')

        normalized.export(output_path, format='wav')
        return str(output_path)

    except Exception as e:
        print(f"音频标准化失败: {e}")
        return input_path  # 返回原文件路径


def remove_silence(input_path, output_path=None, silence_thresh=-40, min_silence_len=500):
    """
    移除静音部分
    """
    try:
        from pydub import AudioSegment
        from pydub.silence import split_on_silence

        audio = AudioSegment.from_file(input_path)

        # 分割非静音部分
        chunks = split_on_silence(
            audio,
            min_silence_len=min_silence_len,  # 静音最小长度（毫秒）
            silence_thresh=silence_thresh,    # 静音阈值（dB）
            keep_silence=200                  # 每段前后保留的静音（毫秒）
        )

        # 合并所有非静音部分
        if chunks:
            combined = sum(chunks)
        else:
            combined = audio

        if output_path is None:
            output_path = Path(input_path).with_suffix('.nonsilent.wav')

        combined.export(output_path, format='wav')
        return str(output_path)

    except Exception as e:
        print(f"移除静音失败: {e}")
        return input_path


def extract_audio_segment(input_path, start_time, end_time, output_path=None):
    """
    提取音频片段
    start_time, end_time: 秒数
    """
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(input_path)

        # 转换为毫秒
        start_ms = start_time * 1000
        end_ms = end_time * 1000

        segment = audio[start_ms:end_ms]

        if output_path is None:
            output_path = Path(input_path).with_suffix(f'.{start_time}-{end_time}.wav')

        segment.export(output_path, format='wav')
        return str(output_path)

    except Exception as e:
        print(f"提取音频片段失败: {e}")
        return None


def check_audio_quality(file_path):
    """
    检查音频质量
    返回质量评估结果
    """
    try:
        info = get_audio_info(file_path)

        quality_score = 0
        issues = []

        # 检查采样率
        if 'frame_rate' in info:
            if info['frame_rate'] < 16000:
                issues.append(f"采样率过低: {info['frame_rate']} Hz (建议≥16000 Hz)")
                quality_score -= 2
            elif info['frame_rate'] >= 44100:
                quality_score += 1

        # 检查声道
        if 'channels' in info and info['channels'] > 1:
            quality_score += 1  # 立体声加分

        # 检查文件大小
        if 'file_size' in info:
            size_mb = info['file_size'] / (1024 * 1024)
            if size_mb < 0.1:
                issues.append(f"文件过小: {size_mb:.2f} MB (可能质量不佳)")
                quality_score -= 1
            elif size_mb > 100:
                issues.append(f"文件过大: {size_mb:.2f} MB (处理可能较慢)")

        # 检查时长
        if 'duration_sec' in info and info['duration_sec'] != '未知':
            if info['duration_sec'] < 1:
                issues.append("音频过短")
                quality_score -= 2
            elif info['duration_sec'] > 3600:  # 1小时
                issues.append("音频过长，建议分割处理")
                quality_score -= 1

        # 总体评价
        if quality_score >= 2:
            quality = "优秀"
        elif quality_score >= 0:
            quality = "良好"
        elif quality_score >= -2:
            quality = "一般"
        else:
            quality = "较差"

        return {
            'quality': quality,
            'score': quality_score,
            'issues': issues,
            'info': info
        }

    except Exception as e:
        return {
            'quality': '未知',
            'score': 0,
            'issues': [f"检查过程中出错: {e}"],
            'info': {}
        }


def batch_convert_directory(input_dir, output_dir, target_format='wav'):
    """
    批量转换目录中的音频文件
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    supported_formats = ['.m4a', '.mp3', '.wav', '.flac', '.aac', '.ogg']

    converted_files = []
    failed_files = []

    for audio_file in input_dir.glob('*'):
        if audio_file.suffix.lower() in supported_formats:
            output_file = output_dir / audio_file.with_suffix(f'.{target_format}').name

            print(f"转换: {audio_file.name} -> {output_file.name}")

            try:
                if convert_audio_format(str(audio_file), str(output_file), target_format):
                    converted_files.append(str(output_file))
                else:
                    failed_files.append(str(audio_file))
            except Exception as e:
                print(f"转换失败 {audio_file.name}: {e}")
                failed_files.append(str(audio_file))

    return {
        'converted': converted_files,
        'failed': failed_files,
        'total': len(converted_files) + len(failed_files)
    }


if __name__ == "__main__":
    # 测试代码
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            print(f"检查音频文件: {file_path}")
            quality_info = check_audio_quality(file_path)
            print(f"质量评估: {quality_info['quality']} (得分: {quality_info['score']})")
            if quality_info['issues']:
                print("问题:")
                for issue in quality_info['issues']:
                    print(f"  - {issue}")
        else:
            print(f"文件不存在: {file_path}")
    else:
        print("用法: python audio_utils.py <音频文件路径>")