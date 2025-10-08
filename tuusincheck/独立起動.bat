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
    echo install.batを実行してください
    pause
    exit /b 1
)

:: バックグラウンドで起動（ウィンドウを閉じても継続）
start "" pythonw network_monitor_v2.py

echo アプリをバックグラウンドで起動しました
echo このウィンドウを閉じてもアプリは動作し続けます
timeout /t 3 >nul
exit
