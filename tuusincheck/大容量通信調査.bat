@echo off
chcp 65001 >nul
cd /d "%~dp0"

title 大容量通信調査ツール

echo.
echo ========================================
echo  大容量通信調査ツール
echo ========================================
echo.
echo 100MB級の通信を特定します
echo 5分間の監視でどのアプリが大容量通信しているかを調査
echo.

python 大容量通信調査.py

pause

