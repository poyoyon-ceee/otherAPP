@echo off
chcp 65001 >nul
cd /d "%~dp0"
python network_monitor_v2.py
pause
