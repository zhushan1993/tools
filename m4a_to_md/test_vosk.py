#!/usr/bin/env python3
"""
测试Vosk离线识别引擎
"""

import os
import sys
from pathlib import Path

def test_vosk_import():
    """测试Vosk导入"""
    try:
        import vosk
        print("✅ Vosk包已安装")
        # 尝试获取版本信息
        try:
            version = getattr(vosk, '__version__', '未知')
            print(f"   版本: {version}")
        except:
            print("   版本: 未知")
        return True
    except ImportError as e:
        print(f"❌ Vosk导入失败: {e}")
        return False

def check_vosk_models():
    """检查Vosk模型"""
    import vosk

    # 可能的模型路径
    model_paths = [
        Path.cwd() / "models" / "vosk",
        Path.home() / ".cache" / "vosk",
        Path.home() / ".local" / "share" / "vosk",
    ]

    print("\n🔍 搜索Vosk模型...")
    found_models = []

    for model_path in model_paths:
        if model_path.exists():
            print(f"   检查: {model_path}")
            # 查找模型文件
            for item in model_path.iterdir():
                if item.is_dir():
                    # 检查是否是模型目录（通常包含am、conf等文件）
                    if (item / "am/final.mdl").exists() or (item / "conf/mfcc.conf").exists():
                        print(f"     ✅ 发现模型: {item.name}")
                        found_models.append(str(item))

    return found_models

def download_vosk_model():
    """下载Vosk模型"""
    print("\n📥 尝试下载Vosk中文模型...")

    import urllib.request
    import zipfile

    # 尝试多个可能的模型URL
    model_urls = [
        "https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip",
        "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip",
        "https://alphacephei.com/vosk/models/vosk-model-cn-0.1.zip",
        "https://huggingface.co/alphacephei/vosk-model-small-cn-0.22/resolve/main/vosk-model-small-cn-0.22.zip",
    ]

    model_dir = Path.cwd() / "models" / "vosk"
    model_dir.mkdir(parents=True, exist_ok=True)

    for url in model_urls:
        print(f"   尝试: {url}")
        try:
            filename = url.split("/")[-1]
            zip_path = model_dir / filename

            # 下载
            print(f"   正在下载...")
            urllib.request.urlretrieve(url, zip_path)
            print(f"   下载完成: {zip_path.name}")

            # 解压
            print(f"   正在解压...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(model_dir)

            print(f"   解压完成")

            # 清理zip文件
            zip_path.unlink()
            return True

        except Exception as e:
            print(f"   失败: {e}")
            continue

    return False

def test_speech_recognition_with_vosk():
    """测试speech_recognition的Vosk集成"""
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        print("\n🎤 测试speech_recognition的Vosk支持...")

        # 创建测试音频
        from pydub import AudioSegment
        import tempfile

        # 生成1秒静音
        test_audio = AudioSegment.silent(duration=1000)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_wav = tmp.name
            test_audio.export(test_wav, format='wav')

        print(f"   创建测试音频: {test_wav}")

        # 尝试Vosk识别
        with sr.AudioFile(test_wav) as source:
            audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_vosk(audio_data)
                print(f"   Vosk识别返回: {text[:50]}...")

                # 解析JSON结果
                import json
                result = json.loads(text)
                print(f"   解析结果: {result}")

                return True

            except sr.RequestError as e:
                print(f"   Vosk请求错误: {e}")
                print("   可能原因: 1) 未安装Vosk模型 2) 模型路径错误")

            except Exception as e:
                print(f"   其他错误: {e}")

        # 清理
        os.unlink(test_wav)

    except Exception as e:
        print(f"   测试失败: {e}")

    return False

def main():
    print("=" * 60)
    print("Vosk离线识别引擎测试")
    print("=" * 60)

    # 测试Vosk导入
    if not test_vosk_import():
        print("\n💡 建议: pip install vosk")
        return

    # 检查现有模型
    models = check_vosk_models()

    if models:
        print(f"\n✅ 找到 {len(models)} 个Vosk模型")
        for model in models:
            print(f"   - {model}")
    else:
        print("\n⚠️  未找到Vosk模型")

        # 询问是否下载
        choice = input("\n是否尝试下载Vosk中文模型? (y/N): ")
        if choice.lower() == 'y':
            if download_vosk_model():
                print("✅ 模型下载成功")
                models = check_vosk_models()
            else:
                print("❌ 模型下载失败")
                print("\n💡 手动下载链接:")
                print("   1. 访问: https://alphacephei.com/vosk/models")
                print("   2. 下载 'vosk-model-small-cn-*.zip' (中文模型)")
                print("   3. 解压到: models/vosk/ 目录")
        else:
            print("❌ 未安装模型，Vosk无法使用")

    # 测试识别功能
    if models:
        print("\n" + "=" * 40)
        test_speech_recognition_with_vosk()

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