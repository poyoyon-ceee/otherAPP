const CACHE_NAME = 'todo-list-v1.2'; // キャッシュ名。バージョンアップ時に変更してください
const urlsToCache = [
    './cool_todo_list.html',
    './manifest.json',
    './service-worker.js',
    './ico192192.png', // 使用するアイコンのパスを追加
    './ico512512.png'  // 使用するアイコンのパスを追加
    // 必要に応じて、追加の画像やスクリプト、スタイルシートなどがあればここに追加
];

// インストールイベント: キャッシュを開き、指定されたファイルをキャッシュに追加
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache:', CACHE_NAME);
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.error('Failed to cache during install:', error);
            })
    );
});

// フェッチイベント: リクエストに対し、キャッシュがあればキャッシュから、なければネットワークから取得
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // キャッシュにレスポンスがあればそれを返す
                if (response) {
                    return response;
                }
                // キャッシュになければネットワークから取得
                return fetch(event.request).catch(() => {
                    // ネットワークが利用できない場合のフォールバック（オフラインページなど）
                    // このアプリの場合は、メインHTMLがキャッシュされていれば十分
                    console.log('Fetch failed for:', event.request.url);
                    // 必要であれば、オフライン時に表示する代替コンテンツを返す
                    // 例: return caches.match('/offline.html');
                });
            })
    );
});

// アクティベートイベント: 古いキャッシュをクリア
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        // ホワイトリストにない古いキャッシュを削除
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});