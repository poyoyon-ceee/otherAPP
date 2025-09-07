@echo off
echo PWA自動アップデートバッチファイル
echo ================================

REM 現在のディレクトリに移動
cd /d "%~dp0"

REM service-worker.jsファイルが存在するかチェック
if not exist "service-worker.js" (
    echo エラー: service-worker.jsファイルが見つかりません
    pause
    exit /b 1
)

echo 【ステップ1】Chrome開発者モードでのアップデート準備
echo ================================================
echo.
echo 以下の手順を実行してください：
echo 1. Chromeでアプリケーションを開く
echo 2. F12キーでデベロッパーツールを開く
echo 3. [Application]タブを選択
echo 4. [Service Workers]セクションを確認
echo 5. [Storage] > [Clear storage]でキャッシュをクリア
echo    - [Clear site data]ボタンをクリック
echo 6. 必要に応じて[Update on reload]にチェックを入れる
echo.
echo 準備が完了したら何かキーを押してください...
pause >nul

echo.
echo 【ステップ2】service-worker.jsのバージョンアップデート
echo ================================================

echo 現在のバージョン:
findstr "CACHE_NAME" service-worker.js

echo.
echo バージョンを0.001アップデート中...

REM PowerShellを使用してservice-worker.jsのバージョンを0.001上げる
powershell -Command "(Get-Content 'service-worker.js') -replace 'todo-list-v(\d+)\.(\d+)', { param($match) 'todo-list-v' + $match.Groups[1].Value + '.' + ([float]$match.Groups[2].Value + 0.001) } | Set-Content 'service-worker.js'"

echo    ✓ バージョンアップ完了

echo.
echo 更新後のバージョン:
findstr "CACHE_NAME" service-worker.js

echo.
echo 【ステップ3】アプリケーションサーバーの起動
echo ==========================================

REM start_todo_app_8002.batが存在するかチェック
if not exist "start_todo_app_8002.bat" (
    echo エラー: start_todo_app_8002.batファイルが見つかりません
    pause
    exit /b 1
)

echo サーバーを起動します...
REM start_todo_app_8002.batを起動
call start_todo_app_8002.bat

echo.
echo 【ステップ4】アップデート確認手順
echo ================================
echo.
echo アプリが起動したら以下を確認してください：
echo 1. ブラウザでCtrl+F5（強制リロード）を実行
echo 2. デベロッパーツール > Application > Service Workers で新バージョンを確認
echo 3. Application > Storage でキャッシュが更新されていることを確認
echo.
echo PWAアップデート処理が完了しました！
echo ================================
pause