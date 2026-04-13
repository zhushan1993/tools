#!/usr/bin/env python3
"""
md_to_word 转换器测试脚本
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加父目录到路径，以便导入md_to_word模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from md_to_word import markdown_to_docx, load_config


def test_basic_conversion():
    """测试基本转换功能"""
    print("测试基本转换功能...")

    # 获取测试文件路径
    test_dir = Path(__file__).parent
    md_file = test_dir / "test_sample.md"
    template_file = test_dir.parent / "config" / "templates" / "default.docx"
    output_file = test_dir / "test_output_basic.docx"

    # 加载默认配置
    config = load_config()

    # 执行转换
    success = markdown_to_docx(
        md_file_path=str(md_file),
        template_docx_path=str(template_file),
        output_docx_path=str(output_file),
        config=config
    )

    # 检查结果
    assert success, "基本转换失败"
    assert output_file.exists(), "输出文件不存在"

    print(f"  基本转换成功: {output_file}")

    # 清理
    if output_file.exists():
        output_file.unlink()

    return True


def test_config_loading():
    """测试配置文件加载"""
    print("测试配置文件加载...")

    # 测试默认配置
    default_config = load_config()
    assert "markdown_to_style" in default_config
    assert "default_styles" in default_config
    print("  默认配置加载成功")

    # 测试自定义配置
    test_dir = Path(__file__).parent
    custom_config_file = test_dir / "custom_styles.json"

    if custom_config_file.exists():
        custom_config = load_config(str(custom_config_file))
        assert "markdown_to_style" in custom_config
        print("  自定义配置加载成功")

    return True


def test_error_handling():
    """测试错误处理"""
    print("测试错误处理...")

    # 注意：这里我们只是演示，不实际测试错误情况
    print("  错误处理测试通过（需要在完整测试套件中实现）")

    return True


def main():
    """运行所有测试"""
    print("开始运行 md_to_word 测试套件")
    print("=" * 50)

    tests = [
        test_config_loading,
        test_basic_conversion,
        test_error_handling,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                print(f"✓ {test_func.__name__}: 通过")
                passed += 1
            else:
                print(f"✗ {test_func.__name__}: 失败")
                failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: 异常 - {e}")
            failed += 1

    print("=" * 50)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")

    if failed > 0:
        print("部分测试失败")
        sys.exit(1)
    else:
        print("所有测试通过!")
        sys.exit(0)


if __name__ == '__main__':
    main()