/**
 * 通知ドロップダウンコンポーネント
 *
 * リアルタイム通知を表示
 */
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Check, CheckCheck, X, Trash2 } from 'lucide-react';
import { useNotificationStore, type NotificationItem } from '../stores/notificationStore';

// 重要度に応じた色
function getSeverityColors(severity: NotificationItem['severity']) {
  switch (severity) {
    case 'success':
      return 'bg-green-50 border-green-200 text-green-800';
    case 'error':
      return 'bg-red-50 border-red-200 text-red-800';
    case 'warning':
      return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    default:
      return 'bg-blue-50 border-blue-200 text-blue-800';
  }
}

// 相対時間を取得
function getRelativeTime(timestamp: string): string {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) {
    return 'たった今';
  } else if (diffMin < 60) {
    return `${diffMin}分前`;
  } else if (diffHour < 24) {
    return `${diffHour}時間前`;
  } else {
    return `${diffDay}日前`;
  }
}

export default function NotificationDropdown() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const {
    notifications,
    unreadCount,
    isConnected,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
  } = useNotificationStore();

  // 外側クリックで閉じる
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 通知をクリック
  const handleNotificationClick = (notification: NotificationItem) => {
    markAsRead(notification.id);
    if (notification.actionUrl) {
      navigate(notification.actionUrl);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* 通知ベルボタン */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label="通知"
      >
        <Bell size={24} className={isConnected ? 'text-gray-700' : 'text-gray-400'} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-medium">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
        {/* 接続状態インジケーター */}
        <span
          className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${
            isConnected ? 'bg-green-500' : 'bg-gray-400'
          }`}
        />
      </button>

      {/* ドロップダウン */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-50">
          {/* ヘッダー */}
          <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-gray-900">通知</h3>
              {unreadCount > 0 && (
                <span className="bg-primary-100 text-primary-700 text-xs px-2 py-0.5 rounded-full font-medium">
                  {unreadCount}件の未読
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {notifications.length > 0 && (
                <>
                  <button
                    onClick={markAllAsRead}
                    className="p-1.5 hover:bg-gray-200 rounded-lg transition-colors"
                    title="すべて既読にする"
                  >
                    <CheckCheck size={18} className="text-gray-600" />
                  </button>
                  <button
                    onClick={clearAll}
                    className="p-1.5 hover:bg-red-100 rounded-lg transition-colors"
                    title="すべて削除"
                  >
                    <Trash2 size={18} className="text-gray-600 hover:text-red-600" />
                  </button>
                </>
              )}
            </div>
          </div>

          {/* 通知リスト */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-12 text-center text-gray-500">
                <Bell size={40} className="mx-auto mb-3 opacity-30" />
                <p>通知はありません</p>
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`px-4 py-3 border-b last:border-0 cursor-pointer hover:bg-gray-50 transition-colors ${
                    !notification.read ? 'bg-blue-50/50' : ''
                  }`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className="flex items-start gap-3">
                    {/* 未読インジケーター */}
                    <div className="mt-1.5">
                      {!notification.read ? (
                        <div className="w-2 h-2 rounded-full bg-primary-500" />
                      ) : (
                        <div className="w-2 h-2 rounded-full bg-transparent" />
                      )}
                    </div>

                    {/* コンテンツ */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium border ${getSeverityColors(
                            notification.severity
                          )}`}
                        >
                          {notification.title}
                        </span>
                        <span className="text-xs text-gray-400">
                          {getRelativeTime(notification.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">
                        {notification.message}
                      </p>
                      {notification.actionUrl && (
                        <p className="text-xs text-primary-600 mt-1 hover:underline">
                          詳細を見る →
                        </p>
                      )}
                    </div>

                    {/* アクション */}
                    <div className="flex items-center gap-1">
                      {!notification.read && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            markAsRead(notification.id);
                          }}
                          className="p-1 hover:bg-gray-200 rounded transition-colors"
                          title="既読にする"
                        >
                          <Check size={14} className="text-gray-500" />
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeNotification(notification.id);
                        }}
                        className="p-1 hover:bg-red-100 rounded transition-colors"
                        title="削除"
                      >
                        <X size={14} className="text-gray-500 hover:text-red-600" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* フッター */}
          {!isConnected && (
            <div className="px-4 py-2 bg-yellow-50 border-t text-xs text-yellow-700 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-yellow-500" />
              リアルタイム通知に接続されていません
            </div>
          )}
        </div>
      )}
    </div>
  );
}
