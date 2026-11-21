@echo off
chcp 65001 >nul
echo 正在检查【日常运动_Session】企业微信后台服务状态...
netstat -aon | findstr ":28888" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo [正常运行] 服务正在监听端口 28888，长连接处于就绪状态。
) else (
    echo [未运行] 服务未检测到监听。
)
