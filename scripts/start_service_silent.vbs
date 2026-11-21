Set WshShell = CreateObject("WScript.Shell")
' Run run_bot_service.py silently in the background (0 = hide window)
WshShell.Run "python ""C:\Work\openclaw_projects\wechat_common\scripts\run_bot_service.py""", 0, False
