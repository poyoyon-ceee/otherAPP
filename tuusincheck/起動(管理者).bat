@echo off
chcp 65001 >nul

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Running as admin
cd /d "%~dp0"
echo Starting Tethering Network Monitor V2 with admin privileges...
echo.
python network_monitor_v2.py
pause
