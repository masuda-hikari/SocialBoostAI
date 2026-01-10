/**
 * スケジュール投稿ページ（v2.3）
 */
import { useEffect, useState } from 'react';
import {
  getScheduledPosts,
  createScheduledPost,
  cancelScheduledPost,
  deleteScheduledPost,
  getScheduleStats,
  getUpcomingPosts,
} from '../api';
import { useAuthStore } from '../stores/authStore';
import type {
  ScheduledPostSummary,
  ScheduledPostCreate,
  ScheduleStats,
  ContentPlatform,
} from '../types';
import {
  Calendar,
  Plus,
  Trash2,
  RefreshCw,
  Clock,
  XCircle,
  CheckCircle,
  AlertCircle,
  Lock,
  Twitter,
  Instagram,
  Play,
  Youtube,
  Linkedin,
  Filter,
  BarChart3,
  CalendarDays,
} from 'lucide-react';

// プラン別機能利用可能判定
const canUseScheduling = (role: string): boolean => {
  return ['pro', 'business', 'enterprise'].includes(role);
};

const canUseBulkScheduling = (role: string): boolean => {
  return ['business', 'enterprise'].includes(role);
};

// プラットフォームアイコン
const PlatformIcon = ({ platform }: { platform: ContentPlatform }) => {
  switch (platform) {
    case 'twitter':
      return <Twitter size={16} className="text-blue-500" />;
    case 'instagram':
      return <Instagram size={16} className="text-pink-500" />;
    case 'tiktok':
      return <Play size={16} className="text-black" />;
    case 'youtube':
      return <Youtube size={16} className="text-red-500" />;
    case 'linkedin':
      return <Linkedin size={16} className="text-blue-700" />;
    default:
      return null;
  }
};

// ステータスバッジ
const StatusBadge = ({ status }: { status: string }) => {
  switch (status) {
    case 'pending':
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <Clock size={12} className="mr-1" />
          予約中
        </span>
      );
    case 'published':
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle size={12} className="mr-1" />
          投稿済み
        </span>
      );
    case 'failed':
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <AlertCircle size={12} className="mr-1" />
          失敗
        </span>
      );
    case 'cancelled':
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          <XCircle size={12} className="mr-1" />
          キャンセル
        </span>
      );
    default:
      return null;
  }
};

export default function SchedulePage() {
  const { user } = useAuthStore();
  const [posts, setPosts] = useState<ScheduledPostSummary[]>([]);
  const [upcomingPosts, setUpcomingPosts] = useState<ScheduledPostSummary[]>([]);
  const [stats, setStats] = useState<ScheduleStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  // フィルター
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [platformFilter, setPlatformFilter] = useState<string>('');

  // 新規作成フォーム
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<Partial<ScheduledPostCreate>>({
    platform: 'twitter',
    content: '',
    hashtags: [],
    scheduled_at: '',
    timezone: 'Asia/Tokyo',
  });
  const [hashtagInput, setHashtagInput] = useState('');

  // データ取得
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [postsRes, statsRes, upcomingRes] = await Promise.all([
        getScheduledPosts(1, 50, statusFilter || undefined, platformFilter || undefined),
        getScheduleStats(),
        getUpcomingPosts(7, 10),
      ]);
      setPosts(postsRes.items);
      setStats(statsRes);
      setUpcomingPosts(upcomingRes);
    } catch (error) {
      console.error('スケジュールデータ取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (canUseScheduling(user?.role || 'free')) {
      fetchData();
    } else {
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, platformFilter]);

  // スケジュール作成
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.platform || !formData.content || !formData.scheduled_at) {
      alert('必須項目を入力してください');
      return;
    }

    setIsCreating(true);
    try {
      await createScheduledPost({
        platform: formData.platform as ContentPlatform,
        content: formData.content,
        hashtags: formData.hashtags || [],
        scheduled_at: new Date(formData.scheduled_at).toISOString(),
        timezone: formData.timezone || 'Asia/Tokyo',
      });
      setShowForm(false);
      setFormData({
        platform: 'twitter',
        content: '',
        hashtags: [],
        scheduled_at: '',
        timezone: 'Asia/Tokyo',
      });
      setHashtagInput('');
      await fetchData();
    } catch (error) {
      console.error('スケジュール作成エラー:', error);
      alert('スケジュール作成に失敗しました');
    } finally {
      setIsCreating(false);
    }
  };

  // キャンセル
  const handleCancel = async (id: string) => {
    if (!confirm('この予約をキャンセルしますか？')) return;

    try {
      await cancelScheduledPost(id);
      await fetchData();
    } catch (error) {
      console.error('キャンセルエラー:', error);
      alert('キャンセルに失敗しました');
    }
  };

  // 削除
  const handleDelete = async (id: string) => {
    if (!confirm('この予約を削除しますか？')) return;

    try {
      await deleteScheduledPost(id);
      await fetchData();
    } catch (error) {
      console.error('削除エラー:', error);
      alert('削除に失敗しました');
    }
  };

  // ハッシュタグ追加
  const addHashtag = () => {
    if (hashtagInput.trim()) {
      const tag = hashtagInput.trim().replace(/^#/, '');
      if (tag && !formData.hashtags?.includes(tag)) {
        setFormData({
          ...formData,
          hashtags: [...(formData.hashtags || []), tag],
        });
      }
      setHashtagInput('');
    }
  };

  // ハッシュタグ削除
  const removeHashtag = (tag: string) => {
    setFormData({
      ...formData,
      hashtags: formData.hashtags?.filter((t) => t !== tag) || [],
    });
  };

  // プランチェック
  if (!canUseScheduling(user?.role || 'free')) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">スケジュール投稿</h1>
            <p className="text-gray-600">投稿を予約して自動投稿</p>
          </div>
        </div>

        <div className="card text-center py-12">
          <Lock size={64} className="mx-auto mb-4 text-gray-400" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            スケジュール投稿はProプラン以上でご利用いただけます
          </h3>
          <p className="text-gray-600 mb-6">
            Proプラン（¥1,980/月）にアップグレードすると、
            投稿予約機能をご利用いただけます。
          </p>
          <a href="/billing" className="btn-primary inline-block">
            プランをアップグレード
          </a>
        </div>
      </div>
    );
  }

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
          <h1 className="text-2xl font-bold text-gray-900">スケジュール投稿</h1>
          <p className="text-gray-600">投稿を予約して自動投稿</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchData} className="btn-secondary flex items-center">
            <RefreshCw size={16} className="mr-2" />
            更新
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary flex items-center"
          >
            <Plus size={16} className="mr-2" />
            新規予約
          </button>
        </div>
      </div>

      {/* 統計カード */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="card">
            <div className="text-center">
              <Calendar className="mx-auto text-primary-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-gray-900">{stats.total_scheduled}</p>
              <p className="text-xs text-gray-500">総予約数</p>
            </div>
          </div>
          <div className="card">
            <div className="text-center">
              <Clock className="mx-auto text-yellow-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
              <p className="text-xs text-gray-500">予約中</p>
            </div>
          </div>
          <div className="card">
            <div className="text-center">
              <CheckCircle className="mx-auto text-green-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-gray-900">{stats.published}</p>
              <p className="text-xs text-gray-500">投稿済み</p>
            </div>
          </div>
          <div className="card">
            <div className="text-center">
              <AlertCircle className="mx-auto text-red-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-gray-900">{stats.failed}</p>
              <p className="text-xs text-gray-500">失敗</p>
            </div>
          </div>
          <div className="card">
            <div className="text-center">
              <XCircle className="mx-auto text-gray-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-gray-900">{stats.cancelled}</p>
              <p className="text-xs text-gray-500">キャンセル</p>
            </div>
          </div>
          <div className="card">
            <div className="text-center">
              <CalendarDays className="mx-auto text-blue-500 mb-2" size={24} />
              <p className="text-2xl font-bold text-gray-900">{stats.upcoming_24h}</p>
              <p className="text-xs text-gray-500">24時間以内</p>
            </div>
          </div>
        </div>
      )}

      {/* 新規作成フォーム */}
      {showForm && (
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">新規スケジュール投稿</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  プラットフォーム *
                </label>
                <select
                  value={formData.platform}
                  onChange={(e) =>
                    setFormData({ ...formData, platform: e.target.value as ContentPlatform })
                  }
                  className="input-field"
                >
                  <option value="twitter">Twitter</option>
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube</option>
                  <option value="linkedin">LinkedIn</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  投稿日時 *
                </label>
                <input
                  type="datetime-local"
                  value={formData.scheduled_at}
                  onChange={(e) =>
                    setFormData({ ...formData, scheduled_at: e.target.value })
                  }
                  className="input-field"
                  min={new Date().toISOString().slice(0, 16)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                投稿内容 *
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="input-field"
                rows={4}
                placeholder="投稿内容を入力..."
                maxLength={10000}
              />
              <p className="text-xs text-gray-500 mt-1">
                {formData.content?.length || 0}/10000
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ハッシュタグ
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={hashtagInput}
                  onChange={(e) => setHashtagInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addHashtag();
                    }
                  }}
                  className="input-field flex-1"
                  placeholder="ハッシュタグを入力してEnter"
                />
                <button
                  type="button"
                  onClick={addHashtag}
                  className="btn-secondary"
                >
                  追加
                </button>
              </div>
              {formData.hashtags && formData.hashtags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.hashtags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                    >
                      #{tag}
                      <button
                        type="button"
                        onClick={() => removeHashtag(tag)}
                        className="ml-1 text-blue-500 hover:text-blue-700"
                      >
                        <XCircle size={14} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-4 border-t">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn-secondary"
              >
                キャンセル
              </button>
              <button type="submit" disabled={isCreating} className="btn-primary">
                {isCreating ? '作成中...' : '予約を作成'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 今後の投稿（サイドバー） */}
        <div className="lg:col-span-1">
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <CalendarDays className="mr-2 text-primary-500" size={20} />
              今後の投稿
            </h3>
            {upcomingPosts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Calendar size={48} className="mx-auto mb-2 opacity-50" />
                <p>予約済みの投稿はありません</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {upcomingPosts.map((post) => (
                  <div
                    key={post.id}
                    className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <PlatformIcon platform={post.platform} />
                        <span className="text-xs text-gray-500 capitalize">
                          {post.platform}
                        </span>
                      </div>
                      <StatusBadge status={post.status} />
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-2 mb-2">
                      {post.content_preview}
                    </p>
                    <p className="text-xs text-gray-500 flex items-center">
                      <Clock size={12} className="mr-1" />
                      {new Date(post.scheduled_at).toLocaleString('ja-JP')}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* プラットフォーム別統計 */}
          {stats && Object.keys(stats.by_platform).length > 0 && (
            <div className="card mt-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <BarChart3 className="mr-2 text-primary-500" size={20} />
                プラットフォーム別
              </h3>
              <div className="space-y-2">
                {Object.entries(stats.by_platform).map(([platform, count]) => (
                  <div
                    key={platform}
                    className="flex items-center justify-between p-2 bg-gray-50 rounded"
                  >
                    <div className="flex items-center gap-2">
                      <PlatformIcon platform={platform as ContentPlatform} />
                      <span className="text-sm capitalize">{platform}</span>
                    </div>
                    <span className="text-sm font-medium">{count}件</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 投稿一覧 */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">予約一覧</h3>
              <div className="flex gap-2">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="input-field text-sm py-1"
                >
                  <option value="">全ステータス</option>
                  <option value="pending">予約中</option>
                  <option value="published">投稿済み</option>
                  <option value="failed">失敗</option>
                  <option value="cancelled">キャンセル</option>
                </select>
                <select
                  value={platformFilter}
                  onChange={(e) => setPlatformFilter(e.target.value)}
                  className="input-field text-sm py-1"
                >
                  <option value="">全プラットフォーム</option>
                  <option value="twitter">Twitter</option>
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube</option>
                  <option value="linkedin">LinkedIn</option>
                </select>
              </div>
            </div>

            {posts.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Filter size={48} className="mx-auto mb-2 opacity-50" />
                <p>該当する投稿がありません</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        プラットフォーム
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        内容
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        予約日時
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        ステータス
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {posts.map((post) => (
                      <tr key={post.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <PlatformIcon platform={post.platform} />
                            <span className="text-sm capitalize">{post.platform}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <p className="text-sm text-gray-700 line-clamp-2 max-w-xs">
                            {post.content_preview}
                          </p>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <p className="text-sm text-gray-700">
                            {new Date(post.scheduled_at).toLocaleString('ja-JP')}
                          </p>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <StatusBadge status={post.status} />
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right">
                          <div className="flex justify-end gap-2">
                            {post.status === 'pending' && (
                              <button
                                onClick={() => handleCancel(post.id)}
                                className="text-yellow-600 hover:text-yellow-800 p-1"
                                title="キャンセル"
                              >
                                <XCircle size={18} />
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(post.id)}
                              className="text-red-600 hover:text-red-800 p-1"
                              title="削除"
                            >
                              <Trash2 size={18} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 一括作成のヒント（Business以上） */}
          {canUseBulkScheduling(user?.role || 'free') && (
            <div className="card mt-4 bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
              <div className="flex items-start gap-4">
                <div className="p-2 bg-white rounded-lg">
                  <Calendar className="text-primary-600" size={24} />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">一括スケジュール機能</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Businessプラン以上では、一度に最大20件の投稿を一括でスケジュールできます。
                    AI生成コンテンツページからまとめて予約することも可能です。
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
