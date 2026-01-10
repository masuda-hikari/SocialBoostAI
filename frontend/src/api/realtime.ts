/**
 * リアルタイムダッシュボードAPI
 */
import apiClient from './client';

// プラットフォーム別メトリクス
export interface PlatformMetrics {
  platform: string;
  total_posts: number;
  total_likes: number;
  total_engagement: number;
  engagement_rate: number;
  last_analysis: string | null;
}

// トレンドハッシュタグ
export interface TrendingHashtag {
  tag: string;
  count: number;
  engagement_rate?: number;
}

// アクティビティ項目
export interface ActivityItem {
  type: 'analysis' | 'report';
  id: string;
  platform: string;
  created_at: string;
  summary: Record<string, unknown>;
}

// 週間比較
export interface WeekOverWeek {
  current: number;
  previous: number;
  change: number;
  change_percent: number;
}

// リアルタイムダッシュボードレスポンス
export interface RealtimeDashboard {
  user_id: string;
  timestamp: string;
  total_analyses: number;
  total_reports: number;
  platforms: PlatformMetrics[];
  trending_hashtags: TrendingHashtag[];
  recent_activity: ActivityItem[];
  best_posting_times: Record<string, number[]>;
  week_over_week: WeekOverWeek;
}

// ライブメトリクス
export interface LiveMetrics {
  timestamp: string;
  is_connected: boolean;
  metrics: {
    user_connections: number;
    total_connections: number;
  };
}

// プラットフォーム比較データ
export interface PlatformComparisonData {
  platform: string;
  analysis_count: number;
  total_posts: number;
  total_likes: number;
  total_engagement: number;
  engagement_rate: {
    average: number;
    min: number;
    max: number;
  };
}

export interface PlatformComparisonResponse {
  period_days: number;
  platforms: PlatformComparisonData[];
  winner: string | null;
  timestamp: string;
}

/**
 * リアルタイムダッシュボードを取得
 *
 * @param days 集計日数（デフォルト: 7）
 * @returns ダッシュボードデータ
 */
export async function getRealtimeDashboard(days: number = 7): Promise<RealtimeDashboard> {
  const response = await apiClient.get<RealtimeDashboard>('/api/v1/realtime/dashboard', {
    params: { days },
  });
  return response.data;
}

/**
 * ライブメトリクスを取得
 *
 * @returns ライブメトリクス
 */
export async function getLiveMetrics(): Promise<LiveMetrics> {
  const response = await apiClient.get<LiveMetrics>('/api/v1/realtime/live-metrics');
  return response.data;
}

/**
 * 最近のアクティビティを取得
 *
 * @param limit 取得件数（デフォルト: 20）
 * @param activityType フィルタ（analysis または report）
 * @returns アクティビティリスト
 */
export async function getRecentActivity(
  limit: number = 20,
  activityType?: 'analysis' | 'report'
): Promise<ActivityItem[]> {
  const response = await apiClient.get<ActivityItem[]>('/api/v1/realtime/activity', {
    params: {
      limit,
      activity_type: activityType,
    },
  });
  return response.data;
}

/**
 * プラットフォーム比較を取得
 *
 * @param days 集計日数（デフォルト: 30）
 * @returns プラットフォーム比較データ
 */
export async function getPlatformComparison(days: number = 30): Promise<PlatformComparisonResponse> {
  const response = await apiClient.get<PlatformComparisonResponse>('/api/v1/realtime/platform-comparison', {
    params: { days },
  });
  return response.data;
}
