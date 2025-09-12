# WebアプリケーションEXE化仕様書

## 概要
この文書は、既存のWebアプリケーション（HTML/CSS/JavaScript）を、PyInstallerを使用してWindowsの実行ファイル（EXE）として配布可能な形式に変換する手順とベストプラクティスを記載したものです。

カウネット注文票作成システムのEXE化プロジェクトで培った知見を元に、他のWebアプリケーションでも使用できる汎用的な仕様書として作成しました。

## 前提条件
- 既存のWebアプリケーション（HTML/CSS/JavaScript）
- Python 3.8以上
- PyInstaller
- Windows環境（動作確認用）

## アーキテクチャ概要

### 基本構造
```
WebApp/
├── webapp_main.py              # メインPythonファイル
├── webapp_v1_0.spec           # PyInstaller設定ファイル
├── webapp_app.ico            # アプリケーションアイコン
├── favicon.ico               # ファビコン
├── index.html                # メインHTML
├── manifest.json             # PWAマニフェスト
├── service-worker.js         # サービスワーカー
├── files/                    # 静的ファイル
│   ├── css/                  # CSSファイル
│   ├── js/                   # JavaScriptファイル
│   ├── images/               # 画像ファイル
│   └── icons/                # アイコンファイル
├── DATA/                     # 初期データファイル
├── dist/                     # ビルド出力先
│   ├── WebApp_v1_0.exe       # 生成される実行ファイル
│   ├── conf/                 # 設定ファイル保存先
│   └── data/                 # ユーザーデータ保存先
└── build/                    # ビルド中間ファイル
```

## 1. メインPythonファイルの作成

### 1.1 基本テンプレート
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[アプリケーション名] - EXE化対応版
WebブラウザとHTTPサーバーを統合したスタンドアロンアプリケーション
"""

import os
import sys
import threading
import webbrowser
import time
import socket
import subprocess
import platform
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import urllib.parse
import tkinter as tk
from tkinter import filedialog
import ctypes
from datetime import datetime
import signal
import atexit
```

### 1.2 カスタムHTTPRequestHandlerクラス
```python
class WebAppHTTPRequestHandler(SimpleHTTPRequestHandler):
    """カスタムHTTPリクエストハンドラー"""
    
    def __init__(self, *args, **kwargs):
        # 実行ファイルのディレクトリを基準にする
        if getattr(sys, 'frozen', False):
            # PyInstallerでパッケージ化された場合
            self.directory = sys._MEIPASS
        else:
            # 開発環境での実行
            self.directory = os.path.dirname(os.path.abspath(__file__))
        
        # データ保存用ディレクトリの設定
        self.setup_data_directories()
        
        super().__init__(*args, directory=self.directory, **kwargs)
    
    def setup_data_directories(self):
        """データディレクトリの設定"""
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        # confフォルダとdataフォルダを設定
        conf_dir = os.path.join(exe_dir, 'conf')
        data_dir = os.path.join(exe_dir, 'data')
        
        # フォルダが存在しない場合は作成
        for directory in [conf_dir, data_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        self.conf_dir = conf_dir
        self.data_dir = data_dir
    
    def log_message(self, format, *args):
        """ログメッセージを無効化（コンソールをクリーンに保つ）"""
        pass
    
    def end_headers(self):
        """CORSヘッダーを追加"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
```

### 1.3 API エンドポイント
```python
    def do_POST(self):
        """POST リクエストを処理"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/save-data':
            self.handle_save_data()
        elif parsed_path.path == '/api/load-data':
            self.handle_load_data()
        elif parsed_path.path == '/api/set-data-folder':
            self.handle_set_data_folder()
        elif parsed_path.path == '/api/get-data-folder':
            self.handle_get_data_folder()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_OPTIONS(self):
        """OPTIONSリクエストを処理（CORS対応）"""
        self.send_response(200)
        self.end_headers()
```

### 1.4 フォルダ選択機能
```python
def select_folder_simple():
    """シンプルなTkinterフォルダ選択ダイアログ"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()  # 即座に非表示
        
        # ダイアログを前面に表示
        root.attributes("-topmost", True)
        root.focus_force()
        root.lift()
        
        selected_folder = filedialog.askdirectory(
            title="データ保存フォルダを選択してください",
            parent=root
        )
        
        root.destroy()
        return selected_folder if selected_folder else None
    except Exception as e:
        print(f"フォルダ選択エラー: {e}")
        return None
```

### 1.5 ブラウザ起動機能
```python
def open_app_window(url):
    """個別ウィンドウでアプリケーションを開く"""
    system = platform.system().lower()
    
    # Chrome アプリケーションモードでの起動
    chrome_paths = []
    if system == "windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
    
    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            try:
                subprocess.Popen([
                    chrome_path,
                    f"--app={url}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    f"--user-data-dir={os.path.join(os.getcwd(), '.chrome_profile')}"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                   creationflags=subprocess.CREATE_NO_WINDOW)
                return True
            except Exception as e:
                continue
    
    # フォールバック: デフォルトブラウザ
    webbrowser.open(url)
    return True
```

## 2. PyInstaller設定ファイル（.spec）

### 2.1 基本テンプレート
```python
# -*- mode: python ; coding: utf-8 -*-
"""
[アプリケーション名] - PyInstaller設定ファイル
Date: [作成日]
Version: [バージョン]
"""

# 分析フェーズ
a = Analysis(
    ['webapp_main.py'],  # メインPythonファイル
    pathex=['.'],
    binaries=[],
    datas=[
        ('index.html', '.'),
        ('manifest.json', '.'), 
        ('service-worker.js', '.'),
        ('files', 'files'),      # 静的ファイル
        ('DATA', 'DATA'),        # 初期データ
        ('webapp_app.ico', '.'),
        ('favicon.ico', '.')
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'http.server',
        'urllib.parse',
        'json',
        'threading',
        'webbrowser',
        'socket',
        'subprocess',
        'platform',
        'ctypes',
        'datetime',
        'signal',
        'atexit'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'pygame',
        'unittest'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# パッケージング
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 実行ファイル作成
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WebApp_v1_0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI モード
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='webapp_app.ico'
)
```

## 3. JavaScript側の修正

### 3.1 LocalStorageとServer APIの併用
```javascript
// サーバーAPI呼び出し関数
async function saveToServer(type, data) {
    try {
        const response = await fetch('/api/save-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: type,
                data: data
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('サーバー保存成功:', result.message);
            return true;
        }
    } catch (error) {
        console.error('サーバー保存エラー:', error);
        // フォールバックとしてLocalStorageを使用
        localStorage.setItem(`webapp_${type}`, JSON.stringify(data));
        return false;
    }
}

async function loadFromServer(type) {
    try {
        const response = await fetch('/api/load-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: type
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            return result.data;
        }
    } catch (error) {
        console.error('サーバー読み込みエラー:', error);
        // フォールバックとしてLocalStorageを使用
        const saved = localStorage.getItem(`webapp_${type}`);
        return saved ? JSON.parse(saved) : null;
    }
}
```

### 3.2 シンプル化されたデータ処理
フリーズ対策のため、複雑な非同期処理は避け、直接的なlocalStorage操作を使用：

```javascript
// シンプルなデータ保存・読み込み
function saveDataSimple(key, data) {
    try {
        localStorage.setItem(`webapp_${key}`, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('データ保存エラー:', error);
        return false;
    }
}

function loadDataSimple(key) {
    try {
        const saved = localStorage.getItem(`webapp_${key}`);
        return saved ? JSON.parse(saved) : null;
    } catch (error) {
        console.error('データ読み込みエラー:', error);
        return null;
    }
}
```

## 4. ビルド手順

### 4.1 開発環境の準備
```bash
# Python仮想環境の作成（推奨）
python -m venv webapp_env
webapp_env\Scripts\activate

# 必要なライブラリをインストール
pip install pyinstaller
```

### 4.2 ビルド実行
```bash
# 開発ディレクトリに移動
cd /path/to/webapp

# PyInstallerでビルド
python -m PyInstaller webapp_v1_0.spec --clean

# または直接コマンドで
python -m PyInstaller webapp_main.py --onefile --windowed --icon=webapp_app.ico --add-data "index.html;." --add-data "files;files"
```

### 4.3 プロセス管理とクリーンアップ
```python
def main():
    """メイン関数"""
    def cleanup():
        """アプリケーション終了時のクリーンアップ"""
        print("クリーンアップを実行中...")
        try:
            import psutil
            current_process = psutil.Process(os.getpid())
            children = current_process.children(recursive=True)
            for child in children:
                child.terminate()
        except:
            pass
        sys.exit(0)
    
    # 終了処理を登録
    atexit.register(cleanup)
    signal.signal(signal.SIGTERM, lambda signum, frame: cleanup())
    signal.signal(signal.SIGINT, lambda signum, frame: cleanup())
```

## 5. トラブルシューティング

### 5.1 よくある問題と対策

#### JavaScript フリーズ問題
- **原因**: 複雑な非同期処理、Service Workerのキャッシュ競合
- **対策**: シンプルなlocalStorage操作に変更、Service Worker無効化

#### プロセス残存問題
- **原因**: 子プロセスの適切な終了処理不足
- **対策**: `atexit`、`signal`ハンドラーによるクリーンアップ実装

#### パス関連エラー
- **原因**: PyInstallerのパッケージ化後のパス変更
- **対策**: `sys._MEIPASS`の使用、相対パスの調整

#### ファイル読み書きエラー
- **原因**: 実行ファイル内のファイルは読み取り専用
- **対策**: 設定・データファイルを外部フォルダ（conf/data）に配置

### 5.2 パフォーマンス最適化

#### ファイルサイズ削減
```python
excludes=[
    'matplotlib', 'numpy', 'pandas', 'scipy',
    'PIL', 'pygame', 'unittest', 'tkinter.dnd',
    'tkinter.colorchooser', 'tkinter.commondialog'
]
```

#### 起動速度向上
- UPX圧縮の有効化: `upx=True`
- 不要なインポートの削除
- 遅延ロードの実装

## 6. 配布用パッケージング

### 6.1 配布フォルダ構成
```
WebApp_Distribution/
├── WebApp_v1_0.exe          # メイン実行ファイル
├── conf/                    # 設定ファイル（初期状態）
├── data/                    # データファイル（空）
├── README.txt               # 使用方法説明
└── LICENCE.txt              # ライセンス情報
```

### 6.2 インストーラー作成（オプション）
- NSIS、Inno Setup等を使用してインストーラーを作成
- レジストリ登録、スタートメニューへの登録
- アンインストーラーの同梱

## 7. セキュリティ考慮事項

### 7.1 基本セキュリティ
- HTTPサーバーはlocalhostのみでバインド
- 不要なポートは使用しない
- ユーザー入力の適切なサニタイズ

### 7.2 データ保護
- 重要なデータは暗号化
- 設定ファイルの適切な権限設定
- 一時ファイルの適切な削除

## 8. 実装チェックリスト

### 8.1 必須実装項目
- [ ] メインPythonファイルの作成
- [ ] HTTPRequestHandlerのカスタマイズ
- [ ] PyInstaller設定ファイル（.spec）の作成
- [ ] アイコンファイルの準備
- [ ] JavaScript側のAPI連携実装
- [ ] データ保存・読み込み機能
- [ ] プロセス管理・クリーンアップ機能

### 8.2 推奨実装項目
- [ ] フォルダ選択機能
- [ ] CSV出力機能
- [ ] エラーハンドリング
- [ ] ログ出力機能
- [ ] 設定ファイル管理
- [ ] ブラウザ自動起動

### 8.3 テスト項目
- [ ] 開発環境での動作確認
- [ ] EXEファイルでの動作確認
- [ ] データ保存・読み込みテスト
- [ ] エラーケースのテスト
- [ ] プロセス終了のテスト
- [ ] 複数起動時の動作テスト

## 9. バージョン管理

### 9.1 ファイル命名規則
- メインファイル: `webapp_main.py`
- 設定ファイル: `webapp_v1_0.spec`
- 実行ファイル: `WebApp_v1_0.exe`

### 9.2 バージョン更新手順
1. 設定ファイル名の更新（例: `webapp_v1_1.spec`）
2. 実行ファイル名の更新
3. バージョン番号の確認・更新
4. 変更履歴の記録

## 参考情報

### 関連技術
- [PyInstaller公式ドキュメント](https://pyinstaller.readthedocs.io/)
- [Python HTTPサーバー](https://docs.python.org/3/library/http.server.html)
- [Tkinter ファイルダイアログ](https://docs.python.org/3/library/tkinter.filedialog.html)

### サンプルプロジェクト
- カウネット注文票作成システム（このドキュメントのベース）
- 基本的なWebアプリEXE化のテンプレート

---

**作成日**: 2025-08-31  
**更新日**: 2025-08-31  
**バージョン**: 1.0  
**作成者**: Claude Code Assistant