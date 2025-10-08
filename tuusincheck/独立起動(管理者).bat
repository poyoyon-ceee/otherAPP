@echo off
chcp 65001 >nul

:: 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 管理者権限で再起動中...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 管理者として実行中
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

echo アプリを管理者権限でバックグラウンド起動しました
echo このウィンドウを閉じてもアプリは動作し続けます
timeout /t 3 >nul
exit
