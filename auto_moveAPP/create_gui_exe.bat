@echo off
chcp 65001 >nul
title GUI版EXE化ツール

echo ============================================
echo   GUI版EXE化ツール（エラー対策版）
echo ============================================
echo.

:: Pythonの存在確認
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません
    pause
    exit /b 1
)

:: 必要なライブラリのインストール確認
echo 必要なライブラリを確認中...
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

pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo watchdogライブラリをインストール中...
    pip install watchdog
    if errorlevel 1 (
        echo エラー: watchdogライブラリのインストールに失敗しました
        pause
        exit /b 1
    )
)

echo.
echo GUI版EXEファイルを作成中...
echo.

:: 既存のdistフォルダをクリーンアップ
if exist "dist" (
    echo 既存のdistフォルダを削除中...
    rmdir /s /q "dist"
)

if exist "build" (
    echo 既存のbuildフォルダを削除中...
    rmdir /s /q "build"
)

:: PyInstallerでEXE作成（エラー対策版）
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "ダウンロード自動振り分けGUI" ^
    --add-data "config.json;." ^
    --hidden-import "watchdog" ^
    --hidden-import "watchdog.observers" ^
    --hidden-import "watchdog.events" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "json" ^
    --hidden-import "hashlib" ^
    --hidden-import "pathlib" ^
    --hidden-import "threading" ^
    --hidden-import "subprocess" ^
    --clean ^
    file_mover_gui.py

echo.
if exist "dist\ダウンロード自動振り分けGUI.exe" (
    echo ✓ GUI版EXEファイルの作成が完了しました！
    echo.
    echo 作成されたファイル: dist\ダウンロード自動振り分けGUI.exe
    echo.
    echo 特徴:
    echo - 設定画面付きGUI
    echo - スタートアップ設定機能
    echo - 設定ファイルは外部ファイル
    echo - ログ表示機能
    echo - エラー対策済み
    echo.
    echo 使用方法:
    echo 1. dist\ダウンロード自動振り分けGUI.exe を実行
    echo 2. 「設定」ボタンで振り分けルールを設定
    echo 3. 「スタートアップ設定」でPC起動時自動開始を設定
    echo 4. 「監視開始」ボタンで監視を開始
    echo.
) else (
    echo ✗ EXEファイルの作成に失敗しました
    echo.
    echo エラーログを確認してください
    echo.
)

echo 作業完了
pause
