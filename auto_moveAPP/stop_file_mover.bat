@echo off
chcp 65001 >nul
title ファイル振り分けアプリ停止ツール

echo ============================================
echo   ファイル振り分けアプリ停止ツール
echo ============================================
echo.

echo 実行中のファイル振り分けアプリを停止しています...

:: Pythonプロセスを検索して停止
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr "file_auto_mover" >nul
if not errorlevel 1 (
    echo ファイル振り分けアプリを停止中...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *file_auto_mover*" >nul 2>&1
    if not errorlevel 1 (
        echo ✓ アプリケーションを停止しました
    ) else (
        echo アプリケーションの停止に失敗しました
    )
) else (
    echo 実行中のファイル振り分けアプリが見つかりませんでした
)

:: より確実な方法でPythonプロセスを停止
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /i "python"') do (
    wmic process where "ProcessId=%%i" get CommandLine /format:list | findstr "file_auto_mover" >nul
    if not errorlevel 1 (
        echo プロセス %%i を停止中...
        taskkill /F /PID %%i >nul 2>&1
    )
)

echo.
echo 停止処理が完了しました
pause
