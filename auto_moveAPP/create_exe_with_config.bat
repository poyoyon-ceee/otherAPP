@echo off
chcp 65001 >nul
title EXE化ツール（設定ファイル組み込み版）

echo ============================================
echo   EXE化ツール（設定ファイル組み込み版）
echo ============================================
echo.

:: Pythonの存在確認
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません
    pause
    exit /b 1
)

:: PyInstallerのインストール確認
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstallerをインストール中...
    pip install pyinstaller
    if errorlevel 1 (
        echo エラー: PyInstallerのインストールに失敗しました
        pause
        exit /b 1
    )
)

echo EXEファイルを作成中（設定ファイル組み込み）...
echo.

:: PyInstallerでEXE作成（設定ファイルを含める）
pyinstaller --onefile --windowed --name "ダウンロード自動振り分け" --add-data "config.json;." --icon=NONE file_auto_mover.py

if exist "dist\ダウンロード自動振り分け.exe" (
    echo.
    echo ✓ EXEファイルの作成が完了しました！
    echo.
    echo 作成されたファイル: dist\ダウンロード自動振り分け.exe
    echo.
    echo 特徴:
    echo - 設定ファイルがEXEに組み込まれています
    echo - 単一ファイルで配布可能
    echo - 初回実行時に設定ファイルが自動生成されます
    echo.
) else (
    echo.
    echo ✗ EXEファイルの作成に失敗しました
    echo.
)

echo 作業完了
pause
