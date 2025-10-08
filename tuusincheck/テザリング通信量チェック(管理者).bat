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

echo ========================================
echo  テザリング通信量チェック V2
echo  (管理者モード)
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

echo 管理者権限でアプリを起動します...
echo より多くのプロセス情報にアクセスできます
echo.
python network_monitor_v2.py

if errorlevel 1 (
    echo.
    echo [エラー] アプリの起動に失敗しました
    pause
)
exit /b
