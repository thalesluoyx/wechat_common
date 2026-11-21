"""
Proactive Notification Sender with Local IPC Multiplexer & Multi-Channel Support
"""

import asyncio
from typing import Optional
import aiohttp
from wecom_aibot_sdk import WSClient
from .config import (
    WeComConfig,
    get_config,
    DEFAULT_AUTH_WAIT_RETRIES,
    DEFAULT_AUTH_WAIT_INTERVAL_SEC,
)
from .utils.formatting import format_markdown_body, format_text_body


class WeComNotifier:
    """Manages proactive outbound notifications with IPC multiplexing across multiple channels."""

    def __init__(self, config: Optional[WeComConfig] = None):
        self.config = config or get_config()

    async def _send_via_ipc(
        self,
        content: str,
        chat_id: str,
        msg_type: str = "markdown",
        channel_id: Optional[str] = None,
        bot_id: Optional[str] = None
    ) -> Optional[bool]:
        """Try sending via local daemon IPC to reuse existing WebSocket."""
        url = f"http://127.0.0.1:{self.config.ipc_port}/send"
        payload = {
            "content": content,
            "chat_id": chat_id,
            "msg_type": msg_type
        }
        if channel_id:
            payload["channel_id"] = channel_id
        if bot_id:
            payload["bot_id"] = bot_id

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2.0)) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("errcode") == 0
                    return None
        except Exception:
            return None

    async def send_async(
        self,
        content: str,
        chat_id: Optional[str] = None,
        msg_type: str = "markdown",
        channel_id: Optional[str] = None,
        bot_id: Optional[str] = None
    ) -> bool:
        """Send message, prioritizing local IPC daemon multiplexing."""
        target_channel = self.config.get_channel(channel_id=channel_id, bot_id=bot_id)
        target_chat = chat_id or (target_channel.last_chat_id if target_channel else self.config.last_chat_id)
        if not target_chat:
            return False

        # 1. Try local IPC first (zero risk of kicking daemon)
        ipc_result = await self._send_via_ipc(content, target_chat, msg_type, channel_id, bot_id)
        if ipc_result is not None:
            return ipc_result

        # 2. Fallback: Standalone WebSocket connection if daemon is not running
        if not target_channel or not target_channel.bot_id or not target_channel.bot_secret:
            return False

        client = WSClient({
            "bot_id": target_channel.bot_id,
            "secret": target_channel.bot_secret
        })

        try:
            await client.connect_async()
            for _ in range(DEFAULT_AUTH_WAIT_RETRIES):
                if client.is_authenticated:
                    break
                await asyncio.sleep(DEFAULT_AUTH_WAIT_INTERVAL_SEC)

            if not client.is_authenticated:
                await client.disconnect()
                return False

            # WeCom AI Bot proactive send requires markdown
            body = format_markdown_body(content)

            res = await client.send_message(target_chat, body)
            await client.disconnect()
            return getattr(res, "errcode", 0) == 0
        except Exception:
            try:
                await client.disconnect()
            except Exception:
                pass
            return False

    def send(
        self,
        content: str,
        chat_id: Optional[str] = None,
        msg_type: str = "markdown",
        channel_id: Optional[str] = None,
        bot_id: Optional[str] = None
    ) -> bool:
        """Synchronous wrapper for send_async."""
        return asyncio.run(self.send_async(content, chat_id=chat_id, msg_type=msg_type, channel_id=channel_id, bot_id=bot_id))


def send_wecom_message(
    content: str,
    chat_id: Optional[str] = None,
    msg_type: str = "markdown",
    channel_id: Optional[str] = None,
    bot_id: Optional[str] = None,
    config: Optional[WeComConfig] = None
) -> bool:
    """Convenience function to send a message via configured WeCom channel."""
    notifier = WeComNotifier(config=config)
    return notifier.send(content, chat_id=chat_id, msg_type=msg_type, channel_id=channel_id, bot_id=bot_id)
