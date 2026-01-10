import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  generateContent,
  rewriteContent,
  generateABVariations,
  generateContentCalendar,
  generateTrendingContent,
  getGenerationHistory,
  deleteGenerationHistory,
} from '../api';
import type {
  ContentPlatform,
  ContentTone,
  ContentGoal,
  GeneratedContent,
  ABTestResponse,
  ContentCalendarResponse,
  TrendingContentResponse,
} from '../types';
import { useAuthStore } from '../stores/authStore';

// プラットフォーム設定
const PLATFORMS: { value: ContentPlatform; label: string; color: string }[] = [
  { value: 'twitter', label: 'Twitter/X', color: 'bg-sky-500' },
  { value: 'instagram', label: 'Instagram', color: 'bg-gradient-to-r from-pink-500 to-purple-500' },
  { value: 'tiktok', label: 'TikTok', color: 'bg-gradient-to-r from-cyan-500 to-black' },
  { value: 'youtube', label: 'YouTube', color: 'bg-red-500' },
  { value: 'linkedin', label: 'LinkedIn', color: 'bg-blue-700' },
];

const TONES: { value: ContentTone; label: string }[] = [
  { value: 'casual', label: 'カジュアル' },
  { value: 'professional', label: 'プロフェッショナル' },
  { value: 'humorous', label: 'ユーモラス' },
  { value: 'educational', label: '教育的' },
  { value: 'inspirational', label: '感動的' },
  { value: 'promotional', label: 'プロモーション' },
];

const GOALS: { value: ContentGoal; label: string }[] = [
  { value: 'engagement', label: 'エンゲージメント獲得' },
  { value: 'awareness', label: '認知度向上' },
  { value: 'conversion', label: 'コンバージョン' },
  { value: 'traffic', label: 'トラフィック誘導' },
  { value: 'community', label: 'コミュニティ構築' },
];

type TabType = 'generate' | 'rewrite' | 'abtest' | 'calendar' | 'trending' | 'history';

export default function ContentPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabType>('generate');

  // 生成フォーム状態
  const [generateForm, setGenerateForm] = useState({
    platform: 'twitter' as ContentPlatform,
    topic: '',
    keywords: '',
    tone: 'casual' as ContentTone,
    goal: 'engagement' as ContentGoal,
    target_audience: '',
    include_hashtags: true,
    include_cta: false,
  });

  // リライトフォーム状態
  const [rewriteForm, setRewriteForm] = useState({
    original_content: '',
    source_platform: 'twitter' as ContentPlatform,
    target_platform: 'instagram' as ContentPlatform,
    preserve_hashtags: false,
    tone: 'casual' as ContentTone,
  });

  // A/Bテストフォーム状態
  const [abTestForm, setAbTestForm] = useState({
    base_topic: '',
    platform: 'twitter' as ContentPlatform,
    variation_count: 3,
    tone: 'casual' as ContentTone,
  });

  // カレンダーフォーム状態
  const [calendarForm, setCalendarForm] = useState({
    platforms: ['twitter'] as ContentPlatform[],
    days: 7,
    posts_per_day: 2,
    topics: '',
    tone: 'casual' as ContentTone,
    goal: 'engagement' as ContentGoal,
  });

  // トレンドフォーム状態
  const [trendForm, setTrendForm] = useState({
    platform: 'twitter' as ContentPlatform,
    trend_keywords: '',
    brand_context: '',
    tone: 'casual' as ContentTone,
  });

  // 結果状態
  const [generatedResult, setGeneratedResult] = useState<GeneratedContent | null>(null);
  const [abTestResult, setAbTestResult] = useState<ABTestResponse | null>(null);
  const [calendarResult, setCalendarResult] = useState<ContentCalendarResponse | null>(null);
  const [trendResult, setTrendResult] = useState<TrendingContentResponse | null>(null);

  // 履歴取得
  const { data: history } = useQuery({
    queryKey: ['content-history'],
    queryFn: () => getGenerationHistory(),
  });

  // 生成ミューテーション
  const generateMutation = useMutation({
    mutationFn: generateContent,
    onSuccess: (data) => {
      setGeneratedResult(data);
      queryClient.invalidateQueries({ queryKey: ['content-history'] });
    },
  });

  const rewriteMutation = useMutation({
    mutationFn: rewriteContent,
    onSuccess: (data) => {
      setGeneratedResult(data);
      queryClient.invalidateQueries({ queryKey: ['content-history'] });
    },
  });

  const abTestMutation = useMutation({
    mutationFn: generateABVariations,
    onSuccess: (data) => {
      setAbTestResult(data);
      queryClient.invalidateQueries({ queryKey: ['content-history'] });
    },
  });

  const calendarMutation = useMutation({
    mutationFn: generateContentCalendar,
    onSuccess: (data) => {
      setCalendarResult(data);
      queryClient.invalidateQueries({ queryKey: ['content-history'] });
    },
  });

  const trendMutation = useMutation({
    mutationFn: generateTrendingContent,
    onSuccess: (data) => {
      setTrendResult(data);
      queryClient.invalidateQueries({ queryKey: ['content-history'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteGenerationHistory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-history'] });
    },
  });

  const isPro = user?.role !== 'free';

  const handleGenerate = () => {
    generateMutation.mutate({
      platform: generateForm.platform,
      topic: generateForm.topic || undefined,
      keywords: generateForm.keywords ? generateForm.keywords.split(',').map(k => k.trim()) : undefined,
      tone: generateForm.tone,
      goal: generateForm.goal,
      target_audience: generateForm.target_audience || undefined,
      include_hashtags: generateForm.include_hashtags,
      include_cta: generateForm.include_cta,
    });
  };

  const handleRewrite = () => {
    rewriteMutation.mutate({
      original_content: rewriteForm.original_content,
      source_platform: rewriteForm.source_platform,
      target_platform: rewriteForm.target_platform,
      preserve_hashtags: rewriteForm.preserve_hashtags,
      tone: rewriteForm.tone,
    });
  };

  const handleABTest = () => {
    abTestMutation.mutate({
      base_topic: abTestForm.base_topic,
      platform: abTestForm.platform,
      variation_count: abTestForm.variation_count,
      tone: abTestForm.tone,
    });
  };

  const handleCalendar = () => {
    calendarMutation.mutate({
      platforms: calendarForm.platforms,
      days: calendarForm.days,
      posts_per_day: calendarForm.posts_per_day,
      topics: calendarForm.topics ? calendarForm.topics.split(',').map(t => t.trim()) : undefined,
      tone: calendarForm.tone,
      goal: calendarForm.goal,
    });
  };

  const handleTrend = () => {
    trendMutation.mutate({
      platform: trendForm.platform,
      trend_keywords: trendForm.trend_keywords.split(',').map(k => k.trim()),
      brand_context: trendForm.brand_context || undefined,
      tone: trendForm.tone,
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('クリップボードにコピーしました');
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">AIコンテンツ生成</h1>

      {/* タブ */}
      <div className="flex flex-wrap gap-2 mb-6 border-b pb-4">
        {[
          { id: 'generate', label: 'コンテンツ生成', icon: '✨' },
          { id: 'rewrite', label: 'リライト', icon: '🔄' },
          { id: 'abtest', label: 'A/Bテスト', icon: '🧪', pro: true },
          { id: 'calendar', label: 'カレンダー', icon: '📅', pro: true },
          { id: 'trending', label: 'トレンド活用', icon: '🔥', pro: true },
          { id: 'history', label: '履歴', icon: '📜' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            disabled={tab.pro && !isPro}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-indigo-600 text-white'
                : tab.pro && !isPro
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {tab.icon} {tab.label}
            {tab.pro && !isPro && ' (Pro)'}
          </button>
        ))}
      </div>

      {/* コンテンツ生成タブ */}
      {activeTab === 'generate' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">生成設定</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  プラットフォーム
                </label>
                <select
                  value={generateForm.platform}
                  onChange={(e) => setGenerateForm({ ...generateForm, platform: e.target.value as ContentPlatform })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {PLATFORMS.map((p) => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  トピック
                </label>
                <input
                  type="text"
                  value={generateForm.topic}
                  onChange={(e) => setGenerateForm({ ...generateForm, topic: e.target.value })}
                  placeholder="例: 新商品のお知らせ"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  キーワード（カンマ区切り）
                </label>
                <input
                  type="text"
                  value={generateForm.keywords}
                  onChange={(e) => setGenerateForm({ ...generateForm, keywords: e.target.value })}
                  placeholder="例: AI, 効率化, ビジネス"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    トーン
                  </label>
                  <select
                    value={generateForm.tone}
                    onChange={(e) => setGenerateForm({ ...generateForm, tone: e.target.value as ContentTone })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {TONES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    目標
                  </label>
                  <select
                    value={generateForm.goal}
                    onChange={(e) => setGenerateForm({ ...generateForm, goal: e.target.value as ContentGoal })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {GOALS.map((g) => (
                      <option key={g.value} value={g.value}>{g.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ターゲットオーディエンス
                </label>
                <input
                  type="text"
                  value={generateForm.target_audience}
                  onChange={(e) => setGenerateForm({ ...generateForm, target_audience: e.target.value })}
                  placeholder="例: 20-30代のビジネスパーソン"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={generateForm.include_hashtags}
                    onChange={(e) => setGenerateForm({ ...generateForm, include_hashtags: e.target.checked })}
                    className="mr-2"
                  />
                  ハッシュタグを含める
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={generateForm.include_cta}
                    onChange={(e) => setGenerateForm({ ...generateForm, include_cta: e.target.checked })}
                    className="mr-2"
                  />
                  CTAを含める
                </label>
              </div>

              <button
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
                className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {generateMutation.isPending ? '生成中...' : '✨ コンテンツを生成'}
              </button>
            </div>
          </div>

          {/* 結果表示 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">生成結果</h2>
            {generatedResult ? (
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <span className={`px-2 py-1 rounded text-white text-sm ${PLATFORMS.find(p => p.value === generatedResult.platform)?.color || 'bg-gray-500'}`}>
                      {PLATFORMS.find(p => p.value === generatedResult.platform)?.label}
                    </span>
                    <button
                      onClick={() => copyToClipboard(generatedResult.main_text)}
                      className="text-indigo-600 hover:text-indigo-800 text-sm"
                    >
                      📋 コピー
                    </button>
                  </div>
                  <p className="whitespace-pre-wrap">{generatedResult.main_text}</p>
                </div>

                {generatedResult.hashtags.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">ハッシュタグ</h3>
                    <div className="flex flex-wrap gap-2">
                      {generatedResult.hashtags.map((tag, i) => (
                        <span key={i} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {generatedResult.call_to_action && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">CTA</h3>
                    <p className="text-gray-600">{generatedResult.call_to_action}</p>
                  </div>
                )}

                {generatedResult.media_suggestion && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">メディア提案</h3>
                    <p className="text-gray-600">{generatedResult.media_suggestion}</p>
                  </div>
                )}

                {generatedResult.estimated_engagement && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">期待効果</h3>
                    <p className="text-gray-600">{generatedResult.estimated_engagement}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                生成されたコンテンツがここに表示されます
              </p>
            )}
          </div>
        </div>
      )}

      {/* リライトタブ */}
      {activeTab === 'rewrite' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">リライト設定</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  元のコンテンツ
                </label>
                <textarea
                  value={rewriteForm.original_content}
                  onChange={(e) => setRewriteForm({ ...rewriteForm, original_content: e.target.value })}
                  rows={4}
                  placeholder="リライトしたいコンテンツを入力..."
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    元のプラットフォーム
                  </label>
                  <select
                    value={rewriteForm.source_platform}
                    onChange={(e) => setRewriteForm({ ...rewriteForm, source_platform: e.target.value as ContentPlatform })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {PLATFORMS.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    変換先プラットフォーム
                  </label>
                  <select
                    value={rewriteForm.target_platform}
                    onChange={(e) => setRewriteForm({ ...rewriteForm, target_platform: e.target.value as ContentPlatform })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {PLATFORMS.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  トーン
                </label>
                <select
                  value={rewriteForm.tone}
                  onChange={(e) => setRewriteForm({ ...rewriteForm, tone: e.target.value as ContentTone })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {TONES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={rewriteForm.preserve_hashtags}
                  onChange={(e) => setRewriteForm({ ...rewriteForm, preserve_hashtags: e.target.checked })}
                  className="mr-2"
                />
                元のハッシュタグを保持
              </label>

              <button
                onClick={handleRewrite}
                disabled={rewriteMutation.isPending || !rewriteForm.original_content}
                className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {rewriteMutation.isPending ? 'リライト中...' : '🔄 リライト'}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">リライト結果</h2>
            {generatedResult ? (
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <span className={`px-2 py-1 rounded text-white text-sm ${PLATFORMS.find(p => p.value === generatedResult.platform)?.color || 'bg-gray-500'}`}>
                      {PLATFORMS.find(p => p.value === generatedResult.platform)?.label}
                    </span>
                    <button
                      onClick={() => copyToClipboard(generatedResult.main_text)}
                      className="text-indigo-600 hover:text-indigo-800 text-sm"
                    >
                      📋 コピー
                    </button>
                  </div>
                  <p className="whitespace-pre-wrap">{generatedResult.main_text}</p>
                </div>
                {generatedResult.hashtags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {generatedResult.hashtags.map((tag, i) => (
                      <span key={i} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                リライト結果がここに表示されます
              </p>
            )}
          </div>
        </div>
      )}

      {/* A/Bテストタブ */}
      {activeTab === 'abtest' && isPro && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">A/Bテスト設定</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  トピック
                </label>
                <input
                  type="text"
                  value={abTestForm.base_topic}
                  onChange={(e) => setAbTestForm({ ...abTestForm, base_topic: e.target.value })}
                  placeholder="例: 新機能リリースのお知らせ"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    プラットフォーム
                  </label>
                  <select
                    value={abTestForm.platform}
                    onChange={(e) => setAbTestForm({ ...abTestForm, platform: e.target.value as ContentPlatform })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {PLATFORMS.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    バリエーション数
                  </label>
                  <select
                    value={abTestForm.variation_count}
                    onChange={(e) => setAbTestForm({ ...abTestForm, variation_count: parseInt(e.target.value) })}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={4}>4</option>
                    <option value={5}>5</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  トーン
                </label>
                <select
                  value={abTestForm.tone}
                  onChange={(e) => setAbTestForm({ ...abTestForm, tone: e.target.value as ContentTone })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {TONES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleABTest}
                disabled={abTestMutation.isPending || !abTestForm.base_topic}
                className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {abTestMutation.isPending ? '生成中...' : '🧪 バリエーション生成'}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">バリエーション結果</h2>
            {abTestResult ? (
              <div className="space-y-4">
                {abTestResult.variations.map((v, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm font-medium">
                        バリエーション {v.version}
                      </span>
                      <button
                        onClick={() => copyToClipboard(v.text)}
                        className="text-indigo-600 hover:text-indigo-800 text-sm"
                      >
                        📋
                      </button>
                    </div>
                    <p className="text-sm text-gray-500 mb-2">{v.focus}</p>
                    <p className="whitespace-pre-wrap">{v.text}</p>
                    {v.hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {v.hashtags.map((tag, j) => (
                          <span key={j} className="text-blue-600 text-sm">#{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                バリエーションがここに表示されます
              </p>
            )}
          </div>
        </div>
      )}

      {/* カレンダータブ */}
      {activeTab === 'calendar' && isPro && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">カレンダー設定</h2>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  日数
                </label>
                <select
                  value={calendarForm.days}
                  onChange={(e) => setCalendarForm({ ...calendarForm, days: parseInt(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value={7}>1週間</option>
                  <option value={14}>2週間</option>
                  <option value={30}>1ヶ月</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  1日あたりの投稿数
                </label>
                <select
                  value={calendarForm.posts_per_day}
                  onChange={(e) => setCalendarForm({ ...calendarForm, posts_per_day: parseInt(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value={1}>1件</option>
                  <option value={2}>2件</option>
                  <option value={3}>3件</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  トピック（カンマ区切り）
                </label>
                <input
                  type="text"
                  value={calendarForm.topics}
                  onChange={(e) => setCalendarForm({ ...calendarForm, topics: e.target.value })}
                  placeholder="例: 製品紹介, Tips, お客様の声"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
            </div>
            <button
              onClick={handleCalendar}
              disabled={calendarMutation.isPending}
              className="mt-4 bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {calendarMutation.isPending ? '生成中...' : '📅 カレンダー生成'}
            </button>
          </div>

          {calendarResult && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                投稿カレンダー（{calendarResult.total_items}件）
              </h2>
              <div className="space-y-4">
                {calendarResult.items.map((item, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-center gap-4 mb-2">
                      <span className="font-medium">
                        {new Date(item.scheduled_date).toLocaleDateString('ja-JP')}
                      </span>
                      <span className="text-gray-500">{item.optimal_time}</span>
                      <span className={`px-2 py-1 rounded text-white text-sm ${PLATFORMS.find(p => p.value === item.platform)?.color || 'bg-gray-500'}`}>
                        {PLATFORMS.find(p => p.value === item.platform)?.label}
                      </span>
                    </div>
                    <p className="font-medium text-gray-700">{item.topic}</p>
                    <p className="mt-2 text-gray-600">{item.draft_content}</p>
                    {item.hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {item.hashtags.map((tag, j) => (
                          <span key={j} className="text-blue-600 text-sm">#{tag}</span>
                        ))}
                      </div>
                    )}
                    <p className="text-sm text-gray-400 mt-2">{item.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* トレンドタブ */}
      {activeTab === 'trending' && isPro && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">トレンド設定</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  トレンドキーワード（カンマ区切り）
                </label>
                <input
                  type="text"
                  value={trendForm.trend_keywords}
                  onChange={(e) => setTrendForm({ ...trendForm, trend_keywords: e.target.value })}
                  placeholder="例: AI, ChatGPT, 働き方改革"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  プラットフォーム
                </label>
                <select
                  value={trendForm.platform}
                  onChange={(e) => setTrendForm({ ...trendForm, platform: e.target.value as ContentPlatform })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {PLATFORMS.map((p) => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ブランドコンテキスト
                </label>
                <textarea
                  value={trendForm.brand_context}
                  onChange={(e) => setTrendForm({ ...trendForm, brand_context: e.target.value })}
                  rows={3}
                  placeholder="例: SaaS企業。生産性向上ツールを提供。"
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>

              <button
                onClick={handleTrend}
                disabled={trendMutation.isPending || !trendForm.trend_keywords}
                className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {trendMutation.isPending ? '生成中...' : '🔥 トレンドコンテンツ生成'}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">トレンドコンテンツ</h2>
            {trendResult ? (
              <div className="space-y-4">
                {trendResult.contents.map((content, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm text-gray-500">コンテンツ {i + 1}</span>
                      <button
                        onClick={() => copyToClipboard(content.main_text)}
                        className="text-indigo-600 hover:text-indigo-800 text-sm"
                      >
                        📋
                      </button>
                    </div>
                    <p className="whitespace-pre-wrap">{content.main_text}</p>
                    {content.hashtags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {content.hashtags.map((tag, j) => (
                          <span key={j} className="text-blue-600 text-sm">#{tag}</span>
                        ))}
                      </div>
                    )}
                    {content.estimated_engagement && (
                      <p className="text-sm text-green-600 mt-2">
                        📊 {content.estimated_engagement}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                トレンドコンテンツがここに表示されます
              </p>
            )}
          </div>
        </div>
      )}

      {/* 履歴タブ */}
      {activeTab === 'history' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">生成履歴</h2>
          {history && history.items.length > 0 ? (
            <div className="space-y-2">
              {history.items.map((item) => (
                <div key={item.id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <span className={`px-2 py-1 rounded text-white text-xs mr-2 ${PLATFORMS.find(p => p.value === item.platform)?.color || 'bg-gray-500'}`}>
                      {PLATFORMS.find(p => p.value === item.platform)?.label}
                    </span>
                    <span className="text-sm text-gray-500">{item.content_type}</span>
                    <p className="text-gray-700 truncate max-w-md">{item.preview}</p>
                    <span className="text-xs text-gray-400">
                      {new Date(item.created_at).toLocaleString('ja-JP')}
                    </span>
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate(item.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    削除
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">
              履歴がありません
            </p>
          )}
        </div>
      )}
    </div>
  );
}
