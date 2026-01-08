/**
 * 分析ページ（Twitter + Instagram対応）
 */
import { useEffect, useState } from 'react';
import {
  getAnalyses,
  createAnalysis,
  deleteAnalysis,
  getInstagramAnalyses,
  createInstagramAnalysis,
  deleteInstagramAnalysis,
} from '../api';
import { useAuthStore } from '../stores/authStore';
import type { Analysis, InstagramAnalysis } from '../types';
import {
  BarChart3,
  Plus,
  Trash2,
  RefreshCw,
  Hash,
  Clock,
  Heart,
  Repeat,
  Instagram,
  Twitter,
  Bookmark,
  MessageCircle,
  Film,
  Lock,
} from 'lucide-react';

// 統合分析型
type UnifiedAnalysis = Analysis | InstagramAnalysis;

// プラットフォーム判定
const isInstagramAnalysis = (analysis: UnifiedAnalysis): analysis is InstagramAnalysis => {
  return analysis.platform === 'instagram';
};

// プラン別Instagram利用可能判定
const canUseInstagram = (role: string): boolean => {
  return ['pro', 'business', 'enterprise'].includes(role);
};

export default function AnalysisPage() {
  const { user } = useAuthStore();
  const [analyses, setAnalyses] = useState<UnifiedAnalysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<UnifiedAnalysis | null>(null);

  // タブ管理（twitter / instagram）
  const [activeTab, setActiveTab] = useState<'twitter' | 'instagram'>('twitter');

  // 新規分析フォーム
  const [showForm, setShowForm] = useState(false);
  const [periodDays, setPeriodDays] = useState(7);

  // 分析取得
  const fetchAnalyses = async () => {
    setIsLoading(true);
    try {
      if (activeTab === 'twitter') {
        const response = await getAnalyses(1, 20);
        setAnalyses(response.items);
      } else {
        // Instagram（Proプラン以上のみ）
        if (canUseInstagram(user?.role || 'free')) {
          const response = await getInstagramAnalyses(1, 20);
          setAnalyses(response.items);
        } else {
          setAnalyses([]);
        }
      }
      setSelectedAnalysis(null);
    } catch (error) {
      console.error('分析一覧取得エラー:', error);
      setAnalyses([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // 分析作成
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      if (activeTab === 'twitter') {
        const newAnalysis = await createAnalysis({
          platform: 'twitter',
          period_days: periodDays,
        });
        setAnalyses([newAnalysis, ...analyses]);
        setSelectedAnalysis(newAnalysis);
      } else {
        const newAnalysis = await createInstagramAnalysis({
          period_days: periodDays,
        });
        setAnalyses([newAnalysis, ...analyses]);
        setSelectedAnalysis(newAnalysis);
      }
      setShowForm(false);
    } catch (error) {
      console.error('分析作成エラー:', error);
      alert('分析の作成に失敗しました');
    } finally {
      setIsCreating(false);
    }
  };

  // 分析削除
  const handleDelete = async (id: string) => {
    if (!confirm('この分析を削除しますか？')) return;

    try {
      if (activeTab === 'twitter') {
        await deleteAnalysis(id);
      } else {
        await deleteInstagramAnalysis(id);
      }
      setAnalyses(analyses.filter((a) => a.id !== id));
      if (selectedAnalysis?.id === id) {
        setSelectedAnalysis(null);
      }
    } catch (error) {
      console.error('分析削除エラー:', error);
      alert('分析の削除に失敗しました');
    }
  };

  // ローディング表示
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Instagram未対応プランの表示
  const renderInstagramUpgradePrompt = () => (
    <div className="card text-center py-12">
      <Lock size={64} className="mx-auto mb-4 text-gray-400" />
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        Instagram分析はProプラン以上でご利用いただけます
      </h3>
      <p className="text-gray-600 mb-6">
        Proプラン（¥1,980/月）にアップグレードすると、
        Instagram分析機能をご利用いただけます。
      </p>
      <a href="/billing" className="btn-primary inline-block">
        プランをアップグレード
      </a>
    </div>
  );

  // Twitter分析詳細表示
  const renderTwitterDetail = (analysis: Analysis) => (
    <div className="space-y-6">
      {/* サマリーカード */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-center">
            <BarChart3 className="mx-auto text-primary-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_posts}
            </p>
            <p className="text-xs text-gray-500">総投稿数</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <Heart className="mx-auto text-red-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_likes.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">総いいね</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <Repeat className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_retweets.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">総リツイート</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <BarChart3 className="mx-auto text-yellow-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.engagement_rate.toFixed(2)}%
            </p>
            <p className="text-xs text-gray-500">エンゲージメント率</p>
          </div>
        </div>
      </div>

      {/* 詳細情報 */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分析詳細</h3>
        <div className="space-y-4">
          {/* 最適投稿時間 */}
          <div className="flex items-center p-4 bg-gray-50 rounded-lg">
            <Clock className="text-primary-500 mr-4" size={24} />
            <div>
              <p className="font-medium text-gray-900">最適投稿時間</p>
              <p className="text-sm text-gray-600">
                {analysis.summary.best_hour !== null
                  ? `${analysis.summary.best_hour}:00 〜 ${analysis.summary.best_hour + 1}:00`
                  : 'データ不足'}
              </p>
            </div>
          </div>

          {/* トップハッシュタグ */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center mb-3">
              <Hash className="text-blue-500 mr-2" size={20} />
              <p className="font-medium text-gray-900">トップハッシュタグ</p>
            </div>
            {analysis.summary.top_hashtags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {analysis.summary.top_hashtags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">ハッシュタグデータなし</p>
            )}
          </div>

          {/* メタ情報 */}
          <div className="text-sm text-gray-500 border-t pt-4">
            <p>分析ID: {analysis.id}</p>
            <p>
              作成日: {new Date(analysis.created_at).toLocaleString('ja-JP')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  // Instagram分析詳細表示
  const renderInstagramDetail = (analysis: InstagramAnalysis) => (
    <div className="space-y-6">
      {/* サマリーカード */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="card">
          <div className="text-center">
            <BarChart3 className="mx-auto text-primary-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_posts}
            </p>
            <p className="text-xs text-gray-500">総投稿数</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <Film className="mx-auto text-purple-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_reels}
            </p>
            <p className="text-xs text-gray-500">リール数</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <Heart className="mx-auto text-red-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_likes.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">総いいね</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <MessageCircle className="mx-auto text-blue-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_comments.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">総コメント</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <Bookmark className="mx-auto text-yellow-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_saves.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">総保存数</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <BarChart3 className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.engagement_rate.toFixed(2)}%
            </p>
            <p className="text-xs text-gray-500">ER</p>
          </div>
        </div>
      </div>

      {/* 詳細情報 */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分析詳細</h3>
        <div className="space-y-4">
          {/* 最適投稿時間 */}
          <div className="flex items-center p-4 bg-gradient-to-r from-pink-50 to-purple-50 rounded-lg">
            <Clock className="text-pink-500 mr-4" size={24} />
            <div>
              <p className="font-medium text-gray-900">最適投稿時間</p>
              <p className="text-sm text-gray-600">
                {analysis.summary.best_hour !== null
                  ? `${analysis.summary.best_hour}:00 〜 ${analysis.summary.best_hour + 1}:00`
                  : 'データ不足'}
              </p>
            </div>
          </div>

          {/* トップハッシュタグ */}
          <div className="p-4 bg-gradient-to-r from-pink-50 to-purple-50 rounded-lg">
            <div className="flex items-center mb-3">
              <Hash className="text-pink-500 mr-2" size={20} />
              <p className="font-medium text-gray-900">トップハッシュタグ</p>
            </div>
            {analysis.summary.top_hashtags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {analysis.summary.top_hashtags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gradient-to-r from-pink-100 to-purple-100 text-pink-700 rounded-full text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">ハッシュタグデータなし</p>
            )}
          </div>

          {/* コンテンツパターン（詳細取得時のみ表示） */}
          {analysis.content_patterns && analysis.content_patterns.length > 0 && (
            <div className="p-4 bg-gradient-to-r from-pink-50 to-purple-50 rounded-lg">
              <p className="font-medium text-gray-900 mb-3">コンテンツパターン分析</p>
              <div className="space-y-2">
                {analysis.content_patterns.map((pattern, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center p-2 bg-white rounded"
                  >
                    <span className="text-sm text-gray-700 capitalize">
                      {pattern.pattern_type}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {pattern.count}件 (平均ER: {pattern.avg_engagement.toFixed(1)})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* レコメンデーション（詳細取得時のみ表示） */}
          {analysis.recommendations && (
            <div className="p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
              <p className="font-medium text-gray-900 mb-3">AIレコメンデーション</p>
              <p className="text-sm text-gray-600">{analysis.recommendations.reasoning}</p>
            </div>
          )}

          {/* メタ情報 */}
          <div className="text-sm text-gray-500 border-t pt-4">
            <p>分析ID: {analysis.id}</p>
            <p>
              作成日: {new Date(analysis.created_at).toLocaleString('ja-JP')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">分析</h1>
          <p className="text-gray-600">ソーシャルメディアのパフォーマンスを分析</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchAnalyses} className="btn-secondary flex items-center">
            <RefreshCw size={16} className="mr-2" />
            更新
          </button>
          {(activeTab === 'twitter' || canUseInstagram(user?.role || 'free')) && (
            <button
              onClick={() => setShowForm(true)}
              className="btn-primary flex items-center"
            >
              <Plus size={16} className="mr-2" />
              新規分析
            </button>
          )}
        </div>
      </div>

      {/* プラットフォームタブ */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab('twitter')}
          className={`flex items-center px-6 py-3 border-b-2 transition-colors ${
            activeTab === 'twitter'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Twitter size={20} className="mr-2" />
          Twitter
        </button>
        <button
          onClick={() => setActiveTab('instagram')}
          className={`flex items-center px-6 py-3 border-b-2 transition-colors ${
            activeTab === 'instagram'
              ? 'border-pink-500 text-pink-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Instagram size={20} className="mr-2" />
          Instagram
          {!canUseInstagram(user?.role || 'free') && (
            <Lock size={14} className="ml-1 text-gray-400" />
          )}
        </button>
      </div>

      {/* Instagram未対応プラン */}
      {activeTab === 'instagram' && !canUseInstagram(user?.role || 'free') ? (
        renderInstagramUpgradePrompt()
      ) : (
        <>
          {/* 新規分析フォーム */}
          {showForm && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                新規{activeTab === 'twitter' ? 'Twitter' : 'Instagram'}分析を作成
              </h3>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    分析期間（日数）
                  </label>
                  <select
                    value={periodDays}
                    onChange={(e) => setPeriodDays(Number(e.target.value))}
                    className="input-field"
                  >
                    <option value={7}>過去7日間</option>
                    <option value={14}>過去14日間</option>
                    <option value={30}>過去30日間</option>
                    <option value={60}>過去60日間</option>
                    <option value={90}>過去90日間</option>
                  </select>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="btn-secondary"
                  >
                    キャンセル
                  </button>
                  <button type="submit" disabled={isCreating} className="btn-primary">
                    {isCreating ? '作成中...' : '分析を開始'}
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 分析一覧 */}
            <div className="lg:col-span-1">
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {activeTab === 'twitter' ? 'Twitter' : 'Instagram'}分析履歴
                </h3>
                {analyses.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    {activeTab === 'twitter' ? (
                      <Twitter size={48} className="mx-auto mb-4 opacity-50" />
                    ) : (
                      <Instagram size={48} className="mx-auto mb-4 opacity-50" />
                    )}
                    <p>まだ分析がありません</p>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[600px] overflow-y-auto">
                    {analyses.map((analysis) => (
                      <div
                        key={analysis.id}
                        onClick={() => setSelectedAnalysis(analysis)}
                        className={`p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedAnalysis?.id === analysis.id
                            ? activeTab === 'twitter'
                              ? 'bg-blue-100 border-blue-300'
                              : 'bg-pink-100 border-pink-300'
                            : 'bg-gray-50 hover:bg-gray-100'
                        } border`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900 capitalize flex items-center">
                              {activeTab === 'twitter' ? (
                                <Twitter size={14} className="mr-1 text-blue-500" />
                              ) : (
                                <Instagram size={14} className="mr-1 text-pink-500" />
                              )}
                              {analysis.platform}
                            </p>
                            <p className="text-xs text-gray-500">
                              {new Date(analysis.period_start).toLocaleDateString('ja-JP')} -{' '}
                              {new Date(analysis.period_end).toLocaleDateString('ja-JP')}
                            </p>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(analysis.id);
                            }}
                            className="text-gray-400 hover:text-red-500 transition-colors"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 分析詳細 */}
            <div className="lg:col-span-2">
              {selectedAnalysis ? (
                isInstagramAnalysis(selectedAnalysis) ? (
                  renderInstagramDetail(selectedAnalysis)
                ) : (
                  renderTwitterDetail(selectedAnalysis)
                )
              ) : (
                <div className="card">
                  <div className="text-center py-12 text-gray-500">
                    {activeTab === 'twitter' ? (
                      <Twitter size={64} className="mx-auto mb-4 opacity-50" />
                    ) : (
                      <Instagram size={64} className="mx-auto mb-4 opacity-50" />
                    )}
                    <p className="text-lg">分析を選択してください</p>
                    <p className="text-sm mt-2">
                      左側の一覧から分析を選択するか、新規分析を作成してください
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
