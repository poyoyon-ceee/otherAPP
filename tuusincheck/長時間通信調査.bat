@echo off
chcp 65001 >nul
cd /d "%~dp0"

title 長時間通信調査ツール

echo.
echo ========================================
echo  長時間通信調査ツール
echo ========================================
echo.
echo より長い時間で監視して大容量通信を検出
echo デフォルト：30分間監視、50MB以上で検出
echo.

python 長時間通信調査.py

pause

