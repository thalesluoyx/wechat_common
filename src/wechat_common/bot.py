"""
Interactive Multi-Channel Bot Daemon & Session Manager with Local IPC Multiplexer
Supports multiple WeCom Bots concurrently connected to dedicated Antigravity Sessions.
"""

import os
import asyncio
from dataclasses import dataclass
from typing import Callable, Optional, Awaitable, Dict, List, Any
from aiohttp import web

# 避免 Windows 系统 socks:// 代理引发 websocket 异常
os.environ.setdefault('no_proxy', '*')
os.environ.setdefault('NO_PROXY', '*')
from wecom_aibot_sdk import WSClient, generate_req_id, WsFrame
from .config import WeComConfig, ChannelConfig, get_config
from .session_bridge import AntigravitySessionBridge
from .utils.formatting import format_markdown_body

MessageHandlerCallback = Callable[[str, str, WsFrame], Awaitable[Optional[str]]]


class ChannelRunner:
    """Manages the lifecycle, WebSocket connection, and Antigravity bridge for a single channel."""

    def __init__(
        self,
        config: ChannelConfig,
        parent_config: WeComConfig,
        custom_handler: Optional[MessageHandlerCallback] = None
    ):
        self.config = config
        self.parent_config = parent_config
        self.custom_handler = custom_handler
        self.client: Optional[WSClient] = None
        self.bridge = AntigravitySessionBridge(
            session_id=config.session_id,
            name=config.name,
            prompt_template=config.prompt_template,
            timeout_sec=config.timeout_sec,
            flow_log_path=config.flow_log_path
        )

    def setup_handlers(self, client: WSClient) -> None:
        async def on_all(frame: WsFrame):
            body = frame.body or {}
            from_info = body.get("from") or {}
            userid = from_info.get("userid") if isinstance(from_info, dict) else None
            chat_id = body.get("chatid") or userid
            if chat_id and chat_id != self.config.last_chat_id:
                self.config.last_chat_id = chat_id
                self.parent_config.save()

        async def on_message(frame: WsFrame):
            body = frame.body or {}
            from_info = body.get("from") or {}
            userid = from_info.get("userid") if isinstance(from_info, dict) else None
            chat_id = body.get("chatid") or userid
            if chat_id and chat_id != self.config.last_chat_id:
                self.config.last_chat_id = chat_id
                self.parent_config.save()

            text_info = body.get("text", {})
            user_text = text_info.get("content", "").strip()
            if not user_text:
                return

            reply_text: Optional[str] = None

            # 1. Check custom handler (if specified for this channel)
            if self.custom_handler:
                try:
                    reply_text = await self.custom_handler(user_text, chat_id or "", frame)
                except Exception as e:
                    print(f"[{self.config.name}] Custom handler error: {e}", flush=True)

            # 2. Native AI carrier invocation via Antigravity Session Bridge
            if reply_text is None and self.config.session_id:
                print(f"[{self.config.name}] 正在调用 Antigravity 会话载体 ({self.config.session_id})...", flush=True)
                try:
                    reply_text = await self.bridge.invoke_async(user_text)
                except Exception as e:
                    print(f"[{self.config.name}] Bridge invocation error: {e}", flush=True)

            # 3. Default friendly fallback
            if reply_text is None:
                reply_text = (
                    f"收到您的消息：*{user_text}*\n\n"
                    f"⚠️ 会话响应超时或正在处理中。您可以稍候在电脑端 Antigravity 会话中查看进展。"
                )

            stream_id = generate_req_id("stream")
            try:
                await client.reply_stream(frame, stream_id, reply_text, finish=True)
            except Exception as e:
                print(f"[{self.config.name}] Reply stream error: {e}", flush=True)

        client.on("*", on_all)
        client.on("message", on_message)

    async def run_loop(self, stop_event: asyncio.Event) -> None:
        """Connection and auto-reconnect loop for this channel."""
        while not stop_event.is_set():
            try:
                self.client = WSClient({
                    "bot_id": self.config.bot_id,
                    "secret": self.config.bot_secret
                })
                self.setup_handlers(self.client)
                print(f"[{self.config.name}] 正在连接企业微信 WebSocket (bot_id={self.config.bot_id[:10]}...)...", flush=True)
                await self.client.connect_async()
                print(f"[{self.config.name}] 已连接并鉴权成功！", flush=True)

                while not stop_event.is_set():
                    if not self.client.is_connected:
                        print(f"[{self.config.name}] 检测到连接断开，准备重连...", flush=True)
                        break
                    await asyncio.sleep(2)
            except Exception as e:
                print(f"[{self.config.name}] 连接异常: {e}", flush=True)
                await asyncio.sleep(3)


class WeComBotService:
    """Manages long-running interactive WebSocket connections for all configured channels with local IPC."""

    def __init__(
        self,
        config: Optional[WeComConfig] = None,
        custom_handler: Optional[MessageHandlerCallback] = None,
        custom_handlers: Optional[Dict[str, MessageHandlerCallback]] = None
    ):
        self.config = config or get_config()
        self._custom_handlers: Dict[str, MessageHandlerCallback] = custom_handlers or {}
        if custom_handler and self.config.primary_channel:
            self._custom_handlers[self.config.primary_channel.id] = custom_handler

        self._runners: Dict[str, ChannelRunner] = {}
        self._stop_event = asyncio.Event()
        self._http_runner: Optional[web.AppRunner] = None

    def _init_runners(self) -> None:
        self._runners.clear()
        for ch in self.config.channels:
            if ch.enabled:
                handler = self._custom_handlers.get(ch.id)
                self._runners[ch.id] = ChannelRunner(ch, self.config, custom_handler=handler)

    def get_runner(self, channel_id: Optional[str] = None, bot_id: Optional[str] = None) -> Optional[ChannelRunner]:
        if channel_id and channel_id in self._runners:
            return self._runners[channel_id]
        if bot_id:
            for runner in self._runners.values():
                if runner.config.bot_id == bot_id:
                    return runner
        if self._runners:
            # Fallback to primary runner
            for runner in self._runners.values():
                if runner.config.enabled:
                    return runner
            return next(iter(self._runners.values()))
        return None

    async def _handle_ipc_send(self, request: web.Request) -> web.Response:
        """Handle IPC request to send message using appropriate channel WebSocket."""
        try:
            data = await request.json()
            content = data.get("content", "")
            channel_id = data.get("channel_id")
            bot_id = data.get("bot_id")
            target_chat = data.get("chat_id")

            runner = self.get_runner(channel_id=channel_id, bot_id=bot_id)
            if not runner:
                return web.json_response({"errcode": -1, "errmsg": "no active channel available"}, status=400)

            target_chat = target_chat or runner.config.last_chat_id
            if not target_chat:
                return web.json_response({"errcode": -1, "errmsg": "no chat_id specified"}, status=400)

            if not runner.client or not runner.client.is_authenticated:
                return web.json_response({"errcode": -2, "errmsg": f"websocket not ready for channel {runner.config.name}"}, status=503)

            body = format_markdown_body(content)
            res = await runner.client.send_message(target_chat, body)
            errcode = getattr(res, "errcode", 0)
            return web.json_response({"errcode": errcode, "errmsg": getattr(res, "errmsg", "ok")})
        except Exception as e:
            return web.json_response({"errcode": -3, "errmsg": str(e)}, status=500)

    async def _start_ipc_server(self) -> None:
        """Start local HTTP server for connection multiplexing."""
        app = web.Application()
        app.router.add_post("/send", self._handle_ipc_send)
        self._http_runner = web.AppRunner(app)
        await self._http_runner.setup()
        site = web.TCPSite(self._http_runner, "127.0.0.1", self.config.ipc_port)
        await site.start()
        print(f"[Bot Service] Local IPC server listening on http://127.0.0.1:{self.config.ipc_port}", flush=True)

    async def _stop_ipc_server(self) -> None:
        if self._http_runner:
            await self._http_runner.cleanup()

    async def start_async(self) -> None:
        """Starts WebSocket loops for all enabled channels and local IPC server."""
        self._stop_event.clear()
        self._init_runners()

        if not self._runners:
            print("[Bot Service] 警告: 未找到任何已启用的通道配置！请检查 wecom_config.json", flush=True)
            return

        print(f"[Bot Service] 启动多通道服务 (共 {len(self._runners)} 个活跃通道):", flush=True)
        for runner in self._runners.values():
            print(f"  - 通道 [{runner.config.name}] (id={runner.config.id}): Bot={runner.config.bot_id[:12]}... -> 会话={runner.config.session_id}", flush=True)

        await self._start_ipc_server()

        # Gather all channel runner loops concurrently
        tasks = [runner.run_loop(self._stop_event) for runner in self._runners.values()]
        await asyncio.gather(*tasks)

    def stop(self) -> None:
        """Stops the daemon and all channels."""
        self._stop_event.set()
        for runner in self._runners.values():
            if runner.client:
                try:
                    asyncio.run(runner.client.disconnect())
                except Exception:
                    pass
        try:
            asyncio.run(self._stop_ipc_server())
        except Exception:
            pass

    def start(self) -> None:
        """Synchronous blocking start."""
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            self.stop()
