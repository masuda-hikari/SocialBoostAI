/**
 * 課金ページ
 */
import { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import {
  getPlans,
  getSubscription,
  createCheckoutSession,
  createPortalSession,
} from '../api';
import type { PlanInfo, Subscription, PlanTier } from '../types';
import { Check, Crown, Zap, Building2, Rocket } from 'lucide-react';

export default function BillingPage() {
  const { user } = useAuthStore();
  const [plans, setPlans] = useState<PlanInfo[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<PlanTier | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [plansRes, subRes] = await Promise.all([getPlans(), getSubscription()]);
        setPlans(plansRes);
        setSubscription(subRes);
      } catch (error) {
        console.error('データ取得エラー:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleUpgrade = async (tier: PlanTier) => {
    if (tier === 'free') return;

    setCheckoutLoading(tier);
    try {
      const response = await createCheckoutSession({
        plan: tier,
        success_url: `${window.location.origin}/billing?success=true`,
        cancel_url: `${window.location.origin}/billing?canceled=true`,
      });
      window.location.href = response.checkout_url;
    } catch (error) {
      console.error('Checkout作成エラー:', error);
      alert('チェックアウトの作成に失敗しました');
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const response = await createPortalSession(window.location.href);
      window.location.href = response.portal_url;
    } catch (error) {
      console.error('Portal作成エラー:', error);
      alert('サブスクリプション管理ページの作成に失敗しました');
    }
  };

  const getPlanIcon = (tier: PlanTier) => {
    switch (tier) {
      case 'free':
        return <Rocket className="text-gray-500" size={32} />;
      case 'pro':
        return <Zap className="text-primary-500" size={32} />;
      case 'business':
        return <Crown className="text-yellow-500" size={32} />;
      case 'enterprise':
        return <Building2 className="text-purple-500" size={32} />;
    }
  };

  const formatPrice = (price: number) => {
    if (price === 0) return '無料';
    return `¥${price.toLocaleString()}`;
  };

  const formatLimit = (value: number) => {
    if (value === -1) return '無制限';
    return value.toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const currentPlan = user?.role || 'free';

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">料金プラン</h1>
        <p className="text-gray-600">あなたのニーズに合ったプランを選択してください</p>
      </div>

      {/* 現在のサブスクリプション */}
      {subscription && subscription.status === 'active' && (
        <div className="card bg-primary-50 border border-primary-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium text-primary-900">現在のプラン</h3>
              <p className="text-sm text-primary-700 capitalize">
                {subscription.plan}プラン -{' '}
                {new Date(subscription.current_period_end).toLocaleDateString('ja-JP')}まで
              </p>
              {subscription.cancel_at_period_end && (
                <p className="text-sm text-red-600 mt-1">
                  期間終了後にキャンセルされます
                </p>
              )}
            </div>
            <button onClick={handleManageSubscription} className="btn-outline">
              サブスクリプション管理
            </button>
          </div>
        </div>
      )}

      {/* プランカード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => {
          const isCurrentPlan = currentPlan === plan.tier;
          const isPopular = plan.tier === 'pro';

          return (
            <div
              key={plan.tier}
              className={`card relative ${
                isPopular ? 'ring-2 ring-primary-500 shadow-lg' : ''
              } ${isCurrentPlan ? 'bg-primary-50' : ''}`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-primary-500 text-white text-xs font-medium px-3 py-1 rounded-full">
                    人気
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <div className="flex justify-center mb-4">{getPlanIcon(plan.tier)}</div>
                <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-3xl font-bold text-gray-900">
                    {formatPrice(plan.price_monthly)}
                  </span>
                  {plan.price_monthly > 0 && (
                    <span className="text-gray-500">/月</span>
                  )}
                </div>
              </div>

              <ul className="space-y-3 mb-6">
                <li className="flex items-center text-sm">
                  <Check size={16} className="text-green-500 mr-2 flex-shrink-0" />
                  <span>
                    API呼出: <strong>{formatLimit(plan.api_calls_per_day)}</strong>/日
                  </span>
                </li>
                <li className="flex items-center text-sm">
                  <Check size={16} className="text-green-500 mr-2 flex-shrink-0" />
                  <span>
                    レポート: <strong>{formatLimit(plan.reports_per_month)}</strong>/月
                  </span>
                </li>
                <li className="flex items-center text-sm">
                  <Check size={16} className="text-green-500 mr-2 flex-shrink-0" />
                  <span>
                    プラットフォーム: <strong>{formatLimit(plan.platforms)}</strong>
                  </span>
                </li>
                <li className="flex items-center text-sm">
                  <Check size={16} className="text-green-500 mr-2 flex-shrink-0" />
                  <span>
                    履歴: <strong>{formatLimit(plan.history_days)}</strong>日分
                  </span>
                </li>
              </ul>

              {isCurrentPlan ? (
                <button
                  disabled
                  className="w-full py-3 px-4 bg-gray-100 text-gray-500 font-medium rounded-lg cursor-not-allowed"
                >
                  現在のプラン
                </button>
              ) : plan.tier === 'enterprise' ? (
                <a
                  href="mailto:contact@socialboostai.com"
                  className="block w-full py-3 px-4 text-center bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
                >
                  お問い合わせ
                </a>
              ) : plan.tier === 'free' ? (
                <button
                  disabled
                  className="w-full py-3 px-4 bg-gray-100 text-gray-500 font-medium rounded-lg cursor-not-allowed"
                >
                  無料プラン
                </button>
              ) : (
                <button
                  onClick={() => handleUpgrade(plan.tier)}
                  disabled={checkoutLoading === plan.tier}
                  className={`w-full py-3 px-4 font-medium rounded-lg transition-colors ${
                    isPopular
                      ? 'bg-primary-600 hover:bg-primary-700 text-white'
                      : 'bg-gray-900 hover:bg-gray-800 text-white'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {checkoutLoading === plan.tier ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      処理中...
                    </span>
                  ) : (
                    'アップグレード'
                  )}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* FAQ */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">よくある質問</h3>
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900">いつでもキャンセルできますか？</h4>
            <p className="text-sm text-gray-600 mt-1">
              はい、いつでもキャンセル可能です。キャンセル後も現在の請求期間の終了まで利用できます。
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">プランを変更するとどうなりますか？</h4>
            <p className="text-sm text-gray-600 mt-1">
              アップグレードは即座に反映されます。ダウングレードは次の請求期間から適用されます。
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900">支払い方法は？</h4>
            <p className="text-sm text-gray-600 mt-1">
              クレジットカード（Visa、Mastercard、American Express、JCB）に対応しています。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
