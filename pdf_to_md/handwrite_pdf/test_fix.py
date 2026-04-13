#!/usr/bin/env python3
"""
测试PaddleOCR修复方案
"""

import sys
from PIL import Image, ImageDraw
import tempfile
import os

def test_ocr_call():
    """测试不同的OCR调用方式"""

    from paddleocr import PaddleOCR

    print("初始化PaddleOCR...")
    ocr = PaddleOCR(use_textline_orientation=True, lang='ch')
    print("初始化完成")

    # 创建测试图像
    img = Image.new('RGB', (200, 100), color='white')
    d = ImageDraw.Draw(img)
    d.text((20, 40), '测试中文手写体', fill='black')

    # 保存为临时文件
    temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_img.name)
    temp_img.close()

    # 将PIL图像转换为numpy数组
    import numpy as np
    img_np = np.array(img)

    test_cases = [
        ("方案1: ocr.ocr() 不带cls参数", lambda: ocr.ocr(img_np)),
        ("方案2: ocr.predict() 方法", lambda: ocr.predict(img_np)),
        ("方案3: ocr.ocr() 带use_doc_orientation_classify=True",
         lambda: ocr.ocr(img_np, use_doc_orientation_classify=True)),
        ("方案4: ocr.predict() 带use_doc_orientation_classify=True",
         lambda: ocr.predict(img_np, use_doc_orientation_classify=True)),
    ]

    for name, func in test_cases:
        print(f"\n{name}:")
        try:
            result = func()
            if result is not None:
                print(f"  成功！结果类型: {type(result)}")
                # 尝试提取文本
                if isinstance(result, list) and len(result) > 0:
                    print(f"  检测到 {len(result)} 行")
                    for i, line in enumerate(result[:2]):  # 只显示前2行
                        if line is not None:
                            print(f"  行{i}: {line}")
            else:
                print("  返回None")
        except Exception as e:
            print(f"  失败: {e}")

    # 清理
    os.unlink(temp_img.name)

    print("\n" + "="*50)
    print("总结：")
    print("根据测试，推荐使用方案2或方案4（使用predict方法）")
    print("因为DeprecationWarning提示：'Please use predict instead'")

if __name__ == '__main__':
    try:
        test_ocr_call()
    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)