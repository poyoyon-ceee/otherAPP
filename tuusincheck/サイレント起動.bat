@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: Pythonのチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    pause
    exit /b 1
)

:: psutilのチェック
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo [エラー] 必要なパッケージがインストールされていません
    pause
    exit /b 1
)

:: サイレントモード＆最小化で起動
start "" pythonw network_monitor_v2.py --silent --minimized

echo サイレントモードで起動しました
echo ポップアップは表示されません
timeout /t 2 >nul
exit
