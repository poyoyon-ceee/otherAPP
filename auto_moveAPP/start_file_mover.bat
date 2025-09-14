@echo off
chcp 65001 >nul
title ダウンロードフォルダ自動振り分けアプリ

echo ============================================
echo   ダウンロードフォルダ自動振り分けアプリ
echo ============================================
echo.

:: 現在のディレクトリを取得
set "APP_DIR=%~dp0"

:: Pythonの存在確認
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません
    echo Python 3.7以上をインストールしてください
    pause
    exit /b 1
)

:: 必要なライブラリのインストール確認
echo 必要なライブラリを確認中...
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo watchdogライブラリをインストール中...
    pip install watchdog
    if errorlevel 1 (
        echo エラー: ライブラリのインストールに失敗しました
        pause
        exit /b 1
    )
)

:: アプリケーション起動
echo.
echo アプリケーションを起動中...
echo 終了するには Ctrl+C を押してください
echo.

cd /d "%APP_DIR%"
python file_auto_mover.py

echo.
echo アプリケーションが終了しました
pause
