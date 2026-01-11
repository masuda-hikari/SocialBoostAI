/**
 * PWAインストールプロンプトコンポーネント
 * アプリインストールを促すバナーを表示
 */
import { useState, useEffect } from 'react';
import { Download, X, Smartphone } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

// スタンドアロンモードかどうかを判定する関数（初期値用）
const getIsStandalone = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(display-mode: standalone)').matches;
};

export function PWAInstallPrompt() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  // 初期状態でスタンドアロンモードかどうかをチェック
  const [isInstalled, setIsInstalled] = useState(getIsStandalone);

  useEffect(() => {
    // 既にインストール済みなら何もしない
    if (isInstalled) {
      return;
    }

    // インストール済みかローカルストレージで確認
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10);
      // 7日間は非表示
      if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        return;
      }
    }

    // beforeinstallpromptイベントをキャプチャ
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
      // 少し遅延させて表示
      setTimeout(() => setIsVisible(true), 3000);
    };

    // アプリがインストールされたとき
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsVisible(false);
      setInstallPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;

    try {
      await installPrompt.prompt();
      const choiceResult = await installPrompt.userChoice;

      if (choiceResult.outcome === 'accepted') {
        console.log('[PWA] User accepted install prompt');
        setIsInstalled(true);
      } else {
        console.log('[PWA] User dismissed install prompt');
      }

      setIsVisible(false);
      setInstallPrompt(null);
    } catch (error) {
      console.error('[PWA] Install prompt error:', error);
    }
  };

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  };

  // インストール済みまたは非表示の場合
  if (isInstalled || !isVisible || !installPrompt) {
    return null;
  }

  return (
    <div
      className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl shadow-2xl p-4 z-50 animate-slide-up"
      role="alert"
      aria-label="アプリをインストール"
    >
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 p-1 rounded-full hover:bg-white/20 transition-colors"
        aria-label="閉じる"
      >
        <X className="w-5 h-5" />
      </button>

      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
          <Smartphone className="w-6 h-6" />
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg mb-1">アプリをインストール</h3>
          <p className="text-sm text-white/80 mb-3">
            ホーム画面に追加して、いつでもすぐにアクセス。オフラインでも利用可能です。
          </p>

          <div className="flex gap-2">
            <button
              onClick={handleInstall}
              className="flex items-center gap-2 bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold text-sm hover:bg-blue-50 transition-colors"
            >
              <Download className="w-4 h-4" />
              インストール
            </button>
            <button
              onClick={handleDismiss}
              className="px-4 py-2 rounded-lg text-sm text-white/80 hover:bg-white/10 transition-colors"
            >
              後で
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slide-up {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}

/**
 * オフライン状態表示コンポーネント
 */
export function OfflineIndicator() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOffline) {
    return null;
  }

  return (
    <div
      className="fixed top-0 left-0 right-0 bg-yellow-500 text-yellow-900 text-center py-2 px-4 text-sm font-medium z-50"
      role="alert"
      aria-live="polite"
    >
      <span className="inline-flex items-center gap-2">
        <span className="w-2 h-2 bg-yellow-900 rounded-full animate-pulse" />
        オフラインモードです。一部の機能が制限されています。
      </span>
    </div>
  );
}

/**
 * PWA更新通知コンポーネント
 */
export function PWAUpdateNotification() {
  const [showUpdate, setShowUpdate] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                setWaitingWorker(newWorker);
                setShowUpdate(true);
              }
            });
          }
        });
      });

      // 定期的に更新をチェック（1時間ごと）
      const intervalId = setInterval(() => {
        navigator.serviceWorker.ready.then((registration) => {
          registration.update();
        });
      }, 60 * 60 * 1000);

      return () => clearInterval(intervalId);
    }
  }, []);

  const handleUpdate = () => {
    if (waitingWorker) {
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
    }
    window.location.reload();
  };

  const handleDismiss = () => {
    setShowUpdate(false);
  };

  if (!showUpdate) {
    return null;
  }

  return (
    <div
      className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-80 bg-gray-800 text-white rounded-xl shadow-2xl p-4 z-50"
      role="alert"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
          <Download className="w-5 h-5 text-green-400" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold mb-1">アップデート利用可能</h4>
          <p className="text-sm text-gray-400 mb-3">
            新しいバージョンが利用可能です。更新して最新機能を利用しましょう。
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleUpdate}
              className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors"
            >
              今すぐ更新
            </button>
            <button
              onClick={handleDismiss}
              className="px-4 py-2 text-gray-400 text-sm hover:text-white transition-colors"
            >
              後で
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
