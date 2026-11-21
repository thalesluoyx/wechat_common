# Handoff: 企业微信与 Antigravity 会话多通道网关与 Sidecar 架构

## Session Metadata
- Created: 2026-11-21 15:30:58
- Project: C:\Work\openclaw_projects\wechat_common
- Branch: main
- Git Commit: 05dc133 (Initial milestone commit)
- Session duration: 约 4.5 小时

## Recent Commits
- Initializing git repository and creating first milestone commit for multi-channel gateway.

## Handoff Chain
- Continues from: None (fresh start)
- Supersedes: None

## Current State Summary
本项目成功实现了企业微信智能机器人（WeCom AI Bot）与 Google Antigravity 会话之间的多通道双向打通与 Sidecar 自动化运维。系统由原先单一硬编码通道全面演进为声明式、可配置的多通道（Multi-Channel）架构，目前已同时在线运行两个独立通道：【日常运动】（绑定至运动管理会话 `b3f54d18...`）与【2027寒假】（绑定至旅行攻略会话 `d973899e...`）。后台服务已正式注册为 Antigravity 官方 Sidecar（`wecom-channel-daemon`），随 Antigravity 启动自动在后台运行、监听 IPC 28888 端口并保持长连接断线重连。所有 11 个单元测试 100% 离线通过，`.gitignore` 已完善配置并配备脱敏样例。

## Important Context
1. **敏感凭证绝不入库**：生产真实密钥保存在 `data/wecom_config.json` 与 Obsidian 本地镜像目录中，该文件已被严格 `.gitignore`。新环境或公开仓库请严格使用 `data/wecom_config.example.json` 作为模板。
2. **会话 UUID 映射机制**：
   - 【日常运动】：`b3f54d18-42b5-45e4-aebe-d9ca18f31103`
   - 【2027寒假】：`d973899e-43c3-405d-be73-5aa5b86e2df8`
   - 【健身私教】（保留独立会话，未接入打扰）：`9ba2c4db-e97a-4aa9-a452-53c67aa4abb9`
3. **IPC 端口架构约定**：本地网络固定占用 `28888` 端口。外部 Python 脚本通过向 `http://127.0.0.1:28888/send` 发送 POST 请求复用长连接，杜绝重复建立 WebSocket 导致连接互踢。
4. **Sidecar 管理机制**：服务配置于 `C:\Users\33991\.gemini\config\sidecars\wecom-channel-daemon\sidecar.json`。修改代码后若需强制重载，仅需终止当前运行的 Python 进程，Antigravity 宿主会根据 `restart_policy: always` 在 2 秒内拉起最新进程。

## Immediate Next Steps
1. 执行 Git 首次全量提交，并将代码推送至 GitHub 远程仓库：`https://github.com/thalesluoyx/wechat_common.git`
2. 持续观察手机企业微信端【日常运动】与【2027寒假】两个机器人的日常对话响应与交互稳定性
3. 如后续需新增其他助理（例如【健身私教】或【待办助理】），仅需向 `data/wecom_config.json` 追加对应通道即可

## Architecture Overview
系统采用“Sidecar 宿主常驻守护 + 异步长连接池 + 会话原生 AI 载体 + IPC 复用分流”架构：
1. **企业微信网关层**：通过官方 `wss://openws.work.weixin.qq.com` 建立反向 WebSocket 长连接，无需公网 IP 与复杂防火墙打洞。
2. **Sidecar 守护层**：位于 `~/.gemini/config/sidecars/wecom-channel-daemon/`，由 Antigravity 统一纳管生命周期，配置 `restart_policy: always` 实现异常自愈。
3. **多通道路由引擎**：`WeComBotService` 解析 `wecom_config.json` 中的 `channels` 数组，并发驱动多个 `ChannelRunner`，各自独立处理 WebSocket 消息与断线重连。
4. **会话原生驱动器**：`AntigravitySessionBridge` 直接调用 `language_server.exe agentapi send-message`，将消息原生推入指定会话，由该会话的模型、技能（如 `record.js` 运动落库）自主执行并由 Antigravity UI 实时渲染。
5. **IPC 端口多路复用**：本地开放 HTTP 28888 端口（`/send`），支持外部脚本（如每日提醒、运动周报）按 `channel_id` 或 `bot_id` 路由推送，零延迟复用长连接。

## Critical Files
| File | Purpose | Relevance |
|------|---------|-----------|
| `src/wechat_common/config.py` | 统一配置模型与环境解析 | 定义 `ChannelConfig` 与 `WeComConfig`，实现多通道加载与平滑向后兼容 |
| `src/wechat_common/bot.py` | 多通道 WebSocket 服务与 IPC 转发 | 核心守护进程，管理并发 `WSClient` 实例与本地 HTTP 28888 服务 |
| `src/wechat_common/session_bridge.py` | Antigravity 会话桥接器 | 通过 `language_server.exe` 原生调用 `agentapi` 并轮询截获真实 AI 回复 |
| `src/wechat_common/activity_session.py` | 日常运动专用处理器 | 负责力量器械拦截提示、运动命令落库与大模型超时本地规则兜底 |
| `src/wechat_common/notifier.py` | 主动推送引擎 | 提供 `send_wecom_message` API，优先走本地 IPC，支持多通道路由 |
| `scripts/run_bot_service.py` | Sidecar 服务主入口 | Antigravity Sidecar 调用的启动脚本 |
| `data/wecom_config.json` | 核心多通道配置（包含真实凭证） | 生产环境生效的 Bot 与会话映射表（已在 `.gitignore` 中绝对忽略） |
| `data/wecom_config.example.json` | 脱敏配置样例 | 供新环境克隆参考的无密配置模版 |
| `~/.gemini/config/sidecars/wecom-channel-daemon/sidecar.json` | Antigravity Sidecar 注册表 | 让守护服务随 Antigravity 启动自动运行的常驻配置文件 |

## Files Modified
| File | Changes | Rationale |
|------|---------|-----------|
| `src/wechat_common/config.py` | 引入 `ChannelConfig`，支持多通道解析与向后兼容 | 支撑可配置的多 Bot <-> 会话绑定需求 |
| `src/wechat_common/bot.py` | 实现 `ChannelRunner`，并发多 WebSocket 监听与多通道路由 | 实现多通道并行隔离与 IPC 分发 |
| `src/wechat_common/session_bridge.py` | 新增通用会话桥接器，处理安全模板替换与 transcript 轮询 | 让任意 Antigravity 会话均可作为 AI 载体 |
| `src/wechat_common/activity_session.py` | 增加深蹲等关键字拦截与 `record.js` 本地兜底 | 确保运动会话专注且数据不丢失 |
| `src/wechat_common/notifier.py` | 支持 `channel_id` 参数路由推送 | 支撑按指定 Bot 渠道发送主动通知 |
| `scripts/run_bot_service.py` | 更新多通道启动日志与入口组织 | Sidecar 统一拉起入口 |
| `docs/architecture.md` | 全面重写架构、Mermaid 时序图与技术规范 | 建立准确的系统级技术档案 |
| `README.md` | 更新为现代化 `src-layout` 规范、Sidecar 说明与快速上手 | 保持开源与协作友好 |
| `.gitignore` | 增加白名单规则、系统文件与临时文件过滤 | 提高安全性并保持仓库整洁 |
| `data/wecom_config.example.json` | 新增脱敏配置样例 | 提供标准配置模板 |

## Decisions Made
| Decision | Options Considered | Rationale |
|----------|-------------------|-----------|
| 使用 Antigravity Sidecar 取代 Windows 启动项 | Windows Startup VBS / Schtasks / Antigravity Sidecar | Sidecar 深度融入 Antigravity 生态，自启自愈，且由同一宿主管理生命周期，避免端口冲突 |
| 使用 `agentapi send-message` 作为调用载体 | 直接改写磁盘 JSONL / CLI 子进程交互 / 原生 agentapi | 只有 `agentapi` 才能真正唤醒该会话的智能体并驱动 React 界面状态更新 |
| 声明式 `channels` 数组配置结构 | 单文件硬编码 / 多配置文件 / 统一多通道 JSON 列表 | 统一列表结构清晰易读，增删通道只需复制粘贴一段 JSON，同时兼顾旧版平滑升级 |

## Assumptions Made
1. Antigravity 宿主常驻运行，`language_server.exe` 路径固定位于 `C:\Users\33991\AppData\Local\Programs\Antigravity\resources\bin\language_server.exe`。
2. Python 运行环境为 `C:\Users\33991\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`。
3. 企业微信网关长连接采用反向 WebSocket，无需开放外部入站端口。

## Potential Gotchas
1. **重连冲突**：严禁同时通过手动命令行和 Sidecar 启动两个守护进程，否则会在 WeCom 网关产生相同 `bot_id` 互踢，并在 28888 端口产生 `OSError: [Errno 10048]`。
2. **Windows 代理穿透**：Windows 系统全局代理如果对本地流量劫持，可能引发 WebSocket 握手失败。所有入口脚本已配置 `NO_PROXY=*`。
3. **Subprocess 换行截断**：直接调用可执行文件传递复杂多行文本，不要包装在 Windows `cmd.exe /c` 字符串中。

## Blockers/Open Questions
- 无已知阻断问题。双通道长连接与本地 IPC 均处于正常监听状态。

## Deferred Items
- 健身私教 Bot 接入：用户明确要求暂不接入大重量健身私教，目前已设置关键词拦截引导，待后续需要时再新建通道绑定。

## Environment State
### Tools/Services Used
- Python 3.11 (`hermes-agent` venv)
- aiohttp, wecom-aibot-sdk, pytest, pytest-asyncio
- Google Antigravity 2.0 (Language Server agentapi)
- 企业微信 Intelligent Bot WSS 网关

### Active Processes
- Sidecar 进程：`wecom-channel-daemon`（监听 127.0.0.1:28888，长连接至企业微信）
- 日志文件：`C:\Users\33991\.gemini\antigravity\sidecar_data\wecom-channel-daemon\logs\sidecar.log`

### Environment Variables
- `NO_PROXY` (设为 `*` 防止本地回环被代理拦截)
- `no_proxy` (设为 `*`)
- `WECOM_CONFIG_PATH` (可选，默认指向 `data/wecom_config.json`)

## Related Resources
- 架构文档：[docs/architecture.md](docs/architecture.md)
- 项目说明：[README.md](README.md)
- 示例配置：[data/wecom_config.example.json](data/wecom_config.example.json)
- GitHub 仓库：https://github.com/thalesluoyx/wechat_common.git
