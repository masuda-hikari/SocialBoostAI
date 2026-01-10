/**
 * ランディングページ
 * サービス紹介、料金プラン、CTA
 */
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  Zap,
  BarChart3,
  Clock,
  MessageSquare,
  Shield,
  Check,
  ArrowRight,
  Crown,
  Rocket,
  Building2,
  Star,
} from 'lucide-react';

// 機能一覧
const features = [
  {
    icon: TrendingUp,
    title: 'エンゲージメント分析',
    description:
      'いいね、リツイート、リプライを詳細に分析し、どの投稿が効果的かを可視化します。',
  },
  {
    icon: Clock,
    title: '最適投稿時間提案',
    description:
      'AIがあなたのフォロワーの行動パターンを分析し、最適な投稿タイミングを提案します。',
  },
  {
    icon: Zap,
    title: 'バイラルパターン検出',
    description:
      '過去のバズ投稿を分析し、バイラルになる可能性の高いコンテンツパターンを特定します。',
  },
  {
    icon: BarChart3,
    title: 'トレンド分析',
    description:
      'リアルタイムでトレンドを追跡し、関連するコンテンツアイデアを自動生成します。',
  },
  {
    icon: MessageSquare,
    title: 'AI返信提案',
    description:
      'フォロワーからのリプライに対する最適な返信文案をAIが自動生成します。',
  },
  {
    icon: Shield,
    title: '安全なデータ管理',
    description:
      'お客様のデータは暗号化して保存。APIキーも安全に管理されます。',
  },
];

// 料金プラン
const plans = [
  {
    tier: 'free',
    name: 'Free',
    price: 0,
    icon: Rocket,
    iconColor: 'text-gray-500',
    features: [
      '1プラットフォーム',
      '過去7日分析',
      '月1回レポート',
      'API呼出100回/日',
    ],
    cta: '無料で始める',
    popular: false,
  },
  {
    tier: 'pro',
    name: 'Pro',
    price: 1980,
    icon: Zap,
    iconColor: 'text-primary-500',
    features: [
      '1プラットフォーム',
      '過去90日分析',
      '週1回レポート',
      'API呼出1000回/日',
      'AI提案機能',
    ],
    cta: 'Proを始める',
    popular: true,
  },
  {
    tier: 'business',
    name: 'Business',
    price: 4980,
    icon: Crown,
    iconColor: 'text-yellow-500',
    features: [
      '3プラットフォーム',
      '無制限履歴',
      'リアルタイムレポート',
      'API呼出10000回/日',
      'AI提案機能',
      '優先サポート',
    ],
    cta: 'Businessを始める',
    popular: false,
  },
  {
    tier: 'enterprise',
    name: 'Enterprise',
    price: -1, // 要見積
    icon: Building2,
    iconColor: 'text-purple-500',
    features: [
      '無制限アカウント',
      '専用サポート',
      'カスタム分析',
      'API利用無制限',
      'SLA保証',
      'オンボーディング',
    ],
    cta: 'お問い合わせ',
    popular: false,
  },
];

// ユーザーの声（想定）
const testimonials = [
  {
    name: '田中 太郎',
    role: 'マーケター',
    content:
      'SocialBoostAIを使い始めてから、投稿のエンゲージメント率が3倍に。最適投稿時間の提案が特に役立っています。',
    avatar: 'T',
  },
  {
    name: '佐藤 花子',
    role: 'インフルエンサー',
    content:
      'どの投稿がバズるかが事前にわかるようになりました。フォロワー数が2ヶ月で50%増加！',
    avatar: 'S',
  },
  {
    name: '鈴木 一郎',
    role: 'EC運営者',
    content:
      'AI返信提案のおかげで、顧客対応の時間が半分に。売上も20%アップしました。',
    avatar: 'S',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* スキップリンク */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[60] focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg"
      >
        メインコンテンツへスキップ
      </a>

      {/* ヘッダー */}
      <header className="fixed top-0 left-0 right-0 bg-white/80 backdrop-blur-md z-50 border-b border-gray-100" role="banner">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8" aria-label="メインナビゲーション">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-primary-600">
                SocialBoostAI
              </span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a
                href="#features"
                className="text-gray-600 hover:text-primary-600 transition-colors"
              >
                機能
              </a>
              <a
                href="#pricing"
                className="text-gray-600 hover:text-primary-600 transition-colors"
              >
                料金
              </a>
              <a
                href="#testimonials"
                className="text-gray-600 hover:text-primary-600 transition-colors"
              >
                お客様の声
              </a>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="text-gray-600 hover:text-primary-600 transition-colors"
              >
                ログイン
              </Link>
              <Link
                to="/register"
                className="btn-primary inline-flex items-center"
              >
                無料で始める
                <ArrowRight size={16} className="ml-1" />
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* ヒーローセクション */}
      <main id="main-content">
      <section className="pt-32 pb-20 bg-gradient-to-br from-primary-50 via-white to-primary-50" aria-labelledby="hero-heading">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 id="hero-heading" className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
              AIの力で
              <span className="text-primary-600">ソーシャルメディア</span>を
              <br />
              成功に導く
            </h1>
            <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto">
              SocialBoostAIは、データ分析とAI提案で投稿の効果を最大化。
              最適な投稿時間、バイラルパターン、トレンド分析を自動で行い、
              あなたのエンゲージメントを飛躍的に向上させます。
            </p>
            <div className="mt-10 flex flex-col sm:flex-row justify-center gap-4">
              <Link
                to="/register"
                className="btn-primary inline-flex items-center justify-center text-lg py-3 px-8"
              >
                無料で始める
                <ArrowRight size={20} className="ml-2" />
              </Link>
              <a
                href="#features"
                className="btn-outline inline-flex items-center justify-center text-lg py-3 px-8"
              >
                機能を見る
              </a>
            </div>
            <p className="mt-4 text-sm text-gray-500">
              クレジットカード不要・7日間の全機能お試し付き
            </p>
          </div>
        </div>
      </section>

      {/* 実績セクション */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-primary-600">10,000+</div>
              <div className="text-gray-600 mt-1">分析された投稿</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">3x</div>
              <div className="text-gray-600 mt-1">平均エンゲージメント向上</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">500+</div>
              <div className="text-gray-600 mt-1">アクティブユーザー</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary-600">98%</div>
              <div className="text-gray-600 mt-1">顧客満足度</div>
            </div>
          </div>
        </div>
      </section>

      {/* 機能セクション */}
      <section id="features" className="py-20" aria-labelledby="features-heading">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 id="features-heading" className="text-3xl font-bold text-gray-900">
              成功を加速する機能
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              AIとデータ分析の力で、あなたのソーシャルメディア運用を支援
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8" role="list">
            {features.map((feature, index) => (
              <article key={index} className="card hover:shadow-lg transition-shadow" role="listitem">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="text-primary-600" size={24} aria-hidden="true" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* 料金セクション */}
      <section id="pricing" className="py-20 bg-gray-50" aria-labelledby="pricing-heading">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 id="pricing-heading" className="text-3xl font-bold text-gray-900">
              シンプルな料金体系
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              あなたのニーズに合ったプランを選択
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.tier}
                className={`card relative ${
                  plan.popular ? 'ring-2 ring-primary-500 shadow-lg' : ''
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-primary-500 text-white text-xs font-medium px-3 py-1 rounded-full">
                      人気
                    </span>
                  </div>
                )}
                <div className="text-center mb-6">
                  <div className="flex justify-center mb-4">
                    <plan.icon className={plan.iconColor} size={32} />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">
                    {plan.name}
                  </h3>
                  <div className="mt-2">
                    {plan.price === -1 ? (
                      <span className="text-2xl font-bold text-gray-900">
                        要見積
                      </span>
                    ) : plan.price === 0 ? (
                      <span className="text-3xl font-bold text-gray-900">
                        無料
                      </span>
                    ) : (
                      <>
                        <span className="text-3xl font-bold text-gray-900">
                          ¥{plan.price.toLocaleString()}
                        </span>
                        <span className="text-gray-500">/月</span>
                      </>
                    )}
                  </div>
                </div>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center text-sm">
                      <Check
                        size={16}
                        className="text-green-500 mr-2 flex-shrink-0"
                      />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                {plan.tier === 'enterprise' ? (
                  <a
                    href="mailto:contact@socialboostai.com"
                    className="block w-full py-3 px-4 text-center bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
                  >
                    {plan.cta}
                  </a>
                ) : (
                  <Link
                    to="/register"
                    className={`block w-full py-3 px-4 text-center font-medium rounded-lg transition-colors ${
                      plan.popular
                        ? 'bg-primary-600 hover:bg-primary-700 text-white'
                        : 'bg-gray-900 hover:bg-gray-800 text-white'
                    }`}
                  >
                    {plan.cta}
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* お客様の声 */}
      <section id="testimonials" className="py-20" aria-labelledby="testimonials-heading">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 id="testimonials-heading" className="text-3xl font-bold text-gray-900">お客様の声</h2>
            <p className="mt-4 text-lg text-gray-600">
              SocialBoostAIをご利用いただいている皆様から
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="card">
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      size={16}
                      className="text-yellow-400 fill-current"
                    />
                  ))}
                </div>
                <p className="text-gray-600 mb-4">"{testimonial.content}"</p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-medium">
                    {testimonial.avatar}
                  </div>
                  <div className="ml-3">
                    <div className="font-medium text-gray-900">
                      {testimonial.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {testimonial.role}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      </main>

      {/* CTA セクション */}
      <section className="py-20 bg-primary-600" aria-labelledby="cta-heading">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 id="cta-heading" className="text-3xl font-bold text-white">
            今すぐ始めましょう
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            無料プランでSocialBoostAIの力を体験してください。
            クレジットカードは不要です。
          </p>
          <div className="mt-8">
            <Link
              to="/register"
              className="inline-flex items-center justify-center bg-white text-primary-600 hover:bg-primary-50 font-medium text-lg py-3 px-8 rounded-lg transition-colors"
            >
              無料で始める
              <ArrowRight size={20} className="ml-2" />
            </Link>
          </div>
        </div>
      </section>

      {/* フッター */}
      <footer className="py-12 bg-gray-900 text-white" role="contentinfo">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <span className="text-2xl font-bold">SocialBoostAI</span>
              <p className="mt-4 text-gray-400 text-sm">
                AIの力でソーシャルメディアの成功を支援
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-4">サービス</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>
                  <a href="#features" className="hover:text-white transition-colors">
                    機能
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="hover:text-white transition-colors">
                    料金
                  </a>
                </li>
                <li>
                  <Link to="/login" className="hover:text-white transition-colors">
                    ログイン
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-4">法的情報</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>
                  <Link to="/terms" className="hover:text-white transition-colors">
                    利用規約
                  </Link>
                </li>
                <li>
                  <Link to="/privacy" className="hover:text-white transition-colors">
                    プライバシーポリシー
                  </Link>
                </li>
                <li>
                  <Link
                    to="/legal/tokushoho"
                    className="hover:text-white transition-colors"
                  >
                    特定商取引法に基づく表記
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-4">お問い合わせ</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>
                  <a
                    href="mailto:support@socialboostai.com"
                    className="hover:text-white transition-colors"
                  >
                    support@socialboostai.com
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t border-gray-800 text-center text-gray-400 text-sm">
            <p>© 2026 SocialBoostAI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
