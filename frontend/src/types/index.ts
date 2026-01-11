/**
 * API型定義
 */

// 認証関連
export type UserRole = 'free' | 'pro' | 'business' | 'enterprise' | 'admin';

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

// =============================================================================
// LinkedIn分析関連（v1.5）
// =============================================================================

export interface LinkedInAnalysisSummary {
  total_posts: number;
  total_articles: number;
  total_impressions: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_clicks: number;
  engagement_rate: number;
  click_through_rate: number;
  virality_rate: number;
  avg_likes_per_post: number;
  best_hour: number | null;
  best_days: string[];
  top_hashtags: string[];
}

export interface LinkedInContentPattern {
  pattern_type: string;
  count: number;
  avg_engagement: number;
}

export interface LinkedInDailyBreakdown {
  weekday: number;
  weekday_name: string;
  avg_likes: number;
  avg_shares: number;
  avg_comments: number;
  avg_clicks: number;
  avg_impressions: number;
  post_count: number;
  total_engagement: number;
}

export interface LinkedInMediaTypePerformance {
  media_type: string;
  avg_engagement: number;
}

export interface LinkedInAnalysis {
  id: string;
  user_id: string;
  platform: 'linkedin';
  period_start: string;
  period_end: string;
  summary: LinkedInAnalysisSummary;
  created_at: string;
  // 詳細情報（詳細取得時のみ）
  hourly_breakdown?: Array<{
    hour: number;
    avg_likes: number;
    avg_shares: number;
    post_count: number;
  }>;
  daily_breakdown?: LinkedInDailyBreakdown[];
  content_patterns?: LinkedInContentPattern[];
  recommendations?: {
    best_hours: number[];
    best_days: string[];
    suggested_hashtags: string[];
    best_media_type: string;
    best_post_length: string;
    reasoning: string;
  };
  avg_post_length?: number;
  media_type_performance?: LinkedInMediaTypePerformance[];
}

export interface LinkedInAnalysisRequest {
  period_days?: number;
}

// =============================================================================
// AIコンテンツ生成関連（v1.6）
// =============================================================================

export type ContentPlatform = 'twitter' | 'instagram' | 'tiktok' | 'youtube' | 'linkedin';
export type ContentType = 'post' | 'thread' | 'story' | 'reel' | 'video' | 'article' | 'caption';
export type ContentTone = 'professional' | 'casual' | 'humorous' | 'educational' | 'inspirational' | 'promotional';
export type ContentGoal = 'engagement' | 'awareness' | 'conversion' | 'traffic' | 'community';

export interface ContentGenerationRequest {
  platform: ContentPlatform;
  content_type?: ContentType;
  topic?: string;
  keywords?: string[];
  tone?: ContentTone;
  goal?: ContentGoal;
  reference_content?: string;
  target_audience?: string;
  include_hashtags?: boolean;
  include_cta?: boolean;
  max_length?: number;
}

export interface GeneratedContent {
  id: string;
  platform: ContentPlatform;
  content_type: ContentType;
  main_text: string;
  hashtags: string[];
  call_to_action: string | null;
  media_suggestion: string | null;
  estimated_engagement: string | null;
  created_at: string;
}

export interface ContentRewriteRequest {
  original_content: string;
  source_platform: ContentPlatform;
  target_platform: ContentPlatform;
  preserve_hashtags?: boolean;
  tone?: ContentTone;
}

export interface ABTestVariationRequest {
  base_topic: string;
  platform: ContentPlatform;
  variation_count?: number;
  tone?: ContentTone;
}

export interface ContentVariation {
  version: string;
  text: string;
  hashtags: string[];
  focus: string;
}

export interface ABTestResponse {
  id: string;
  topic: string;
  platform: ContentPlatform;
  variations: ContentVariation[];
  created_at: string;
}

export interface ContentCalendarRequest {
  platforms: ContentPlatform[];
  days?: number;
  posts_per_day?: number;
  topics?: string[];
  tone?: ContentTone;
  goal?: ContentGoal;
}

export interface ContentCalendarItem {
  scheduled_date: string;
  platform: ContentPlatform;
  content_type: ContentType;
  topic: string;
  draft_content: string;
  hashtags: string[];
  optimal_time: string;
  rationale: string;
}

export interface ContentCalendarResponse {
  id: string;
  user_id: string;
  period_start: string;
  period_end: string;
  total_items: number;
  items: ContentCalendarItem[];
  created_at: string;
}

export interface TrendingContentRequest {
  platform: ContentPlatform;
  trend_keywords: string[];
  brand_context?: string;
  tone?: ContentTone;
}

export interface TrendingContentResponse {
  id: string;
  platform: ContentPlatform;
  trend_keywords: string[];
  contents: GeneratedContent[];
  created_at: string;
}

export interface ContentGenerationSummary {
  id: string;
  user_id: string;
  platform: ContentPlatform;
  content_type: string;
  preview: string;
  created_at: string;
}

// =============================================================================
// スケジュール投稿関連（v2.3）
// =============================================================================

export type ScheduledPostStatus = 'pending' | 'published' | 'failed' | 'cancelled';
export type ScheduledPostMediaType = 'image' | 'video' | 'none';

export interface ScheduledPostCreate {
  platform: ContentPlatform;
  content: string;
  hashtags?: string[];
  media_urls?: string[];
  media_type?: ScheduledPostMediaType;
  scheduled_at: string;
  timezone?: string;
  metadata?: Record<string, unknown>;
}

export interface ScheduledPostUpdate {
  content?: string;
  hashtags?: string[];
  media_urls?: string[];
  media_type?: ScheduledPostMediaType;
  scheduled_at?: string;
  timezone?: string;
  metadata?: Record<string, unknown>;
}

export interface ScheduledPost {
  id: string;
  user_id: string;
  platform: ContentPlatform;
  content: string;
  hashtags: string[];
  media_urls: string[];
  media_type: ScheduledPostMediaType | null;
  scheduled_at: string;
  timezone: string;
  status: ScheduledPostStatus;
  published_at: string | null;
  error_message: string | null;
  retry_count: number;
  external_post_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledPostSummary {
  id: string;
  platform: ContentPlatform;
  content_preview: string;
  scheduled_at: string;
  status: ScheduledPostStatus;
  created_at: string;
}

export interface ScheduledPostListResponse {
  items: ScheduledPostSummary[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface BulkScheduleRequest {
  posts: ScheduledPostCreate[];
}

export interface BulkScheduleResponse {
  created: number;
  failed: number;
  scheduled_posts: ScheduledPost[];
  errors: string[];
}

export interface ScheduleStats {
  total_scheduled: number;
  pending: number;
  published: number;
  failed: number;
  cancelled: number;
  upcoming_24h: number;
  by_platform: Record<string, number>;
  by_status: Record<string, number>;
}

// =============================================================================
// 管理者機能関連（v2.5）
// =============================================================================

export type AdminUserRole = 'free' | 'pro' | 'business' | 'enterprise' | 'admin';

export interface AdminUserSummary {
  id: string;
  email: string;
  username: string;
  role: AdminUserRole;
  is_active: boolean;
  created_at: string;
  analysis_count: number;
  report_count: number;
  scheduled_post_count: number;
}

export interface AdminUserListResponse {
  users: AdminUserSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface AdminUserDetail {
  id: string;
  email: string;
  username: string;
  role: AdminUserRole;
  is_active: boolean;
  stripe_customer_id: string | null;
  created_at: string;
  updated_at: string;
  analysis_count: number;
  report_count: number;
  scheduled_post_count: number;
  subscription: {
    id: string;
    plan: string;
    status: string;
    current_period_start: string;
    current_period_end: string;
    cancel_at_period_end: boolean;
  } | null;
}

export interface AdminUserUpdateRequest {
  username?: string;
  role?: AdminUserRole;
  is_active?: boolean;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  users_by_plan: Record<string, number>;
  total_analyses: number;
  total_reports: number;
  total_scheduled_posts: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
}

export interface RevenueStats {
  active_subscriptions: number;
  subscriptions_by_plan: Record<string, number>;
  monthly_recurring_revenue_jpy: number;
  churn_rate: number;
}

export interface ActivityLogEntry {
  type: string;
  user_id: string;
  username: string;
  description: string;
  timestamp: string;
}

export interface ActivityLogResponse {
  entries: ActivityLogEntry[];
  total: number;
}
