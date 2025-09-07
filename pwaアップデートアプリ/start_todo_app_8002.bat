@echo off

SET PYTHON_DIR=%~dp0python-portable


cd /d "%~dp0"

echo Service Worker version updated to v1.201
echo Starting PWA update process...

start cmd /k "%PYTHON_DIR%\python.exe" -m http.server 8002


timeout /t 3 >nul
start chrome http://localhost:8002/cool_todo_list.html
exit