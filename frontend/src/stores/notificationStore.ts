/**
 * 通知ストア（Zustand）
 *
 * WebSocket経由のリアルタイム通知を管理
 */
import { create } from 'zustand';
import {
  getWebSocketClient,
  connectWebSocket,
  disconnectWebSocket,
  type NotificationType,
  type AnalysisCompletePayload,
  type ReportReadyPayload,
  type SystemNotificationPayload,
  type SubscriptionUpdatePayload,
  type ProgressPayload,
} from '../api';

// 通知項目
export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  severity: 'info' | 'success' | 'warning' | 'error';
  payload: Record<string, unknown>;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
}

// 進捗状態
export interface ProgressState {
  analysisId: string;
  progress: number;
  status: string;
}

// ストア状態
interface NotificationState {
  // 接続状態
  isConnected: boolean;
  connectionError: string | null;

  // 通知リスト
  notifications: NotificationItem[];
  unreadCount: number;

  // 進捗状態
  progressStates: Map<string, ProgressState>;

  // アクション
  connect: () => Promise<void>;
  disconnect: () => void;
  addNotification: (notification: NotificationItem) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  updateProgress: (analysisId: string, progress: number, status: string) => void;
  clearProgress: (analysisId: string) => void;
}

// 通知タイプからタイトルを取得
function getTitleForType(type: NotificationType): string {
  switch (type) {
    case 'analysis_started':
      return '分析開始';
    case 'analysis_progress':
      return '分析進捗';
    case 'analysis_complete':
      return '分析完了';
    case 'analysis_failed':
      return '分析失敗';
    case 'report_generating':
      return 'レポート生成中';
    case 'report_ready':
      return 'レポート完了';
    case 'report_failed':
      return 'レポート失敗';
    case 'subscription_updated':
      return 'サブスクリプション更新';
    case 'subscription_expiring':
      return 'サブスクリプション期限';
    case 'payment_failed':
      return '支払い失敗';
    case 'system_notification':
      return 'システム通知';
    case 'maintenance_scheduled':
      return 'メンテナンス予定';
    case 'dashboard_update':
      return 'ダッシュボード更新';
    case 'metrics_update':
      return 'メトリクス更新';
    default:
      return '通知';
  }
}


// ペイロードからメッセージを生成
function getMessageFromPayload(type: NotificationType, payload: Record<string, unknown>): string {
  switch (type) {
    case 'analysis_started':
      return `${payload.platform || 'プラットフォーム'}の分析を開始しました`;
    case 'analysis_complete': {
      const data = payload as unknown as AnalysisCompletePayload;
      return `${data.platform}の分析が完了しました（${data.total_posts}件、エンゲージメント率${(data.engagement_rate * 100).toFixed(1)}%）`;
    }
    case 'analysis_failed':
      return `分析に失敗しました: ${payload.error_message || '不明なエラー'}`;
    case 'report_ready': {
      const data = payload as unknown as ReportReadyPayload;
      return `${data.report_type}レポートが完成しました`;
    }
    case 'subscription_updated': {
      const data = payload as unknown as SubscriptionUpdatePayload;
      return `プランが${data.plan}に変更されました`;
    }
    case 'payment_failed':
      return '支払いに失敗しました。支払い方法を確認してください。';
    case 'system_notification': {
      const data = payload as unknown as SystemNotificationPayload;
      return data.message;
    }
    case 'maintenance_scheduled':
      return `メンテナンスが予定されています: ${payload.message || ''}`;
    default:
      return (payload.message as string) || '新しい通知があります';
  }
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  isConnected: false,
  connectionError: null,
  notifications: [],
  unreadCount: 0,
  progressStates: new Map(),

  connect: async () => {
    try {
      const client = getWebSocketClient();

      // イベントハンドラを設定
      client.on('connected', () => {
        set({ isConnected: true, connectionError: null });
      });

      // 分析進捗
      client.on<ProgressPayload>('analysis_progress', (payload) => {
        get().updateProgress(payload.analysis_id, payload.progress, payload.status);
      });

      // 分析完了
      client.on<AnalysisCompletePayload>('analysis_complete', (payload) => {
        get().clearProgress(payload.analysis_id);
        get().addNotification({
          id: `notif_${Date.now()}`,
          type: 'analysis_complete',
          title: getTitleForType('analysis_complete'),
          message: getMessageFromPayload('analysis_complete', payload as unknown as Record<string, unknown>),
          severity: 'success',
          payload: payload as unknown as Record<string, unknown>,
          timestamp: new Date().toISOString(),
          read: false,
          actionUrl: `/analysis/${payload.analysis_id}`,
        });
      });

      // レポート完了
      client.on<ReportReadyPayload>('report_ready', (payload) => {
        get().addNotification({
          id: `notif_${Date.now()}`,
          type: 'report_ready',
          title: getTitleForType('report_ready'),
          message: getMessageFromPayload('report_ready', payload as unknown as Record<string, unknown>),
          severity: 'success',
          payload: payload as unknown as Record<string, unknown>,
          timestamp: new Date().toISOString(),
          read: false,
          actionUrl: payload.html_url || `/reports/${payload.report_id}`,
        });
      });

      // システム通知
      client.on<SystemNotificationPayload>('system_notification', (payload) => {
        get().addNotification({
          id: `notif_${Date.now()}`,
          type: 'system_notification',
          title: payload.title,
          message: payload.message,
          severity: payload.severity,
          payload: payload as unknown as Record<string, unknown>,
          timestamp: new Date().toISOString(),
          read: false,
          actionUrl: payload.action_url,
        });
      });

      // サブスクリプション更新
      client.on<SubscriptionUpdatePayload>('subscription_updated', (payload) => {
        get().addNotification({
          id: `notif_${Date.now()}`,
          type: 'subscription_updated',
          title: getTitleForType('subscription_updated'),
          message: getMessageFromPayload('subscription_updated', payload as unknown as Record<string, unknown>),
          severity: 'info',
          payload: payload as unknown as Record<string, unknown>,
          timestamp: new Date().toISOString(),
          read: false,
        });
      });

      // 支払い失敗
      client.on('payment_failed', (payload) => {
        get().addNotification({
          id: `notif_${Date.now()}`,
          type: 'payment_failed',
          title: getTitleForType('payment_failed'),
          message: getMessageFromPayload('payment_failed', payload as Record<string, unknown>),
          severity: 'error',
          payload: payload as Record<string, unknown>,
          timestamp: new Date().toISOString(),
          read: false,
          actionUrl: '/billing',
        });
      });

      // エラー
      client.on('error', (payload) => {
        console.error('[NotificationStore] WebSocketエラー:', payload);
        set({ connectionError: (payload as Record<string, unknown>).message as string });
      });

      await connectWebSocket();
    } catch (error) {
      console.error('[NotificationStore] 接続エラー:', error);
      set({
        isConnected: false,
        connectionError: error instanceof Error ? error.message : '接続エラー',
      });
    }
  },

  disconnect: () => {
    disconnectWebSocket();
    set({ isConnected: false });
  },

  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(0, 50), // 最大50件
      unreadCount: state.unreadCount + 1,
    }));
  },

  markAsRead: (id) => {
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id && !n.read ? { ...n, read: true } : n
      );
      const unreadCount = notifications.filter((n) => !n.read).length;
      return { notifications, unreadCount };
    });
  },

  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    }));
  },

  removeNotification: (id) => {
    set((state) => {
      const notification = state.notifications.find((n) => n.id === id);
      const wasUnread = notification && !notification.read;
      return {
        notifications: state.notifications.filter((n) => n.id !== id),
        unreadCount: wasUnread ? state.unreadCount - 1 : state.unreadCount,
      };
    });
  },

  clearAll: () => {
    set({ notifications: [], unreadCount: 0 });
  },

  updateProgress: (analysisId, progress, status) => {
    set((state) => {
      const newProgressStates = new Map(state.progressStates);
      newProgressStates.set(analysisId, { analysisId, progress, status });
      return { progressStates: newProgressStates };
    });
  },

  clearProgress: (analysisId) => {
    set((state) => {
      const newProgressStates = new Map(state.progressStates);
      newProgressStates.delete(analysisId);
      return { progressStates: newProgressStates };
    });
  },
}));
