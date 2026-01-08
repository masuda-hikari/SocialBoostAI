/**
 * API型定義
 */

// 認証関連
export type UserRole = 'free' | 'pro' | 'business' | 'enterprise';

export interface User {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  created_at: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

// 分析関連
export interface AnalysisSummary {
  total_posts: number;
  total_likes: number;
  total_retweets: number;
  engagement_rate: number;
  best_hour: number | null;
  top_hashtags: string[];
}

export interface Analysis {
  id: string;
  user_id: string;
  platform: string;
  period_start: string;
  period_end: string;
  summary: AnalysisSummary;
  created_at: string;
}

export interface AnalysisRequest {
  platform?: string;
  period_days?: number;
}

// レポート関連
export type ReportType = 'weekly' | 'monthly' | 'custom';

export interface Report {
  id: string;
  user_id: string;
  report_type: ReportType;
  platform: string;
  period_start: string;
  period_end: string;
  html_url: string | null;
  created_at: string;
}

export interface ReportRequest {
  report_type: ReportType;
  platform?: string;
  start_date?: string;
  end_date?: string;
}

// 課金関連
export type PlanTier = 'free' | 'pro' | 'business' | 'enterprise';

export interface PlanInfo {
  tier: PlanTier;
  name: string;
  price_monthly: number;
  api_calls_per_day: number;
  reports_per_month: number;
  platforms: number;
  history_days: number;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan: PlanTier;
  status: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at: string | null;
  created_at: string;
}

export interface CheckoutSessionRequest {
  plan: PlanTier;
  success_url: string;
  cancel_url: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
}

// エラーレスポンス
export interface ErrorResponse {
  error: string;
  detail: string | null;
  code: string;
}

// ページネーション
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// ユーザー統計
export interface UserStats {
  total_analyses: number;
  total_reports: number;
  api_calls_today: number;
  api_calls_limit: number;
}

// Instagram分析関連
export interface InstagramAnalysisSummary {
  total_posts: number;
  total_reels: number;
  total_likes: number;
  total_comments: number;
  total_saves: number;
  engagement_rate: number;
  best_hour: number | null;
  top_hashtags: string[];
}

export interface InstagramContentPattern {
  pattern_type: string;
  count: number;
  avg_engagement: number;
}

export interface InstagramAnalysis {
  id: string;
  user_id: string;
  platform: 'instagram';
  period_start: string;
  period_end: string;
  summary: InstagramAnalysisSummary;
  created_at: string;
  // 詳細情報（詳細取得時のみ）
  hourly_breakdown?: Array<{
    hour: number;
    avg_likes: number;
    post_count: number;
  }>;
  content_patterns?: InstagramContentPattern[];
  recommendations?: {
    best_hours: number[];
    suggested_hashtags: string[];
    reasoning: string;
  };
}

export interface InstagramAnalysisRequest {
  period_days?: number;
}

// =============================================================================
// クロスプラットフォーム比較関連（v1.2）
// =============================================================================

export interface PlatformPerformanceSummary {
  platform: string;
  total_posts: number;
  total_engagement: number;
  avg_engagement_rate: number;
  avg_likes_per_post: number;
  avg_comments_per_post: number;
  avg_shares_per_post: number;
  best_hour: number | null;
  top_hashtags: string[];
}

export interface ComparisonItem {
  metric_name: string;
  twitter_value: number | null;
  instagram_value: number | null;
  difference_percent: number | null;
  winner: 'twitter' | 'instagram' | 'tie' | null;
  insight: string;
}

export interface CrossPlatformComparison {
  id: string;
  user_id: string;
  period_start: string;
  period_end: string;
  platforms_analyzed: string[];
  twitter_performance: PlatformPerformanceSummary | null;
  instagram_performance: PlatformPerformanceSummary | null;
  comparison_items: ComparisonItem[];
  overall_winner: 'twitter' | 'instagram' | 'tie' | null;
  cross_platform_insights: string[];
  strategic_recommendations: string[];
  synergy_opportunities: string[];
  created_at: string;
}

export interface CrossPlatformComparisonSummary {
  id: string;
  user_id: string;
  period_start: string;
  period_end: string;
  platforms: string[];
  total_posts: number;
  total_engagement: number;
  best_platform: string | null;
  key_insight: string;
  created_at: string;
}

export interface CrossPlatformComparisonRequest {
  twitter_analysis_id?: string;
  instagram_analysis_id?: string;
  period_days?: number;
}

// =============================================================================
// TikTok分析関連（v1.3）
// =============================================================================

export interface TikTokAnalysisSummary {
  total_videos: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  engagement_rate: number;
  view_to_like_ratio: number;
  avg_views_per_video: number;
  best_hour: number | null;
  best_duration_range: string | null;
  top_hashtags: string[];
}

export interface TikTokSoundInfo {
  sound_id: string;
  sound_name: string;
  usage_count: number;
  avg_engagement: number;
  is_trending: boolean;
}

export interface TikTokContentPattern {
  pattern_type: string;
  count: number;
  avg_engagement: number;
}

export interface TikTokAnalysis {
  id: string;
  user_id: string;
  platform: 'tiktok';
  period_start: string;
  period_end: string;
  summary: TikTokAnalysisSummary;
  created_at: string;
  // 詳細情報（詳細取得時のみ）
  hourly_breakdown?: Array<{
    hour: number;
    avg_likes: number;
    avg_views: number;
    post_count: number;
  }>;
  content_patterns?: TikTokContentPattern[];
  sound_analysis?: TikTokSoundInfo[];
  recommendations?: {
    best_hours: number[];
    suggested_hashtags: string[];
    best_duration: string;
    trending_sounds: string[];
    reasoning: string;
  };
  avg_video_duration?: number;
  duet_performance?: number | null;
  stitch_performance?: number | null;
}

export interface TikTokAnalysisRequest {
  period_days?: number;
}

// =============================================================================
// YouTube分析関連（v1.4）
// =============================================================================

export interface YouTubeAnalysisSummary {
  total_videos: number;
  total_shorts: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  engagement_rate: number;
  view_to_like_ratio: number;
  avg_views_per_video: number;
  best_hour: number | null;
  best_duration_range: string | null;
  top_tags: string[];
}

export interface YouTubeTagInfo {
  tag: string;
  usage_count: number;
  total_views: number;
  avg_engagement: number;
  effectiveness_score: number;
}

export interface YouTubeCategoryInfo {
  category_id: string;
  category_name: string;
  video_count: number;
  total_views: number;
  avg_engagement: number;
}

export interface YouTubeContentPattern {
  pattern_type: string;
  count: number;
  avg_engagement: number;
}

export interface YouTubeShortsVsVideo {
  shorts_count: number;
  shorts_avg_views: number;
  shorts_avg_engagement: number;
  regular_count: number;
  regular_avg_views: number;
  regular_avg_engagement: number;
  views_ratio: number;
  engagement_ratio: number;
}

export interface YouTubeAnalysis {
  id: string;
  user_id: string;
  platform: 'youtube';
  period_start: string;
  period_end: string;
  summary: YouTubeAnalysisSummary;
  created_at: string;
  // 詳細情報（詳細取得時のみ）
  hourly_breakdown?: Array<{
    hour: number;
    avg_likes: number;
    avg_views: number;
    post_count: number;
  }>;
  content_patterns?: YouTubeContentPattern[];
  tag_analysis?: YouTubeTagInfo[];
  category_analysis?: YouTubeCategoryInfo[];
  recommendations?: {
    best_hours: number[];
    suggested_hashtags: string[];
    best_duration: string;
    shorts_recommendation: string;
    reasoning: string;
  };
  avg_video_duration?: number;
  shorts_vs_video?: YouTubeShortsVsVideo | null;
}

export interface YouTubeAnalysisRequest {
  period_days?: number;
}
