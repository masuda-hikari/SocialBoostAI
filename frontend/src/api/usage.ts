/**
 * 使用量モニタリングAPI
 */

import apiClient from './client';
import type {
  ApiCallLogsResponse,
  DailyUsage,
  MonthlyUsageSummary,
  PlanLimits,
  UpgradeRecommendation,
  UsageDashboard,
  UsageHistoryResponse,
  UsageLimitCheckResponse,
  UsageTrend,
  UsageWithLimits,
} from '../types';

/**
 * 使用量ダッシュボード取得
 */
export const getUsageDashboard = async (): Promise<UsageDashboard> => {
  const response = await apiClient.get('/usage/dashboard');
  return response.data;
};

/**
 * 今日の使用量取得
 */
export const getTodayUsage = async (): Promise<DailyUsage> => {
  const response = await apiClient.get('/usage/today');
  return response.data;
};

/**
 * 使用量と制限取得
 */
export const getUsageWithLimits = async (): Promise<UsageWithLimits> => {
  const response = await apiClient.get('/usage/with-limits');
  return response.data;
};

/**
 * プラン制限取得
 */
export const getUsagePlanLimits = async (): Promise<PlanLimits> => {
  const response = await apiClient.get('/usage/limits');
  return response.data;
};

/**
 * 使用量履歴取得
 */
export const getUsageHistory = async (
  days: number = 30
): Promise<UsageHistoryResponse> => {
  const response = await apiClient.get('/usage/history', {
    params: { days },
  });
  return response.data;
};

/**
 * 月次使用量サマリー取得
 */
export const getMonthlyUsageSummary = async (
  yearMonth?: string
): Promise<MonthlyUsageSummary | null> => {
  const response = await apiClient.get('/usage/monthly', {
    params: yearMonth ? { year_month: yearMonth } : undefined,
  });
  return response.data;
};

/**
 * 使用量トレンド取得
 */
export const getUsageTrend = async (
  days: number = 7
): Promise<UsageTrend> => {
  const response = await apiClient.get('/usage/trend', {
    params: { days },
  });
  return response.data;
};

/**
 * API呼び出しログ取得
 */
export const getApiCallLogs = async (
  page: number = 1,
  perPage: number = 20,
  endpointFilter?: string
): Promise<ApiCallLogsResponse> => {
  const response = await apiClient.get('/usage/logs', {
    params: {
      page,
      per_page: perPage,
      ...(endpointFilter && { endpoint: endpointFilter }),
    },
  });
  return response.data;
};

/**
 * アップグレード推奨取得
 */
export const getUpgradeRecommendation = async (): Promise<UpgradeRecommendation> => {
  const response = await apiClient.get('/usage/upgrade-recommendation');
  return response.data;
};

/**
 * 使用量制限チェック
 */
export const checkUsageLimit = async (
  usageType: string,
  count: number = 1
): Promise<UsageLimitCheckResponse> => {
  const response = await apiClient.get(`/usage/check/${usageType}`, {
    params: { count },
  });
  return response.data;
};
