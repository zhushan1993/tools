#!/usr/bin/env python3
"""
测试脚本：验证工具的基本功能
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加父目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_dependencies():
    """测试依赖是否安装"""
    print("🔍 测试依赖安装...")
    missing = []

    try:
        import speech_recognition
        print("  ✅ speech_recognition")
    except ImportError:
        missing.append("speech_recognition")
        print("  ❌ speech_recognition")

    try:
        from pydub import AudioSegment
        print("  ✅ pydub")
    except ImportError:
        missing.append("pydub")
        print("  ❌ pydub")

    try:
        import chardet
        print("  ✅ chardet")
    except ImportError:
        missing.append("chardet")
        print("  ❌ chardet")

    if missing:
        print(f"\n❌ 缺少依赖: {', '.join(missing)}")
        print("运行: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ 所有依赖已安装")
        return True


def test_audio_conversion():
    """测试音频转换功能"""
    print("\n🔧 测试音频转换...")

    try:
        from pydub import AudioSegment

        # 创建测试音频（静音）
        test_audio = AudioSegment.silent(duration=1000)  # 1秒静音

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_wav = tmp.name
            test_audio.export(test_wav, format='wav')

        print(f"  ✅ 创建测试音频: {Path(test_wav).name}")

        # 尝试加载
        loaded = AudioSegment.from_wav(test_wav)
        print(f"  ✅ 加载音频: 时长={len(loaded)}ms")

        # 清理
        os.unlink(test_wav)
        print("  ✅ 清理临时文件")

        return True

    except Exception as e:
        print(f"  ❌ 音频转换测试失败: {e}")
        return False


def test_speech_recognition():
    """测试语音识别功能（离线测试）"""
    print("\n🎤 测试语音识别...")

    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        # 创建测试音频文件（静音）
        from pydub import AudioSegment
        test_audio = AudioSegment.silent(duration=2000)  # 2秒静音

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_wav = tmp.name
            test_audio.export(test_wav, format='wav')

        # 测试是否能读取音频文件
        with sr.AudioFile(test_wav) as source:
            audio_data = recognizer.record(source)
            print(f"  ✅ 读取音频文件: {len(audio_data.get_raw_data())} 字节")

        # 清理
        os.unlink(test_wav)

        print("  ⚠️  语音识别API测试需要网络连接，跳过在线测试")
        return True

    except Exception as e:
        print(f"  ❌ 语音识别测试失败: {e}")
        return False


def test_text_processing():
    """测试文本处理功能"""
    print("\n📝 测试文本处理...")

    try:
        # 导入本地模块
        from script import text_utils

        test_text = "这是一个测试文本。它包含多个句子。这是第三个句子。"

        # 测试清理文本
        cleaned = text_utils.clean_transcription_text(test_text)
        print(f"  ✅ 文本清理: {cleaned[:30]}...")

        # 测试句子分割
        sentences = text_utils.split_into_sentences(test_text)
        print(f"  ✅ 句子分割: {len(sentences)} 个句子")

        # 测试关键词提取
        keywords = text_utils.extract_keywords(test_text, top_k=3)
        print(f"  ✅ 关键词提取: {keywords}")

        # 测试语言检测
        language = text_utils.detect_language(test_text)
        print(f"  ✅ 语言检测: {language}")

        return True

    except Exception as e:
        print(f"  ❌ 文本处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """测试配置功能"""
    print("\n⚙️  测试配置...")

    try:
        from script import config

        # 获取配置
        cfg = config.get_config()
        print(f"  ✅ 获取配置: {len(cfg)} 个配置节")

        # 检查必要路径
        required_paths = ['input_dir', 'output_dir', 'script_dir']
        for path_name in required_paths:
            path = cfg['paths'][path_name]
            if isinstance(path, Path):
                print(f"  ✅ 路径配置 {path_name}: {path}")
            else:
                print(f"  ❌ 路径配置 {path_name} 不是Path对象")

        # 打印配置摘要
        config.print_config_summary()

        return True

    except Exception as e:
        print(f"  ❌ 配置测试失败: {e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n📁 测试目录结构...")

    tool_root = Path(__file__).parent.parent
    required_dirs = ['input', 'output', 'script']
    required_files = ['README.md', 'requirements.txt']

    all_ok = True

    # 检查目录
    for dir_name in required_dirs:
        dir_path = tool_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"  ✅ 目录存在: {dir_name}/")
        else:
            print(f"  ❌ 目录缺失: {dir_name}/")
            all_ok = False

    # 检查文件
    for file_name in required_files:
        file_path = tool_root / file_name
        if file_path.exists() and file_path.is_file():
            print(f"  ✅ 文件存在: {file_name}")
        else:
            print(f"  ❌ 文件缺失: {file_name}")
            all_ok = False

    return all_ok


def test_sample_file():
    """测试示例文件"""
    print("\n📄 测试示例文件...")

    input_dir = Path(__file__).parent.parent / 'input'
    m4a_files = list(input_dir.glob('*.m4a'))

    if not m4a_files:
        print("  ⚠️  未找到示例.m4a文件，跳过文件测试")
        print("  💡 请将录音文件放入 input/ 目录")
        return True

    sample_file = m4a_files[0]
    print(f"  ✅ 找到示例文件: {sample_file.name}")

    # 检查文件大小
    file_size_mb = sample_file.stat().st_size / (1024 * 1024)
    print(f"  📊 文件大小: {file_size_mb:.1f} MB")

    if file_size_mb > 100:
        print("  ⚠️  文件较大，处理可能需要较长时间")
    elif file_size_mb < 0.1:
        print("  ⚠️  文件过小，可能无法识别")

    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行测试套件")
    print("=" * 60)

    tests = [
        ("依赖安装", test_dependencies),
        ("目录结构", test_directory_structure),
        ("示例文件", test_sample_file),
        ("音频转换", test_audio_conversion),
        ("语音识别", test_speech_recognition),
        ("文本处理", test_text_processing),
        ("配置系统", test_configuration),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"  结果: {'✅ 通过' if success else '❌ 失败'}")
        except Exception as e:
            print(f"  💥 测试异常: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name:20} {status}")

    print(f"\n📊 总计: {passed}/{total} 个测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！工具可以正常使用。")
        print("\n下一步：")
        print("  1. 激活虚拟环境: source .venv/bin/activate")
        print("  2. 尝试转换: python script/m4a_to_md.py -i input/示例文件.m4a")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查上述问题。")
        print("\n建议：")
        print("  1. 确保已安装所有依赖: pip install -r requirements.txt")
        print("  2. 检查系统依赖（FFmpeg等）是否已安装")
        print("  3. 查看详细错误信息以解决问题")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生未预期错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)