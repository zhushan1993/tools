#!/usr/bin/env python3
"""
文本处理工具函数
"""

import re
import json
import jieba
import jieba.analyse
from datetime import datetime
from collections import Counter


def clean_transcription_text(text):
    """
    清理转录文本
    """
    if not text:
        return ""

    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)

    # 移除特殊字符（保留中文、英文、数字、常见标点）
    # 保留：中文、英文、数字、常见标点，空格
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？；："\'、.,!?;:()\-—~]', '', text)

    # 规范化标点
    text = text.replace('，', ', ')
    text = text.replace('。', '. ')
    text = text.replace('！', '! ')
    text = text.replace('？', '? ')
    text = text.replace('；', '; ')
    text = text.replace('：', ': ')
    text = text.replace('、', ', ')

    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def split_into_sentences(text, language='zh'):
    """
    将文本分割成句子
    """
    if not text:
        return []

    if language == 'zh':
        # 中文句子分割：按标点分割
        sentences = re.split(r'[。！？；]+', text)
    else:
        # 英文句子分割
        sentences = re.split(r'[.!?;]+', text)

    # 过滤空句子并去除空白
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def extract_keywords(text, top_k=10, language='zh'):
    """
    提取关键词
    """
    if not text or len(text) < 10:
        return []

    try:
        if language == 'zh':
            # 使用jieba提取中文关键词
            keywords = jieba.analyse.extract_tags(
                text,
                topK=top_k,
                withWeight=False,
                allowPOS=('n', 'ns', 'nr', 'nt', 'nz', 'v', 'vn', 'a')
            )
        else:
            # 英文关键词提取（简单版）
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            word_counts = Counter(words)

            # 过滤常见词
            common_words = {'the', 'and', 'you', 'that', 'for', 'are', 'with',
                           'this', 'have', 'from', 'they', 'would', 'there',
                           'their', 'what', 'about', 'which', 'when', 'were'}

            keywords = [word for word, count in word_counts.most_common(top_k*2)
                       if word not in common_words][:top_k]

        return keywords

    except Exception:
        # 备用方案：按词频提取
        words = re.findall(r'\w+', text.lower())
        word_counts = Counter(words)

        # 过滤短词和常见词
        common_words = {'the', 'and', 'you', 'that', 'for', 'are', 'with',
                       'this', 'have', 'from', 'they', 'would', 'there',
                       'their', 'what', 'about', 'which', 'when', 'were',
                       '的', '了', '在', '是', '我', '有', '和', '就',
                       '不', '人', '都', '一', '一个', '上', '也', '很',
                       '到', '说', '要', '去', '你', '会', '着', '没有',
                       '看', '好', '自己', '这', '那'}

        keywords = [word for word, count in word_counts.most_common(top_k*3)
                   if len(word) > 1 and word not in common_words][:top_k]

        return keywords


def generate_summary(text, max_sentences=5, language='zh'):
    """
    生成文本摘要
    """
    sentences = split_into_sentences(text, language)

    if len(sentences) <= max_sentences:
        return ' '.join(sentences)

    # 简单算法：选择最长的句子
    sentences_with_length = [(i, s, len(s)) for i, s in enumerate(sentences)]
    sentences_with_length.sort(key=lambda x: x[2], reverse=True)

    selected_indices = sorted([i for i, _, _ in sentences_with_length[:max_sentences]])
    summary = ' '.join(sentences[i] for i in selected_indices)

    return summary


def format_timestamp(seconds, include_hours=True):
    """
    格式化时间戳
    """
    if include_hours or seconds >= 3600:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


def add_timestamps_to_transcript(transcript, chunk_duration=30):
    """
    为转录文本添加时间戳
    transcript: 原始文本
    返回带时间戳的文本列表
    """
    sentences = split_into_sentences(transcript)

    if not sentences:
        return []

    # 假设每个句子平均占用一定时间
    # 简单分配：前几个句子在第一个时间段，依此类推
    sentences_per_chunk = max(1, len(sentences) // (len(sentences) // 5 + 1))

    timestamped = []
    current_time = 0

    for i, sentence in enumerate(sentences):
        # 每sentences_per_chunk个句子增加一个时间块
        if i % sentences_per_chunk == 0:
            current_time = (i // sentences_per_chunk) * chunk_duration

        timestamp = format_timestamp(current_time)
        timestamped.append(f"[{timestamp}] {sentence}")

    return timestamped


def detect_language(text):
    """
    检测文本语言
    返回 'zh', 'en', 或 'mixed'
    """
    if not text:
        return 'unknown'

    # 统计中文字符和英文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    total_chars = len(text.replace(' ', ''))

    if total_chars == 0:
        return 'unknown'

    chinese_ratio = chinese_chars / total_chars
    english_ratio = english_chars / total_chars

    if chinese_ratio > 0.7:
        return 'zh'
    elif english_ratio > 0.7:
        return 'en'
    else:
        return 'mixed'


def format_markdown_heading(text, level=1):
    """
    格式化为Markdown标题
    """
    if level < 1 or level > 6:
        level = 1

    hashes = '#' * level
    return f"{hashes} {text}"


def format_markdown_list(items, ordered=False):
    """
    格式化为Markdown列表
    """
    lines = []
    for i, item in enumerate(items, 1):
        if ordered:
            lines.append(f"{i}. {item}")
        else:
            lines.append(f"- {item}")
    return '\n'.join(lines)


def format_markdown_table(headers, rows):
    """
    格式化为Markdown表格
    """
    if not headers or not rows:
        return ""

    # 创建表头
    table = []
    table.append('| ' + ' | '.join(headers) + ' |')

    # 创建分隔线
    table.append('|' + '|'.join(['---' for _ in headers]) + '|')

    # 添加数据行
    for row in rows:
        table.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')

    return '\n'.join(table)


def analyze_text_complexity(text):
    """
    分析文本复杂度
    """
    if not text:
        return {
            'char_count': 0,
            'word_count': 0,
            'sentence_count': 0,
            'avg_sentence_length': 0,
            'readability': 'N/A'
        }

    # 字符数
    char_count = len(text)

    # 词数（中英文混合）
    chinese_words = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    word_count = chinese_words + english_words

    # 句子数
    sentences = split_into_sentences(text)
    sentence_count = len(sentences)

    # 平均句子长度
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    # 可读性评分（简单版）
    if avg_sentence_length < 10:
        readability = '简单'
    elif avg_sentence_length < 20:
        readability = '中等'
    else:
        readability = '复杂'

    return {
        'char_count': char_count,
        'word_count': word_count,
        'sentence_count': sentence_count,
        'avg_sentence_length': round(avg_sentence_length, 1),
        'readability': readability
    }


def create_text_statistics(text, filename):
    """
    创建文本统计信息
    """
    stats = analyze_text_complexity(text)
    keywords = extract_keywords(text, top_k=8)
    language = detect_language(text)
    summary = generate_summary(text, max_sentences=3, language=language)

    stats_md = f"""## 文本统计

**基本信息：**
- 文件：{filename}
- 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 语言：{language}

**统计信息：**
- 字符数：{stats['char_count']}
- 词数：{stats['word_count']}
- 句子数：{stats['sentence_count']}
- 平均句长：{stats['avg_sentence_length']} 词/句
- 可读性：{stats['readability']}

**关键词：** {', '.join(keywords[:8])}

**摘要：**
{summary}
"""

    return stats_md


if __name__ == "__main__":
    # 测试代码
    test_text = "这是一个测试文本。它包含多个句子。这是第三个句子。关键词包括：测试、文本、句子。"

    print("原始文本:", test_text)
    print("清理后:", clean_transcription_text(test_text))
    print("句子:", split_into_sentences(test_text))
    print("关键词:", extract_keywords(test_text))
    print("语言:", detect_language(test_text))
    print("复杂度:", analyze_text_complexity(test_text))
    print("时间戳文本:", add_timestamps_to_transcript(test_text))