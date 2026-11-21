# wechat_common

企业微信（WeCom）通用集成套件，专为 **Google Antigravity AI Agent**、专属会话通信通道、智能提醒与运动打卡打造。

---

## 🌟 核心特性

1. **Antigravity 原生 Sidecar 守护**：
   - 托管于 Antigravity Sidecar 子系统（`~/.gemini/config/sidecars/wecom-channel-daemon/`）。
   - **随 Antigravity 启动自动运行**，具备 `"restart_policy": "always"` 进程级高可用自愈能力。
2. **多通道可配置绑定（Multi-Channel Architecture）**：
   - 支持配置多个企业微信智能 Bot，分别绑定至独立的 Antigravity 会话 UUID。
   - 【日常运动 Bot】与【健身私教 Bot】完全物理隔离，保留专属上下文记忆。
3. **原生会话载体驱动（Session as AI Carrier）**：
   - 通过 `language_server.exe agentapi send-message` 驱动目标会话，由会话内的智能体自主执行工具（如 `record.js` 打卡与 SQLite 落库），会话窗口实时同步。
4. **本地 IPC 端口多路复用 (:28888)**：
   - 定时提醒与周报推送脚本通过本地 HTTP IPC 复用已建立的长连接，零延迟且永不触发重连踢下线。
5. **本地规则兜底保障**：
   - 遇大模型调度极端超时，自动回退至本地规则引擎直接落库，确保打卡数据 100% 不丢。

---

## 📂 目录结构 (Standard src-layout)

```text
wechat_common/
├── src/
│   └── wechat_common/
│       ├── __init__.py
│       ├── config.py           # 统一配置中心与多通道 ChannelConfig 模型
│       ├── bot.py              # 多通道 WebSocket 监听引擎与 IPC 转发服务
│       ├── session_bridge.py   # Antigravity 会话桥接器 (language_server agentapi)
│       ├── activity_session.py # 日常运动专用处理器与 record.js 兜底引擎
│       ├── notifier.py         # 主动推送引擎 (支持 IPC 复用与降级直连)
│       └── utils/
│           ├── __init__.py
│           └── formatting.py   # Markdown 与文本格式化工具
├── tests/                      # 严格符合 pytest 隔离标准的单元测试 (100% Pass)
│   ├── conftest.py
│   ├── test_activity_session.py
│   ├── test_config.py
│   └── test_notifier.py
├── docs/                       # 系统架构与设计文档
│   └── architecture.md         # 完整架构、时序图与设计规范
├── data/                       # 数据与运行时日志
│   ├── wecom_config.json       # 核心通道配置文件
│   └── service.log             # 守护服务运行日志
├── scripts/                    # 可执行入口与工具
│   ├── run_bot_service.py      # 服务主入口 (Sidecar 启动脚本)
│   ├── run_daemon.bat          # Windows 批处理入口
│   └── send_notification.py    # CLI 通知工具
├── pyproject.toml              # 项目构建与依赖声明
└── README.md
```

---

## ⚙️ 配置文件说明 (`wecom_config.json`)

配置文件路径：`data/wecom_config.json`（已与 Obsidian `0-数据与脚本/wecom_config.json` 同步）。

```json
{
  "corp_id": "ww3ee9feeacefff47d",
  "ipc_port": 28888,
  "channels": [
    {
      "id": "daily_activity",
      "name": "日常运动",
      "enabled": true,
      "bot_id": "aibHijIfgjxior5g9W-WFBdeoqN8QhnrSh_",
      "bot_secret": "ghRhejm1GRcCHQPlNdW777nFobWgGGcega20NaDCEDN",
      "session_id": "b3f54d18-42b5-45e4-aebe-d9ca18f31103",
      "prompt_template": "用户通过微信发来日常运动消息：{user_text}\n请按照工作区日常运动规则进行记录或回答，若为运动打卡请使用 record.js 写入数据库，并给出简明亲切的回复。",
      "flow_log_path": "c:/Work/MyObsidian/我的笔记/健康/1-日常追踪/日常运动微信流水.md",
      "timeout_sec": 35,
      "last_chat_id": "LuoYuXun"
    }
  ]
}
```

### ➕ 如何增加新 Bot 与会话绑定？
1. 在企业微信管理后台创建一个新智能 Bot，获取 `bot_id` 与 `secret`。
2. 在 Antigravity 中获取或创建目标会话的 `UUID`（例如健身私教：`9ba2c4db-e97a-4aa9-a452-53c67aa4abb9`）。
3. 向 `channels` 列表中追加对应对象并保存。服务重启后即可同时监听多个 Bot！

---

## 🪐 Sidecar 自动运行

服务已注册为 Antigravity 官方 Sidecar：
- **配置文件**：`~/.gemini/config/sidecars/wecom-channel-daemon/sidecar.json`
- **自动启动**：只要打开 Antigravity，本守护服务即在后台自动拉起并运行。
- **运行日志**：`~/.gemini/antigravity/sidecar_data/wecom-channel-daemon/logs/sidecar.log`

---

## 🛠️ CLI 常用命令

### 1. 发送主动通知
```bash
python scripts/send_notification.py "这是一条测试通知"
python scripts/send_notification.py --markdown "### 今日训练完成\n- 散步 8,500 步"
```

### 2. 运行单元测试
```bash
pytest tests/
```
*(当前测试套件共 11 个测试用例，100% 离线 Mock 且全部通过)*
