/**
 * 分析ページ
 */
import { useEffect, useState } from 'react';
import { getAnalyses, createAnalysis, deleteAnalysis } from '../api';
import type { Analysis } from '../types';
import {
  BarChart3,
  Plus,
  Trash2,
  RefreshCw,
  Hash,
  Clock,
  Heart,
  Repeat,
} from 'lucide-react';

export default function AnalysisPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null);

  // 新規分析フォーム
  const [showForm, setShowForm] = useState(false);
  const [platform, setPlatform] = useState('twitter');
  const [periodDays, setPeriodDays] = useState(7);

  const fetchAnalyses = async () => {
    setIsLoading(true);
    try {
      const response = await getAnalyses(1, 20);
      setAnalyses(response.items);
    } catch (error) {
      console.error('分析一覧取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      const newAnalysis = await createAnalysis({ platform, period_days: periodDays });
      setAnalyses([newAnalysis, ...analyses]);
      setShowForm(false);
      setSelectedAnalysis(newAnalysis);
    } catch (error) {
      console.error('分析作成エラー:', error);
      alert('分析の作成に失敗しました');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('この分析を削除しますか？')) return;

    try {
      await deleteAnalysis(id);
      setAnalyses(analyses.filter((a) => a.id !== id));
      if (selectedAnalysis?.id === id) {
        setSelectedAnalysis(null);
      }
    } catch (error) {
      console.error('分析削除エラー:', error);
      alert('分析の削除に失敗しました');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

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
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary flex items-center"
          >
            <Plus size={16} className="mr-2" />
            新規分析
          </button>
        </div>
      </div>

      {/* 新規分析フォーム */}
      {showForm && (
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">新規分析を作成</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                プラットフォーム
              </label>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className="input-field"
              >
                <option value="twitter">Twitter</option>
                <option value="instagram" disabled>
                  Instagram（近日対応）
                </option>
              </select>
            </div>
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
            <h3 className="text-lg font-medium text-gray-900 mb-4">分析履歴</h3>
            {analyses.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <BarChart3 size={48} className="mx-auto mb-4 opacity-50" />
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
                        ? 'bg-primary-100 border-primary-300'
                        : 'bg-gray-50 hover:bg-gray-100'
                    } border`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900 capitalize">
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
            <div className="space-y-6">
              {/* サマリーカード */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card">
                  <div className="text-center">
                    <BarChart3 className="mx-auto text-primary-500 mb-2" size={24} />
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedAnalysis.summary.total_posts}
                    </p>
                    <p className="text-xs text-gray-500">総投稿数</p>
                  </div>
                </div>
                <div className="card">
                  <div className="text-center">
                    <Heart className="mx-auto text-red-500 mb-2" size={24} />
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedAnalysis.summary.total_likes.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500">総いいね</p>
                  </div>
                </div>
                <div className="card">
                  <div className="text-center">
                    <Repeat className="mx-auto text-green-500 mb-2" size={24} />
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedAnalysis.summary.total_retweets.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500">総リツイート</p>
                  </div>
                </div>
                <div className="card">
                  <div className="text-center">
                    <BarChart3 className="mx-auto text-yellow-500 mb-2" size={24} />
                    <p className="text-2xl font-bold text-gray-900">
                      {selectedAnalysis.summary.engagement_rate.toFixed(2)}%
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
                        {selectedAnalysis.summary.best_hour !== null
                          ? `${selectedAnalysis.summary.best_hour}:00 〜 ${selectedAnalysis.summary.best_hour + 1}:00`
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
                    {selectedAnalysis.summary.top_hashtags.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {selectedAnalysis.summary.top_hashtags.map((tag, index) => (
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
                    <p>分析ID: {selectedAnalysis.id}</p>
                    <p>
                      作成日:{' '}
                      {new Date(selectedAnalysis.created_at).toLocaleString('ja-JP')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="text-center py-12 text-gray-500">
                <BarChart3 size={64} className="mx-auto mb-4 opacity-50" />
                <p className="text-lg">分析を選択してください</p>
                <p className="text-sm mt-2">
                  左側の一覧から分析を選択するか、新規分析を作成してください
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
