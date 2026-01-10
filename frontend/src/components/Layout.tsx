/**
 * レイアウトコンポーネント（WebSocket通知対応）
 */
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useNotificationStore } from '../stores/notificationStore';
import NotificationDropdown from './NotificationDropdown';
import { ActiveProgressBars } from './ProgressBar';
import {
  LayoutDashboard,
  BarChart3,
  GitCompare,
  FileText,
  CreditCard,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles,
} from 'lucide-react';
import { useState } from 'react';

export default function Layout() {
  const { user, logout } = useAuthStore();
  const { connect, disconnect, isConnected } = useNotificationStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // WebSocket接続
  useEffect(() => {
    // ログイン状態ならWebSocket接続
    if (user) {
      connect().catch((error) => {
        console.error('[Layout] WebSocket接続エラー:', error);
      });
    }

    // クリーンアップ時に切断
    return () => {
      disconnect();
    };
  }, [user, connect, disconnect]);

  const handleLogout = async () => {
    disconnect(); // WebSocket切断
    await logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'ダッシュボード', icon: LayoutDashboard },
    { path: '/analysis', label: '分析', icon: BarChart3 },
    { path: '/comparison', label: 'プラットフォーム比較', icon: GitCompare },
    { path: '/content', label: 'AI生成', icon: Sparkles },
    { path: '/reports', label: 'レポート', icon: FileText },
    { path: '/billing', label: '課金', icon: CreditCard },
    { path: '/settings', label: '設定', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* スキップリンク（キーボードナビゲーション用） */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg"
      >
        メインコンテンツへスキップ
      </a>

      {/* モバイルメニューボタン */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg bg-white shadow-md"
          aria-label={sidebarOpen ? 'メニューを閉じる' : 'メニューを開く'}
          aria-expanded={sidebarOpen}
        >
          {sidebarOpen ? <X size={24} aria-hidden="true" /> : <Menu size={24} aria-hidden="true" />}
        </button>
      </div>

      {/* サイドバー */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        role="navigation"
        aria-label="メインナビゲーション"
      >
        <div className="flex flex-col h-full">
          {/* ロゴ */}
          <div className="flex items-center justify-center h-16 border-b">
            <Link to="/dashboard" className="text-xl font-bold text-primary-600">
              SocialBoostAI
            </Link>
          </div>

          {/* ナビゲーション */}
          <nav className="flex-1 px-4 py-6 space-y-2" aria-label="サイドバーナビゲーション">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className="flex items-center px-4 py-3 text-gray-700 rounded-lg hover:bg-primary-50 hover:text-primary-600 transition-colors"
                aria-label={item.label}
              >
                <item.icon size={20} className="mr-3" aria-hidden="true" />
                {item.label}
              </Link>
            ))}
          </nav>

          {/* ユーザー情報 */}
          <div className="p-4 border-t">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-primary-600 font-medium">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">{user?.username}</p>
                <p className="text-xs text-gray-500 capitalize">{user?.role} プラン</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-2 text-gray-700 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors"
              aria-label="ログアウト"
            >
              <LogOut size={20} className="mr-3" aria-hidden="true" />
              ログアウト
            </button>
          </div>
        </div>
      </aside>

      {/* オーバーレイ（モバイル） */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* トップバー（通知） */}
      <header className="lg:ml-64 fixed top-0 right-0 left-0 lg:left-64 h-16 bg-white border-b z-20 flex items-center justify-end px-4 md:px-6">
        <div className="flex items-center gap-4">
          {/* 接続状態インジケーター（小さめ） */}
          <div
            className={`hidden md:flex items-center gap-1.5 text-xs ${
              isConnected ? 'text-green-600' : 'text-gray-400'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
              }`}
            />
            {isConnected ? 'リアルタイム' : 'オフライン'}
          </div>

          {/* 通知ドロップダウン */}
          <NotificationDropdown />
        </div>
      </header>

      {/* メインコンテンツ */}
      <main id="main-content" className="lg:ml-64 min-h-screen pt-16" role="main">
        <div className="p-6">
          <Outlet />
        </div>
      </main>

      {/* アクティブな進捗バー（フローティング） */}
      <ActiveProgressBars />
    </div>
  );
}
