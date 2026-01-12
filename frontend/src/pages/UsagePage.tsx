/**
 * 使用量モニタリングページ
 */

import { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowUp,
  BarChart3,
  Clock,
  Gauge,
  RefreshCw,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getUsageDashboard, getUsageHistory } from '../api/usage';

// プラン別の表示名
const PLAN_NAMES: Record<string, string> = {
  free: 'Free',
  pro: 'Pro',
  business: 'Business',
  enterprise: 'Enterprise',
};

// 使用量タイプの表示名
const USAGE_TYPE_NAMES: Record<string, string> = {
  api_calls: 'API呼び出し',
  analyses: '分析実行',
  reports: 'レポート生成',
  scheduled_posts: 'スケジュール投稿',
  ai_generations: 'AI生成',
};

export default function UsagePage() {
  const [historyDays, setHistoryDays] = useState(7);

  // 使用量ダッシュボード取得
  const {
    data: dashboard,
    isLoading: isDashboardLoading,
    refetch: refetchDashboard,
  } = useQuery({
    queryKey: ['usageDashboard'],
    queryFn: getUsageDashboard,
    refetchInterval: 60000, // 1分ごとに更新
  });

  // 使用量履歴取得
  const { data: history, isLoading: isHistoryLoading } = useQuery({
    queryKey: ['usageHistory', historyDays],
    queryFn: () => getUsageHistory(historyDays),
  });

  const isLoading = isDashboardLoading || isHistoryLoading;

  // 使用率のプログレスバーの色を決定
  const getUsageColor = (percent: number): string => {
    if (percent < 0) return 'bg-gray-400'; // 無制限
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Gauge className="w-7 h-7 text-indigo-600" />
          使用量モニタリング
        </h1>
        <button
          onClick={() => refetchDashboard()}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          aria-label="更新"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          更新
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent" />
        </div>
      ) : dashboard ? (
        <>
          {/* プラン情報 & アップグレード推奨 */}
          <div className="mb-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 現在のプラン */}
            <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-indigo-100 text-sm">現在のプラン</p>
                  <p className="text-3xl font-bold mt-1">
                    {PLAN_NAMES[dashboard.current_plan] || dashboard.current_plan}
                  </p>
                </div>
                <Zap className="w-12 h-12 text-indigo-200" />
              </div>
            </div>

            {/* アップグレード推奨 */}
            {dashboard.upgrade_recommendation?.should_upgrade && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-6 h-6 text-amber-500 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-amber-800">
                      アップグレードをお勧めします
                    </p>
                    <p className="text-amber-700 text-sm mt-1">
                      {dashboard.upgrade_recommendation.reason}
                    </p>
                    {dashboard.upgrade_recommendation.recommended_plan && (
                      <button className="mt-3 px-4 py-2 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600 transition-colors">
                        {PLAN_NAMES[dashboard.upgrade_recommendation.recommended_plan]}
                        プランにアップグレード
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 今日の使用量 */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-600" />
              今日の使用量
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {Object.entries(dashboard.usage_with_limits.usage_percent).map(
                ([type, percent]) => (
                  <UsageCard
                    key={type}
                    label={USAGE_TYPE_NAMES[type] || type}
                    current={
                      type === 'api_calls'
                        ? dashboard.usage_with_limits.today.api_calls
                        : type === 'analyses'
                        ? dashboard.usage_with_limits.today.analyses_run
                        : type === 'reports'
                        ? dashboard.usage_with_limits.today.reports_generated
                        : type === 'scheduled_posts'
                        ? dashboard.usage_with_limits.today.scheduled_posts
                        : dashboard.usage_with_limits.today.ai_generations
                    }
                    limit={
                      type === 'api_calls'
                        ? dashboard.usage_with_limits.limits.api_calls_per_day
                        : type === 'analyses'
                        ? dashboard.usage_with_limits.limits.analyses_per_day
                        : type === 'reports'
                        ? dashboard.usage_with_limits.limits.reports_per_month
                        : type === 'scheduled_posts'
                        ? dashboard.usage_with_limits.limits.scheduled_posts_per_day
                        : dashboard.usage_with_limits.limits.ai_generations_per_day
                    }
                    remaining={dashboard.usage_with_limits.remaining[type]}
                    percent={percent}
                    getColor={getUsageColor}
                  />
                )
              )}
            </div>
          </div>

          {/* トレンド */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
              使用量トレンド（前週比）
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(dashboard.trend.trend_percent).map(
                ([type, percent]) => (
                  <TrendCard
                    key={type}
                    label={USAGE_TYPE_NAMES[type] || type}
                    trendPercent={percent}
                  />
                )
              )}
            </div>
          </div>

          {/* 使用量履歴 */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                使用量履歴
              </h2>
              <select
                value={historyDays}
                onChange={(e) => setHistoryDays(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                aria-label="表示期間"
              >
                <option value={7}>過去7日</option>
                <option value={14}>過去14日</option>
                <option value={30}>過去30日</option>
              </select>
            </div>
            {history && (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          日付
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          API呼び出し
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          分析
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          レポート
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          スケジュール
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          AI生成
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {history.daily_usage.map((day, index) => (
                        <tr
                          key={day.date}
                          className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                        >
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            {new Date(day.date).toLocaleDateString('ja-JP', {
                              month: 'short',
                              day: 'numeric',
                              weekday: 'short',
                            })}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 text-right">
                            {day.api_calls.toLocaleString()}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 text-right">
                            {day.analyses_run}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 text-right">
                            {day.reports_generated}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 text-right">
                            {day.scheduled_posts}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 text-right">
                            {day.ai_generations}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-gray-100">
                      <tr>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                          合計
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                          {history.total.api_calls.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                          {history.total.analyses_run}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                          {history.total.reports_generated}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                          {history.total.scheduled_posts}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                          {history.total.ai_generations}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* 月次サマリー */}
          {dashboard.monthly_summary && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-indigo-600" />
                今月のサマリー（{dashboard.monthly_summary.year_month}）
              </h2>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">API呼び出し</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboard.monthly_summary.total_api_calls.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">分析実行</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboard.monthly_summary.total_analyses}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">レポート生成</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboard.monthly_summary.total_reports}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">スケジュール投稿</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboard.monthly_summary.total_scheduled_posts}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">AI生成</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dashboard.monthly_summary.total_ai_generations}
                    </p>
                  </div>
                </div>
                {dashboard.monthly_summary.peak_date && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-sm text-gray-500">
                      ピーク日: {new Date(dashboard.monthly_summary.peak_date).toLocaleDateString('ja-JP')}
                      （{dashboard.monthly_summary.peak_daily_api_calls.toLocaleString()} API呼び出し）
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* プラットフォーム別使用量 */}
          {Object.keys(dashboard.usage_with_limits.today.platform_usage).length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                プラットフォーム別使用量
              </h2>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  {Object.entries(dashboard.usage_with_limits.today.platform_usage).map(
                    ([platform, count]) => (
                      <div key={platform} className="text-center">
                        <p className="text-sm text-gray-500 capitalize">{platform}</p>
                        <p className="text-2xl font-bold text-gray-900">{count}</p>
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-gray-500">
          使用量データの取得に失敗しました
        </div>
      )}
    </div>
  );
}

// 使用量カードコンポーネント
interface UsageCardProps {
  label: string;
  current: number;
  limit: number;
  remaining: number;
  percent: number;
  getColor: (percent: number) => string;
}

function UsageCard({
  label,
  current,
  limit,
  remaining,
  percent,
  getColor,
}: UsageCardProps) {
  const isUnlimited = limit < 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{current.toLocaleString()}</p>
      <p className="text-xs text-gray-400 mb-2">
        {isUnlimited ? '無制限' : `/ ${limit.toLocaleString()}`}
      </p>
      {!isUnlimited && (
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getColor(percent)} transition-all duration-300`}
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
        </div>
      )}
      <p className="text-xs text-gray-500 mt-1">
        残り: {isUnlimited ? '無制限' : remaining.toLocaleString()}
      </p>
    </div>
  );
}

// トレンドカードコンポーネント
interface TrendCardProps {
  label: string;
  trendPercent: number;
}

function TrendCard({ label, trendPercent }: TrendCardProps) {
  const isPositive = trendPercent > 0;
  const isNegative = trendPercent < 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <div className="flex items-center gap-2">
        {isPositive && <ArrowUp className="w-5 h-5 text-red-500" />}
        {isNegative && (
          <ArrowUp className="w-5 h-5 text-green-500 transform rotate-180" />
        )}
        <span
          className={`text-xl font-bold ${
            isPositive
              ? 'text-red-600'
              : isNegative
              ? 'text-green-600'
              : 'text-gray-600'
          }`}
        >
          {trendPercent > 0 ? '+' : ''}
          {trendPercent.toFixed(1)}%
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1">前週比</p>
    </div>
  );
}
