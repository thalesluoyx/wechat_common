#!/usr/bin/env python3
"""
Entrypoint: Send Notification via WeCom
Usage:
  python send_notification.py "消息内容"
  python send_notification.py --markdown "### 标题\n内容"
  python send_notification.py --chatid "UserID" "消息内容"
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wechat_common import send_wecom_message, get_config

if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Send WeCom notification")
    parser.add_argument("message", nargs="+", help="Content of notification")
    parser.add_argument("--markdown", action="store_true", default=True, help="Send as markdown (default: True)")
    parser.add_argument("--chatid", type=str, default=None, help="Target chat or user ID")

    args = parser.parse_args()
    msg_content = " ".join(args.message)
    # WeCom proactive send only supports markdown or template_card
    msg_type = "markdown"

    success = send_wecom_message(
        content=msg_content,
        chat_id=args.chatid,
        msg_type=msg_type
    )

    if success:
        print("企业微信通知发送成功")
        sys.exit(0)
    else:
        print("企业微信通知发送失败", file=sys.stderr)
        sys.exit(1)
