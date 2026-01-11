// SocialBoostAI Service Worker
// バージョン管理でキャッシュ更新を制御
const CACHE_VERSION = 'v2.9.0';
const STATIC_CACHE_NAME = `socialboostai-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE_NAME = `socialboostai-dynamic-${CACHE_VERSION}`;
const API_CACHE_NAME = `socialboostai-api-${CACHE_VERSION}`;

// 静的リソース（アプリシェル）
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.svg',
  '/offline.html',
  '/icons/icon-192x192.svg',
  '/icons/icon-512x512.svg'
];

// キャッシュ対象のAPI
const CACHEABLE_API_PATTERNS = [
  /\/api\/v1\/health/,
  /\/api\/v1\/user\/me/
];

// キャッシュしないパス
const NO_CACHE_PATTERNS = [
  /\/api\/v1\/auth\//,
  /\/api\/v1\/billing\//,
  /\/api\/v1\/ws\//
];

// インストール時に静的リソースをキャッシュ
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker...');
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        // 即座にアクティブ化
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Failed to cache static assets:', error);
      })
  );
});

// アクティベーション時に古いキャッシュを削除
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName.startsWith('socialboostai-') &&
                     cacheName !== STATIC_CACHE_NAME &&
                     cacheName !== DYNAMIC_CACHE_NAME &&
                     cacheName !== API_CACHE_NAME;
            })
            .map((cacheName) => {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        // 即座にコントロール開始
        return self.clients.claim();
      })
  );
});

// フェッチ時のキャッシュ戦略
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 同一オリジンのリクエストのみ処理
  if (url.origin !== location.origin) {
    return;
  }

  // キャッシュ除外対象
  if (NO_CACHE_PATTERNS.some((pattern) => pattern.test(url.pathname))) {
    return;
  }

  // APIリクエスト: Network First
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }

  // 静的リソース: Cache First
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirstStrategy(request));
    return;
  }

  // ページナビゲーション: Network First with Offline Fallback
  if (request.mode === 'navigate') {
    event.respondWith(navigationStrategy(request));
    return;
  }

  // その他: Stale While Revalidate
  event.respondWith(staleWhileRevalidateStrategy(request));
});

// Cache First戦略（静的リソース向け）
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache First failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Network First戦略（API向け）
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);

    // 成功したAPIレスポンスをキャッシュ
    if (networkResponse.ok && shouldCacheApi(request.url)) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // オフライン時のAPIエラーレスポンス
    return new Response(
      JSON.stringify({ error: 'offline', message: 'ネットワークに接続されていません' }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// ナビゲーション戦略（ページ遷移向け）
async function navigationStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('[SW] Navigation failed, serving offline page');
    const cachedResponse = await caches.match('/offline.html');
    if (cachedResponse) {
      return cachedResponse;
    }

    // オフラインページもない場合のフォールバック
    return new Response(
      '<html><body><h1>オフライン</h1><p>インターネット接続を確認してください</p></body></html>',
      {
        status: 503,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      }
    );
  }
}

// Stale While Revalidate戦略（その他のリソース向け）
async function staleWhileRevalidateStrategy(request) {
  const cachedResponse = await caches.match(request);

  const fetchPromise = fetch(request)
    .then((networkResponse) => {
      if (networkResponse.ok) {
        const cache = caches.open(DYNAMIC_CACHE_NAME);
        cache.then((c) => c.put(request, networkResponse.clone()));
      }
      return networkResponse;
    })
    .catch(() => cachedResponse);

  return cachedResponse || fetchPromise;
}

// 静的アセット判定
function isStaticAsset(pathname) {
  const staticExtensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf'];
  return staticExtensions.some((ext) => pathname.endsWith(ext));
}

// APIキャッシュ対象判定
function shouldCacheApi(url) {
  return CACHEABLE_API_PATTERNS.some((pattern) => pattern.test(url));
}

// プッシュ通知受信
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  let data = {
    title: 'SocialBoostAI',
    body: '新しい通知があります',
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-notification'
  };

  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: data.badge,
      tag: data.tag,
      data: data.url || '/',
      requireInteraction: data.requireInteraction || false,
      actions: data.actions || []
    })
  );
});

// 通知クリック
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');
  event.notification.close();

  const urlToOpen = event.notification.data || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // 既存ウィンドウがあればフォーカス
        for (const client of windowClients) {
          if (client.url.includes(location.origin) && 'focus' in client) {
            client.navigate(urlToOpen);
            return client.focus();
          }
        }
        // 新しいウィンドウを開く
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// バックグラウンド同期
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-analytics') {
    event.waitUntil(syncAnalytics());
  }
});

async function syncAnalytics() {
  // オフライン中に蓄積された分析データを送信
  console.log('[SW] Syncing analytics data...');
  // 実装は将来の拡張で追加
}

// 定期的なバックグラウンド同期（PWAが対応している場合）
self.addEventListener('periodicsync', (event) => {
  console.log('[SW] Periodic sync:', event.tag);

  if (event.tag === 'update-dashboard') {
    event.waitUntil(updateDashboardData());
  }
});

async function updateDashboardData() {
  console.log('[SW] Updating dashboard data in background...');
  // 実装は将来の拡張で追加
}

console.log('[SW] Service Worker loaded');
