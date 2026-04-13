#!/usr/bin/env python3
"""
iPhone录音转Markdown工具
将.m4a音频文件转换为结构化的Markdown记录
"""

import os
import sys
import argparse
import glob
from pathlib import Path
import warnings

# 抑制一些不重要的警告
warnings.filterwarnings('ignore')

def check_dependencies():
    """检查必要的依赖是否已安装"""
    missing_deps = []

    try:
        import speech_recognition as sr
    except ImportError:
        missing_deps.append("speech_recognition")

    try:
        from pydub import AudioSegment
    except ImportError:
        missing_deps.append("pydub")

    try:
        import chardet
    except ImportError:
        missing_deps.append("chardet")

    if missing_deps:
        print("错误: 缺少必要的依赖库")
        print("请安装以下库:")
        for dep in missing_deps:
            print(f"  pip install {dep}")
        print("\n或运行:")
        print("  pip install -r requirements.txt")
        return False

    return True


def get_cpu_temperature():
    """
    获取CPU温度（摄氏度）
    返回最高核心温度，如果无法获取则返回None
    """
    try:
        # 方法1: 读取/sys/class/thermal/thermal_zone*/temp（Linux通用）
        import glob
        thermal_files = glob.glob('/sys/class/thermal/thermal_zone*/temp')

        if thermal_files:
            max_temp = 0
            for thermal_file in thermal_files:
                try:
                    with open(thermal_file, 'r') as f:
                        temp = int(f.read().strip())
                    # 转换为摄氏度（通常是毫摄氏度）
                    temp_c = temp / 1000.0
                    max_temp = max(max_temp, temp_c)
                except:
                    continue

            if max_temp > 0:
                return max_temp

        # 方法2: 尝试使用sensors命令
        try:
            import subprocess
            result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=2)
            # 简单解析输出，寻找温度值
            import re
            # 查找类似 "Core 0: +65.0°C" 的模式
            patterns = [r'Core\s*\d+:\s*[\+\-]?(\d+\.?\d*)[°]?C',
                       r'CPU Temp:\s*[\+\-]?(\d+\.?\d*)[°]?C',
                       r'Tdie:\s*[\+\-]?(\d+\.?\d*)[°]?C',
                       r'Tctl:\s*[\+\-]?(\d+\.?\d*)[°]?C']

            for line in result.stdout.split('\n'):
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        return float(match.group(1))
        except:
            pass

        return None

    except Exception as e:
        # 静默失败，不干扰主流程
        return None


def monitor_temperature(warning_threshold=85, critical_threshold=95):
    """
    监控CPU温度，如果过高则打印警告
    参数:
        warning_threshold: 警告温度阈值（摄氏度）
        critical_threshold: 危险温度阈值（摄氏度）
    返回: 当前温度（如果可获取）
    """
    temp = get_cpu_temperature()

    if temp is not None:
        if temp >= critical_threshold:
            print(f"⚠️  警告：CPU温度过高 ({temp:.1f}°C ≥ {critical_threshold}°C)，建议暂停任务")
            return temp
        elif temp >= warning_threshold:
            print(f"⚠️  注意：CPU温度较高 ({temp:.1f}°C ≥ {warning_threshold}°C)，请关注散热")
            return temp
        elif temp > 70:
            print(f"ℹ️  CPU温度: {temp:.1f}°C（正常范围）")

    return temp


def run_with_timeout(func, args=(), kwargs={}, timeout=300, default=None):
    """
    带超时执行的函数包装器（使用线程）
    参数:
        func: 要执行的函数
        args: 位置参数
        kwargs: 关键字参数
        timeout: 超时时间（秒）
        default: 超时或失败时返回的默认值
    返回: 函数结果或默认值
    """
    import threading
    import time
    import queue as thread_queue

    class ResultHolder:
        def __init__(self):
            self.result = default
            self.exception = None
            self.completed = False

    def worker(result_holder, *args, **kwargs):
        try:
            print(f"DEBUG: 线程开始执行 {func.__name__}")
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            print(f"DEBUG: 线程完成 {func.__name__}，耗时 {elapsed:.1f}秒")
            result_holder.result = result
            result_holder.completed = True
        except Exception as e:
            print(f"DEBUG: 线程异常 {func.__name__}: {e}")
            result_holder.exception = e

    print(f"DEBUG: run_with_timeout启动，超时 {timeout}秒")
    result_holder = ResultHolder()
    thread = threading.Thread(target=worker, args=(result_holder, *args), kwargs=kwargs)
    thread.daemon = True  # 设置为守护线程，主线程退出时会被终止
    thread.start()

    print(f"DEBUG: 等待线程完成，超时 {timeout}秒")
    thread.join(timeout)

    if thread.is_alive():
        print(f"⚠️  警告: {func.__name__} 执行超时（{timeout}秒），线程将被放弃")
        # 线程是守护线程，主线程退出时会被终止
        return default

    print(f"DEBUG: 线程已结束，检查结果")
    if result_holder.completed:
        print(f"DEBUG: 函数执行成功")
        return result_holder.result
    elif result_holder.exception is not None:
        print(f"⚠️  函数执行出错: {result_holder.exception}")
        return default
    else:
        print(f"DEBUG: 函数未完成也未抛出异常")
        return default


def check_audio_format(audio_path):
    """
    检查音频文件格式是否适合Whisper转录
    返回: (是否合适, 描述信息)
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_wav(audio_path)

        checks = []

        # 检查采样率
        if audio.frame_rate != 16000:
            checks.append(f"采样率 {audio.frame_rate}Hz (推荐16000Hz)")

        # 检查声道数
        if audio.channels > 1:
            checks.append(f"{audio.channels}声道 (推荐单声道)")

        # 检查时长
        duration_ms = len(audio)
        if duration_ms < 500:  # 小于0.5秒
            checks.append(f"音频过短 ({duration_ms/1000:.1f}秒)")

        # 检查文件大小
        import os
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            checks.append("音频文件为空")

        if checks:
            return False, f"音频格式问题: {'; '.join(checks)}"
        else:
            return True, f"音频格式合适: {duration_ms/1000:.1f}秒, {audio.frame_rate}Hz, {audio.channels}声道"

    except Exception as e:
        return False, f"无法检查音频格式: {e}"


def convert_m4a_to_wav(m4a_path, wav_path=None):
    """
    将m4a文件转换为wav格式
    返回wav文件路径
    """
    try:
        from pydub import AudioSegment

        print(f"正在转换音频格式: {Path(m4a_path).name}")

        # 如果未指定wav路径，使用临时文件
        if wav_path is None:
            wav_path = Path(m4a_path).with_suffix('.wav')

        # 加载m4a文件并转换为wav
        audio = AudioSegment.from_file(m4a_path, format="m4a")

        # 设置适当的参数：单声道，16kHz采样率（节省处理时间）
        audio = audio.set_channels(1)  # 单声道
        audio = audio.set_frame_rate(16000)  # 16kHz

        # 导出为wav
        audio.export(wav_path, format="wav")

        print(f"音频转换完成: {wav_path.name}")
        return str(wav_path)

    except Exception as e:
        print(f"音频转换失败: {e}")
        # 尝试使用系统命令（如果pydub失败）
        try:
            import subprocess
            if wav_path is None:
                wav_path = Path(m4a_path).with_suffix('.wav')

            # 使用ffmpeg直接转换
            cmd = [
                'ffmpeg', '-i', m4a_path,
                '-ac', '1',  # 单声道
                '-ar', '16000',  # 16kHz采样率
                '-y',  # 覆盖输出文件
                str(wav_path)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            print(f"使用ffmpeg转换完成: {wav_path.name}")
            return str(wav_path)

        except Exception as e2:
            print(f"ffmpeg转换也失败: {e2}")
            return None


def transcribe_audio(audio_path, language='zh-CN', engine='google'):
    """
    使用指定的引擎转录音频文件
    返回转录文本
    """
    print(f"DEBUG: transcribe_audio开始, audio_path={audio_path}, engine={engine}")
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        print(f"正在转录: {Path(audio_path).name} (引擎: {engine})")

        with sr.AudioFile(audio_path) as source:
            # 读取整个音频文件
            audio_data = recognizer.record(source)

            try:
                if engine == 'google':
                    # 使用Google Web Speech API（免费，需要网络）
                    text = recognizer.recognize_google(audio_data, language=language)
                elif engine == 'google_cloud':
                    # 使用Google Cloud Speech API（需要API密钥）
                    # 需要设置环境变量 GOOGLE_APPLICATION_CREDENTIALS
                    api_key = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                    if not api_key:
                        print("警告: GOOGLE_APPLICATION_CREDENTIALS 环境变量未设置，使用默认配置")
                    text = recognizer.recognize_google_cloud(audio_data, language=language)
                elif engine == 'vosk':
                    # 使用Vosk离线识别
                    try:
                        # speech_recognition内置Vosk支持
                        # Vosk不需要language参数，使用默认模型
                        text = recognizer.recognize_vosk(audio_data)
                        # Vosk返回JSON格式，需要提取文本
                        import json
                        result = json.loads(text)
                        text = result.get('text', '')
                        if not text:
                            print("Vosk识别成功但未返回文本")
                    except sr.RequestError as e:
                        print(f"Vosk识别失败: {e}")
                        print("请确保已安装Vosk并下载中文语言模型")
                        return ""
                    except Exception as e:
                        print(f"Vosk处理错误: {e}")
                        print("请检查Vosk配置")
                        return ""
                elif engine == 'whisper':
                    # 使用OpenAI Whisper离线识别
                    # Whisper使用简短语言代码（如'zh'而不是'zh-CN'）
                    whisper_language = language
                    if language.lower() in ['zh-cn', 'zh-tw', 'zh-hk', 'zh-sg']:
                        whisper_language = 'zh'
                    elif language.lower() in ['en-us', 'en-gb', 'en-au', 'en-ca']:
                        whisper_language = 'en'
                    elif language.lower() in ['ja-jp']:
                        whisper_language = 'ja'
                    elif language.lower() in ['ko-kr']:
                        whisper_language = 'ko'

                    try:
                        # 尝试使用speech_recognition内置的Whisper支持
                        text = recognizer.recognize_whisper(audio_data, language=whisper_language)
                    except sr.RequestError as e:
                        print(f"speech_recognition Whisper失败: {e}")
                        print("尝试直接使用Whisper库...")
                        # 回退到直接使用Whisper库
                        try:
                            import whisper
                            import tempfile
                            import numpy as np

                            # 将音频数据保存为临时文件
                            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                                temp_wav = tmp.name
                                # 需要将audio_data转换为wav文件
                                # 这是一个简化实现，实际可能需要更复杂的转换
                                try:
                                    # 尝试使用soundfile保存
                                    import soundfile as sf
                                    # 从AudioData获取原始数据
                                    audio_np = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
                                    sf.write(temp_wav, audio_np, audio_data.sample_rate)
                                except:
                                    # 如果soundfile失败，使用pydub
                                    from pydub import AudioSegment
                                    audio_segment = AudioSegment(
                                        data=audio_data.get_raw_data(),
                                        sample_width=audio_data.sample_width,
                                        frame_rate=audio_data.sample_rate,
                                        channels=1
                                    )
                                    audio_segment.export(temp_wav, format='wav')

                            # 加载模型（第一次会下载） - 使用较小的模型以节省内存
                            model_size = "tiny"  # tiny(72MB), base(140MB), small(500MB), medium(1.5GB), large(3GB)
                            model = whisper.load_model(model_size)

                            # 转录，禁用fp16（CPU不支持），带超时保护
                            def transcribe_chunk():
                                return model.transcribe(temp_wav, language=whisper_language, fp16=False, verbose=None)

                            result = run_with_timeout(transcribe_chunk, timeout=60, default=None)

                            if result is None:
                                print("⚠️  分块转录超时（60秒）")
                                text = ""
                            elif isinstance(result, dict) and "text" in result:
                                text = result["text"]
                            else:
                                print(f"⚠️  分块转录结果格式异常: {type(result)}")
                                text = ""

                            # 清理临时文件
                            import os
                            os.unlink(temp_wav)

                        except ImportError:
                            print("Whisper库未安装，请运行: pip install openai-whisper")
                            return ""
                        except Exception as e:
                            print(f"直接Whisper库也失败: {e}")
                            import traceback
                            traceback.print_exc()
                            return ""
                    except Exception as e:
                        print(f"Whisper处理错误: {e}")
                        print("请检查Whisper配置")
                        return ""
                else:
                    print(f"未知引擎: {engine}，使用默认Google引擎")
                    text = recognizer.recognize_google(audio_data, language=language)

                print("转录完成")
                return text

            except sr.UnknownValueError:
                print("无法识别音频内容")
                return ""
            except sr.RequestError as e:
                print(f"识别服务错误: {e}")
                if engine == 'google':
                    print("请检查网络连接，或尝试使用离线识别引擎")
                    print("安装离线引擎: pip install vosk 或 pip install openai-whisper")
                else:
                    print(f"{engine}引擎请求失败，请检查配置")
                return ""

    except Exception as e:
        print(f"转录过程中出错: {e}")
        return ""


def split_long_audio(audio_path, chunk_duration=30):
    """
    将长音频分割为多个短片段
    返回片段路径列表
    """
    print(f"DEBUG: split_long_audio开始, audio_path={audio_path}, chunk_duration={chunk_duration}")
    try:
        from pydub import AudioSegment
        import tempfile

        audio = AudioSegment.from_wav(audio_path)
        duration_ms = len(audio)
        chunk_ms = chunk_duration * 1000

        chunks = []
        temp_dir = tempfile.mkdtemp()

        # 计算总片段数
        total_chunks = (duration_ms + chunk_ms - 1) // chunk_ms

        # 添加分割进度条（暂时禁用tqdm以调试）
        use_tqdm = False
        iterator = range(0, duration_ms, chunk_ms)
        print(f"开始分割音频为 {total_chunks} 个片段...")

        for i in iterator:
            start = i
            end = min(i + chunk_ms, duration_ms)

            chunk = audio[start:end]
            chunk_path = os.path.join(temp_dir, f"chunk_{i//1000:04d}.wav")
            chunk.export(chunk_path, format="wav")
            chunks.append(chunk_path)

        if not use_tqdm:
            print(f"音频已分割为 {len(chunks)} 个片段")
        return chunks

    except Exception as e:
        print(f"音频分割失败: {e}")
        return [audio_path]  # 返回原文件


def transcribe_with_timestamps(audio_path, language='zh-CN', chunk_duration=30, engine='google'):
    """
    带时间戳的转录
    返回带时间戳的文本列表
    """
    print(f"DEBUG: transcribe_with_timestamps开始, engine={engine}, audio_path={audio_path}")
    # 对于Whisper引擎，使用直接Whisper库转录以获得更好的性能
    if engine == 'whisper':
        print(f"DEBUG: 使用Whisper引擎路径")
        try:
            import whisper
            import numpy as np

            # 加载模型（使用较小的模型以节省内存）
            model_size = "tiny"  # tiny(72MB), base(140MB), small(500MB), medium(1.5GB), large(3GB)
            print(f"加载Whisper模型: {model_size}")
            model = whisper.load_model(model_size)

            # 转换语言代码（Whisper使用简短代码）
            whisper_language = language
            if language.lower() in ['zh-cn', 'zh-tw', 'zh-hk', 'zh-sg']:
                whisper_language = 'zh'
            elif language.lower() in ['en-us', 'en-gb', 'en-au', 'en-ca']:
                whisper_language = 'en'
            elif language.lower() in ['ja-jp']:
                whisper_language = 'ja'
            elif language.lower() in ['ko-kr']:
                whisper_language = 'ko'

            # 获取音频时长用于显示
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(audio_path)
                duration_sec = len(audio) / 1000
                duration_str = f"{int(duration_sec//60)}分{int(duration_sec%60)}秒"
            except:
                duration_str = "未知时长"

            print(f"使用Whisper转录（语言: {whisper_language}, 音频: {duration_str}）...")

            # 转录前检查温度
            monitor_temperature()

            # 检查音频格式
            is_ok, format_msg = check_audio_format(audio_path)
            if not is_ok:
                print(f"⚠️  音频格式警告: {format_msg}")

            # 开始计时
            import time
            start_time = time.time()

            # 定义转录函数（用于超时包装）
            def transcribe_func():
                return model.transcribe(audio_path, language=whisper_language, fp16=False, verbose=None)

            # 执行转录（带超时保护），禁用fp16（CPU不支持）
            # 超时时间 = 音频时长 × 3 + 30秒（安全余量）
            audio_duration = duration_sec if 'duration_sec' in locals() else 30
            timeout_seconds = min(audio_duration * 3 + 30, 600)  # 最长10分钟

            print(f"开始转录，超时时间: {timeout_seconds//60}分{timeout_seconds%60}秒...")
            result = run_with_timeout(transcribe_func, timeout=timeout_seconds, default=None)

            # 检查转录结果
            if result is None:
                raise Exception("Whisper转录超时")

            if not isinstance(result, dict) or "segments" not in result:
                print(f"⚠️  Whisper返回结果格式异常: {type(result)}")
                raise Exception("Whisper返回结果格式异常")

            # 转录完成，计算耗时
            elapsed = time.time() - start_time
            print(f"转录完成，耗时: {elapsed//60:.0f}分{elapsed%60:.0f}秒")

            # 转录后检查温度
            monitor_temperature()

            transcripts = []
            for segment in result.get("segments", []):
                start = segment["start"]
                text = segment["text"].strip()
                if text:
                    # 格式化时间戳
                    timestamp = f"[{int(start)//3600:02d}:{(int(start)%3600)//60:02d}:{int(start)%60:02d}]"
                    transcripts.append(f"{timestamp} {text}")

            print(f"Whisper转录完成，获得 {len(transcripts)} 个片段")
            return transcripts

        except Exception as e:
            print(f"Whisper直接转录失败: {e}")
            print("回退到分块转录方法...")
            # 继续执行下面的分块逻辑

    # 原始分块转录逻辑（用于其他引擎或Whisper回退）
    print(f"DEBUG: 使用分块转录路径")
    chunks = split_long_audio(audio_path, chunk_duration)

    transcripts = []
    total_seconds = 0

    # 设置进度条（暂时禁用tqdm以调试）
    use_tqdm = False
    iterator = enumerate(chunks)
    print(f"开始转录 {len(chunks)} 个音频片段...")

    # 温度监控频率：每处理5个片段检查一次（暂时禁用）
    temp_check_frequency = 1000000  # 很大的数，实际上禁用检查

    for i, chunk_path in iterator:
        # 计算时间戳
        start_time = i * chunk_duration
        end_time = min((i + 1) * chunk_duration, len(chunks) * chunk_duration)

        # 定期检查CPU温度
        if i % temp_check_frequency == 0:
            monitor_temperature()

        # 转录当前片段
        text = transcribe_audio(chunk_path, language, engine)

        if text:
            # 格式化时间戳
            timestamp = f"[{start_time//3600:02d}:{(start_time%3600)//60:02d}:{start_time%60:02d}]"
            transcripts.append(f"{timestamp} {text}")

        # 清理临时文件
        try:
            os.remove(chunk_path)
        except:
            pass

    # 清理临时目录
    try:
        import shutil
        temp_dir = os.path.dirname(chunks[0]) if chunks else None
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except:
        pass

    return transcripts


def create_markdown_content(input_path, transcripts, language='zh-CN', engine='google'):
    """
    创建Markdown格式的内容
    """
    from datetime import datetime
    import os

    file_name = Path(input_path).name
    file_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 获取音频时长（如果可能）
    duration_info = ""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(input_path, format="m4a")
        duration_sec = len(audio) / 1000
        duration_info = f"{int(duration_sec//3600):02d}:{int((duration_sec%3600)//60):02d}:{int(duration_sec%60):02d}"
    except:
        duration_info = "未知"

    content = f"""# 录音记录：{file_name}

**录音信息：**
- 文件名：{file_name}
- 转换时间：{current_time}
- 文件大小：{file_size:.1f} MB
- 持续时间：{duration_info}
- 识别语言：{language}
- 识别引擎：{engine}

## 转录内容

"""

    # 添加带时间戳的转录内容
    if transcripts:
        for line in transcripts:
            content += line + "\n\n"
    else:
        content += "（未识别到语音内容或识别失败）\n\n"

    # 添加总结部分
    content += f"""
## 处理说明

1. 本文件由iPhone录音转换工具自动生成
2. 使用{engine}引擎进行语音识别
3. 识别语言：{language}
4. 建议人工核对重要内容

---

*转录完成时间：{current_time}*
*识别引擎：{engine}*
"""

    return content


def process_single_file(input_path, output_path=None, language='zh-CN', verbose=False, engine='google'):
    """
    处理单个文件
    """
    print(f"DEBUG: process_single_file开始, input_path={input_path}, engine={engine}")
    if not os.path.exists(input_path):
        print(f"错误: 文件不存在: {input_path}")
        return False

    # 设置输出路径
    if output_path is None:
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / Path(input_path).with_suffix('.md').name
    else:
        # 确保output_path是Path对象
        output_path = Path(output_path)

    print(f"处理文件: {Path(input_path).name}")
    print(f"输出到: {output_path}")

    # 检查依赖
    if not check_dependencies():
        return False

    # 步骤1: 转换为wav格式
    wav_path = convert_m4a_to_wav(input_path)
    if not wav_path or not os.path.exists(wav_path):
        print("音频转换失败，无法继续")
        return False

    # 步骤2: 转录（带时间戳）
    print("开始语音识别...")
    transcripts = transcribe_with_timestamps(wav_path, language, chunk_duration=30, engine=engine)

    # 步骤3: 生成Markdown内容
    print("生成Markdown文档...")
    content = create_markdown_content(input_path, transcripts, language, engine)

    # 步骤4: 保存文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 转换完成: {output_path.name}")

    # 清理临时文件
    try:
        if wav_path and os.path.exists(wav_path) and wav_path != input_path:
            os.remove(wav_path)
    except:
        pass

    return True


def process_batch(input_dir, output_dir=None, language='zh-CN', verbose=False, engine='google'):
    """
    批量处理目录中的所有m4a文件
    """
    input_dir = Path(input_dir)
    if not input_dir.exists():
        print(f"错误: 目录不存在: {input_dir}")
        return False

    # 获取所有m4a文件
    m4a_files = list(input_dir.glob("*.m4a"))
    if not m4a_files:
        print(f"在 {input_dir} 中未找到.m4a文件")
        return True

    print(f"找到 {len(m4a_files)} 个.m4a文件")

    # 设置输出目录
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    success_count = 0
    fail_count = 0

    for i, m4a_file in enumerate(m4a_files, 1):
        print(f"\n[{i}/{len(m4a_files)}] 处理: {m4a_file.name}")

        output_file = output_dir / m4a_file.with_suffix('.md').name

        try:
            if process_single_file(str(m4a_file), str(output_file), language, verbose, engine):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"处理失败: {e}")
            fail_count += 1

    print(f"\n{'='*50}")
    print(f"批量处理完成:")
    print(f"  成功: {success_count} 个文件")
    print(f"  失败: {fail_count} 个文件")
    print(f"  输出目录: {output_dir}")

    return fail_count == 0


def main():
    print(f"DEBUG: main()函数被调用")
    parser = argparse.ArgumentParser(
        description='iPhone录音转Markdown工具 - 将.m4a音频文件转换为Markdown记录',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -i input/录音.m4a              # 转换单个文件
  %(prog)s -i input/录音.m4a -o output/记录.md  # 指定输出文件
  %(prog)s --batch input/                # 批量处理目录
  %(prog)s --language zh-CN              # 设置识别语言
  %(prog)s --engine vosk                 # 使用Vosk离线识别（需安装vosk包）
        """
    )

    # 输入选项
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-i', '--input',
                           help='输入.m4a文件路径')
    input_group.add_argument('--batch',
                           help='批量处理目录下的所有.m4a文件')

    # 输出选项
    parser.add_argument('-o', '--output',
                       help='输出Markdown文件路径（仅单个文件模式有效）')
    parser.add_argument('--output-dir',
                       help='输出目录（批量模式有效，默认: m4a_to_md/output/）')

    # 识别选项
    parser.add_argument('--language', default='zh-CN',
                       help='识别语言代码（默认: zh-CN）')
    parser.add_argument('--engine', default='google',
                       choices=['google', 'google_cloud', 'vosk', 'whisper'],
                       help='识别引擎：google(在线), google_cloud(需API), vosk(离线), whisper(离线)（默认: google）')
    parser.add_argument('--chunk-duration', type=int, default=30,
                       help='音频分片时长（秒，默认: 30）')

    # 其他选项
    parser.add_argument('--verbose', action='store_true',
                       help='显示详细输出信息')
    parser.add_argument('--version', action='version',
                       version='%(prog)s 1.0.0')

    args = parser.parse_args()

    try:
        if args.batch:
            # 批量处理模式
            return process_batch(
                input_dir=args.batch,
                output_dir=args.output_dir,
                language=args.language,
                verbose=args.verbose,
                engine=args.engine
            )
        else:
            # 单个文件模式
            return process_single_file(
                input_path=args.input,
                output_path=args.output,
                language=args.language,
                verbose=args.verbose,
                engine=args.engine
            )

    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        return 1
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(0 if main() else 1)