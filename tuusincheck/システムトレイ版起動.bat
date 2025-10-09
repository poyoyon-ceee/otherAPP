@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo システムトレイ対応版セットアップ
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
pip install pystray pillow psutil

if errorlevel 1 (
    echo.
    echo [エラー] パッケージのインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo インストール完了！
echo システムトレイ版を起動します...
echo.
timeout /t 2 >nul

python network_monitor_v3.py

pause
