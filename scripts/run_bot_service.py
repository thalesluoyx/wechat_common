#!/usr/bin/env python3
"""
Entrypoint: Run WeCom Multi-Channel Bot Listener Service Daemon
Configurable bindings between WeCom Bots and Antigravity Sessions.
"""

import os
import sys
from pathlib import Path

# 避免 Windows 系统 socks:// 代理引发 websocket 异常
os.environ.setdefault('no_proxy', '*')
os.environ.setdefault('NO_PROXY', '*')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wechat_common import WeComBotService, get_config, get_daily_activity_session

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    config = get_config()
    session = get_daily_activity_session()

    # Channel-specific custom handlers (e.g. daily_activity has specialized record.js fallback)
    custom_handlers = {
        "daily_activity": session.handle_user_message
    }

    print("=" * 60, flush=True)
    print("🚀 启动 Antigravity <-> 企业微信 多通道协同守护服务", flush=True)
    print(f"📦 配置文件: {config.config_file_path}", flush=True)
    print(f"🌐 本地 IPC 端口: {config.ipc_port}", flush=True)
    print("=" * 60, flush=True)

    bot_service = WeComBotService(
        config=config,
        custom_handlers=custom_handlers
    )

    try:
        bot_service.start()
    except KeyboardInterrupt:
        print("\n[WeCom Service] 后台服务正常退出。", flush=True)
