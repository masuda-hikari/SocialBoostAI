/**
 * ダッシュボードページ（リアルタイム対応）
 */
import { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useNotificationStore } from '../stores/notificationStore';
import {
  getAnalyses,
  getPlanLimits,
  getRealtimeDashboard,
  getPlatformComparison,
  type PlanLimits,
  type RealtimeDashboard,
  type PlatformComparisonResponse,
  type PlatformMetrics,
} from '../api';
import type { Analysis } from '../types';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  FileText,
  Zap,
  ArrowRight,
  RefreshCw,
  Clock,
  Hash,
  Activity,
  Wifi,
  WifiOff,
  Crown,
} from 'lucide-react';
import { Link } from 'react-router-dom';

// プラットフォームカラー
const platformColors: Record<string, { bg: string; text: string; border: string }> = {
  twitter: { bg: 'bg-sky-100', text: 'text-sky-600', border: 'border-sky-200' },
  instagram: { bg: 'bg-pink-100', text: 'text-pink-600', border: 'border-pink-200' },
  tiktok: { bg: 'bg-cyan-100', text: 'text-cyan-600', border: 'border-cyan-200' },
  youtube: { bg: 'bg-red-100', text: 'text-red-600', border: 'border-red-200' },
  linkedin: { bg: 'bg-blue-100', text: 'text-blue-600', border: 'border-blue-200' },
};

// プラットフォームアイコン（絵文字）
const platformIcons: Record<string, string> = {
  twitter: '𝕏',
  instagram: '📷',
  tiktok: '🎵',
  youtube: '▶️',
  linkedin: '💼',
};

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { isConnected, progressStates } = useNotificationStore();
  const [recentAnalyses, setRecentAnalyses] = useState<Analysis[]>([]);
  const [limits, setLimits] = useState<PlanLimits | null>(null);
  const [dashboard, setDashboard] = useState<RealtimeDashboard | null>(null);
  const [, setComparison] = useState<PlatformComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchData = async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    setIsRefreshing(!showLoading);
    try {
      const [analysesRes, limitsRes, dashboardRes] = await Promise.all([
        getAnalyses(1, 5),
        getPlanLimits(),
        getRealtimeDashboard(7).catch(() => null),
      ]);
      setRecentAnalyses(analysesRes.items);
      setLimits(limitsRes);
      if (dashboardRes) setDashboard(dashboardRes);

      // Businessプラン以上ならプラットフォーム比較も取得
      if (user?.role === 'business' || user?.role === 'enterprise') {
        const comparisonRes = await getPlatformComparison(30).catch(() => null);
        if (comparisonRes) setComparison(comparisonRes);
      }

      setLastUpdated(new Date());
    } catch (error) {
      console.error('データ取得エラー:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // 60秒ごとに自動更新
    const interval = setInterval(() => fetchData(false), 60000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const apiUsagePercent = limits
    ? Math.round((limits.api_calls_used_today / limits.api_calls_per_day) * 100)
    : 0;

  // 週間比較の変化
  const weekChange = dashboard?.week_over_week;
  const isPositiveChange = weekChange && weekChange.change_percent > 0;

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            おかえりなさい、{user?.username}さん
          </h1>
          <p className="text-gray-600">ソーシャルメディアのパフォーマンスを確認しましょう</p>
        </div>
        <div className="flex items-center gap-4">
          {/* 接続状態 */}
          <div className="flex items-center gap-2 text-sm">
            {isConnected ? (
              <span className="flex items-center gap-1 text-green-600">
                <Wifi size={16} />
                リアルタイム接続中
              </span>
            ) : (
              <span className="flex items-center gap-1 text-gray-400">
                <WifiOff size={16} />
                オフライン
              </span>
            )}
          </div>
          {/* 更新ボタン */}
          <button
            onClick={() => fetchData(false)}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
            更新
          </button>
          {/* 最終更新 */}
          <span className="text-xs text-gray-400">
            {lastUpdated.toLocaleTimeString('ja-JP')}
          </span>
        </div>
      </div>

      {/* 進捗中の分析がある場合 */}
      {progressStates.size > 0 && (
        <div className="bg-primary-50 border border-primary-200 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <Activity size={20} className="text-primary-600 animate-pulse" />
            <span className="font-medium text-primary-900">分析を実行中...</span>
          </div>
          {Array.from(progressStates.values()).map((progress) => (
            <div key={progress.analysisId} className="ml-8">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-primary-700">{progress.status}</span>
                <span className="text-sm font-medium text-primary-600">{progress.progress}%</span>
              </div>
              <div className="w-full bg-primary-200 rounded-full h-2">
                <div
                  className="bg-primary-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${progress.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* メイン統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-primary-100 rounded-lg">
              <BarChart3 className="text-primary-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">総分析数</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboard?.total_analyses ?? recentAnalyses.length}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="text-green-600" size={24} />
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm text-gray-500">平均エンゲージメント率</p>
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-bold text-gray-900">
                  {recentAnalyses[0]?.summary.engagement_rate.toFixed(2) || '0.00'}%
                </p>
                {weekChange && (
                  <span
                    className={`text-xs font-medium flex items-center ${
                      isPositiveChange ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {isPositiveChange ? (
                      <TrendingUp size={12} className="mr-0.5" />
                    ) : (
                      <TrendingDown size={12} className="mr-0.5" />
                    )}
                    {weekChange.change_percent > 0 ? '+' : ''}
                    {weekChange.change_percent.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="text-blue-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">総レポート数</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboard?.total_reports ?? 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Zap className="text-purple-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">API使用量</p>
              <p className="text-2xl font-bold text-gray-900">{apiUsagePercent}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* プラットフォーム別メトリクス */}
      {dashboard && dashboard.platforms.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">プラットフォーム別パフォーマンス</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboard.platforms.map((platform: PlatformMetrics) => {
              const colors = platformColors[platform.platform] || platformColors.twitter;
              const icon = platformIcons[platform.platform] || '📊';
              return (
                <div
                  key={platform.platform}
                  className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">{icon}</span>
                    <span className={`font-medium capitalize ${colors.text}`}>
                      {platform.platform}
                    </span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">投稿数</span>
                      <span className="font-medium">{platform.total_posts}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">いいね</span>
                      <span className="font-medium">{platform.total_likes.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">エンゲージメント率</span>
                      <span className={`font-medium ${colors.text}`}>
                        {platform.engagement_rate.toFixed(2)}%
                      </span>
                    </div>
                    {platform.last_analysis && (
                      <div className="text-xs text-gray-400 mt-2">
                        最終分析: {new Date(platform.last_analysis).toLocaleDateString('ja-JP')}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* トレンドハッシュタグ & 最適投稿時間 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* トレンドハッシュタグ */}
        {dashboard && dashboard.trending_hashtags.length > 0 && (
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Hash size={20} className="text-primary-600" />
              <h3 className="text-lg font-medium text-gray-900">トレンドハッシュタグ</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {dashboard.trending_hashtags.slice(0, 10).map((tag, index) => (
                <span
                  key={tag.tag}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium ${
                    index < 3
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  #{tag.tag}
                  <span className="ml-1 text-xs opacity-70">({tag.count})</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 最適投稿時間 */}
        {dashboard && Object.keys(dashboard.best_posting_times).length > 0 && (
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={20} className="text-green-600" />
              <h3 className="text-lg font-medium text-gray-900">最適投稿時間</h3>
            </div>
            <div className="space-y-3">
              {Object.entries(dashboard.best_posting_times).map(([platform, hours]) => {
                const colors = platformColors[platform] || platformColors.twitter;
                const icon = platformIcons[platform] || '📊';
                return (
                  <div key={platform} className="flex items-center gap-3">
                    <span className="text-lg">{icon}</span>
                    <span className={`font-medium capitalize ${colors.text} w-24`}>
                      {platform}
                    </span>
                    <div className="flex gap-1">
                      {(hours as number[]).slice(0, 3).map((hour) => (
                        <span
                          key={hour}
                          className={`px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}
                        >
                          {hour}:00
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* API使用量バー */}
      {limits && (
        <div className="card">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-medium text-gray-900">API使用量（今日）</h3>
            <span className="text-sm text-gray-500">
              {limits.api_calls_used_today} / {limits.api_calls_per_day} 回
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${
                apiUsagePercent > 80
                  ? 'bg-red-500'
                  : apiUsagePercent > 50
                  ? 'bg-yellow-500'
                  : 'bg-primary-500'
              }`}
              style={{ width: `${Math.min(apiUsagePercent, 100)}%` }}
            />
          </div>
          {user?.role === 'free' && (
            <p className="mt-2 text-sm text-gray-500">
              <Link to="/billing" className="text-primary-600 hover:underline">
                プランをアップグレード
              </Link>
              して、より多くの分析を実行しましょう
            </p>
          )}
        </div>
      )}

      {/* 最近のアクティビティ */}
      {dashboard && dashboard.recent_activity.length > 0 && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">最近のアクティビティ</h3>
          </div>
          <div className="space-y-3">
            {dashboard.recent_activity.slice(0, 5).map((activity) => {
              const colors = platformColors[activity.platform] || platformColors.twitter;
              const icon = platformIcons[activity.platform] || '📊';
              return (
                <div
                  key={activity.id}
                  className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
                >
                  <span className="text-xl">{icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text}`}
                      >
                        {activity.type === 'analysis' ? '分析' : 'レポート'}
                      </span>
                      <span className="text-sm font-medium capitalize">{activity.platform}</span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {new Date(activity.created_at).toLocaleString('ja-JP')}
                    </span>
                  </div>
                  <Link
                    to={activity.type === 'analysis' ? '/analysis' : '/reports'}
                    className="text-primary-600 hover:text-primary-700"
                  >
                    <ArrowRight size={16} />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 最近の分析（従来のテーブル） */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">最近の分析</h3>
          <Link
            to="/analysis"
            className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center"
          >
            すべて見る
            <ArrowRight size={16} className="ml-1" />
          </Link>
        </div>

        {recentAnalyses.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <BarChart3 size={48} className="mx-auto mb-4 opacity-50" />
            <p>まだ分析がありません</p>
            <Link to="/analysis" className="btn-primary mt-4 inline-block">
              最初の分析を作成
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-gray-500 border-b">
                  <th className="pb-3 font-medium">プラットフォーム</th>
                  <th className="pb-3 font-medium">期間</th>
                  <th className="pb-3 font-medium">投稿数</th>
                  <th className="pb-3 font-medium">エンゲージメント率</th>
                  <th className="pb-3 font-medium">作成日</th>
                </tr>
              </thead>
              <tbody>
                {recentAnalyses.map((analysis) => {
                  const icon = platformIcons[analysis.platform] || '📊';
                  return (
                    <tr key={analysis.id} className="border-b last:border-0">
                      <td className="py-3">
                        <span className="flex items-center gap-2">
                          <span>{icon}</span>
                          <span className="capitalize">{analysis.platform}</span>
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-500">
                        {new Date(analysis.period_start).toLocaleDateString('ja-JP')} -{' '}
                        {new Date(analysis.period_end).toLocaleDateString('ja-JP')}
                      </td>
                      <td className="py-3">{analysis.summary.total_posts}</td>
                      <td className="py-3">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            analysis.summary.engagement_rate > 5
                              ? 'bg-green-100 text-green-700'
                              : analysis.summary.engagement_rate > 2
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {analysis.summary.engagement_rate.toFixed(2)}%
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-500">
                        {new Date(analysis.created_at).toLocaleDateString('ja-JP')}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* クイックアクション */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/analysis"
          className="card hover:shadow-lg transition-shadow cursor-pointer group"
        >
          <div className="flex items-center">
            <div className="p-3 bg-primary-100 rounded-lg group-hover:bg-primary-200 transition-colors">
              <BarChart3 className="text-primary-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="font-medium text-gray-900">新規分析</p>
              <p className="text-sm text-gray-500">パフォーマンスを分析</p>
            </div>
          </div>
        </Link>

        <Link
          to="/reports"
          className="card hover:shadow-lg transition-shadow cursor-pointer group"
        >
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
              <FileText className="text-blue-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="font-medium text-gray-900">レポート作成</p>
              <p className="text-sm text-gray-500">週次/月次レポート</p>
            </div>
          </div>
        </Link>

        <Link
          to="/billing"
          className="card hover:shadow-lg transition-shadow cursor-pointer group"
        >
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
              <Crown className="text-purple-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="font-medium text-gray-900">プランを見る</p>
              <p className="text-sm text-gray-500">機能をアップグレード</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
