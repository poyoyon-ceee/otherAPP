@echo off
chcp 65001 >nul
title スタートアップ登録ツール

echo ============================================
echo   スタートアップ登録ツール
echo ============================================
echo.

:: 管理者権限確認
net session >nul 2>&1
if errorlevel 1 (
    echo このツールは管理者権限で実行する必要があります
    echo 右クリックして「管理者として実行」を選択してください
    pause
    exit /b 1
)

:: 現在のディレクトリを取得
set "APP_DIR=%~dp0"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo アプリケーションの場所: %APP_DIR%
echo スタートアップフォルダ: %STARTUP_DIR%
echo.

:: スタートアップフォルダの存在確認
if not exist "%STARTUP_DIR%" (
    echo エラー: スタートアップフォルダが見つかりません
    pause
    exit /b 1
)

:: ショートカット作成
echo ショートカットを作成中...
set "SHORTCUT_PATH=%STARTUP_DIR%\ダウンロード自動振り分け.lnk"

:: PowerShellを使用してショートカット作成
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%APP_DIR%start_file_mover.bat'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = 'ダウンロードフォルダ自動振り分けアプリ'; $Shortcut.Save()}"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo ✓ スタートアップ登録が完了しました！
    echo   次回PC起動時から自動的にアプリが開始されます
    echo.
    echo 登録内容:
    echo - ショートカット名: ダウンロード自動振り分け
    echo - 起動ファイル: %APP_DIR%start_file_mover.bat
    echo.
) else (
    echo.
    echo ✗ スタートアップ登録に失敗しました
    echo.
)

echo スタートアップ登録を解除する場合は、
echo 以下のフォルダからショートカットを削除してください:
echo %STARTUP_DIR%
echo.

pause
