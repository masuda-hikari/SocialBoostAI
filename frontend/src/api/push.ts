/**
 * プッシュ通知 API
 *
 * Web Push通知のサブスクリプション管理と通知設定
 */
import apiClient from './client';
import type {
  PushNotificationType,
  PushSubscription,
  PushSubscriptionCreate,
  PushSubscriptionUpdate,
  PushSubscriptionListResponse,
  PushNotificationLogsResponse,
  PushNotificationStats,
  VapidPublicKeyResponse,
  TestNotificationResponse,
} from '../types';

/**
 * VAPID公開鍵を取得
 */
export async function getVapidPublicKey(): Promise<string> {
  const response = await apiClient.get<VapidPublicKeyResponse>('/push/vapid-key');
  return response.data.public_key;
}

/**
 * サブスクリプションを登録
 */
export async function createSubscription(
  data: PushSubscriptionCreate
): Promise<PushSubscription> {
  const response = await apiClient.post<PushSubscription>('/push/subscriptions', data);
  return response.data;
}

/**
 * サブスクリプション一覧を取得
 */
export async function getSubscriptions(): Promise<PushSubscriptionListResponse> {
  const response = await apiClient.get<PushSubscriptionListResponse>('/push/subscriptions');
  return response.data;
}

/**
 * プッシュサブスクリプション詳細を取得
 */
export async function getPushSubscription(subscriptionId: string): Promise<PushSubscription> {
  const response = await apiClient.get<PushSubscription>(`/push/subscriptions/${subscriptionId}`);
  return response.data;
}

/**
 * サブスクリプションを更新
 */
export async function updateSubscription(
  subscriptionId: string,
  data: PushSubscriptionUpdate
): Promise<PushSubscription> {
  const response = await apiClient.put<PushSubscription>(`/push/subscriptions/${subscriptionId}`, data);
  return response.data;
}

/**
 * サブスクリプションを削除
 */
export async function deleteSubscription(subscriptionId: string): Promise<void> {
  await apiClient.delete(`/push/subscriptions/${subscriptionId}`);
}

/**
 * 通知ログを取得
 */
export async function getNotificationLogs(
  page: number = 1,
  perPage: number = 20,
  notificationType?: PushNotificationType
): Promise<PushNotificationLogsResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: perPage.toString(),
  });
  if (notificationType) {
    params.append('notification_type', notificationType);
  }
  const response = await apiClient.get<PushNotificationLogsResponse>(`/push/logs?${params.toString()}`);
  return response.data;
}

/**
 * 通知をクリック済みにする
 */
export async function markNotificationClicked(logId: string): Promise<void> {
  await apiClient.post(`/push/logs/${logId}/clicked`);
}

/**
 * 通知統計を取得
 */
export async function getNotificationStats(): Promise<PushNotificationStats> {
  const response = await apiClient.get<PushNotificationStats>('/push/stats');
  return response.data;
}

/**
 * テスト通知を送信
 */
export async function sendTestNotification(): Promise<TestNotificationResponse> {
  const response = await apiClient.post<TestNotificationResponse>('/push/test', {});
  return response.data;
}

// =============================================================================
// ブラウザプッシュ通知ヘルパー関数
// =============================================================================

/**
 * プッシュ通知がサポートされているか確認
 */
export function isPushNotificationSupported(): boolean {
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
}

/**
 * 現在の通知許可状態を取得
 */
export function getNotificationPermission(): NotificationPermission {
  return Notification.permission;
}

/**
 * 通知の許可をリクエスト
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  return await Notification.requestPermission();
}

/**
 * Service Workerからプッシュサブスクリプションを取得
 */
export async function getBrowserPushSubscription(): Promise<PushSubscription | null> {
  if (!isPushNotificationSupported()) {
    return null;
  }

  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();

  if (!subscription) {
    return null;
  }

  // 変換してPushSubscription形式に近づける
  return {
    id: '',
    endpoint: subscription.endpoint,
    device_type: getDeviceType(),
    browser: getBrowserName(),
    os: getOSName(),
    device_name: null,
    enabled: true,
    notification_types: [],
    last_used_at: null,
    created_at: new Date().toISOString(),
  } as unknown as PushSubscription;
}

/**
 * ブラウザでプッシュ通知をサブスクライブ
 */
export async function subscribeToPushNotifications(
  vapidPublicKey: string,
  notificationTypes: PushNotificationType[] = []
): Promise<PushSubscription> {
  if (!isPushNotificationSupported()) {
    throw new Error('プッシュ通知はこのブラウザでサポートされていません');
  }

  // 通知許可を取得
  const permission = await requestNotificationPermission();
  if (permission !== 'granted') {
    throw new Error('通知の許可が必要です');
  }

  // Service Workerを取得
  const registration = await navigator.serviceWorker.ready;

  // 既存のサブスクリプションがあれば解除
  const existingSubscription = await registration.pushManager.getSubscription();
  if (existingSubscription) {
    await existingSubscription.unsubscribe();
  }

  // 新しいサブスクリプションを作成
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
  });

  const keys = subscription.toJSON().keys;
  if (!keys || !keys.p256dh || !keys.auth) {
    throw new Error('サブスクリプションキーの取得に失敗しました');
  }

  // サーバーに登録
  const data: PushSubscriptionCreate = {
    endpoint: subscription.endpoint,
    keys: {
      p256dh: keys.p256dh,
      auth: keys.auth,
    },
    device_type: getDeviceType(),
    browser: getBrowserName(),
    os: getOSName(),
    notification_types: notificationTypes,
  };

  return await createSubscription(data);
}

/**
 * プッシュ通知のサブスクライブを解除
 */
export async function unsubscribeFromPushNotifications(subscriptionId?: string): Promise<void> {
  if (!isPushNotificationSupported()) {
    return;
  }

  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();

  if (subscription) {
    await subscription.unsubscribe();
  }

  // サーバー側のサブスクリプションも削除
  if (subscriptionId) {
    await deleteSubscription(subscriptionId);
  }
}

// =============================================================================
// ユーティリティ関数
// =============================================================================

/**
 * Base64 URLエンコードされた文字列をUint8Arrayに変換
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const buffer = new ArrayBuffer(rawData.length);
  const outputArray = new Uint8Array(buffer);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }

  return outputArray;
}

/**
 * デバイスタイプを判定
 */
function getDeviceType(): string {
  const ua = navigator.userAgent;
  if (/tablet|ipad|playbook|silk/i.test(ua)) {
    return 'tablet';
  }
  if (/mobile|iphone|ipod|android|blackberry|opera mini|iemobile/i.test(ua)) {
    return 'mobile';
  }
  return 'desktop';
}

/**
 * ブラウザ名を取得
 */
function getBrowserName(): string {
  const ua = navigator.userAgent;
  if (ua.includes('Firefox')) return 'Firefox';
  if (ua.includes('SamsungBrowser')) return 'Samsung Browser';
  if (ua.includes('Opera') || ua.includes('OPR')) return 'Opera';
  if (ua.includes('Trident')) return 'Internet Explorer';
  if (ua.includes('Edge')) return 'Edge (Legacy)';
  if (ua.includes('Edg')) return 'Edge';
  if (ua.includes('Chrome')) return 'Chrome';
  if (ua.includes('Safari')) return 'Safari';
  return 'Unknown';
}

/**
 * OS名を取得
 */
function getOSName(): string {
  const ua = navigator.userAgent;
  if (ua.includes('Windows')) return 'Windows';
  if (ua.includes('Mac OS')) return 'macOS';
  if (ua.includes('Linux')) return 'Linux';
  if (ua.includes('Android')) return 'Android';
  if (ua.includes('iOS') || ua.includes('iPhone') || ua.includes('iPad')) return 'iOS';
  return 'Unknown';
}
