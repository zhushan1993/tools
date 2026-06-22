"""
Claude Code IPC — 通过 --permission-prompt-tool stdio 与 Claude Code 通信

处理 NDJSON 格式的 control_request/control_response 协议。
"""

import json
import asyncio
import threading
import logging
from typing import Optional, Callable, Awaitable
from .config import CLAUDE_CONFIG

logger = logging.getLogger(__name__)

# NDJSON 关键字
TYPE_CONTROL_REQUEST = "control_request"
TYPE_CONTROL_RESPONSE = "control_response"
SUBTYPE_CAN_USE_TOOL = "can_use_tool"
SUBTYPE_SUCCESS = "success"

BEHAVIOR_ALLOW = "allow"
BEHAVIOR_DENY = "deny"


class PermissionRequest:
    """一个待处理的授权请求。"""

    def __init__(self, request_id: str, tool_name: str, tool_input: dict,
                 decision_reason: str = "", tool_use_id: str = ""):
        self.request_id = request_id
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.decision_reason = decision_reason
        self.tool_use_id = tool_use_id


class ClaudeIPC:
    """
    通过子进程管理 Claude Code。

    使用 --output-format stream-json --input-format stream-json
    --permission-prompt-tool stdio 模式启动。
    """

    def __init__(
        self,
        on_permission_request: Callable[[PermissionRequest], Awaitable[None]] = None,
        binary: str = None,
        extra_args: list = None,
    ):
        self.binary = binary or CLAUDE_CONFIG["binary"]
        self.extra_args = extra_args or CLAUDE_CONFIG["extra_args"]
        self.on_permission_request = on_permission_request

        self.process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self, user_args: list[str] = None) -> bool:
        """
        启动 Claude Code 子进程。

        Args:
            user_args: 传递给 Claude CLI 的额外参数 (如 -p "prompt")

        Returns:
            是否成功启动
        """
        args = [self.binary,
                "--output-format", "stream-json",
                "--input-format", "stream-json",
                "--permission-prompt-tool", "stdio"]

        if self.extra_args:
            args.extend(self.extra_args)
        if user_args:
            args.extend(user_args)

        logger.info(f"启动 Claude: {' '.join(args)}")

        try:
            self.process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._running = True
            self._reader_task = asyncio.create_task(self._read_loop())
            logger.info(f"Claude 子进程已启动 (PID: {self.process.pid})")
            return True
        except FileNotFoundError:
            logger.error(f"找不到 Claude 可执行文件: {self.binary}")
            logger.error("请确保 Claude Code 已安装: npm install -g @anthropic-ai/claude-code")
            return False
        except Exception as e:
            logger.error(f"启动 Claude 失败: {e}")
            return False

    async def stop(self):
        """停止 Claude 子进程。"""
        self._running = False
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        if self.process and self.process.returncode is None:
            logger.info("终止 Claude 子进程...")
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Claude 进程未响应，强制终止")
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                logger.warning(f"终止 Claude 异常: {e}")

        self.process = None

    async def send_user_input(self, text: str):
        """
        向 Claude 发送用户输入（模拟用户在终端输入）。

        写入 stdin 后添加换行。
        """
        if not self._running or not self.process or not self.process.stdin:
            logger.warning("Claude 未运行，无法发送输入")
            return

        data = (text + "\n").encode("utf-8")
        self.process.stdin.write(data)
        await self.process.stdin.drain()
        logger.info(f"已向 Claude 发送用户输入 ({len(text)} 字符)")

    async def respond_permission(self, request_id: str, allow: bool,
                                  updated_input: dict = None,
                                  message: str = "") -> bool:
        """
        回复授权请求。

        Args:
            request_id: 请求 ID
            allow: 是否允许
            updated_input: 可选的修改后的 tool input
            message: 拒绝时的消息
        """
        if not self._running or not self.process or not self.process.stdin:
            logger.warning("Claude 未运行，无法回复授权")
            return False

        behavior = BEHAVIOR_ALLOW if allow else BEHAVIOR_DENY
        response = {
            "type": TYPE_CONTROL_RESPONSE,
            "response": {
                "subtype": SUBTYPE_SUCCESS,
                "request_id": request_id,
                "response": {
                    "behavior": behavior,
                },
            },
        }

        if allow and updated_input is not None:
            response["response"]["response"]["updatedInput"] = updated_input
        if not allow and message:
            response["response"]["response"]["message"] = message

        data = (json.dumps(response) + "\n").encode("utf-8")
        self.process.stdin.write(data)
        await self.process.stdin.drain()
        logger.info(f"授权回复: {behavior} (request_id={request_id})")
        return True

    async def _read_loop(self):
        """
        后台读取 Claude stdout 的 NDJSON 流，解析 control_request 并回调。
        """
        if not self.process or not self.process.stdout:
            logger.error("Claude stdout 不可用")
            return

        async for line in self.process.stdout:
            if not self._running:
                break

            line = line.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                logger.debug(f"非 JSON 输出: {line[:100]}")
                continue

            # 处理 control_request
            if msg.get("type") == TYPE_CONTROL_REQUEST:
                req_data = msg.get("request", {})
                if req_data.get("subtype") == SUBTYPE_CAN_USE_TOOL:
                    request = PermissionRequest(
                        request_id=msg.get("request_id", ""),
                        tool_name=req_data.get("tool_name", ""),
                        tool_input=req_data.get("input", {}),
                        decision_reason=req_data.get("decision_reason", ""),
                        tool_use_id=req_data.get("tool_use_id", ""),
                    )
                    logger.info(
                        f"收到授权请求: {request.tool_name} "
                        f"(reason: {request.decision_reason})"
                    )
                    if self.on_permission_request:
                        await self.on_permission_request(request)

        logger.info("Claude stdout 流已关闭")

    @property
    def is_running(self) -> bool:
        return self._running and self.process is not None and self.process.returncode is None


# ===== 同步包装（供 server.py 非 asyncio 主循环使用）=====

class SyncClaudeIPC:
    """ClaudeIPC 的同步包装，运行 asyncio 事件循环在后台线程。"""

    def __init__(self):
        self._ipc = ClaudeIPC(on_permission_request=self._async_permission_handler)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self.on_permission_request = None  # 同步回调 (从主线程调用)

    async def _async_permission_handler(self, request: PermissionRequest):
        """Async 回调 —— 将请求转发到主线程。"""
        if self.on_permission_request:
            self.on_permission_request(request)

    def start(self, user_args: list[str] = None) -> bool:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # 启动 Claude 子进程
        success = self._loop.run_until_complete(self._ipc.start(user_args))
        if not success:
            return False

        # 后台线程运行事件循环，持续处理 Claude stdout
        self._loop_thread = threading.Thread(
            target=self._run_event_loop,
            daemon=True,
            name="claude-ipc",
        )
        self._loop_thread.start()
        return True

    def _run_event_loop(self):
        """在后台线程运行 asyncio 事件循环。"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self):
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=3)
        if self._loop and not self._loop.is_closed():
            self._loop.run_until_complete(self._ipc.stop())
            self._loop.close()
        self._loop = None
        self._loop_thread = None

    def respond_permission(self, request_id: str, allow: bool,
                            updated_input: dict = None, message: str = "") -> bool:
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                self._ipc.respond_permission(request_id, allow, updated_input, message),
                self._loop,
            )
            return future.result(timeout=5)
        return False

    def send_user_input(self, text: str):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._ipc.send_user_input(text), self._loop,
            )

    @property
    def is_running(self) -> bool:
        return self._ipc.is_running
