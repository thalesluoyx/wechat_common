"""
Generic Antigravity Session Bridge
Binds any WeCom Bot channel to a specific Antigravity conversation session.
Invokes language_server.exe agentapi natively and captures the real LLM output.
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Union

LANGUAGE_SERVER_EXE = Path(r"C:\Users\33991\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe")
BRAIN_ROOT = Path(r"C:\Users\33991\.gemini\antigravity\brain")


class AntigravitySessionBridge:
    """Binds an incoming text stream to a specific Antigravity conversation session."""

    def __init__(
        self,
        session_id: str,
        name: str = "默认通道",
        prompt_template: Optional[str] = None,
        timeout_sec: int = 35,
        flow_log_path: Optional[Union[str, Path]] = None
    ):
        self.session_id = session_id
        self.name = name
        self.prompt_template = prompt_template or "用户通过企业微信[{name}]发来消息：{user_text}\n请按照工作区技能与规则进行处理，并给出亲切简洁的回复。"
        self.timeout_sec = timeout_sec
        self.flow_log_path = Path(flow_log_path) if flow_log_path else None

        self.brain_dir = BRAIN_ROOT / session_id
        self.transcript_file = self.brain_dir / ".system_generated" / "logs" / "transcript.jsonl"

    async def invoke_async(self, user_text: str, title: Optional[str] = None) -> Optional[str]:
        """Asynchronously invoke the target session agent without blocking the asyncio loop."""
        title_str = title or f"微信[{self.name}]"
        return await asyncio.to_thread(self._invoke_sync, user_text, title_str)

    def _invoke_sync(self, user_text: str, title: str) -> Optional[str]:
        """Synchronously execute agentapi call and poll transcript for PLANNER_RESPONSE."""
        if not self.transcript_file.exists():
            print(f"[SessionBridge:{self.name}] Warning: Transcript file not found at {self.transcript_file}", flush=True)
            return None

        # 1. Record current line count
        try:
            initial_count = len(self.transcript_file.read_text(encoding="utf-8").splitlines())
        except Exception:
            initial_count = 0

        # 2. Format prompt safely with replace to avoid KeyError if user_text contains braces
        formatted_prompt = self.prompt_template.replace("{user_text}", user_text).replace("{name}", self.name)

        # 3. Call language_server.exe directly (safe against Windows batch newline truncations)
        cmd = [
            str(LANGUAGE_SERVER_EXE),
            "agentapi",
            "send-message",
            f"--title={title}",
            self.session_id,
            formatted_prompt
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0:
                print(f"[SessionBridge:{self.name}] agentapi send-message error: {res.stderr}", flush=True)
                return None
        except Exception as e:
            print(f"[SessionBridge:{self.name}] Exception calling language_server: {e}", flush=True)
            return None

        # 4. Wait for the native agent in that session to generate PLANNER_RESPONSE
        start_time = time.time()
        while time.time() - start_time < self.timeout_sec:
            time.sleep(1.0)
            try:
                lines = self.transcript_file.read_text(encoding="utf-8").splitlines()
                if len(lines) > initial_count:
                    for line in reversed(lines[initial_count:]):
                        d = json.loads(line)
                        if d.get("source") == "MODEL" and d.get("type") == "PLANNER_RESPONSE" and d.get("status") == "DONE":
                            content = d.get("content")
                            if content and content.strip():
                                reply = content.strip()
                                self._record_flow_log(user_text, reply)
                                return reply
            except Exception:
                pass

        print(f"[SessionBridge:{self.name}] Timeout after {self.timeout_sec}s waiting for AI session response", flush=True)
        return None

    def _record_flow_log(self, user_text: str, reply_text: str) -> None:
        """Record to local Markdown flow log if configured."""
        if not self.flow_log_path:
            return
        try:
            self.flow_log_path.parent.mkdir(parents=True, exist_ok=True)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.flow_log_path, "a", encoding="utf-8") as f:
                f.write(f"### 🕒 {now_str}\n\n- 👤 **微信输入**：{user_text}\n- 🤖 **AI回复**：\n{reply_text}\n\n---\n\n")
        except Exception as e:
            print(f"[SessionBridge:{self.name}] Flow log write warning: {e}", flush=True)
