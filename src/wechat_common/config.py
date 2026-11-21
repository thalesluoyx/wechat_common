"""
Centralized Configuration for WeCom Integration with Multi-Channel Bot Support
Allows flexible, configurable bindings between WeCom Bots and Antigravity Sessions.
"""

import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any

# Path Constants
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_CONFIG_FILE = DEFAULT_DATA_DIR / "wecom_config.json"
OBSIDIAN_CONFIG_FILE = Path(r"c:\Work\MyObsidian\我的笔记\健康\0-数据与脚本\wecom_config.json")

# Magic Numbers & Timeouts
DEFAULT_CONNECT_TIMEOUT_SEC = 5.0
DEFAULT_AUTH_WAIT_RETRIES = 10
DEFAULT_AUTH_WAIT_INTERVAL_SEC = 0.5
DEFAULT_IPC_PORT = 28888

DEFAULT_BOT_ID = "aibHijIfgjxior5g9W-WFBdeoqN8QhnrSh_"
DEFAULT_BOT_SECRET = "ghRhejm1GRcCHQPlNdW777nFobWgGGcega20NaDCEDN"
DEFAULT_CHAT_ID = "LuoYuXun"
DEFAULT_SESSION_ID = "b3f54d18-42b5-45e4-aebe-d9ca18f31103"


@dataclass
class ChannelConfig:
    id: str
    name: str = "默认通道"
    enabled: bool = True
    bot_id: str = ""
    bot_secret: str = ""
    session_id: str = ""
    prompt_template: str = "用户通过企业微信[{name}]发来消息：{user_text}\n请按照该会话设定的角色、技能与规则进行处理，并给出精准亲切的回复。"
    flow_log_path: Optional[str] = None
    timeout_sec: int = 35
    last_chat_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WeComConfig:
    """Configuration class supporting multi-channel routing with 100% backward compatibility."""

    def __init__(
        self,
        corp_id: str = "ww3ee9feeacefff47d",
        ipc_port: int = DEFAULT_IPC_PORT,
        channels: Optional[List[ChannelConfig]] = None,
        config_file_path: Optional[Path] = None,
        bot_id: Optional[str] = None,
        bot_secret: Optional[str] = None,
        last_chat_id: Optional[str] = None
    ):
        self.corp_id = corp_id
        self.ipc_port = ipc_port
        self.config_file_path = config_file_path
        self.channels: List[ChannelConfig] = channels if channels is not None else []

        if not self.channels:
            self.channels = [
                ChannelConfig(
                    id="daily_activity",
                    name="日常运动",
                    enabled=True,
                    bot_id=bot_id or DEFAULT_BOT_ID,
                    bot_secret=bot_secret or DEFAULT_BOT_SECRET,
                    session_id=DEFAULT_SESSION_ID,
                    prompt_template="用户通过微信发来日常运动消息：{user_text}\n请按照工作区日常运动规则进行记录或回答，若为运动打卡请使用 record.js 写入数据库，并给出简明亲切的回复。",
                    flow_log_path=r"c:\Work\MyObsidian\我的笔记\健康\1-日常追踪\日常运动微信流水.md",
                    timeout_sec=35,
                    last_chat_id=last_chat_id or DEFAULT_CHAT_ID
                )
            ]
        elif bot_id or bot_secret or last_chat_id:
            ch = self.channels[0]
            if bot_id:
                ch.bot_id = bot_id
            if bot_secret:
                ch.bot_secret = bot_secret
            if last_chat_id:
                ch.last_chat_id = last_chat_id

    @property
    def primary_channel(self) -> Optional[ChannelConfig]:
        """Return the first active channel or the first channel."""
        for ch in self.channels:
            if ch.enabled:
                return ch
        return self.channels[0] if self.channels else None

    # Backward compatibility properties
    @property
    def bot_id(self) -> str:
        ch = self.primary_channel
        return ch.bot_id if ch else ""

    @bot_id.setter
    def bot_id(self, val: str) -> None:
        ch = self.primary_channel
        if ch:
            ch.bot_id = val

    @property
    def bot_secret(self) -> str:
        ch = self.primary_channel
        return ch.bot_secret if ch else ""

    @bot_secret.setter
    def bot_secret(self, val: str) -> None:
        ch = self.primary_channel
        if ch:
            ch.bot_secret = val

    @property
    def last_chat_id(self) -> str:
        ch = self.primary_channel
        return ch.last_chat_id if ch else ""

    @last_chat_id.setter
    def last_chat_id(self, val: str) -> None:
        ch = self.primary_channel
        if ch:
            ch.last_chat_id = val

    def get_channel(self, channel_id: Optional[str] = None, bot_id: Optional[str] = None) -> Optional[ChannelConfig]:
        """Lookup channel by channel_id or bot_id, falling back to primary channel."""
        if channel_id:
            for ch in self.channels:
                if ch.id == channel_id:
                    return ch
        if bot_id:
            for ch in self.channels:
                if ch.bot_id == bot_id:
                    return ch
        return self.primary_channel

    def update_chat_id_for_bot(self, bot_id: str, chat_id: str) -> bool:
        """Update last_chat_id for the channel matching bot_id."""
        for ch in self.channels:
            if ch.bot_id == bot_id:
                if ch.last_chat_id != chat_id:
                    ch.last_chat_id = chat_id
                    self.save()
                    return True
                return False
        return False

    def save(self, target_path: Optional[Path] = None) -> None:
        """Persist current configuration to disk."""
        path = target_path or self.config_file_path or DEFAULT_CONFIG_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "corp_id": self.corp_id,
            "ipc_port": self.ipc_port,
            "channels": [ch.to_dict() for ch in self.channels]
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Synchronize to Obsidian config if it exists
        if OBSIDIAN_CONFIG_FILE.exists() and path != OBSIDIAN_CONFIG_FILE:
            try:
                with open(OBSIDIAN_CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass


def get_config(config_path: Optional[Path] = None) -> WeComConfig:
    """
    Load configuration prioritizing environment variables,
    followed by JSON config file, and finally built-in defaults.
    """
    path = config_path or Path(os.getenv("WECOM_CONFIG_PATH", str(DEFAULT_CONFIG_FILE)))
    cfg = WeComConfig(config_file_path=path)

    raw_data: Dict[str, Any] = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            print(f"[Config] Error loading {path}: {e}")

    cfg.corp_id = raw_data.get("corp_id", cfg.corp_id)
    cfg.ipc_port = int(raw_data.get("ipc_port", cfg.ipc_port))

    channels_data = raw_data.get("channels")
    if isinstance(channels_data, list) and len(channels_data) > 0:
        cfg.channels = []
        for item in channels_data:
            if isinstance(item, dict):
                ch = ChannelConfig(
                    id=item.get("id", "default"),
                    name=item.get("name", "默认通道"),
                    enabled=item.get("enabled", True),
                    bot_id=item.get("bot_id", ""),
                    bot_secret=item.get("bot_secret", ""),
                    session_id=item.get("session_id", ""),
                    prompt_template=item.get("prompt_template", "用户通过企业微信[{name}]发来消息：{user_text}\n请按照该会话设定的角色、技能与规则进行处理，并给出精准亲切的回复。"),
                    flow_log_path=item.get("flow_log_path"),
                    timeout_sec=int(item.get("timeout_sec", 35)),
                    last_chat_id=item.get("last_chat_id", "")
                )
                cfg.channels.append(ch)
    elif "bot_id" in raw_data:
        legacy_bot_id = raw_data.get("bot_id", DEFAULT_BOT_ID)
        legacy_bot_secret = raw_data.get("bot_secret", DEFAULT_BOT_SECRET)
        legacy_chat_id = raw_data.get("last_chat_id", DEFAULT_CHAT_ID)
        legacy_session_id = raw_data.get("session_id", DEFAULT_SESSION_ID)

        cfg.channels = [
            ChannelConfig(
                id="daily_activity",
                name="日常运动",
                enabled=True,
                bot_id=legacy_bot_id,
                bot_secret=legacy_bot_secret,
                session_id=legacy_session_id,
                prompt_template="用户通过微信发来日常运动消息：{user_text}\n请按照工作区日常运动规则进行记录或回答，若为运动打卡请使用 record.js 写入数据库，并给出简明亲切的回复。",
                flow_log_path=r"c:\Work\MyObsidian\我的笔记\健康\1-日常追踪\日常运动微信流水.md",
                timeout_sec=35,
                last_chat_id=legacy_chat_id
            )
        ]

    # Environment variables override primary channel
    if os.getenv("WECOM_CORP_ID"):
        cfg.corp_id = os.getenv("WECOM_CORP_ID", cfg.corp_id)
    if os.getenv("WECOM_BOT_ID") and cfg.primary_channel:
        cfg.primary_channel.bot_id = os.getenv("WECOM_BOT_ID", cfg.primary_channel.bot_id)
    if os.getenv("WECOM_BOT_SECRET") and cfg.primary_channel:
        cfg.primary_channel.bot_secret = os.getenv("WECOM_BOT_SECRET", cfg.primary_channel.bot_secret)
    if os.getenv("WECOM_DEFAULT_CHAT_ID") and cfg.primary_channel:
        cfg.primary_channel.last_chat_id = os.getenv("WECOM_DEFAULT_CHAT_ID", cfg.primary_channel.last_chat_id)

    return cfg
