@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Chrome通信調査ツール
echo =====================
echo.

python chrome_network_investigation.py

pause

