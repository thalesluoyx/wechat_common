@echo off
chcp 65001 >nul
echo 正在停止【日常运动_Session】企业微信后台服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":28888" ^| findstr "LISTENING"') do (
    echo 终止进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo 服务已停止。
