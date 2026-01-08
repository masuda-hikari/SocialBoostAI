/**
 * ダッシュボードページ
 */
import { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { getAnalyses, getPlanLimits, type PlanLimits } from '../api';
import type { Analysis } from '../types';
import {
  BarChart3,
  TrendingUp,
  FileText,
  Zap,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [recentAnalyses, setRecentAnalyses] = useState<Analysis[]>([]);
  const [limits, setLimits] = useState<PlanLimits | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analysesRes, limitsRes] = await Promise.all([
          getAnalyses(1, 5),
          getPlanLimits(),
        ]);
        setRecentAnalyses(analysesRes.items);
        setLimits(limitsRes);
      } catch (error) {
        console.error('データ取得エラー:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
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

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          おかえりなさい、{user?.username}さん
        </h1>
        <p className="text-gray-600">ソーシャルメディアのパフォーマンスを確認しましょう</p>
      </div>

      {/* 統計カード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-primary-100 rounded-lg">
              <BarChart3 className="text-primary-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">分析数</p>
              <p className="text-2xl font-bold text-gray-900">{recentAnalyses.length}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="text-green-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">エンゲージメント率</p>
              <p className="text-2xl font-bold text-gray-900">
                {recentAnalyses[0]?.summary.engagement_rate.toFixed(2) || '0.00'}%
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FileText className="text-blue-600" size={24} />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">総投稿数</p>
              <p className="text-2xl font-bold text-gray-900">
                {recentAnalyses.reduce((sum, a) => sum + a.summary.total_posts, 0)}
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

      {/* 最近の分析 */}
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
                {recentAnalyses.map((analysis) => (
                  <tr key={analysis.id} className="border-b last:border-0">
                    <td className="py-3">
                      <span className="capitalize">{analysis.platform}</span>
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
                ))}
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
              <Zap className="text-purple-600" size={24} />
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
