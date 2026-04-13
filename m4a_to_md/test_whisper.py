#!/usr/bin/env python3
"""
测试Whisper离线识别引擎
"""

import os
import sys
from pathlib import Path

def test_whisper_import():
    """测试Whisper导入"""
    try:
        import whisper
        print("✅ Whisper包已安装")

        # 获取版本信息
        try:
            version = getattr(whisper, '__version__', '未知')
            print(f"   版本: {version}")
        except:
            print("   版本: 未知")

        # 列出可用模型
        print("   可用模型:", whisper.available_models())
        return True
    except ImportError as e:
        print(f"❌ Whisper导入失败: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Whisper检查错误: {e}")
        return False

def test_speech_recognition_with_whisper():
    """测试speech_recognition的Whisper集成"""
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        print("\n🎤 测试speech_recognition的Whisper支持...")

        # 创建测试音频
        from pydub import AudioSegment
        import tempfile

        # 生成2秒静音（Whisper需要足够长的音频）
        test_audio = AudioSegment.silent(duration=2000)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_wav = tmp.name
            test_audio.export(test_wav, format='wav')

        print(f"   创建测试音频: {test_wav}")

        # 尝试Whisper识别
        with sr.AudioFile(test_wav) as source:
            audio_data = recognizer.record(source)

            try:
                print("   使用Whisper识别...")
                text = recognizer.recognize_whisper(audio_data, language="zh")
                print(f"   Whisper识别结果: '{text}'")

                if text:
                    print("   ✅ Whisper识别成功")
                    return True
                else:
                    print("   ⚠️  Whisper识别成功但返回空文本")
                    return False

            except sr.RequestError as e:
                print(f"   Whisper请求错误: {e}")
                print("   可能原因: 1) 模型未下载 2) 内存不足")

            except Exception as e:
                print(f"   其他错误: {e}")
                import traceback
                traceback.print_exc()

        # 清理
        os.unlink(test_wav)

    except Exception as e:
        print(f"   测试失败: {e}")
        import traceback
        traceback.print_exc()

    return False

def test_direct_whisper():
    """直接测试Whisper库"""
    print("\n🔧 直接测试Whisper库...")

    try:
        import whisper

        # 创建测试音频
        from pydub import AudioSegment
        import tempfile

        test_audio = AudioSegment.silent(duration=2000)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_wav = tmp.name
            test_audio.export(test_wav, format='wav')

        print(f"   创建测试音频: {test_wav}")

        # 加载小型模型（第一次使用会自动下载）
        print("   加载Whisper模型（第一次使用会下载）...")
        model = whisper.load_model("tiny")
        print(f"   加载模型: {model.__class__.__name__}")

        # 转录
        print("   转录中...")
        result = model.transcribe(test_wav, language="zh")

        print(f"   转录结果: '{result['text']}'")
        print(f"   语言: {result.get('language', '未知')}")

        os.unlink(test_wav)
        return True

    except Exception as e:
        print(f"   直接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Whisper离线识别引擎测试")
    print("=" * 60)

    # 测试Whisper导入
    if not test_whisper_import():
        print("\n💡 建议: pip install openai-whisper")
        return

    print("\n" + "=" * 40)
    print("测试1: speech_recognition集成")
    print("=" * 40)

    # 测试speech_recognition集成
    success1 = test_speech_recognition_with_whisper()

    print("\n" + "=" * 40)
    print("测试2: 直接Whisper库")
    print("=" * 40)

    # 测试直接Whisper库
    success2 = test_direct_whisper()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    if success1 or success2:
        print("✅ Whisper引擎可用")
        print("\n💡 使用命令:")
        print("   python script/m4a_to_md.py -i input/录音.m4a --engine whisper")
    else:
        print("❌ Whisper引擎测试失败")
        print("\n💡 建议:")
        print("   1. 检查网络连接（首次使用需要下载模型）")
        print("   2. 确保有足够的磁盘空间（模型约100-1500MB）")
        print("   3. 检查Python环境")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)