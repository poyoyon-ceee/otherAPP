@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  システムトレイ機能追加セットアップ
echo ========================================
echo.

:: Pythonチェック
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonがインストールされていません
    pause
    exit /b 1
)

echo 必要なパッケージをインストール中...
pip install pystray Pillow

if errorlevel 1 (
    echo.
    echo [エラー] パッケージのインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo ========================================
echo  インストール完了！
echo ========================================
echo.
echo システムトレイ機能が有効になりました
echo.
echo 使い方:
echo 1. 【最終版】完璧な起動_管理者.vbs で起動
echo 2. 最小化ボタンでシステムトレイに格納
echo 3. トレイアイコンをクリックで表示
echo 4. 右クリックでメニュー表示
echo.
pause
