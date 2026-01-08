/**
 * クロスプラットフォーム比較ページ
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import {
  createComparison,
  getComparisons,
  getComparison,
  deleteComparison,
  getAnalyses,
  getInstagramAnalyses,
} from '../api';
import type {
  CrossPlatformComparison,
  CrossPlatformComparisonSummary,
  Analysis,
  InstagramAnalysis,
  UserRole,
} from '../types';

// Businessプラン以上で利用可能
const ALLOWED_ROLES: UserRole[] = ['business', 'enterprise'];

export default function ComparisonPage() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [comparisons, setComparisons] = useState<CrossPlatformComparisonSummary[]>([]);
  const [selectedComparison, setSelectedComparison] = useState<CrossPlatformComparison | null>(null);
  const [twitterAnalyses, setTwitterAnalyses] = useState<Analysis[]>([]);
  const [instagramAnalyses, setInstagramAnalyses] = useState<InstagramAnalysis[]>([]);
  const [selectedTwitterId, setSelectedTwitterId] = useState<string>('');
  const [selectedInstagramId, setSelectedInstagramId] = useState<string>('');
  const [periodDays, setPeriodDays] = useState(7);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canAccess = user && ALLOWED_ROLES.includes(user.role);

  // 比較履歴・分析データ取得
  useEffect(() => {
    if (!canAccess) return;

    const fetchData = async () => {
      try {
        const [comparisonsRes, twitterRes, instagramRes] = await Promise.all([
          getComparisons(),
          getAnalyses(),
          getInstagramAnalyses(),
        ]);
        setComparisons(comparisonsRes.items);
        setTwitterAnalyses(twitterRes.items);
        setInstagramAnalyses(instagramRes.items);
      } catch (err) {
        console.error('データ取得エラー:', err);
      }
    };

    fetchData();
  }, [canAccess]);

  // 比較を実行
  const handleRunComparison = async () => {
    if (!selectedTwitterId && !selectedInstagramId) {
      setError('少なくとも1つのプラットフォームの分析を選択してください');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await createComparison({
        twitter_analysis_id: selectedTwitterId || undefined,
        instagram_analysis_id: selectedInstagramId || undefined,
        period_days: periodDays,
      });
      setSelectedComparison(result);

      // 一覧を更新
      const comparisonsRes = await getComparisons();
      setComparisons(comparisonsRes.items);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '比較の実行に失敗しました';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 比較詳細を表示
  const handleViewComparison = async (id: string) => {
    setLoading(true);
    try {
      const result = await getComparison(id);
      setSelectedComparison(result);
    } catch (err) {
      console.error('比較取得エラー:', err);
    } finally {
      setLoading(false);
    }
  };

  // 比較を削除
  const handleDeleteComparison = async (id: string) => {
    if (!confirm('この比較を削除しますか？')) return;

    try {
      await deleteComparison(id);
      setComparisons(comparisons.filter((c) => c.id !== id));
      if (selectedComparison?.id === id) {
        setSelectedComparison(null);
      }
    } catch (err) {
      console.error('削除エラー:', err);
    }
  };

  // プラン制限表示
  if (!canAccess) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">🔒</div>
            <h1 className="text-2xl font-bold text-gray-800 mb-4">
              クロスプラットフォーム比較
            </h1>
            <p className="text-gray-600 mb-6">
              この機能は<span className="font-semibold text-blue-600">Businessプラン</span>以上で利用可能です。
            </p>
            <p className="text-gray-500 mb-8">
              Twitter/Instagramのパフォーマンスを比較し、
              <br />
              最適なプラットフォーム戦略を立案できます。
            </p>
            <button
              onClick={() => navigate('/billing')}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-700 transition-all"
            >
              プランをアップグレード
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">
            📊 クロスプラットフォーム比較
          </h1>
          <p className="text-gray-600 mt-2">
            Twitter/Instagramのパフォーマンスを比較し、最適な戦略を見つけましょう
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 新規比較パネル */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                新規比較を作成
              </h2>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-2 rounded mb-4">
                  {error}
                </div>
              )}

              {/* Twitter分析選択 */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Twitter分析
                </label>
                <select
                  value={selectedTwitterId}
                  onChange={(e) => setSelectedTwitterId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">選択してください</option>
                  {twitterAnalyses.map((a) => (
                    <option key={a.id} value={a.id}>
                      {new Date(a.created_at).toLocaleDateString()} - {a.summary.total_posts}投稿
                    </option>
                  ))}
                </select>
              </div>

              {/* Instagram分析選択 */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Instagram分析
                </label>
                <select
                  value={selectedInstagramId}
                  onChange={(e) => setSelectedInstagramId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                >
                  <option value="">選択してください</option>
                  {instagramAnalyses.map((a) => (
                    <option key={a.id} value={a.id}>
                      {new Date(a.created_at).toLocaleDateString()} - {a.summary.total_posts}投稿
                    </option>
                  ))}
                </select>
              </div>

              {/* 期間選択 */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  比較期間
                </label>
                <select
                  value={periodDays}
                  onChange={(e) => setPeriodDays(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value={7}>過去7日間</option>
                  <option value={30}>過去30日間</option>
                  <option value={90}>過去90日間</option>
                </select>
              </div>

              <button
                onClick={handleRunComparison}
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-white py-3 rounded-lg font-semibold hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 transition-all disabled:opacity-50"
              >
                {loading ? '比較中...' : '比較を実行'}
              </button>
            </div>

            {/* 比較履歴 */}
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                比較履歴
              </h2>
              {comparisons.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                  比較履歴はありません
                </p>
              ) : (
                <div className="space-y-3">
                  {comparisons.map((c) => (
                    <div
                      key={c.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedComparison?.id === c.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleViewComparison(c.id)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="text-sm font-medium text-gray-800">
                            {c.platforms.map((p) => (
                              <span
                                key={p}
                                className={`inline-block px-2 py-0.5 rounded mr-1 text-xs ${
                                  p === 'twitter'
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'bg-pink-100 text-pink-700'
                                }`}
                              >
                                {p === 'twitter' ? 'Twitter' : 'Instagram'}
                              </span>
                            ))}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {new Date(c.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteComparison(c.id);
                          }}
                          className="text-gray-400 hover:text-red-500"
                        >
                          🗑️
                        </button>
                      </div>
                      {c.best_platform && (
                        <div className="text-xs text-gray-600 mt-2">
                          勝者: {c.best_platform === 'twitter' ? 'Twitter' : c.best_platform === 'instagram' ? 'Instagram' : '同等'}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 比較結果表示エリア */}
          <div className="lg:col-span-2">
            {selectedComparison ? (
              <ComparisonResult comparison={selectedComparison} />
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <div className="text-6xl mb-4">📈</div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  比較結果がここに表示されます
                </h3>
                <p className="text-gray-500">
                  新規比較を作成するか、履歴から選択してください
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// 比較結果コンポーネント
function ComparisonResult({ comparison }: { comparison: CrossPlatformComparison }) {
  const { twitter_performance, instagram_performance, comparison_items, overall_winner } = comparison;

  const getWinnerBadge = (winner: string | null) => {
    if (winner === 'twitter') return <span className="text-blue-600">🏆 Twitter</span>;
    if (winner === 'instagram') return <span className="text-pink-600">🏆 Instagram</span>;
    if (winner === 'tie') return <span className="text-purple-600">🤝 同等</span>;
    return null;
  };

  return (
    <div className="space-y-6">
      {/* 総合結果 */}
      <div className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">総合比較結果</h2>
        <div className="text-4xl font-bold mb-4">
          {getWinnerBadge(overall_winner)}
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="opacity-75">分析期間:</span>
            <div className="font-semibold">
              {new Date(comparison.period_start).toLocaleDateString()} - {new Date(comparison.period_end).toLocaleDateString()}
            </div>
          </div>
          <div>
            <span className="opacity-75">プラットフォーム:</span>
            <div className="font-semibold">
              {comparison.platforms_analyzed.join(' vs ')}
            </div>
          </div>
        </div>
      </div>

      {/* パフォーマンス比較グリッド */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Twitter */}
        {twitter_performance && (
          <div className="bg-white rounded-lg shadow p-6 border-t-4 border-blue-500">
            <h3 className="text-lg font-bold text-blue-600 mb-4 flex items-center">
              <span className="mr-2">🐦</span> Twitter
            </h3>
            <div className="space-y-3">
              <StatItem label="投稿数" value={twitter_performance.total_posts} />
              <StatItem label="総エンゲージメント" value={twitter_performance.total_engagement.toLocaleString()} />
              <StatItem label="エンゲージメント率" value={`${twitter_performance.avg_engagement_rate.toFixed(2)}%`} />
              <StatItem label="平均いいね" value={twitter_performance.avg_likes_per_post.toFixed(1)} />
              <StatItem label="平均RT" value={twitter_performance.avg_shares_per_post.toFixed(1)} />
              {twitter_performance.best_hour !== null && (
                <StatItem label="最適投稿時間" value={`${twitter_performance.best_hour}時`} />
              )}
            </div>
          </div>
        )}

        {/* Instagram */}
        {instagram_performance && (
          <div className="bg-white rounded-lg shadow p-6 border-t-4 border-pink-500">
            <h3 className="text-lg font-bold text-pink-600 mb-4 flex items-center">
              <span className="mr-2">📸</span> Instagram
            </h3>
            <div className="space-y-3">
              <StatItem label="投稿数" value={instagram_performance.total_posts} />
              <StatItem label="総エンゲージメント" value={instagram_performance.total_engagement.toLocaleString()} />
              <StatItem label="エンゲージメント率" value={`${instagram_performance.avg_engagement_rate.toFixed(2)}%`} />
              <StatItem label="平均いいね" value={instagram_performance.avg_likes_per_post.toFixed(1)} />
              <StatItem label="平均コメント" value={instagram_performance.avg_comments_per_post.toFixed(1)} />
              {instagram_performance.best_hour !== null && (
                <StatItem label="最適投稿時間" value={`${instagram_performance.best_hour}時`} />
              )}
            </div>
          </div>
        )}
      </div>

      {/* 詳細比較 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">📊 指標比較</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2 px-3 text-gray-600">指標</th>
                <th className="py-2 px-3 text-blue-600">Twitter</th>
                <th className="py-2 px-3 text-pink-600">Instagram</th>
                <th className="py-2 px-3 text-gray-600">差異</th>
                <th className="py-2 px-3 text-gray-600">勝者</th>
              </tr>
            </thead>
            <tbody>
              {comparison_items.map((item, idx) => (
                <tr key={idx} className="border-b last:border-0">
                  <td className="py-3 px-3 font-medium text-gray-800">
                    {item.metric_name}
                  </td>
                  <td className="py-3 px-3 text-blue-600">
                    {item.twitter_value?.toFixed(1) ?? '-'}
                  </td>
                  <td className="py-3 px-3 text-pink-600">
                    {item.instagram_value?.toFixed(1) ?? '-'}
                  </td>
                  <td className="py-3 px-3">
                    {item.difference_percent !== null && (
                      <span
                        className={
                          item.difference_percent > 0
                            ? 'text-pink-600'
                            : item.difference_percent < 0
                            ? 'text-blue-600'
                            : 'text-gray-500'
                        }
                      >
                        {item.difference_percent > 0 ? '+' : ''}
                        {item.difference_percent.toFixed(1)}%
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3">
                    {item.winner === 'twitter' && (
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm">Twitter</span>
                    )}
                    {item.winner === 'instagram' && (
                      <span className="bg-pink-100 text-pink-700 px-2 py-1 rounded text-sm">Instagram</span>
                    )}
                    {item.winner === 'tie' && (
                      <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">同等</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* インサイト */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">💡 インサイト</h3>
        <div className="space-y-2">
          {comparison.cross_platform_insights.map((insight, idx) => (
            <div key={idx} className="bg-gray-50 rounded-lg p-3 text-gray-700">
              {insight}
            </div>
          ))}
        </div>
      </div>

      {/* 戦略レコメンデーション */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">🎯 戦略レコメンデーション</h3>
        <div className="space-y-2">
          {comparison.strategic_recommendations.map((rec, idx) => (
            <div key={idx} className="bg-blue-50 rounded-lg p-3 text-blue-800">
              {rec}
            </div>
          ))}
        </div>
      </div>

      {/* シナジー機会 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">🔗 シナジー機会</h3>
        <div className="space-y-2">
          {comparison.synergy_opportunities.map((opp, idx) => (
            <div key={idx} className="bg-purple-50 rounded-lg p-3 text-purple-800">
              {opp}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// 統計アイテムコンポーネント
function StatItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-600">{label}</span>
      <span className="font-semibold text-gray-800">{value}</span>
    </div>
  );
}
