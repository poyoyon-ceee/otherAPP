# WebアプリPWA化仕様書

## 1. 概要

Progressive Web App（PWA）は、Webアプリをネイティブアプリのような体験で利用できるようにする技術です。オフライン対応、ホーム画面への追加、プッシュ通知などの機能を提供します。

## 2. PWA化に必要な構成要素

### 2.1 必須ファイル構成
```
project-root/
├── index.html (メインHTMLファイル)
├── manifest.json (Webアプリマニフェスト)
├── service-worker.js (サービスワーカー)
├── icons/
│   ├── icon-192x192.png
│   └── icon-512x512.png
└── start-server.bat (開発用サーバー起動スクリプト)
```

## 3. 各ファイルの詳細仕様

### 3.1 Webアプリマニフェスト（manifest.json）

Webアプリの基本情報とPWA設定を定義するJSONファイル。

```json
{
    "name": "アプリの正式名称",
    "short_name": "アプリの短縮名",
    "description": "アプリの説明文",
    "start_url": "./index.html",
    "display": "standalone",
    "background_color": "#背景色のカラーコード",
    "theme_color": "#テーマカラーのカラーコード",
    "icons": [
        {
            "src": "icons/icon-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "icons/icon-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

#### 主要プロパティ説明
- **name**: ホーム画面やアプリ一覧に表示される正式名称
- **short_name**: スペースが限られた場所で使用される短縮名
- **start_url**: アプリ起動時に最初に読み込まれるURL
- **display**: 表示モード（`standalone`, `fullscreen`, `minimal-ui`, `browser`）
- **background_color**: スプラッシュ画面の背景色
- **theme_color**: ブラウザのアドレスバーやタスクバーの色
- **icons**: 各種サイズのアイコン配列

### 3.2 サービスワーカー（service-worker.js）

オフライン機能とキャッシュ管理を担当するJavaScriptファイル。

```javascript
const CACHE_NAME = 'app-name-v1.0';
const urlsToCache = [
    './',
    './index.html',
    './manifest.json',
    './icons/icon-192x192.png',
    './icons/icon-512x512.png'
    // 必要に応じてCSS、JS、画像ファイルを追加
];

// インストールイベント
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('キャッシュを開きました:', CACHE_NAME);
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.error('インストール時のキャッシュに失敗:', error);
            })
    );
});

// フェッチイベント
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                if (response) {
                    return response;
                }
                return fetch(event.request).catch(() => {
                    console.log('オフライン状態です:', event.request.url);
                });
            })
    );
});

// アクティベートイベント
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        console.log('古いキャッシュを削除:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
```

### 3.3 HTMLファイルの設定

メインHTMLファイルでマニフェストの参照とサービスワーカーの登録を行う。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>アプリタイトル</title>
    
    <!-- PWAマニフェストの参照 -->
    <link rel="manifest" href="manifest.json">
    
    <!-- iOS Safari用の設定 -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <meta name="apple-mobile-web-app-title" content="アプリ名">
    <link rel="apple-touch-icon" href="icons/icon-192x192.png">
    
    <!-- Android Chrome用の設定 -->
    <meta name="theme-color" content="#テーマカラー">
</head>
<body>
    <!-- アプリのコンテンツ -->
    
    <script>
        // サービスワーカーの登録
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('service-worker.js')
                    .then(registration => {
                        console.log('Service Worker登録成功:', registration.scope);
                    })
                    .catch(error => {
                        console.log('Service Worker登録失敗:', error);
                    });
            });
        }
    </script>
</body>
</html>
```

### 3.4 アイコン画像の仕様

PWAアイコンは以下のサイズを最低限用意する：

- **192x192px**: Android ホーム画面用
- **512x512px**: スプラッシュスクリーン用

#### アイコン要件
- ファイル形式：PNG推奨
- 背景：透明または単色
- デザイン：シンプルで視認性の高いもの
- 角丸：システムが自動適用するため不要

### 3.5 開発用サーバー起動スクリプト

PWAはHTTPS環境またはlocalhost環境でのみ動作するため、開発用サーバーが必要。

```batch
@echo off
SET PYTHON_DIR=%~dp0python-portable
cd /d "%~dp0"
start cmd /k "%PYTHON_DIR%\python.exe" -m http.server 8002
timeout /t 3 >nul
start chrome http://localhost:8002/
exit
```

## 4. 実装手順

### 4.1 準備段階
1. 既存のWebアプリの動作確認
2. アイコン画像の作成（192x192, 512x512サイズ）
3. アプリの基本情報（名前、説明、テーマカラー等）の決定

### 4.2 ファイル作成
1. `manifest.json`の作成
2. `service-worker.js`の作成
3. HTMLファイルへのマニフェスト参照追加
4. サービスワーカー登録コードの追加

### 4.3 テスト・検証
1. ローカルサーバーでの動作確認
2. Chrome DevToolsのApplicationタブでPWA要件チェック
3. オフライン動作テスト
4. ホーム画面追加機能のテスト

### 4.4 デプロイ
1. HTTPS対応サーバーへのアップロード
2. 本番環境での動作確認
3. 各種デバイスでのテスト

## 5. PWA要件チェックリスト

### 必須要件
- [ ] HTTPSまたはlocalhost環境での配信
- [ ] Webアプリマニフェストの存在
- [ ] 192x192以上のアイコン設定
- [ ] サービスワーカーの登録
- [ ] オフライン時の基本機能動作

### 推奨要件
- [ ] レスポンシブデザイン対応
- [ ] 高速な読み込み時間
- [ ] クロスブラウザ対応
- [ ] アクセシビリティ配慮
- [ ] SEO最適化

## 6. 注意事項とベストプラクティス

### 6.1 キャッシュ戦略
- **Cache First**: 画像、CSS、JSファイル用
- **Network First**: API通信、動的コンテンツ用
- **Stale While Revalidate**: 頻繁に更新されるコンテンツ用

### 6.2 更新管理
- アプリ更新時はキャッシュ名のバージョンアップが必要
- 不要な古いキャッシュの定期削除
- ユーザーへの更新通知機能の実装検討

### 6.3 パフォーマンス
- 必要最小限のファイルのみキャッシュ
- 大きなファイルは動的読み込み
- 画像の最適化（WebP形式の活用等）

### 6.4 セキュリティ
- HTTPSでの配信必須
- Content Security Policy（CSP）の設定
- クロスオリジンリソースの適切な管理

## 7. トラブルシューティング

### よくある問題と解決方法

**問題**: PWAとして認識されない
- **解決**: manifest.jsonの構文エラーチェック
- **解決**: HTTPSまたはlocalhost環境での実行確認

**問題**: サービスワーカーが更新されない
- **解決**: ブラウザのキャッシュクリア
- **解決**: service-worker.jsのキャッシュ名更新

**問題**: オフライン時に動作しない
- **解決**: 必要なファイルがキャッシュされているか確認
- **解決**: ネットワークエラーハンドリングの実装

この仕様書に従ってWebアプリをPWA化することで、ユーザーにネイティブアプリのような体験を提供できます。