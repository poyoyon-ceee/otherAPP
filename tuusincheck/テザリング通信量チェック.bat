@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  テザリング通信量チェック V2
echo ========================================
echo.

:: Pythonのチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    echo.
    echo Python 3.8以上をインストールしてください
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: psutilのチェック
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo [エラー] 必要なパッケージがインストールされていません
    echo.
    echo 「install.bat」を実行してパッケージをインストールしてください
    echo.
    pause
    exit /b 1
)

echo アプリを起動します...
echo.
python network_monitor_v2.py

if errorlevel 1 (
    echo.
    echo [エラー] アプリの起動に失敗しました
    pause
)
exit /b
