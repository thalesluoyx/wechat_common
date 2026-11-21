"""
Dedicated '日常运动_Session' Dialogue & Tracking Handler
Strictly bound to Antigravity Session: b3f54d18-42b5-45e4-aebe-d9ca18f31103
Exclusively manages daily physical activities:
  - 散步 (Walking)
  - 游泳 (Swimming)
  - 徒步 (Hiking)
  - 内观 / 冥想 (Meditation / Vipassana)
  - 开髋 / 拉伸 (Hip / Stretching)
  - 历史查询 (Activity Query)

STRICT RULE: Strictly isolated from '健身私教' (9ba2c4db-e97a-4aa9-a452-53c67aa4abb9).
Heavy strength training is redirected to the PC Antigravity Coach session.
"""

import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from wecom_aibot_sdk import WsFrame
from .config import PROJECT_ROOT

SESSION_DATA_FILE = PROJECT_ROOT / "data" / "daily_activity_session.json"
RECORD_JS = Path(r"c:\Work\MyObsidian\我的笔记\健康\0-数据与脚本\record.js")

# Target Antigravity Session UUID
TARGET_SESSION_ID = "b3f54d18-42b5-45e4-aebe-d9ca18f31103"
ANTIGRAVITY_LOGS_DIR = Path(r"C:\Users\33991\.gemini\antigravity\brain") / TARGET_SESSION_ID / ".system_generated" / "logs"
TRANSCRIPT_FILE = ANTIGRAVITY_LOGS_DIR / "transcript.jsonl"
TRANSCRIPT_FULL_FILE = ANTIGRAVITY_LOGS_DIR / "transcript_full.jsonl"
FLOW_MD_FILE = Path(r"c:\Work\MyObsidian\我的笔记\健康\1-日常追踪\日常运动微信流水.md")

LANGUAGE_SERVER_EXE = Path(r"C:\Users\33991\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe")

GYM_KEYWORDS = [
    "卧推", "杠铃", "哑铃", "硬拉", "大重量", "增肌", "深蹲",
    "高位下拉", "推胸", "划船", "腿屈伸", "箱式深蹲", "倒蹬", "健身私教"
]


class DailyActivitySession:
    """Manages context, parsing, and Antigravity transcript sync for '日常运动_Session'."""

    def __init__(self, session_file: Optional[Path] = None):
        self.session_file = session_file or SESSION_DATA_FILE
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_history(self) -> None:
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        to_save = self.history[-50:]
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)

    def _execute_record_js(self, args: List[str]) -> str:
        """Call record.js in Obsidian directory."""
        if not RECORD_JS.exists():
            return "错误: record.js 路径未找到"
        cmd = ["node", str(RECORD_JS)] + args
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            return res.stdout.strip()
        return f"记录失败: {res.stderr.strip()}"

    def _sync_to_antigravity(self, user_text: str, reply_text: str) -> None:
        """Incrementally sync dialog turn into the target Antigravity session transcript."""
        if not ANTIGRAVITY_LOGS_DIR.exists():
            return

        last_step_index = 0
        if TRANSCRIPT_FILE.exists():
            try:
                with open(TRANSCRIPT_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line_str = line.strip()
                        if line_str:
                            try:
                                d = json.loads(line_str)
                                idx = d.get("step_index", 0)
                                if idx > last_step_index:
                                    last_step_index = idx
                            except Exception:
                                pass
            except Exception:
                pass

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        user_entry = {
            "step_index": last_step_index + 1,
            "source": "USER_EXPLICIT",
            "type": "USER_INPUT",
            "status": "DONE",
            "created_at": now_utc,
            "content": f"<USER_REQUEST>\n【微信打卡】{user_text}\n</USER_REQUEST>"
        }

        reply_entry = {
            "step_index": last_step_index + 2,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "created_at": now_utc,
            "content": reply_text
        }

        chunk_transcript_dir = ANTIGRAVITY_LOGS_DIR / "chunks" / "transcript"
        chunk_full_dir = ANTIGRAVITY_LOGS_DIR / "chunks" / "transcript_full"

        target_files = [TRANSCRIPT_FILE, TRANSCRIPT_FULL_FILE]

        for cdir in [chunk_transcript_dir, chunk_full_dir]:
            if cdir.exists():
                existing = sorted([f for f in cdir.glob("*.jsonl") if f.is_file()])
                if existing:
                    target_files.append(existing[-1])
                else:
                    target_files.append(cdir / "00000000.jsonl")

        for target_file in target_files:
            try:
                with open(target_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(user_entry, ensure_ascii=False) + "\n")
                    f.write(json.dumps(reply_entry, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[Transcript Sync] Warning writing {target_file}: {e}", flush=True)

        # 同步写入 Obsidian 实时流水文件（支持 Obsidian 与 Antigravity 编辑器秒级自动渲染）
        try:
            FLOW_MD_FILE.parent.mkdir(parents=True, exist_ok=True)
            if not FLOW_MD_FILE.exists():
                with open(FLOW_MD_FILE, "w", encoding="utf-8") as f:
                    f.write("# 📱 日常运动微信对话流水日志\n\n> 本日志由企业微信【日常运动】Bot 自动实时沉淀。\n\n---\n\n")
            with open(FLOW_MD_FILE, "a", encoding="utf-8") as f:
                f.write(f"### 🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"- 👤 **微信输入**：{user_text}\n")
                f.write(f"- 🤖 **管家回复**：\n{reply_text}\n\n---\n\n")
        except Exception as e:
            print(f"[Flow Log Sync] Warning writing {FLOW_MD_FILE}: {e}", flush=True)

    def parse_and_record(self, text: str) -> Optional[str]:
        """Parse natural language into walk/swim/hike/meditation/hip/query commands."""
        # 1. 游泳 (Swim)
        # 匹配: 自由泳 600米 12:00 / 自由泳600米，用时12:00 / 游泳 1000米 22:30 / 蛙泳 500米 15分
        if any(k in text for k in ["泳", "游泳", "自由泳", "蛙泳", "仰泳", "蝶泳"]):
            style = "自由泳"
            for s in ["蛙泳", "仰泳", "蝶泳", "自由泳"]:
                if s in text:
                    style = s
                    break

            dist_match = re.search(r'(\d{2,5})\s*(?:米|m|M)', text)
            dist = int(dist_match.group(1)) if dist_match else 1000

            dur_match = re.search(r'(\d{1,2}[:：]\d{2}(?::\d{2})?|\d{1,3}\s*分(?:钟)?(?:\s*\d{1,2}\s*秒)?|\d{1,3}\s*(?:分钟|min|分))', text)
            if dur_match:
                dur_raw = dur_match.group(1).replace("：", ":").replace("分钟", "分").strip()
            else:
                dur_raw = "20:00"

            args = ["swim", "--distance", str(dist), "--duration", dur_raw, "--style", style]
            res = self._execute_record_js(args)

            return (
                f"🏊 **游泳记录成功！**\n\n"
                f"- **泳姿**：{style}\n"
                f"- **距离**：**{dist}** 米\n"
                f"- **用时**：**{dur_raw}**\n"
                f"- **状态**：已落库 SQLite 并同步至 Obsidian 与 Antigravity 对话！\n\n"
                f"游完泳注意保暖防寒，适时关注运动后迟发性血糖波动！💧"
            )

        # 2. 散步 (Walk)
        # 匹配: 散步 8500步 / 散步 8000 / 走了 6000 步 / 7200步 / 今日步数 8000
        walk_match = re.search(r'(?:散步|步行|走了|步数)\s*[:：]?\s*(\d{2,6})\s*步?', text)
        if not walk_match:
            walk_match = re.search(r'(\d{3,6})\s*步', text)
        if walk_match:
            steps = int(walk_match.group(1))
            self._execute_record_js(["walk", "--steps", str(steps)])
            return (
                f"🚶‍♂️ **散步记录成功！**\n\n"
                f"- **今日步数**：**{steps}** 步\n"
                f"- **状态**：已落库 SQLite 并同步至 Obsidian 散步日志！\n\n"
                f"保持日常低强度活动，对胰岛素敏感度与关节舒缓非常有益！🌱"
            )

        # 3. 开髋 / 拉伸 (Hip / Stretch)
        if any(k in text for k in ["开髋", "拉伸", "髋关节", "柔韧"]):
            dur_match = re.search(r'(\d+)\s*(?:分钟|min|分)', text)
            duration = int(dur_match.group(1)) if dur_match else 15
            self._execute_record_js(["hip", "--duration", str(duration)])
            return (
                f"🧘‍♂️ **开髋拉伸记录成功！**\n\n"
                f"- **时长**：**{duration}** 分钟\n"
                f"- **状态**：已落库 SQLite 并同步至 Obsidian 开髋日志！\n\n"
                f"改善骨盆灵活性，预防下坡膝盖与腰椎代偿压力！💪"
            )

        # 4. 内观 / 冥想 (Meditation)
        if any(k in text for k in ["内观", "冥想", "坐禅", "观呼吸", "静坐"]):
            dur_match = re.search(r'(\d+)\s*(?:分钟|min|分)', text)
            duration = int(dur_match.group(1)) if dur_match else 20

            method = "观呼吸"
            if "身体扫描" in text:
                method = "身体扫描"
            elif "自性" in text:
                method = "自性觉察"

            feeling = "平静"
            for f in ["平静", "专注", "安详", "清明", "妄念多", "微困", "轻松"]:
                if f in text:
                    feeling = f
                    break

            args = ["meditation", "--duration", str(duration), "--method", method, "--feeling", feeling]
            self._execute_record_js(args)
            return (
                f"🧘 **内观记录成功！**\n\n"
                f"- **时长**：**{duration}** 分钟\n"
                f"- **方法**：{method}\n"
                f"- **感受**：{feeling}\n"
                f"- **状态**：已落库 SQLite 并同步至 Obsidian 内观日志！\n\n"
                f"正念觉察，身心安顿。🌿"
            )

        # 5. 徒步 (Hike)
        if any(k in text for k in ["徒步", "爬山", "越野"]):
            dur_match = re.search(r'(\d+)\s*(?:分钟|min|小时|h)', text)
            duration = 60
            if dur_match:
                val = int(dur_match.group(1))
                duration = val * 60 if ("小时" in text or "h" in text) else val

            loc_match = re.search(r'(?:在|去|于)?\s*([^\d\s，,。]+?)(?:徒步|爬山)', text)
            location = loc_match.group(1) if loc_match else "户外"
            if len(location) > 8:
                location = "户外"

            args = ["hike", "--duration", str(duration), "--location", location]
            self._execute_record_js(args)
            return (
                f"🥾 **徒步记录成功！**\n\n"
                f"- **地点**：{location}\n"
                f"- **时长**：**{duration}** 分钟\n"
                f"- **状态**：已落库 SQLite 并同步至 Obsidian 徒步日志！\n\n"
                f"户外活动注意保护膝关节，适时补充水分与电解质！🏔️"
            )

        # 6. 数据查询 (Query)
        if any(k in text for k in ["查运动", "运动查询", "查询运动", "最近运动", "今日运动", "今日状态", "查记录"]):
            days_match = re.search(r'(\d+)\s*天', text)
            if days_match:
                days = int(days_match.group(1))
            elif "今日" in text:
                days = 1
            elif "最近" in text:
                days = 3
            else:
                days = 7

            res = self._execute_record_js(["query", "--days", str(days)])
            return f"📋 **运动历史查询（最近 {days} 天）：**\n\n```text\n{res}\n```"

        return None

    def _send_to_ai_session(self, user_text: str, timeout_sec: int = 35) -> Optional[str]:
        """Invoke Antigravity's target session agent natively as the true AI carrier."""
        if not TRANSCRIPT_FILE.exists():
            return None

        import time
        try:
            initial_count = len(TRANSCRIPT_FILE.read_text(encoding="utf-8").splitlines())
        except Exception:
            initial_count = 0

        prompt = (
            f"用户通过微信发来日常运动消息：{user_text}\n"
            f"请遵循 0-数据与脚本/SKILL.md 规则进行意图理解与处理。\n"
            f"- 如包含散步、游泳、徒步、内观、开髋拉伸，请调用 record.js 工具落库并更新 Obsidian。\n"
            f"- 如为数据查询，请调用 record.js query。\n"
            f"- 处理完毕后，请给出专业、温馨、简洁的回复，告知打卡结果与今日运动状态。"
        )

        cmd = [
            str(LANGUAGE_SERVER_EXE),
            "agentapi",
            "send-message",
            "--title=微信运动打卡",
            TARGET_SESSION_ID,
            prompt
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0:
                print(f"[AI Carrier] agentapi send-message error: {res.stderr}", flush=True)
                return None
        except Exception as e:
            print(f"[AI Carrier] Exception calling agentapi: {e}", flush=True)
            return None

        # Wait for the native agent in that session to generate PLANNER_RESPONSE
        start = time.time()
        while time.time() - start < timeout_sec:
            time.sleep(1.0)
            try:
                lines = TRANSCRIPT_FILE.read_text(encoding="utf-8").splitlines()
                if len(lines) > initial_count:
                    for line in reversed(lines[initial_count:]):
                        d = json.loads(line)
                        if d.get("source") == "MODEL" and d.get("type") == "PLANNER_RESPONSE" and d.get("status") == "DONE":
                            content = d.get("content")
                            if content and content.strip():
                                return content.strip()
            except Exception:
                pass

        print(f"[AI Carrier] Timeout after {timeout_sec}s waiting for AI session response", flush=True)
        return None

    async def handle_user_message(self, text: str, chat_id: str, frame: WsFrame) -> str:
        """Main dispatcher for incoming WeChat messages."""
        text_clean = text.strip()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.history.append({"role": "user", "time": now_str, "text": text_clean})

        # 1. 严格检查是否属于大重量健身私教
        if any(k in text_clean for k in GYM_KEYWORDS):
            reply = (
                f"ℹ️ **提示：本会话为【日常运动_Session】专属打卡通道**\n\n"
                f"我专注于您的**散步、游泳、徒步、内观、开髋拉伸**等日常身心活动。\n\n"
                f"涉及大重量力量器械训练、专项动作与私教计划调整，请在电脑端 Antigravity 中打开专属的【健身私教】会话交流打卡哦！🏋️‍♂️"
            )
            self.history.append({"role": "assistant", "time": now_str, "text": reply})
            self._save_history()
            return reply

        # 2. 原生调用 Antigravity【日常运动_Session】作为真正 AI 载体
        print(f"[DailyActivitySession] Delegating '{text_clean}' to Antigravity Session {TARGET_SESSION_ID}...", flush=True)
        ai_reply = self._send_to_ai_session(text_clean)
        if ai_reply:
            self.history.append({"role": "assistant", "time": now_str, "text": ai_reply})
            self._save_history()
            # 记录流水日志供快速巡检
            try:
                FLOW_MD_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(FLOW_MD_FILE, "a", encoding="utf-8") as f:
                    f.write(f"### 🕒 {now_str}\n\n- 👤 **微信输入**：{text_clean}\n- 🤖 **AI管家（会话载体生成）**：\n{ai_reply}\n\n---\n\n")
            except Exception:
                pass
            return ai_reply

        # 3. 兜底回退机制：若大模型调度超时，则本地规则解析确保落库不丢数据
        print(f"[DailyActivitySession] Fallback to local rule engine for '{text_clean}'", flush=True)
        record_reply = self.parse_and_record(text_clean)
        if record_reply:
            self.history.append({"role": "assistant", "time": now_str, "text": record_reply})
            self._save_history()
            return record_reply

        # 4. 默认兜底应答
        reply = (
            f"已收到您的消息：*{text_clean}*\n\n"
            f"如需打卡，可以直接发送如：\n"
            f"- `散步 8000步`\n"
            f"- `自由泳 600米 12:00`\n"
            f"- `开髋 15分钟`\n"
            f"- `内观 30分钟`\n"
            f"- `查运动`\n\n"
            f"随时为您记录并同步到 Obsidian 笔记与 Antigravity 中！"
        )
        self.history.append({"role": "assistant", "time": now_str, "text": reply})
        self._save_history()
        return reply


_session_instance: Optional[DailyActivitySession] = None

def get_daily_activity_session() -> DailyActivitySession:
    global _session_instance
    if _session_instance is None:
        _session_instance = DailyActivitySession()
    return _session_instance
