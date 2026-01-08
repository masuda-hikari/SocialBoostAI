/**
 * 課金API
 */
import apiClient from './client';
import type {
  PlanInfo,
  PlanTier,
  Subscription,
  CheckoutSessionRequest,
  CheckoutSessionResponse,
} from '../types';

// プラン一覧取得
export const getPlans = async (): Promise<PlanInfo[]> => {
  const response = await apiClient.get<PlanInfo[]>('/api/v1/billing/plans');
  return response.data;
};

// プラン詳細取得
export const getPlan = async (tier: PlanTier): Promise<PlanInfo> => {
  const response = await apiClient.get<PlanInfo>(`/api/v1/billing/plans/${tier}`);
  return response.data;
};

// 現在のサブスクリプション取得
export const getSubscription = async (): Promise<Subscription | null> => {
  try {
    const response = await apiClient.get<Subscription>('/api/v1/billing/subscription');
    return response.data;
  } catch {
    return null;
  }
};

// Checkout Session作成
export const createCheckoutSession = async (
  data: CheckoutSessionRequest
): Promise<CheckoutSessionResponse> => {
  const response = await apiClient.post<CheckoutSessionResponse>(
    '/api/v1/billing/checkout',
    data
  );
  return response.data;
};

// Customer Portal Session作成
export const createPortalSession = async (
  returnUrl: string
): Promise<{ portal_url: string }> => {
  const response = await apiClient.post<{ portal_url: string }>(
    '/api/v1/billing/portal',
    { return_url: returnUrl }
  );
  return response.data;
};

// サブスクリプションキャンセル
export const cancelSubscription = async (
  atPeriodEnd: boolean = true
): Promise<Subscription> => {
  const response = await apiClient.post<Subscription>('/api/v1/billing/cancel', {
    at_period_end: atPeriodEnd,
  });
  return response.data;
};

// プラン制限取得
export interface PlanLimits {
  plan: PlanTier;
  api_calls_per_day: number;
  api_calls_used_today: number;
  reports_per_month: number;
  reports_used_this_month: number;
  platforms: number;
  history_days: number;
}

export const getPlanLimits = async (): Promise<PlanLimits> => {
  const response = await apiClient.get<PlanLimits>('/api/v1/billing/limits');
  return response.data;
};
