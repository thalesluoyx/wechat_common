@echo off
chcp 65001 >nul
cd /d "C:\Work\openclaw_projects\wechat_common"
set NO_PROXY=*
set no_proxy=*
"C:\Users\33991\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" scripts\run_bot_service.py >> data\service.log 2>&1
