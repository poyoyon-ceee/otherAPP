@echo off
chcp 65001 >nul

:: 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 管理者権限で再起動中...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo システムトレイ対応版（管理者）
echo ================================
echo.

:: Pythonチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    pause
    exit /b 1
)

:: 必要なパッケージをインストール
echo 必要なパッケージをインストール中...
pip install pystray pillow psutil >nul 2>&1

echo システムトレイ版を起動します（管理者権限）...
echo システムトレイアイコンから操作できます
echo.
timeout /t 2 >nul

pythonw network_monitor_v3.py --silent --minimized

echo.
echo アプリが起動しました
echo システムトレイアイコンを右クリックしてメニューを表示
timeout /t 3 >nul
exit
