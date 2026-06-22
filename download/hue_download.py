#!/usr/bin/env python3
"""
Hue 数据下载工具
通过 Hue REST API 提交 SQL 查询并下载完整结果 CSV（无行数限制）

用法:
  python3 hue_download.py <sql_file> -o <output.csv>

环境变量:
  HUE_USER      Hue 用户名（可选，不设置则交互输入）
  HUE_PASSWORD  Hue 密码（可选，不设置则交互输入）
"""

import requests
import json
import re
import time
import csv
import os
import sys
import argparse
from pathlib import Path


class HueClient:
    """Hue REST API 客户端"""

    def __init__(self, base_url: str, username: str, password: str, engine: str = "impala"):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.engine = engine
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def login(self) -> bool:
        """登录 Hue"""
        r = self.session.get(f"{self.base_url}/hue/accounts/login/")
        r.raise_for_status()

        csrf = self._extract_csrf(r.text)
        if not csrf:
            print("错误: 无法获取 CSRF token")
            return False

        r2 = self.session.post(
            f"{self.base_url}/hue/accounts/login/",
            data={
                "csrfmiddlewaretoken": csrf,
                "username": self.username,
                "password": self.password,
                "server": "hue",
            },
            headers={"Referer": f"{self.base_url}/hue/accounts/login/"},
        )

        if "login" in r2.url.lower():
            print("错误: 登录失败，请检查用户名和密码")
            return False

        print(f"登录成功: {self.username}")
        return True

    @property
    def _csrf_token(self) -> str:
        return self.session.cookies.get("csrftoken", "")

    @property
    def _headers(self) -> dict:
        return {"X-CSRFToken": self._csrf_token}

    def execute(self, statement: str) -> dict:
        """执行 SQL 查询"""
        notebook = {
            "type": f"query-{self.engine}",
            "name": "API Query",
            "description": "",
            "snippets": [{
                "id": "1",
                "type": self.engine,
                "statement_raw": statement,
                "statement": statement,
            }],
            "isSaved": False,
            "sessions": [],
            "skipHistorify": True,
        }
        snippet = {
            "id": "1",
            "type": self.engine,
            "statement_raw": statement,
            "statement": statement,
            "result": {},
            "properties": {},
        }

        r = self.session.post(
            f"{self.base_url}/notebook/api/execute/",
            data={
                "csrfmiddlewaretoken": self._csrf_token,
                "notebook": json.dumps(notebook),
                "snippet": json.dumps(snippet),
            },
            headers=self._headers,
        )
        r.raise_for_status()
        result = r.json()
        if result.get("status") != 0:
            raise RuntimeError(f"查询提交失败: {result.get('message', result)}")
        return result.get("handle")

    def check_status(self, handle: dict, statement: str) -> str:
        """检查查询状态，返回 'available', 'running', 'failed' 等"""
        # Clean handle values (strip newlines from base64)
        clean_handle = {k: v.strip() if isinstance(v, str) else v for k, v in handle.items()}

        snippet = {
            "type": self.engine,
            "result": {"handle": clean_handle},
            "status": "running",
            "id": "1",
            "statement_raw": statement,
            "statement": statement,
            "variables": [],
            "properties": {"settings": []},
        }
        notebook = {
            "type": self.engine,
            "snippets": [snippet],
            "id": None,
            "name": "",
            "isSaved": False,
            "sessions": [],
        }

        r = self.session.post(
            f"{self.base_url}/notebook/api/check_status",
            data={
                "csrfmiddlewaretoken": self._csrf_token,
                "notebook": json.dumps(notebook),
                "snippet": json.dumps(snippet),
            },
            headers=self._headers,
        )
        r.raise_for_status()
        result = r.json()
        if result.get("status") != 0:
            return "unknown"
        return result.get("query_status", {}).get("status", "unknown")

    def fetch_result_data(self, handle: dict, statement: str, rows: int = 50000, start_row: int = 0) -> dict:
        """分批获取结果"""
        clean_handle = {k: v.strip() if isinstance(v, str) else v for k, v in handle.items()}

        snippet = {
            "type": self.engine,
            "result": {"handle": clean_handle},
            "status": "available",
            "id": "1",
            "statement_raw": statement,
            "statement": statement,
            "variables": [],
            "properties": {"settings": []},
        }
        notebook = {
            "type": self.engine,
            "snippets": [snippet],
            "id": None,
            "name": "",
            "isSaved": False,
            "sessions": [],
        }

        r = self.session.post(
            f"{self.base_url}/notebook/api/fetch_result_data",
            data={
                "csrfmiddlewaretoken": self._csrf_token,
                "notebook": json.dumps(notebook),
                "snippet": json.dumps(snippet),
                "rows": str(rows),
                "startOver": "true" if start_row == 0 else "false",
            },
            headers=self._headers,
        )
        r.raise_for_status()
        return r.json()

    def query_to_csv(self, statement: str, output_path: str) -> bool:
        """执行查询并保存为 CSV"""
        print("提交查询...", end="", flush=True)
        try:
            handle = self.execute(statement)
        except Exception as e:
            print(f" 失败\n错误: {e}")
            return False
        print(" 完成")

        print("等待查询完成", end="", flush=True)
        status = "running"
        while status in ("running", "waiting", "submitted", "starting"):
            time.sleep(2)
            status = self.check_status(handle, statement)
            print(".", end="", flush=True)
        print()

        if status != "available":
            print(f"\n查询失败，状态 = {status}")
            return False

        print("下载结果中...")
        writer = None
        headers = None
        start_row = 0
        max_rows_per_page = 50000
        total_rows = 0
        empty_page_retries = 0
        max_empty_retries = 3

        while empty_page_retries < max_empty_retries:
            result_data = self.fetch_result_data(handle, statement,
                                                  rows=max_rows_per_page,
                                                  start_row=start_row)
            if result_data.get("status") != 0:
                print(f"\n  取数失败: {result_data.get('message', 'unknown error')}")
                break

            result = result_data.get("result", {})
            data = result.get("data", [])
            if not data:
                empty_page_retries += 1
                if empty_page_retries >= max_empty_retries:
                    print(f"\n  无更多数据")
                else:
                    # has_more=true but empty data: retry
                    print(f".", end="", flush=True)
                    time.sleep(1)
                    continue

            # 首次获取到数据：初始化 CSV 写入
            if writer is None and data:
                import csv as csv_module
                meta = result.get("meta", [])
                headers = [col.get("name", f"col{i}") for i, col in enumerate(meta)]
                f_out = open(output_path, "w", encoding="utf-8-sig", newline="")
                writer = csv_module.writer(f_out)
                writer.writerow(headers)
                print(f"  列数: {len(headers)}: {headers}")

            if data and writer:
                writer.writerows(data)
                total_rows += len(data)
                start_row += len(data)
                has_more = result.get("has_more", False)
                print(f"  已获取 {total_rows:,} 行" + (f" (还有更多)" if has_more else ""))
                if not has_more:
                    break

        if writer:
            f_out.close()
            file_size = os.path.getsize(output_path)
            print(f"完成: {output_path}")
            print(f"  行数: {total_rows:,}")
            print(f"  大小: {file_size/1024/1024:.1f} MB")
            return True
        else:
            print("未获取到数据")
            return False

    @staticmethod
    def _extract_csrf(html: str) -> str:
        match = re.search(r"""name=["']csrfmiddlewaretoken["']\s+value=["']([^"']+)["']""", html)
        return match.group(1) if match else None


def main():
    parser = argparse.ArgumentParser(description="Hue 数据下载工具")
    parser.add_argument("sql_file", nargs="?", help="SQL 查询文件路径")
    parser.add_argument("-o", "--output", help="输出 CSV 文件路径")
    parser.add_argument("--host", default="http://10.212.129.61:8889", help="Hue 地址")
    parser.add_argument("-u", "--user", default=os.environ.get("HUE_USER"), help="Hue 用户名")
    parser.add_argument("-p", "--password", default=os.environ.get("HUE_PASSWORD"), help="Hue 密码")
    parser.add_argument("--engine", default="impala", choices=["impala", "hive"], help="查询引擎")
    parser.add_argument("-q", "--query", help="直接指定 SQL 语句（替代 sql_file）")

    args = parser.parse_args()

    # 确定 SQL
    sql = None
    if args.query:
        sql = args.query
    elif args.sql_file:
        sql_path = Path(args.sql_file)
        if not sql_path.exists():
            print(f"错误: 文件不存在: {sql_path}")
            sys.exit(1)
        sql = sql_path.read_text(encoding="utf-8")
    else:
        parser.print_help()
        print("\n请指定 sql_file 或 --query")
        sys.exit(1)

    # 确定输出路径
    if args.output:
        output_path = args.output
    elif args.sql_file:
        output_path = Path(args.sql_file).with_suffix(".csv").name
    else:
        output_path = "hue_result.csv"

    # 凭证
    password = args.password
    if not password:
        import getpass
        password = getpass.getpass("Hue 密码: ")
    username = args.user
    if not username:
        username = input("Hue 用户名: ")

    # 执行
    client = HueClient(args.host, username, password, engine=args.engine)
    if not client.login():
        sys.exit(1)

    print(f"引擎: {args.engine}")
    print(f"输出: {output_path}")
    print(f"SQL ({len(sql)} 字符): {sql[:120].strip()}...")
    print()

    success = client.query_to_csv(sql, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
