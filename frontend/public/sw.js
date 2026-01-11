// SocialBoostAI Service Worker
// バージョン管理でキャッシュ更新を制御
const CACHE_VERSION = 'v2.11.0';
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

// 通知タイプ別のアイコンとデフォルト設定
const NOTIFICATION_TYPES = {
  analysis_complete: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-analysis',
    defaultTitle: '分析が完了しました',
    defaultBody: 'ソーシャルメディア分析の結果をご確認ください',
    defaultUrl: '/dashboard'
  },
  report_ready: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-report',
    defaultTitle: 'レポートが完成しました',
    defaultBody: '最新のレポートをダウンロードできます',
    defaultUrl: '/reports'
  },
  scheduled_post_published: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-schedule',
    defaultTitle: '投稿が公開されました',
    defaultBody: 'スケジュールされた投稿が正常に公開されました',
    defaultUrl: '/schedule'
  },
  scheduled_post_failed: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-schedule-error',
    defaultTitle: '投稿の公開に失敗しました',
    defaultBody: '投稿の公開中にエラーが発生しました',
    defaultUrl: '/schedule',
    requireInteraction: true
  },
  weekly_summary: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-weekly',
    defaultTitle: '週次サマリー',
    defaultBody: '今週のソーシャルメディアパフォーマンスをご確認ください',
    defaultUrl: '/dashboard'
  },
  engagement_alert: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-engagement',
    defaultTitle: 'エンゲージメントアラート',
    defaultBody: '投稿が注目を集めています！',
    defaultUrl: '/dashboard'
  },
  subscription_update: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-subscription',
    defaultTitle: 'サブスクリプション更新',
    defaultBody: 'プランに関するお知らせがあります',
    defaultUrl: '/billing'
  },
  system: {
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-system',
    defaultTitle: 'SocialBoostAI',
    defaultBody: 'システムからのお知らせ',
    defaultUrl: '/dashboard'
  }
};

// プッシュ通知受信
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');

  let notificationData = {
    title: 'SocialBoostAI',
    body: '新しい通知があります',
    icon: '/icons/icon-192x192.svg',
    badge: '/icons/icon-72x72.svg',
    tag: 'socialboostai-notification',
    url: '/dashboard',
    notification_type: 'system',
    log_id: null,
    requireInteraction: false,
    actions: []
  };

  if (event.data) {
    try {
      const payload = event.data.json();

      // 通知タイプに応じたデフォルト設定を適用
      const typeConfig = NOTIFICATION_TYPES[payload.notification_type] || NOTIFICATION_TYPES.system;

      notificationData = {
        ...notificationData,
        icon: typeConfig.icon,
        badge: typeConfig.badge,
        tag: typeConfig.tag,
        title: payload.title || typeConfig.defaultTitle,
        body: payload.body || typeConfig.defaultBody,
        url: payload.url || typeConfig.defaultUrl,
        notification_type: payload.notification_type || 'system',
        log_id: payload.log_id || null,
        requireInteraction: payload.requireInteraction || typeConfig.requireInteraction || false,
        data: payload.data || {}
      };

      // アクションボタンがあれば追加
      if (payload.actions && Array.isArray(payload.actions)) {
        notificationData.actions = payload.actions;
      }
    } catch (e) {
      console.error('[SW] Failed to parse push data:', e);
      notificationData.body = event.data.text();
    }
  }

  const options = {
    body: notificationData.body,
    icon: notificationData.icon,
    badge: notificationData.badge,
    tag: notificationData.tag,
    data: {
      url: notificationData.url,
      notification_type: notificationData.notification_type,
      log_id: notificationData.log_id,
      ...notificationData.data
    },
    requireInteraction: notificationData.requireInteraction,
    vibrate: [200, 100, 200],
    timestamp: Date.now()
  };

  // アクションがあれば追加（Chromeでサポート）
  if (notificationData.actions.length > 0) {
    options.actions = notificationData.actions;
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, options)
  );
});

// 通知クリック
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');
  event.notification.close();

  const notificationData = event.notification.data || {};
  const urlToOpen = notificationData.url || '/';
  const logId = notificationData.log_id;

  // クリック追跡
  if (logId) {
    trackNotificationClick(logId).catch((error) => {
      console.error('[SW] Failed to track notification click:', error);
    });
  }

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

// 通知閉じる
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed');
  // 必要に応じて閉じたことを記録
});

// 通知クリックをサーバーに記録
async function trackNotificationClick(logId) {
  try {
    const response = await fetch(`/api/v1/push/logs/${logId}/clicked`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    if (!response.ok) {
      console.warn('[SW] Click tracking failed:', response.status);
    }
  } catch (error) {
    console.error('[SW] Click tracking error:', error);
  }
}

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
