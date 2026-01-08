/**
 * 分析ページ（Twitter + Instagram + TikTok対応）
 */
import { useEffect, useState } from 'react';
import {
  getAnalyses,
  createAnalysis,
  deleteAnalysis,
  getInstagramAnalyses,
  createInstagramAnalysis,
  deleteInstagramAnalysis,
  getTikTokAnalyses,
  createTikTokAnalysis,
  deleteTikTokAnalysis,
} from '../api';
import { useAuthStore } from '../stores/authStore';
import type { Analysis, InstagramAnalysis, TikTokAnalysis } from '../types';
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
  Play,
  Eye,
  Share2,
  Music,
} from 'lucide-react';

// 統合分析型
type UnifiedAnalysis = Analysis | InstagramAnalysis | TikTokAnalysis;

// プラットフォームタブ
type PlatformTab = 'twitter' | 'instagram' | 'tiktok';

// プラットフォーム判定
const isInstagramAnalysis = (analysis: UnifiedAnalysis): analysis is InstagramAnalysis => {
  return analysis.platform === 'instagram';
};

const isTikTokAnalysis = (analysis: UnifiedAnalysis): analysis is TikTokAnalysis => {
  return analysis.platform === 'tiktok';
};

// プラン別機能利用可能判定
const canUsePlatform = (role: string, platform: PlatformTab): boolean => {
  if (platform === 'twitter') return true;
  // Instagram, TikTokはProプラン以上
  return ['pro', 'business', 'enterprise'].includes(role);
};

export default function AnalysisPage() {
  const { user } = useAuthStore();
  const [analyses, setAnalyses] = useState<UnifiedAnalysis[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState<UnifiedAnalysis | null>(null);

  // タブ管理
  const [activeTab, setActiveTab] = useState<PlatformTab>('twitter');

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
      } else if (activeTab === 'instagram') {
        if (canUsePlatform(user?.role || 'free', 'instagram')) {
          const response = await getInstagramAnalyses(1, 20);
          setAnalyses(response.items);
        } else {
          setAnalyses([]);
        }
      } else if (activeTab === 'tiktok') {
        if (canUsePlatform(user?.role || 'free', 'tiktok')) {
          const response = await getTikTokAnalyses(1, 20);
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
      } else if (activeTab === 'instagram') {
        const newAnalysis = await createInstagramAnalysis({
          period_days: periodDays,
        });
        setAnalyses([newAnalysis, ...analyses]);
        setSelectedAnalysis(newAnalysis);
      } else if (activeTab === 'tiktok') {
        const newAnalysis = await createTikTokAnalysis({
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
      } else if (activeTab === 'instagram') {
        await deleteInstagramAnalysis(id);
      } else if (activeTab === 'tiktok') {
        await deleteTikTokAnalysis(id);
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

  // プラン未対応プラットフォームの表示
  const renderUpgradePrompt = (platform: string) => (
    <div className="card text-center py-12">
      <Lock size={64} className="mx-auto mb-4 text-gray-400" />
      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        {platform}分析はProプラン以上でご利用いただけます
      </h3>
      <p className="text-gray-600 mb-6">
        Proプラン（¥1,980/月）にアップグレードすると、
        {platform}分析機能をご利用いただけます。
      </p>
      <a href="/billing" className="btn-primary inline-block">
        プランをアップグレード
      </a>
    </div>
  );

  // Twitter分析詳細表示
  const renderTwitterDetail = (analysis: Analysis) => (
    <div className="space-y-6">
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

      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分析詳細</h3>
        <div className="space-y-4">
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

      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分析詳細</h3>
        <div className="space-y-4">
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

  // TikTok分析詳細表示
  const renderTikTokDetail = (analysis: TikTokAnalysis) => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="card">
          <div className="text-center">
            <Play className="mx-auto text-black mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_videos}
            </p>
            <p className="text-xs text-gray-500">総動画数</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <Eye className="mx-auto text-cyan-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_views.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">総再生数</p>
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
            <Share2 className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.total_shares.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">総シェア</p>
          </div>
        </div>
        <div className="card">
          <div className="text-center">
            <BarChart3 className="mx-auto text-yellow-500 mb-2" size={24} />
            <p className="text-2xl font-bold text-gray-900">
              {analysis.summary.engagement_rate.toFixed(2)}%
            </p>
            <p className="text-xs text-gray-500">ER</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分析詳細</h3>
        <div className="space-y-4">
          <div className="flex items-center p-4 bg-gradient-to-r from-cyan-50 to-black/5 rounded-lg">
            <Clock className="text-cyan-600 mr-4" size={24} />
            <div>
              <p className="font-medium text-gray-900">最適投稿時間</p>
              <p className="text-sm text-gray-600">
                {analysis.summary.best_hour !== null
                  ? `${analysis.summary.best_hour}:00 〜 ${analysis.summary.best_hour + 1}:00`
                  : 'データ不足'}
              </p>
            </div>
          </div>

          <div className="flex items-center p-4 bg-gradient-to-r from-cyan-50 to-black/5 rounded-lg">
            <Film className="text-cyan-600 mr-4" size={24} />
            <div>
              <p className="font-medium text-gray-900">最適動画長</p>
              <p className="text-sm text-gray-600">
                {analysis.summary.best_duration_range || 'データ不足'}
              </p>
            </div>
          </div>

          <div className="flex items-center p-4 bg-gradient-to-r from-cyan-50 to-black/5 rounded-lg">
            <Eye className="text-cyan-600 mr-4" size={24} />
            <div>
              <p className="font-medium text-gray-900">いいね率</p>
              <p className="text-sm text-gray-600">
                {analysis.summary.view_to_like_ratio.toFixed(2)}% (いいね/再生)
              </p>
            </div>
          </div>

          <div className="p-4 bg-gradient-to-r from-cyan-50 to-black/5 rounded-lg">
            <div className="flex items-center mb-3">
              <Hash className="text-cyan-600 mr-2" size={20} />
              <p className="font-medium text-gray-900">トップハッシュタグ</p>
            </div>
            {analysis.summary.top_hashtags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {analysis.summary.top_hashtags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gradient-to-r from-cyan-100 to-gray-100 text-cyan-700 rounded-full text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">ハッシュタグデータなし</p>
            )}
          </div>

          {/* サウンド分析 */}
          {analysis.sound_analysis && analysis.sound_analysis.length > 0 && (
            <div className="p-4 bg-gradient-to-r from-cyan-50 to-black/5 rounded-lg">
              <div className="flex items-center mb-3">
                <Music className="text-cyan-600 mr-2" size={20} />
                <p className="font-medium text-gray-900">トレンドサウンド</p>
              </div>
              <div className="space-y-2">
                {analysis.sound_analysis.slice(0, 3).map((sound, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center p-2 bg-white rounded"
                  >
                    <span className="text-sm text-gray-700 flex items-center">
                      {sound.is_trending && (
                        <span className="mr-2 text-xs bg-red-100 text-red-600 px-1 rounded">
                          トレンド
                        </span>
                      )}
                      {sound.sound_name}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {sound.usage_count}回使用
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

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

  // プラットフォームアイコン取得
  const getPlatformIcon = (platform: PlatformTab) => {
    switch (platform) {
      case 'twitter':
        return <Twitter size={20} className="mr-2" />;
      case 'instagram':
        return <Instagram size={20} className="mr-2" />;
      case 'tiktok':
        return <Play size={20} className="mr-2" />;
    }
  };

  // タブスタイル取得
  const getTabStyle = (platform: PlatformTab, isActive: boolean) => {
    const baseStyle = 'flex items-center px-6 py-3 border-b-2 transition-colors';
    if (!isActive) {
      return `${baseStyle} border-transparent text-gray-500 hover:text-gray-700`;
    }
    switch (platform) {
      case 'twitter':
        return `${baseStyle} border-blue-500 text-blue-600`;
      case 'instagram':
        return `${baseStyle} border-pink-500 text-pink-600`;
      case 'tiktok':
        return `${baseStyle} border-black text-black`;
    }
  };

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
          {canUsePlatform(user?.role || 'free', activeTab) && (
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
          className={getTabStyle('twitter', activeTab === 'twitter')}
        >
          {getPlatformIcon('twitter')}
          Twitter
        </button>
        <button
          onClick={() => setActiveTab('instagram')}
          className={getTabStyle('instagram', activeTab === 'instagram')}
        >
          {getPlatformIcon('instagram')}
          Instagram
          {!canUsePlatform(user?.role || 'free', 'instagram') && (
            <Lock size={14} className="ml-1 text-gray-400" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('tiktok')}
          className={getTabStyle('tiktok', activeTab === 'tiktok')}
        >
          {getPlatformIcon('tiktok')}
          TikTok
          {!canUsePlatform(user?.role || 'free', 'tiktok') && (
            <Lock size={14} className="ml-1 text-gray-400" />
          )}
        </button>
      </div>

      {/* プラン未対応表示 */}
      {!canUsePlatform(user?.role || 'free', activeTab) ? (
        renderUpgradePrompt(activeTab === 'instagram' ? 'Instagram' : 'TikTok')
      ) : (
        <>
          {/* 新規分析フォーム */}
          {showForm && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                新規{activeTab === 'twitter' ? 'Twitter' : activeTab === 'instagram' ? 'Instagram' : 'TikTok'}分析を作成
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
                  {activeTab === 'twitter' ? 'Twitter' : activeTab === 'instagram' ? 'Instagram' : 'TikTok'}分析履歴
                </h3>
                {analyses.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    {getPlatformIcon(activeTab)}
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
                              : activeTab === 'instagram'
                              ? 'bg-pink-100 border-pink-300'
                              : 'bg-gray-200 border-gray-400'
                            : 'bg-gray-50 hover:bg-gray-100'
                        } border`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-gray-900 capitalize flex items-center">
                              {activeTab === 'twitter' ? (
                                <Twitter size={14} className="mr-1 text-blue-500" />
                              ) : activeTab === 'instagram' ? (
                                <Instagram size={14} className="mr-1 text-pink-500" />
                              ) : (
                                <Play size={14} className="mr-1 text-black" />
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
                isTikTokAnalysis(selectedAnalysis) ? (
                  renderTikTokDetail(selectedAnalysis)
                ) : isInstagramAnalysis(selectedAnalysis) ? (
                  renderInstagramDetail(selectedAnalysis)
                ) : (
                  renderTwitterDetail(selectedAnalysis)
                )
              ) : (
                <div className="card">
                  <div className="text-center py-12 text-gray-500">
                    {activeTab === 'twitter' ? (
                      <Twitter size={64} className="mx-auto mb-4 opacity-50" />
                    ) : activeTab === 'instagram' ? (
                      <Instagram size={64} className="mx-auto mb-4 opacity-50" />
                    ) : (
                      <Play size={64} className="mx-auto mb-4 opacity-50" />
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
