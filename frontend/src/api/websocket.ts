/**
 * WebSocketクライアント
 *
 * リアルタイム通知を受信するためのWebSocketクライアント
 */

// 通知タイプ
export type NotificationType =
  | 'analysis_started'
  | 'analysis_progress'
  | 'analysis_complete'
  | 'analysis_failed'
  | 'report_generating'
  | 'report_ready'
  | 'report_failed'
  | 'subscription_updated'
  | 'subscription_expiring'
  | 'payment_failed'
  | 'system_notification'
  | 'maintenance_scheduled'
  | 'dashboard_update'
  | 'metrics_update'
  | 'connected'
  | 'ping'
  | 'pong'
  | 'error';

// 通知メッセージ
export interface WebSocketNotification {
  type: NotificationType;
  payload: Record<string, unknown>;
  timestamp?: string;
  notification_id?: string;
}

// 分析完了ペイロード
export interface AnalysisCompletePayload {
  analysis_id: string;
  platform: string;
  period_start: string;
  period_end: string;
  total_posts: number;
  engagement_rate: number;
  best_hour?: number;
  top_hashtags?: string[];
}

// レポート完了ペイロード
export interface ReportReadyPayload {
  report_id: string;
  report_type: string;
  platform: string;
  period_start: string;
  period_end: string;
  html_url?: string;
}

// システム通知ペイロード
export interface SystemNotificationPayload {
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  action_url?: string;
}

// サブスクリプション更新ペイロード
export interface SubscriptionUpdatePayload {
  plan: string;
  status: string;
  previous_plan?: string;
  current_period_end?: string;
}

// 進捗ペイロード
export interface ProgressPayload {
  analysis_id: string;
  progress: number;
  status: string;
}

// WebSocket接続オプション
export interface WebSocketOptions {
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

// WebSocketイベントハンドラ
export type WebSocketEventHandler<T = unknown> = (payload: T) => void;

/**
 * WebSocketクライアントクラス
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private options: Required<WebSocketOptions>;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private eventHandlers: Map<NotificationType, Set<WebSocketEventHandler>> = new Map();
  private url: string = '';

  constructor(options: WebSocketOptions = {}) {
    this.options = {
      autoReconnect: options.autoReconnect ?? true,
      reconnectInterval: options.reconnectInterval ?? 5000,
      maxReconnectAttempts: options.maxReconnectAttempts ?? 10,
      pingInterval: options.pingInterval ?? 30000,
    };
  }

  /**
   * WebSocket接続
   */
  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const wsUrl = baseUrl.replace(/^http/, 'ws');
      this.url = `${wsUrl}/ws?token=${encodeURIComponent(token)}`;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] 接続成功');
          this.reconnectAttempts = 0;
          this.startPing();
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] 接続終了:', event.code, event.reason);
          this.stopPing();

          if (this.options.autoReconnect && event.code !== 4001) {
            this.scheduleReconnect(token);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] エラー:', error);
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketNotification = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (e) {
            console.error('[WebSocket] メッセージパースエラー:', e);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * WebSocket切断
   */
  disconnect(): void {
    this.options.autoReconnect = false;
    this.stopPing();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'クライアントによる切断');
      this.ws = null;
    }

    console.log('[WebSocket] 切断完了');
  }

  /**
   * 接続状態を確認
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * イベントハンドラを登録
   */
  on<T = unknown>(type: NotificationType, handler: WebSocketEventHandler<T>): () => void {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, new Set());
    }
    this.eventHandlers.get(type)!.add(handler as WebSocketEventHandler);

    // 登録解除関数を返す
    return () => {
      const handlers = this.eventHandlers.get(type);
      if (handlers) {
        handlers.delete(handler as WebSocketEventHandler);
      }
    };
  }

  /**
   * イベントハンドラを解除
   */
  off<T = unknown>(type: NotificationType, handler: WebSocketEventHandler<T>): void {
    const handlers = this.eventHandlers.get(type);
    if (handlers) {
      handlers.delete(handler as WebSocketEventHandler);
    }
  }

  /**
   * すべてのイベントハンドラを解除
   */
  offAll(): void {
    this.eventHandlers.clear();
  }

  /**
   * メッセージを送信
   */
  send(message: Record<string, unknown>): void {
    if (!this.isConnected()) {
      console.warn('[WebSocket] 接続されていません');
      return;
    }

    this.ws!.send(JSON.stringify(message));
  }

  /**
   * メッセージ処理
   */
  private handleMessage(message: WebSocketNotification): void {
    const { type, payload } = message;

    // pong応答は無視
    if (type === 'pong') {
      return;
    }

    console.log('[WebSocket] 受信:', type, payload);

    // 登録されたハンドラを呼び出し
    const handlers = this.eventHandlers.get(type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(payload);
        } catch (e) {
          console.error('[WebSocket] ハンドラエラー:', e);
        }
      });
    }

    // ワイルドカードハンドラ（すべてのイベント）
    const allHandlers = this.eventHandlers.get('*' as NotificationType);
    if (allHandlers) {
      allHandlers.forEach((handler) => {
        try {
          handler(message);
        } catch (e) {
          console.error('[WebSocket] ワイルドカードハンドラエラー:', e);
        }
      });
    }
  }

  /**
   * 再接続スケジュール
   */
  private scheduleReconnect(token: string): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('[WebSocket] 最大再接続試行回数に達しました');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.options.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);

    console.log(`[WebSocket] ${delay}ms後に再接続 (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect(token).catch(() => {
        // 再接続失敗時はoncloseで再試行される
      });
    }, delay);
  }

  /**
   * Ping開始
   */
  private startPing(): void {
    this.pingTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, this.options.pingInterval);
  }

  /**
   * Ping停止
   */
  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }
}

// シングルトンインスタンス
let wsClient: WebSocketClient | null = null;

/**
 * WebSocketクライアントを取得
 */
export function getWebSocketClient(): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient();
  }
  return wsClient;
}

/**
 * WebSocket接続を開始
 */
export async function connectWebSocket(): Promise<void> {
  const token = localStorage.getItem('access_token');
  if (!token) {
    console.warn('[WebSocket] トークンがありません');
    return;
  }

  const client = getWebSocketClient();
  if (!client.isConnected()) {
    await client.connect(token);
  }
}

/**
 * WebSocket接続を切断
 */
export function disconnectWebSocket(): void {
  if (wsClient) {
    wsClient.disconnect();
  }
}

export default getWebSocketClient;
