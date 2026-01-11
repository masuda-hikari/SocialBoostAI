/**
 * オンボーディングページ
 *
 * 新規ユーザー向けのステップウィザード形式のセットアップガイド
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  ChevronRight,
  Twitter,
  Instagram,
  BarChart3,
  Bell,
  Sparkles,
  ArrowRight,
  X,
} from 'lucide-react';
import {
  getOnboardingStatus,
  startOnboarding,
  completeOnboardingStep,
  skipOnboardingStep,
  skipAllOnboarding,
} from '../api/onboarding';
import type {
  OnboardingStatusResponse,
  OnboardingStepName,
} from '../api/onboarding';

// ステップ情報
const STEP_INFO: Record<
  OnboardingStepName,
  {
    title: string;
    description: string;
    icon: React.ReactNode;
  }
> = {
  welcome: {
    title: 'ようこそ！',
    description: 'SocialBoostAIへようこそ。AIがあなたのSNS成長をサポートします。',
    icon: <Sparkles className="w-8 h-8 text-indigo-500" />,
  },
  connect_platform: {
    title: 'プラットフォーム接続',
    description: '分析したいSNSプラットフォームを選択してください。',
    icon: <Twitter className="w-8 h-8 text-blue-500" />,
  },
  select_goals: {
    title: '目標設定',
    description: 'あなたのSNS活用の目標を教えてください。',
    icon: <BarChart3 className="w-8 h-8 text-green-500" />,
  },
  setup_notifications: {
    title: '通知設定',
    description: 'レポートや分析結果の通知方法を設定します。',
    icon: <Bell className="w-8 h-8 text-yellow-500" />,
  },
  first_analysis: {
    title: '最初の分析',
    description: 'さっそく最初の分析を実行してみましょう。',
    icon: <BarChart3 className="w-8 h-8 text-purple-500" />,
  },
  complete: {
    title: 'セットアップ完了',
    description: '準備が整いました！ダッシュボードで成長を始めましょう。',
    icon: <CheckCircle className="w-8 h-8 text-green-500" />,
  },
};

// プラットフォームオプション
const PLATFORMS = [
  { id: 'twitter', name: 'Twitter/X', icon: <Twitter className="w-5 h-5" />, color: 'bg-blue-500' },
  { id: 'instagram', name: 'Instagram', icon: <Instagram className="w-5 h-5" />, color: 'bg-pink-500' },
];

// 目標オプション
const GOALS = [
  { id: 'followers', label: 'フォロワーを増やしたい' },
  { id: 'engagement', label: 'エンゲージメントを向上させたい' },
  { id: 'brand', label: 'ブランド認知度を高めたい' },
  { id: 'sales', label: '売上・コンバージョンを増やしたい' },
  { id: 'community', label: 'コミュニティを構築したい' },
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<OnboardingStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  // ステップごとの選択状態
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const [notificationSettings, setNotificationSettings] = useState({
    email_weekly_report: true,
    email_analysis_complete: true,
    email_tips: false,
  });

  // オンボーディング状態を取得
  useEffect(() => {
    async function loadStatus() {
      try {
        const response = await getOnboardingStatus();
        setStatus(response);

        // 完了済みならダッシュボードへ
        if (response.is_completed) {
          navigate('/dashboard');
        }
      } catch (error) {
        console.error('オンボーディング状態取得エラー:', error);
      } finally {
        setLoading(false);
      }
    }

    loadStatus();
  }, [navigate]);

  // オンボーディング開始
  useEffect(() => {
    async function start() {
      if (status && !status.started_at) {
        try {
          const response = await startOnboarding();
          setStatus(response);
        } catch (error) {
          console.error('オンボーディング開始エラー:', error);
        }
      }
    }

    start();
  }, [status]);

  // ステップ完了
  const handleCompleteStep = async (data?: Record<string, unknown>) => {
    if (!status) return;

    setProcessing(true);
    try {
      const response = await completeOnboardingStep({
        step_name: status.current_step,
        data,
      });
      setStatus(response);

      // 完了ステップなら遷移
      if (response.is_completed) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('ステップ完了エラー:', error);
    } finally {
      setProcessing(false);
    }
  };

  // ステップスキップ
  const handleSkipStep = async () => {
    if (!status) return;

    setProcessing(true);
    try {
      const response = await skipOnboardingStep(status.current_step);
      setStatus(response);
    } catch (error) {
      console.error('ステップスキップエラー:', error);
    } finally {
      setProcessing(false);
    }
  };

  // 全スキップ
  const handleSkipAll = async () => {
    setProcessing(true);
    try {
      await skipAllOnboarding({ reason: 'ユーザーがスキップを選択' });
      navigate('/dashboard');
    } catch (error) {
      console.error('全スキップエラー:', error);
    } finally {
      setProcessing(false);
    }
  };

  // ステップコンテンツのレンダリング
  const renderStepContent = () => {
    if (!status) return null;

    const currentStep = status.current_step;
    const stepInfo = STEP_INFO[currentStep];

    switch (currentStep) {
      case 'welcome':
        return (
          <div className="text-center space-y-6">
            <div className="flex justify-center">{stepInfo.icon}</div>
            <h2 className="text-2xl font-bold text-gray-900">{stepInfo.title}</h2>
            <p className="text-gray-600">{stepInfo.description}</p>

            <div className="bg-indigo-50 rounded-lg p-6 space-y-4">
              <h3 className="font-semibold text-indigo-900">SocialBoostAIでできること</h3>
              <ul className="text-left space-y-3 text-indigo-800">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" />
                  <span>5つのプラットフォーム（Twitter、Instagram、TikTok、YouTube、LinkedIn）の分析</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" />
                  <span>AIによるコンテンツ提案と最適投稿時間の分析</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-0.5" />
                  <span>投稿スケジュール管理とリアルタイム通知</span>
                </li>
              </ul>
            </div>

            <button
              onClick={() => handleCompleteStep()}
              disabled={processing}
              className="w-full py-3 px-6 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              はじめる
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        );

      case 'connect_platform':
        return (
          <div className="space-y-6">
            <div className="flex justify-center">{stepInfo.icon}</div>
            <h2 className="text-2xl font-bold text-gray-900 text-center">{stepInfo.title}</h2>
            <p className="text-gray-600 text-center">{stepInfo.description}</p>

            <div className="grid grid-cols-2 gap-4">
              {PLATFORMS.map((platform) => (
                <button
                  key={platform.id}
                  onClick={() => setSelectedPlatform(platform.id)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedPlatform === platform.id
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className={`w-10 h-10 ${platform.color} rounded-full flex items-center justify-center text-white mx-auto mb-2`}>
                    {platform.icon}
                  </div>
                  <span className="font-medium text-gray-900">{platform.name}</span>
                </button>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSkipStep}
                disabled={processing}
                className="flex-1 py-3 px-6 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50"
              >
                スキップ
              </button>
              <button
                onClick={() => handleCompleteStep({ platform: selectedPlatform })}
                disabled={processing || !selectedPlatform}
                className="flex-1 py-3 px-6 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                次へ
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        );

      case 'select_goals':
        return (
          <div className="space-y-6">
            <div className="flex justify-center">{stepInfo.icon}</div>
            <h2 className="text-2xl font-bold text-gray-900 text-center">{stepInfo.title}</h2>
            <p className="text-gray-600 text-center">{stepInfo.description}</p>

            <div className="space-y-3">
              {GOALS.map((goal) => (
                <button
                  key={goal.id}
                  onClick={() => {
                    setSelectedGoals((prev) =>
                      prev.includes(goal.id)
                        ? prev.filter((g) => g !== goal.id)
                        : [...prev, goal.id]
                    );
                  }}
                  className={`w-full p-4 rounded-lg border-2 text-left transition-all flex items-center gap-3 ${
                    selectedGoals.includes(goal.id)
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                      selectedGoals.includes(goal.id)
                        ? 'border-indigo-500 bg-indigo-500'
                        : 'border-gray-300'
                    }`}
                  >
                    {selectedGoals.includes(goal.id) && (
                      <CheckCircle className="w-4 h-4 text-white" />
                    )}
                  </div>
                  <span className="font-medium text-gray-900">{goal.label}</span>
                </button>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSkipStep}
                disabled={processing}
                className="flex-1 py-3 px-6 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50"
              >
                スキップ
              </button>
              <button
                onClick={() => handleCompleteStep({ goals: selectedGoals })}
                disabled={processing || selectedGoals.length === 0}
                className="flex-1 py-3 px-6 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                次へ
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        );

      case 'setup_notifications':
        return (
          <div className="space-y-6">
            <div className="flex justify-center">{stepInfo.icon}</div>
            <h2 className="text-2xl font-bold text-gray-900 text-center">{stepInfo.title}</h2>
            <p className="text-gray-600 text-center">{stepInfo.description}</p>

            <div className="space-y-4">
              {[
                { key: 'email_weekly_report', label: '週次レポートをメールで受け取る', description: '毎週月曜日に前週の分析レポートをお届けします' },
                { key: 'email_analysis_complete', label: '分析完了をメールで通知', description: '分析が完了したらすぐにお知らせします' },
                { key: 'email_tips', label: 'SNS活用のヒントを受け取る', description: '成長のためのヒントやベストプラクティスをお届けします' },
              ].map((item) => (
                <label
                  key={item.key}
                  className="flex items-start gap-4 p-4 rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={notificationSettings[item.key as keyof typeof notificationSettings]}
                    onChange={(e) =>
                      setNotificationSettings((prev) => ({
                        ...prev,
                        [item.key]: e.target.checked,
                      }))
                    }
                    className="mt-1 h-5 w-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <div>
                    <span className="font-medium text-gray-900 block">{item.label}</span>
                    <span className="text-sm text-gray-500">{item.description}</span>
                  </div>
                </label>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSkipStep}
                disabled={processing}
                className="flex-1 py-3 px-6 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50"
              >
                スキップ
              </button>
              <button
                onClick={() => handleCompleteStep(notificationSettings)}
                disabled={processing}
                className="flex-1 py-3 px-6 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                次へ
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        );

      case 'first_analysis':
        return (
          <div className="space-y-6">
            <div className="flex justify-center">{stepInfo.icon}</div>
            <h2 className="text-2xl font-bold text-gray-900 text-center">{stepInfo.title}</h2>
            <p className="text-gray-600 text-center">{stepInfo.description}</p>

            <div className="bg-purple-50 rounded-lg p-6 space-y-4">
              <h3 className="font-semibold text-purple-900">分析でわかること</h3>
              <ul className="text-left space-y-2 text-purple-800">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-purple-500" />
                  最適な投稿時間帯
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-purple-500" />
                  効果的なハッシュタグ
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-purple-500" />
                  エンゲージメント傾向
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-purple-500" />
                  AIによる改善提案
                </li>
              </ul>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleSkipStep}
                disabled={processing}
                className="flex-1 py-3 px-6 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50"
              >
                あとで
              </button>
              <button
                onClick={() => handleCompleteStep({ skipped_analysis: false })}
                disabled={processing}
                className="flex-1 py-3 px-6 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                分析ページへ
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        );

      case 'complete':
        return (
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-12 h-12 text-green-500" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">{stepInfo.title}</h2>
            <p className="text-gray-600">{stepInfo.description}</p>

            <div className="bg-green-50 rounded-lg p-6">
              <p className="text-green-800">
                🎉 おめでとうございます！セットアップが完了しました。
                ダッシュボードであなたのSNS成長を始めましょう。
              </p>
            </div>

            <button
              onClick={() => handleCompleteStep()}
              disabled={processing}
              className="w-full py-3 px-6 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              ダッシュボードへ
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* ヘッダー */}
      <header className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-indigo-600" />
          <span className="font-bold text-xl text-gray-900">SocialBoostAI</span>
        </div>
        <button
          onClick={handleSkipAll}
          disabled={processing}
          className="text-gray-500 hover:text-gray-700 flex items-center gap-1 text-sm"
          aria-label="オンボーディングをスキップ"
        >
          スキップ
          <X className="w-4 h-4" />
        </button>
      </header>

      {/* プログレスバー */}
      <div className="px-6 py-2">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">セットアップ進捗</span>
            <span className="text-sm font-medium text-indigo-600">{status?.progress_percent || 0}%</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-600 rounded-full transition-all duration-500"
              style={{ width: `${status?.progress_percent || 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* ステップインジケーター */}
      <div className="px-6 py-4">
        <div className="max-w-lg mx-auto flex justify-center gap-2">
          {status?.steps
            .filter((step) => step.name !== 'complete')
            .map((step, index) => (
              <div
                key={step.name}
                className={`w-3 h-3 rounded-full ${
                  step.status === 'completed' || step.status === 'skipped'
                    ? 'bg-indigo-600'
                    : step.status === 'in_progress'
                    ? 'bg-indigo-400 animate-pulse'
                    : 'bg-gray-300'
                }`}
                aria-label={`ステップ ${index + 1}: ${STEP_INFO[step.name].title}`}
              />
            ))}
        </div>
      </div>

      {/* メインコンテンツ */}
      <main className="px-6 py-8">
        <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-xl p-8">
          {renderStepContent()}
        </div>
      </main>
    </div>
  );
}
