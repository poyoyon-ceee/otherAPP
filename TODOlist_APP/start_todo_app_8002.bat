@echo off
setlocal enabledelayedexpansion

SET PYTHON_DIR=%~dp0python-portable
cd /d "%~dp0"

echo Updating Service Worker version...

REM service-worker.jsファイルから現在のバージョンを抽出
for /f "tokens=2 delims=-v" %%a in ('findstr /C:"todo-list-v" service-worker.js') do (
    set "version_part=%%a"
)

REM バージョン番号から数値部分を抽出（'; を除去）
for /f "tokens=1 delims='" %%b in ("!version_part!") do (
    set "current_version=%%b"
)

REM PowerShellを使用してバージョンを0.001増加
for /f %%c in ('powershell -command "[decimal]!current_version! + 0.001"') do (
    set "new_version=%%c"
)

echo Current version: !current_version!
echo New version: !new_version!

REM service-worker.jsファイルのバージョンを更新
powershell -command "(Get-Content 'service-worker.js') -replace 'todo-list-v!current_version!', 'todo-list-v!new_version!' | Set-Content 'service-worker.js'"

echo Service Worker updated to version !new_version!

start cmd /k "%PYTHON_DIR%\python.exe" -m http.server 8002
timeout /t 3 >nul
start chrome http://localhost:8002/cool_todo_list.html
exit