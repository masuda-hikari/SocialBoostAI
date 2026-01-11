/**
 * 管理者ダッシュボードページ
 *
 * 運用者向けのシステム管理機能を提供
 * - システム統計
 * - 収益統計
 * - ユーザー管理
 * - アクティビティログ
 */

import { useEffect, useState } from 'react';
import {
  getSystemStats,
  getRevenueStats,
  getUsers,
  getActivityLog,
  updateUser,
  deleteUser,
  resetUserPassword,
} from '../api';
import type {
  SystemStats,
  RevenueStats,
  AdminUserSummary,
  ActivityLogEntry,
  AdminUserRole,
} from '../types';
import { useAuthStore } from '../stores/authStore';

export default function AdminPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<
    'overview' | 'users' | 'activity'
  >('overview');

  // 権限チェック
  const isAdmin =
    user?.role === 'admin' || user?.role === 'enterprise';

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            アクセス権限がありません
          </h1>
          <p className="text-gray-600">
            このページは管理者専用です。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          管理者ダッシュボード
        </h1>

        {/* タブナビゲーション */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8" aria-label="タブ">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              概要
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'users'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ユーザー管理
            </button>
            <button
              onClick={() => setActiveTab('activity')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'activity'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              アクティビティ
            </button>
          </nav>
        </div>

        {/* タブコンテンツ */}
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'users' && <UsersTab />}
        {activeTab === 'activity' && <ActivityTab />}
      </div>
    </div>
  );
}

// =============================================================================
// 概要タブ
// =============================================================================

function OverviewTab() {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [revenueStats, setRevenueStats] = useState<RevenueStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [sys, rev] = await Promise.all([
          getSystemStats(),
          getRevenueStats(),
        ]);
        setSystemStats(sys);
        setRevenueStats(rev);
        setError(null);
      } catch (err) {
        setError('統計の取得に失敗しました');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* システム統計 */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          システム統計
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="総ユーザー数"
            value={systemStats?.total_users ?? 0}
            icon="👥"
          />
          <StatCard
            label="アクティブユーザー"
            value={systemStats?.active_users ?? 0}
            icon="✅"
          />
          <StatCard
            label="今日の新規"
            value={systemStats?.new_users_today ?? 0}
            icon="🆕"
          />
          <StatCard
            label="今週の新規"
            value={systemStats?.new_users_this_week ?? 0}
            icon="📈"
          />
        </div>
      </section>

      {/* プラン別ユーザー */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          プラン別ユーザー
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {['free', 'pro', 'business', 'enterprise', 'admin'].map((plan) => (
            <div
              key={plan}
              className="bg-white rounded-lg shadow p-4 text-center"
            >
              <div className="text-sm text-gray-500 capitalize">{plan}</div>
              <div className="text-2xl font-bold text-gray-900">
                {systemStats?.users_by_plan?.[plan] ?? 0}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 収益統計 */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          収益統計
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="アクティブサブスク"
            value={revenueStats?.active_subscriptions ?? 0}
            icon="💳"
          />
          <StatCard
            label="MRR"
            value={`¥${(revenueStats?.monthly_recurring_revenue_jpy ?? 0).toLocaleString()}`}
            icon="💰"
            isText
          />
          <StatCard
            label="解約率"
            value={`${revenueStats?.churn_rate ?? 0}%`}
            icon="📉"
            isText
          />
          <StatCard
            label="総分析数"
            value={systemStats?.total_analyses ?? 0}
            icon="📊"
          />
        </div>
      </section>

      {/* コンテンツ統計 */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          コンテンツ統計
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            label="総分析数"
            value={systemStats?.total_analyses ?? 0}
            icon="📊"
          />
          <StatCard
            label="総レポート数"
            value={systemStats?.total_reports ?? 0}
            icon="📄"
          />
          <StatCard
            label="スケジュール投稿数"
            value={systemStats?.total_scheduled_posts ?? 0}
            icon="📅"
          />
        </div>
      </section>
    </div>
  );
}

// 統計カードコンポーネント
function StatCard({
  label,
  value,
  icon,
  isText = false,
}: {
  label: string;
  value: number | string;
  icon: string;
  isText?: boolean;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm text-gray-500">{label}</div>
          <div className="text-2xl font-bold text-gray-900">
            {isText ? value : Number(value).toLocaleString()}
          </div>
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  );
}

// =============================================================================
// ユーザー管理タブ
// =============================================================================

function UsersTab() {
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await getUsers({
        page,
        per_page: 20,
        search: searchQuery || undefined,
        role: roleFilter || undefined,
      });
      setUsers(response.users);
      setTotal(response.total);
      setError(null);
    } catch (err) {
      setError('ユーザー一覧の取得に失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, roleFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleRoleChange = async (
    userId: string,
    newRole: AdminUserRole
  ) => {
    try {
      await updateUser(userId, { role: newRole });
      fetchUsers();
    } catch (err) {
      console.error('ロール更新エラー:', err);
      alert('ロールの更新に失敗しました');
    }
  };

  const handleToggleActive = async (
    userId: string,
    currentActive: boolean
  ) => {
    try {
      await updateUser(userId, { is_active: !currentActive });
      fetchUsers();
    } catch (err) {
      console.error('ステータス更新エラー:', err);
      alert('ステータスの更新に失敗しました');
    }
  };

  const handleDelete = async (userId: string) => {
    if (!confirm('このユーザーを無効化しますか？')) return;
    try {
      await deleteUser(userId);
      fetchUsers();
    } catch (err) {
      console.error('削除エラー:', err);
      alert('ユーザーの削除に失敗しました');
    }
  };

  const handleResetPassword = async (userId: string) => {
    if (!confirm('パスワードをリセットしますか？')) return;
    try {
      const response = await resetUserPassword(userId);
      alert(`仮パスワード: ${response.temporary_password}\n\nこのパスワードを安全にユーザーに伝えてください。`);
    } catch (err) {
      console.error('パスワードリセットエラー:', err);
      alert('パスワードリセットに失敗しました');
    }
  };

  return (
    <div className="space-y-6">
      {/* 検索・フィルター */}
      <div className="flex flex-col sm:flex-row gap-4">
        <form onSubmit={handleSearch} className="flex-1">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="メールアドレスまたはユーザー名で検索"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 border"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              検索
            </button>
          </div>
        </form>
        <select
          value={roleFilter}
          onChange={(e) => {
            setRoleFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-3 py-2 border"
        >
          <option value="">全てのプラン</option>
          <option value="free">Free</option>
          <option value="pro">Pro</option>
          <option value="business">Business</option>
          <option value="enterprise">Enterprise</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* ユーザーテーブル */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <>
          <div className="bg-white shadow overflow-hidden rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ユーザー
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    プラン
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ステータス
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    統計
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    登録日
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {user.username}
                      </div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={user.role}
                        onChange={(e) =>
                          handleRoleChange(
                            user.id,
                            e.target.value as AdminUserRole
                          )
                        }
                        className="text-sm rounded border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
                      >
                        <option value="free">Free</option>
                        <option value="pro">Pro</option>
                        <option value="business">Business</option>
                        <option value="enterprise">Enterprise</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() =>
                          handleToggleActive(user.id, user.is_active)
                        }
                        className={`px-2 py-1 text-xs font-semibold rounded ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.is_active ? 'アクティブ' : '無効'}
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>分析: {user.analysis_count}</div>
                      <div>レポート: {user.report_count}</div>
                      <div>スケジュール: {user.scheduled_post_count}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString('ja-JP')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleResetPassword(user.id)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="パスワードリセット"
                      >
                        🔑
                      </button>
                      <button
                        onClick={() => handleDelete(user.id)}
                        className="text-red-600 hover:text-red-900"
                        title="無効化"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ページネーション */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              全 {total} 件中 {(page - 1) * 20 + 1}〜
              {Math.min(page * 20, total)} 件を表示
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                前へ
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page * 20 >= total}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                次へ
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// =============================================================================
// アクティビティタブ
// =============================================================================

function ActivityTab() {
  const [activities, setActivities] = useState<ActivityLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        setLoading(true);
        const response = await getActivityLog({ page, per_page: 50 });
        setActivities(response.entries);
        setTotal(response.total);
        setError(null);
      } catch (err) {
        setError('アクティビティログの取得に失敗しました');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchActivity();
  }, [page]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'analysis':
        return '📊';
      case 'report':
        return '📄';
      case 'scheduled_post':
        return '📅';
      case 'user_registration':
        return '👤';
      default:
        return '📌';
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'analysis':
        return 'bg-blue-100 text-blue-800';
      case 'report':
        return 'bg-green-100 text-green-800';
      case 'scheduled_post':
        return 'bg-purple-100 text-purple-800';
      case 'user_registration':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow overflow-hidden rounded-lg">
        <ul className="divide-y divide-gray-200">
          {activities.map((activity, index) => (
            <li key={index} className="px-6 py-4">
              <div className="flex items-center space-x-4">
                <div className="text-2xl">
                  {getActivityIcon(activity.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded ${getActivityColor(
                        activity.type
                      )}`}
                    >
                      {activity.type}
                    </span>
                    <span className="font-medium text-gray-900">
                      {activity.username}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {activity.description}
                  </p>
                </div>
                <div className="text-sm text-gray-400">
                  {new Date(activity.timestamp).toLocaleString('ja-JP')}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* ページネーション */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">全 {total} 件</div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            前へ
          </button>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page * 50 >= total}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            次へ
          </button>
        </div>
      </div>
    </div>
  );
}
