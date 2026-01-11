/**
 * オンボーディングAPI
 */

import apiClient from './client';

// オンボーディングステップ名
export type OnboardingStepName =
  | 'welcome'
  | 'connect_platform'
  | 'select_goals'
  | 'setup_notifications'
  | 'first_analysis'
  | 'complete';

// ステップステータス
export type OnboardingStepStatus =
  | 'not_started'
  | 'in_progress'
  | 'completed'
  | 'skipped';

// オンボーディングステップ
export interface OnboardingStep {
  name: OnboardingStepName;
  status: OnboardingStepStatus;
  completed_at: string | null;
  data: Record<string, unknown> | null;
}

// オンボーディング状態レスポンス
export interface OnboardingStatusResponse {
  is_completed: boolean;
  current_step: OnboardingStepName;
  steps: OnboardingStep[];
  started_at: string | null;
  completed_at: string | null;
  progress_percent: number;
}

// ステップ完了リクエスト
export interface OnboardingCompleteStepRequest {
  step_name: OnboardingStepName;
  data?: Record<string, unknown>;
}

// スキップリクエスト
export interface OnboardingSkipRequest {
  reason?: string;
}

/**
 * オンボーディング状態を取得
 */
export async function getOnboardingStatus(): Promise<OnboardingStatusResponse> {
  const response = await apiClient.get<OnboardingStatusResponse>(
    '/api/v1/onboarding/status'
  );
  return response.data;
}

/**
 * オンボーディングを開始
 */
export async function startOnboarding(): Promise<OnboardingStatusResponse> {
  const response = await apiClient.post<OnboardingStatusResponse>(
    '/api/v1/onboarding/start'
  );
  return response.data;
}

/**
 * ステップを完了
 */
export async function completeOnboardingStep(
  request: OnboardingCompleteStepRequest
): Promise<OnboardingStatusResponse> {
  const response = await apiClient.post<OnboardingStatusResponse>(
    '/api/v1/onboarding/complete-step',
    request
  );
  return response.data;
}

/**
 * ステップをスキップ
 */
export async function skipOnboardingStep(
  stepName: OnboardingStepName
): Promise<OnboardingStatusResponse> {
  const response = await apiClient.post<OnboardingStatusResponse>(
    `/api/v1/onboarding/skip-step/${stepName}`
  );
  return response.data;
}

/**
 * オンボーディング全体をスキップ
 */
export async function skipAllOnboarding(
  request?: OnboardingSkipRequest
): Promise<OnboardingStatusResponse> {
  const response = await apiClient.post<OnboardingStatusResponse>(
    '/api/v1/onboarding/skip-all',
    request || {}
  );
  return response.data;
}

/**
 * オンボーディングをリセット（開発用）
 */
export async function resetOnboarding(): Promise<OnboardingStatusResponse> {
  const response = await apiClient.post<OnboardingStatusResponse>(
    '/api/v1/onboarding/reset'
  );
  return response.data;
}
