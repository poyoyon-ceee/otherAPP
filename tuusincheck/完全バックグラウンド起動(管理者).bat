@echo off
chcp 65001 >nul

:: 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 管理者として実行中
cd /d "%~dp0"

:: Pythonのチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    timeout /t 3 >nul
    exit /b 1
)

:: psutilのチェック
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo [エラー] 必要なパッケージがインストールされていません
    timeout /t 3 >nul
    exit /b 1
)

:: 完全バックグラウンドで起動（GUIは最小化状態、フォーカス奪取なし、管理者権限）
start /min "" pythonw network_monitor_v2.py --silent --minimized

exit
