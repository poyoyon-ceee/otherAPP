@echo off
chcp 65001 >nul
title EXE化ツール

echo ============================================
echo   EXE化ツール（PyInstaller使用）
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

echo EXEファイルを作成中...
echo.

:: PyInstallerでEXE作成
pyinstaller --onefile --windowed --name "ダウンロード自動振り分け" --icon=NONE file_auto_mover.py

if exist "dist\ダウンロード自動振り分け.exe" (
    echo.
    echo ✓ EXEファイルの作成が完了しました！
    echo.
    echo 作成されたファイル: dist\ダウンロード自動振り分け.exe
    echo.
    echo 注意: config.jsonファイルも一緒に配布してください
    echo.
) else (
    echo.
    echo ✗ EXEファイルの作成に失敗しました
    echo.
)

echo 作業完了
pause
