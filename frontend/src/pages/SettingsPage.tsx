/**
 * 設定ページ
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../stores/authStore';
import {
  getEmailPreferences,
  updateEmailPreferences,
  getEmailStatus,
  sendTestEmail,
  type EmailPreferences,
  type EmailPreferencesUpdate
} from '../api/email';
import { User, Lock, AlertCircle, Check, Mail, Loader2, Info, Smartphone } from 'lucide-react';
import PushNotificationSettings from '../components/PushNotificationSettings';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'notifications' | 'push'>(
    'profile'
  );

  // プッシュ通知用メッセージ
  const [pushMessage, setPushMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // プロフィール状態
  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [profileSaved, setProfileSaved] = useState(false);

  // セキュリティ状態
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSaved, setPasswordSaved] = useState(false);

  // メールステータス取得
  const { data: emailStatus } = useQuery({
    queryKey: ['emailStatus'],
    queryFn: getEmailStatus,
    staleTime: 5 * 60 * 1000, // 5分キャッシュ
  });

  // メール設定取得
  const { data: emailPrefs, isLoading: isLoadingPrefs } = useQuery({
    queryKey: ['emailPreferences'],
    queryFn: getEmailPreferences,
    staleTime: 1 * 60 * 1000, // 1分キャッシュ
  });

  // メール設定更新
  const updatePrefsMutation = useMutation({
    mutationFn: (prefs: EmailPreferencesUpdate) => updateEmailPreferences(prefs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emailPreferences'] });
    },
  });

  // テストメール送信
  const sendTestMutation = useMutation({
    mutationFn: (templateType: 'welcome' | 'analysis_complete' | 'weekly_report' | 'engagement_alert') =>
      sendTestEmail(templateType),
  });

  // ローカル通知設定状態（オプティミスティック更新用）
  const [localOverrides, setLocalOverrides] = useState<Partial<EmailPreferences>>({});

  // 実際の設定値（APIデータ + ローカルオーバーライド）
  const notificationSettings: EmailPreferences | null = emailPrefs
    ? { ...emailPrefs, ...localOverrides }
    : null;

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: プロフィール更新API呼び出し
    setProfileSaved(true);
    setTimeout(() => setProfileSaved(false), 3000);
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');

    if (newPassword !== confirmPassword) {
      setPasswordError('新しいパスワードが一致しません');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('パスワードは8文字以上で入力してください');
      return;
    }

    // TODO: パスワード変更API呼び出し
    setPasswordSaved(true);
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setTimeout(() => setPasswordSaved(false), 3000);
  };

  const handleNotificationChange = async (key: keyof EmailPreferencesUpdate, value: boolean) => {
    if (!emailPrefs) return;

    // ローカルオーバーライドを即座に更新（オプティミスティック更新）
    setLocalOverrides((prev) => ({
      ...prev,
      [key]: value,
    }));

    // APIに保存
    try {
      await updatePrefsMutation.mutateAsync({ [key]: value });
      // 成功したらオーバーライドをクリア（キャッシュが更新されるため）
      setLocalOverrides((prev) => {
        const newOverrides = { ...prev };
        delete newOverrides[key];
        return newOverrides;
      });
    } catch (error) {
      // エラー時はオーバーライドをクリア（元の値に戻す）
      setLocalOverrides((prev) => {
        const newOverrides = { ...prev };
        delete newOverrides[key];
        return newOverrides;
      });
      console.error('通知設定の更新に失敗しました:', error);
    }
  };

  const handleSendTestEmail = async () => {
    try {
      await sendTestMutation.mutateAsync('welcome');
    } catch (error) {
      console.error('テストメール送信に失敗しました:', error);
    }
  };

  const tabs = [
    { id: 'profile', label: 'プロフィール', icon: User },
    { id: 'security', label: 'セキュリティ', icon: Lock },
    { id: 'notifications', label: 'メール通知', icon: Mail },
    { id: 'push', label: 'プッシュ通知', icon: Smartphone },
  ] as const;

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">設定</h1>
        <p className="text-gray-600">アカウント設定を管理</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* サイドナビ */}
        <div className="lg:col-span-1">
          <div className="card">
            <nav className="space-y-1" role="navigation" aria-label="設定メニュー">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  aria-current={activeTab === tab.id ? 'page' : undefined}
                  className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <tab.icon size={20} className="mr-3" aria-hidden="true" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* コンテンツ */}
        <div className="lg:col-span-3">
          {/* プロフィール */}
          {activeTab === 'profile' && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                プロフィール設定
              </h3>
              <form onSubmit={handleProfileSave} className="space-y-4">
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                    ユーザー名
                  </label>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    メールアドレス
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input-field"
                  />
                </div>
                <div className="flex items-center gap-4">
                  <button type="submit" className="btn-primary">
                    保存
                  </button>
                  {profileSaved && (
                    <span className="text-green-600 flex items-center">
                      <Check size={16} className="mr-1" aria-hidden="true" />
                      保存しました
                    </span>
                  )}
                </div>
              </form>
            </div>
          )}

          {/* セキュリティ */}
          {activeTab === 'security' && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                パスワード変更
              </h3>
              <form onSubmit={handlePasswordChange} className="space-y-4">
                {passwordError && (
                  <div className="flex items-center p-4 bg-red-50 rounded-lg text-red-700" role="alert">
                    <AlertCircle size={20} className="mr-2" aria-hidden="true" />
                    {passwordError}
                  </div>
                )}
                <div>
                  <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-1">
                    現在のパスワード
                  </label>
                  <input
                    id="currentPassword"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
                    新しいパスワード
                  </label>
                  <input
                    id="newPassword"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input-field"
                    required
                    minLength={8}
                  />
                  <p className="mt-1 text-xs text-gray-500">8文字以上</p>
                </div>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                    新しいパスワード（確認）
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input-field"
                    required
                  />
                </div>
                <div className="flex items-center gap-4">
                  <button type="submit" className="btn-primary">
                    パスワード変更
                  </button>
                  {passwordSaved && (
                    <span className="text-green-600 flex items-center">
                      <Check size={16} className="mr-1" aria-hidden="true" />
                      変更しました
                    </span>
                  )}
                </div>
              </form>
            </div>
          )}

          {/* メール通知設定 */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              {/* メールステータス */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900 flex items-center">
                    <Mail size={20} className="mr-2" aria-hidden="true" />
                    メール通知状態
                  </h3>
                  {emailStatus?.enabled ? (
                    <span className="flex items-center text-green-600 text-sm">
                      <Check size={16} className="mr-1" aria-hidden="true" />
                      有効
                    </span>
                  ) : (
                    <span className="flex items-center text-yellow-600 text-sm">
                      <AlertCircle size={16} className="mr-1" aria-hidden="true" />
                      無効
                    </span>
                  )}
                </div>
                {!emailStatus?.enabled && (
                  <div className="flex items-start p-4 bg-yellow-50 rounded-lg text-yellow-700 text-sm">
                    <Info size={20} className="mr-2 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <p>
                      メール通知が無効です。サーバー管理者にSMTP設定を依頼してください。
                      設定が完了すると、以下の通知を受け取れるようになります。
                    </p>
                  </div>
                )}
                {emailStatus?.enabled && (
                  <div className="flex items-center gap-4">
                    <button
                      onClick={handleSendTestEmail}
                      disabled={sendTestMutation.isPending}
                      className="btn-secondary text-sm"
                    >
                      {sendTestMutation.isPending ? (
                        <>
                          <Loader2 size={16} className="mr-2 animate-spin" aria-hidden="true" />
                          送信中...
                        </>
                      ) : (
                        'テストメールを送信'
                      )}
                    </button>
                    {sendTestMutation.isSuccess && (
                      <span className="text-green-600 text-sm">
                        テストメールを送信しました
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* メール通知設定 */}
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-4">メール通知設定</h3>

                {isLoadingPrefs ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 size={24} className="animate-spin text-primary-600" aria-label="読み込み中" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <NotificationToggle
                      title="週次レポート通知"
                      description="週次レポートが生成されたらメールで通知"
                      checked={notificationSettings?.weekly_report ?? true}
                      onChange={(checked) => handleNotificationChange('weekly_report', checked)}
                      disabled={updatePrefsMutation.isPending}
                    />
                    <NotificationToggle
                      title="月次レポート通知"
                      description="月次レポートが生成されたらメールで通知"
                      checked={notificationSettings?.monthly_report ?? true}
                      onChange={(checked) => handleNotificationChange('monthly_report', checked)}
                      disabled={updatePrefsMutation.isPending}
                    />
                    <NotificationToggle
                      title="分析完了通知"
                      description="分析が完了したらメールで通知"
                      checked={notificationSettings?.analysis_complete ?? true}
                      onChange={(checked) => handleNotificationChange('analysis_complete', checked)}
                      disabled={updatePrefsMutation.isPending}
                    />
                    <NotificationToggle
                      title="エンゲージメントアラート"
                      description="投稿が急上昇したらメールで通知"
                      checked={notificationSettings?.engagement_alerts ?? true}
                      onChange={(checked) => handleNotificationChange('engagement_alerts', checked)}
                      disabled={updatePrefsMutation.isPending}
                    />
                    <NotificationToggle
                      title="課金関連通知"
                      description="支払い関連の重要な通知を受け取る"
                      checked={notificationSettings?.billing_notifications ?? true}
                      onChange={(checked) => handleNotificationChange('billing_notifications', checked)}
                      disabled={updatePrefsMutation.isPending}
                    />
                  </div>
                )}

                {updatePrefsMutation.isPending && (
                  <div className="mt-4 flex items-center text-gray-500 text-sm">
                    <Loader2 size={16} className="mr-2 animate-spin" aria-hidden="true" />
                    保存中...
                  </div>
                )}
              </div>
            </div>
          )}

          {/* プッシュ通知設定 */}
          {activeTab === 'push' && (
            <div className="card">
              {pushMessage && (
                <div
                  className={`mb-4 p-4 rounded-lg flex items-center ${
                    pushMessage.type === 'success'
                      ? 'bg-green-50 text-green-700'
                      : 'bg-red-50 text-red-700'
                  }`}
                  role="alert"
                >
                  {pushMessage.type === 'success' ? (
                    <Check size={20} className="mr-2" aria-hidden="true" />
                  ) : (
                    <AlertCircle size={20} className="mr-2" aria-hidden="true" />
                  )}
                  {pushMessage.text}
                  <button
                    onClick={() => setPushMessage(null)}
                    className="ml-auto p-1 hover:opacity-70"
                    aria-label="閉じる"
                  >
                    ×
                  </button>
                </div>
              )}
              <PushNotificationSettings
                onSuccess={(message) => {
                  setPushMessage({ type: 'success', text: message });
                  setTimeout(() => setPushMessage(null), 5000);
                }}
                onError={(message) => {
                  setPushMessage({ type: 'error', text: message });
                  setTimeout(() => setPushMessage(null), 5000);
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// 通知トグルコンポーネント
interface NotificationToggleProps {
  title: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

function NotificationToggle({
  title,
  description,
  checked,
  onChange,
  disabled
}: NotificationToggleProps) {
  const id = title.replace(/\s+/g, '-').toLowerCase();

  return (
    <label
      htmlFor={id}
      className={`flex items-center justify-between p-4 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
    >
      <div>
        <p className="font-medium text-gray-900">{title}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="w-5 h-5 text-primary-600 rounded focus:ring-primary-500"
      />
    </label>
  );
}
