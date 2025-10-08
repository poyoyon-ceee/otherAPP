@echo off
chcp 65001
echo Tethering Network Monitor App - Installing Dependencies
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

echo Python detected:
python --version

echo.
echo Installing required packages...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error: Package installation failed
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
echo To start the app, run:
echo python network_monitor.py
echo.
pause