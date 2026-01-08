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
