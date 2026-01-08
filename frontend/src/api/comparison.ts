/**
 * クロスプラットフォーム比較API
 */
import type {
  CrossPlatformComparison,
  CrossPlatformComparisonRequest,
  CrossPlatformComparisonSummary,
  PaginatedResponse,
} from '../types';
import apiClient from './client';

/**
 * クロスプラットフォーム比較を作成
 */
export async function createComparison(
  request: CrossPlatformComparisonRequest
): Promise<CrossPlatformComparison> {
  const response = await apiClient.post<CrossPlatformComparison>(
    '/api/v1/cross-platform/comparisons',
    request
  );
  return response.data;
}

/**
 * 比較履歴一覧を取得
 */
export async function getComparisons(
  page = 1,
  perPage = 20
): Promise<PaginatedResponse<CrossPlatformComparisonSummary>> {
  const response = await apiClient.get<
    PaginatedResponse<CrossPlatformComparisonSummary>
  >('/api/v1/cross-platform/comparisons', {
    params: { page, per_page: perPage },
  });
  return response.data;
}

/**
 * 比較詳細を取得
 */
export async function getComparison(
  comparisonId: string
): Promise<CrossPlatformComparison> {
  const response = await apiClient.get<CrossPlatformComparison>(
    `/api/v1/cross-platform/comparisons/${comparisonId}`
  );
  return response.data;
}

/**
 * 比較を削除
 */
export async function deleteComparison(comparisonId: string): Promise<void> {
  await apiClient.delete(`/api/v1/cross-platform/comparisons/${comparisonId}`);
}
