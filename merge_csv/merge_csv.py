#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并指定文件夹下的多个CSV文件
去除重复的标题行，只保留第一个文件的标题
"""

import os
import sys
import glob


def merge_csv_files(input_folder, output_file='merged.csv', output_encoding='utf-8'):
    """
    合并文件夹下的所有CSV文件
    只保留指定列：检查站名称,排队长度(KM),预计通过时间(min),时间

    Args:
        input_folder: 输入文件夹路径
        output_file: 输出文件路径，默认为当前目录的merged.csv
        output_encoding: 输出文件编码，默认为utf-8
    """
    # 需要保留的列
    required_columns = ['检查站名称', '排队长度(KM)', '预计通过时间(min)', '时间']

    # 获取所有CSV文件并按名称排序
    csv_files = glob.glob(os.path.join(input_folder, '*.csv'))
    csv_files.sort()  # 按文件路径排序

    if not csv_files:
        print(f"在文件夹 {input_folder} 中没有找到CSV文件")
        return

    print(f"找到 {len(csv_files)} 个CSV文件:")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")

    # 确定编码
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030']

    # 打开输出文件
    print(f"输出文件编码: {output_encoding}")
    with open(output_file, 'w', newline='', encoding=output_encoding) as outfile:
        header_written = False

        for i, csv_file in enumerate(csv_files):
            print(f"处理文件: {os.path.basename(csv_file)}...")

            # 尝试不同的编码打开文件
            file_handle = None
            used_encoding = None

            for encoding in encodings_to_try:
                try:
                    file_handle = open(csv_file, 'r', encoding=encoding)
                    # 测试读取一行
                    file_handle.readline()
                    file_handle.seek(0)  # 重置文件指针
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    if file_handle:
                        file_handle.close()
                    continue

            if file_handle is None:
                print(f"  警告: 无法解码文件 {csv_file}，跳过")
                continue

            print(f"  使用编码: {used_encoding}")

            try:
                # 读取标题行（第一行）
                header_line = file_handle.readline().rstrip('\n\r')
                if not header_line:
                    print(f"  警告: 文件为空，跳过")
                    continue

                # 解析标题行
                headers = header_line.split(',')

                # 查找所需列的索引
                column_indices = []
                missing_columns = []
                for col in required_columns:
                    try:
                        idx = headers.index(col)
                        column_indices.append(idx)
                    except ValueError:
                        missing_columns.append(col)

                # 检查是否所有必需列都存在
                if missing_columns:
                    print(f"  错误: 文件缺少必需的列: {missing_columns}，跳过此文件")
                    continue

                # 如果是第一个文件，写入过滤后的标题行
                if not header_written:
                    outfile.write(','.join(required_columns) + '\n')
                    header_written = True

                # 读取并处理数据行
                line_count = 0
                for line in file_handle:
                    line = line.rstrip('\n\r')
                    if not line:  # 跳过空行
                        continue

                    fields = line.split(',')

                    # 检查字段数是否匹配标题列数
                    if len(fields) != len(headers):
                        print(f"  警告: 第{line_count+2}行列数不匹配（期望{len(headers)}，实际{len(fields)}），跳过此行")
                        line_count += 1
                        continue

                    # 提取所需列
                    selected_fields = []
                    for idx in column_indices:
                        if idx < len(fields):
                            selected_fields.append(fields[idx])
                        else:
                            selected_fields.append('')  # 如果索引超出范围，使用空值

                    # 写入过滤后的行
                    outfile.write(','.join(selected_fields) + '\n')
                    line_count += 1

                print(f"  处理了 {line_count} 行数据")

            except Exception as e:
                print(f"  处理文件时出错: {e}")
                import traceback
                traceback.print_exc()
            finally:
                file_handle.close()

    print(f"\n合并完成！输出文件: {output_file}")
    print(f"总文件数: {len(csv_files)}")


def main():
    # 默认参数
    input_folder = os.path.join(os.path.dirname(__file__), 'input', 'merge01')
    output_file = os.path.join(os.path.dirname(__file__), 'merged_result.csv')
    output_encoding = 'utf-8'

    # 解析命令行参数
    args = sys.argv[1:]
    i = 0

    while i < len(args):
        arg = args[i]

        if arg in ['-e', '--encoding']:
            if i + 1 < len(args):
                output_encoding = args[i + 1]
                i += 2
            else:
                print("错误: -e/--encoding 参数需要指定编码")
                print_usage()
                return
        elif arg in ['-h', '--help']:
            print_usage()
            return
        elif arg.startswith('-'):
            print(f"错误: 未知参数 {arg}")
            print_usage()
            return
        else:
            # 位置参数
            if input_folder == os.path.join(os.path.dirname(__file__), 'input', 'merge01'):
                input_folder = arg
            elif output_file == os.path.join(os.path.dirname(__file__), 'merged_result.csv'):
                output_file = arg
            else:
                print("错误: 参数太多")
                print_usage()
                return
            i += 1

    # 检查文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"错误: 文件夹不存在: {input_folder}")
        return

    # 检查输出目录是否存在，如果不存在则创建
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 验证编码
    supported_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-8-sig']
    if output_encoding.lower() not in supported_encodings:
        print(f"警告: 不支持的编码 {output_encoding}，使用默认编码 utf-8")
        print(f"支持的编码: {', '.join(supported_encodings)}")
        output_encoding = 'utf-8'

    # 执行合并
    merge_csv_files(input_folder, output_file, output_encoding)


def print_usage():
    """打印使用说明"""
    print("用法: python merge_csv.py [选项] [输入文件夹路径] [输出文件路径]")
    print()
    print("选项:")
    print("  -e, --encoding ENCODING  指定输出文件编码 (默认: utf-8)")
    print("                          支持: utf-8, gbk, gb2312, gb18030, utf-8-sig")
    print("  -h, --help              显示帮助信息")
    print()
    print("示例:")
    print("  python merge_csv.py                                      # 使用默认路径 input/merge01")
    print("  python merge_csv.py ./my_csv_folder                      # 指定输入文件夹")
    print("  python merge_csv.py ./my_csv_folder ./output.csv         # 指定输入和输出")
    print("  python merge_csv.py -e gbk ./my_csv_folder              # 指定GBK编码")
    print("  python merge_csv.py -e gbk ./my_csv_folder ./output.csv # 指定编码、输入和输出")


if __name__ == '__main__':
    main()