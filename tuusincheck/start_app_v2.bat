@echo off
chcp 65001
title Tethering Network Monitor V2
echo Starting Tethering Network Monitor V2...
echo This version shows estimated per-app network usage
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8 or higher
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo Required packages are not installed
    echo Please run install.bat to install packages
    pause
    exit /b 1
)

echo Starting app...
python network_monitor_v2.py

pause
