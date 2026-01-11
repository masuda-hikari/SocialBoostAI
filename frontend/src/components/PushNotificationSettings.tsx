/**
 * プッシュ通知設定コンポーネント
 *
 * ブラウザプッシュ通知のサブスクリプション管理と設定
 */
import { useState, useEffect, useCallback } from 'react';
import {
  Bell,
  BellOff,
  Smartphone,
  Monitor,
  Tablet,
  Trash2,
  RefreshCw,
  Check,
  AlertCircle,
  Info,
} from 'lucide-react';
import type { PushSubscription, PushNotificationType, PushNotificationStats } from '../types';
import * as pushApi from '../api/push';

interface Props {
  onError?: (error: string) => void;
  onSuccess?: (message: string) => void;
}

// 通知タイプのラベルマッピング
const notificationTypeLabels: Record<PushNotificationType, string> = {
  analysis_complete: '分析完了',
  report_ready: 'レポート完了',
  scheduled_post_published: '投稿公開',
  scheduled_post_failed: '投稿失敗',
  weekly_summary: '週次サマリー',
  engagement_alert: 'エンゲージメントアラート',
  subscription_update: 'サブスクリプション更新',
  system: 'システム通知',
};

// 全通知タイプ
const allNotificationTypes: PushNotificationType[] = [
  'analysis_complete',
  'report_ready',
  'scheduled_post_published',
  'scheduled_post_failed',
  'weekly_summary',
  'engagement_alert',
  'subscription_update',
  'system',
];

export default function PushNotificationSettings({ onError, onSuccess }: Props) {
  const [isSupported, setIsSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [subscriptions, setSubscriptions] = useState<PushSubscription[]>([]);
  const [stats, setStats] = useState<PushNotificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState<PushNotificationType[]>([
    'analysis_complete',
    'report_ready',
    'scheduled_post_published',
    'scheduled_post_failed',
  ]);
  const [testingSending, setTestingSending] = useState(false);

  // 初期化
  useEffect(() => {
    const checkSupport = () => {
      const supported = pushApi.isPushNotificationSupported();
      setIsSupported(supported);
      if (supported) {
        setPermission(pushApi.getNotificationPermission());
      }
    };
    checkSupport();
  }, []);

  // データ読み込み
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [subsResponse, statsResponse] = await Promise.all([
        pushApi.getSubscriptions(),
        pushApi.getNotificationStats(),
      ]);
      setSubscriptions(subsResponse.items);
      setStats(statsResponse);
    } catch (error) {
      console.error('プッシュ通知設定の読み込みに失敗:', error);
      onError?.('プッシュ通知設定の読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  }, [onError]);

  useEffect(() => {
    if (isSupported) {
      loadData();
    }
  }, [isSupported, loadData]);

  // サブスクライブ
  const handleSubscribe = async () => {
    try {
      setSubscribing(true);

      // VAPID公開鍵を取得
      const vapidKey = await pushApi.getVapidPublicKey();

      // ブラウザでサブスクライブ
      await pushApi.subscribeToPushNotifications(vapidKey, selectedTypes);

      // 許可状態を更新
      setPermission(pushApi.getNotificationPermission());

      // データを再読み込み
      await loadData();

      onSuccess?.('プッシュ通知を有効にしました');
    } catch (error) {
      console.error('サブスクライブに失敗:', error);
      const message = error instanceof Error ? error.message : 'サブスクライブに失敗しました';
      onError?.(message);
    } finally {
      setSubscribing(false);
    }
  };

  // サブスクリプション削除
  const handleDeleteSubscription = async (subscription: PushSubscription) => {
    try {
      await pushApi.unsubscribeFromPushNotifications(subscription.id);
      await loadData();
      onSuccess?.('サブスクリプションを削除しました');
    } catch (error) {
      console.error('削除に失敗:', error);
      onError?.('サブスクリプションの削除に失敗しました');
    }
  };

  // 通知設定更新
  const handleUpdateSubscription = async (
    subscription: PushSubscription,
    updates: { enabled?: boolean; notification_types?: PushNotificationType[] }
  ) => {
    try {
      await pushApi.updateSubscription(subscription.id, updates);
      await loadData();
      onSuccess?.('設定を更新しました');
    } catch (error) {
      console.error('更新に失敗:', error);
      onError?.('設定の更新に失敗しました');
    }
  };

  // テスト通知送信
  const handleSendTestNotification = async () => {
    try {
      setTestingSending(true);
      const result = await pushApi.sendTestNotification();
      if (result.status === 'ok') {
        onSuccess?.(`テスト通知を送信しました (成功: ${result.sent}, 失敗: ${result.failed})`);
      } else if (result.status === 'no_subscriptions') {
        onError?.('有効なサブスクリプションがありません');
      }
    } catch (error) {
      console.error('テスト送信に失敗:', error);
      onError?.('テスト通知の送信に失敗しました');
    } finally {
      setTestingSending(false);
    }
  };

  // デバイスアイコンを取得
  const getDeviceIcon = (deviceType: string | null) => {
    switch (deviceType) {
      case 'mobile':
        return <Smartphone className="h-5 w-5" />;
      case 'tablet':
        return <Tablet className="h-5 w-5" />;
      default:
        return <Monitor className="h-5 w-5" />;
    }
  };

  // 通知タイプ選択のトグル
  const toggleNotificationType = (type: PushNotificationType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  // サポートされていない場合
  if (!isSupported) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 mr-3" />
          <div>
            <h4 className="text-sm font-medium text-yellow-800">
              プッシュ通知はこのブラウザでサポートされていません
            </h4>
            <p className="mt-1 text-sm text-yellow-700">
              Chrome、Firefox、Edge、Safari（iOS 16.4以降）で利用可能です。
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Bell className="h-5 w-5 text-gray-600 mr-2" aria-hidden="true" />
          <h3 className="text-lg font-medium text-gray-900">プッシュ通知</h3>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
          aria-label="更新"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* 許可状態の表示 */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">通知許可状態</p>
            <p className="text-sm text-gray-500 mt-1">
              {permission === 'granted' && 'プッシュ通知が許可されています'}
              {permission === 'denied' && 'プッシュ通知がブロックされています'}
              {permission === 'default' && 'プッシュ通知の許可が必要です'}
            </p>
          </div>
          <div
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              permission === 'granted'
                ? 'bg-green-100 text-green-800'
                : permission === 'denied'
                ? 'bg-red-100 text-red-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {permission === 'granted' && '許可済み'}
            {permission === 'denied' && 'ブロック'}
            {permission === 'default' && '未設定'}
          </div>
        </div>

        {permission === 'denied' && (
          <div className="mt-3 bg-red-50 border border-red-200 rounded p-3">
            <p className="text-sm text-red-700">
              ブラウザの設定から通知を許可してください。
            </p>
          </div>
        )}
      </div>

      {/* 新規サブスクライブセクション */}
      {permission !== 'denied' && subscriptions.length === 0 && (
        <div className="border border-blue-200 bg-blue-50 rounded-lg p-4">
          <div className="flex items-start">
            <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3" aria-hidden="true" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-blue-800">
                このデバイスでプッシュ通知を有効にする
              </h4>
              <p className="mt-1 text-sm text-blue-700">
                分析完了やレポート生成時に通知を受け取れます。
              </p>

              {/* 通知タイプ選択 */}
              <div className="mt-3">
                <p className="text-xs font-medium text-blue-800 mb-2">受信する通知:</p>
                <div className="flex flex-wrap gap-2">
                  {allNotificationTypes.map((type) => (
                    <button
                      key={type}
                      onClick={() => toggleNotificationType(type)}
                      className={`px-2 py-1 text-xs rounded-full border ${
                        selectedTypes.includes(type)
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-blue-700 border-blue-300 hover:bg-blue-100'
                      }`}
                    >
                      {selectedTypes.includes(type) && (
                        <Check className="inline-block h-3 w-3 mr-1" />
                      )}
                      {notificationTypeLabels[type]}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleSubscribe}
                disabled={subscribing || selectedTypes.length === 0}
                className="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {subscribing ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    設定中...
                  </>
                ) : (
                  <>
                    <Bell className="h-4 w-4 mr-2" />
                    通知を有効にする
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* サブスクリプション一覧 */}
      {subscriptions.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b">
            <h4 className="text-sm font-medium text-gray-900">登録済みデバイス</h4>
          </div>
          <ul className="divide-y divide-gray-200" role="list">
            {subscriptions.map((sub) => (
              <li key={sub.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 p-2 bg-gray-100 rounded-lg text-gray-600">
                      {getDeviceIcon(sub.device_type)}
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">
                        {sub.device_name || `${sub.browser || 'ブラウザ'} (${sub.os || 'OS'})`}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {sub.device_type === 'mobile' && 'モバイル'}
                        {sub.device_type === 'tablet' && 'タブレット'}
                        {sub.device_type === 'desktop' && 'デスクトップ'}
                        {!sub.device_type && 'デバイス'}
                        {sub.last_used_at && ` • 最終使用: ${new Date(sub.last_used_at).toLocaleDateString('ja-JP')}`}
                      </p>

                      {/* 受信する通知タイプ */}
                      <div className="mt-2 flex flex-wrap gap-1">
                        {sub.notification_types.length > 0 ? (
                          sub.notification_types.map((type) => (
                            <span
                              key={type}
                              className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                            >
                              {notificationTypeLabels[type as PushNotificationType] || type}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400">全通知を受信</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {/* 有効/無効トグル */}
                    <button
                      onClick={() => handleUpdateSubscription(sub, { enabled: !sub.enabled })}
                      className={`p-2 rounded-lg ${
                        sub.enabled
                          ? 'bg-green-100 text-green-600 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                      }`}
                      aria-label={sub.enabled ? '通知を無効にする' : '通知を有効にする'}
                    >
                      {sub.enabled ? (
                        <Bell className="h-4 w-4" />
                      ) : (
                        <BellOff className="h-4 w-4" />
                      )}
                    </button>

                    {/* 削除ボタン */}
                    <button
                      onClick={() => handleDeleteSubscription(sub)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                      aria-label="削除"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* テスト通知送信 */}
      {subscriptions.length > 0 && subscriptions.some((s) => s.enabled) && (
        <div className="flex items-center justify-between bg-gray-50 rounded-lg p-4">
          <div>
            <p className="text-sm font-medium text-gray-900">テスト通知</p>
            <p className="text-xs text-gray-500">プッシュ通知が正常に動作するか確認します</p>
          </div>
          <button
            onClick={handleSendTestNotification}
            disabled={testingSending}
            className="inline-flex items-center px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 disabled:opacity-50"
          >
            {testingSending ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                送信中...
              </>
            ) : (
              <>
                <Bell className="h-4 w-4 mr-2" />
                テスト送信
              </>
            )}
          </button>
        </div>
      )}

      {/* 統計表示 */}
      {stats && stats.total_subscriptions > 0 && (
        <div className="border rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">通知統計</h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats.total_sent}</p>
              <p className="text-xs text-gray-500">送信済み</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">{stats.total_clicked}</p>
              <p className="text-xs text-gray-500">クリック</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{stats.total_failed}</p>
              <p className="text-xs text-gray-500">失敗</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {(stats.click_rate * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">クリック率</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
