/**
 * スケジュール投稿API（v2.3）
 */
import apiClient from './client';
import type {
  ScheduledPost,
  ScheduledPostCreate,
  ScheduledPostUpdate,
  ScheduledPostSummary,
  ScheduledPostListResponse,
  BulkScheduleRequest,
  BulkScheduleResponse,
  ScheduleStats,
} from '../types';

const BASE_URL = '/api/v1/schedule';

/**
 * スケジュール投稿一覧取得
 */
export const getScheduledPosts = async (
  page: number = 1,
  perPage: number = 20,
  status?: string,
  platform?: string
): Promise<ScheduledPostListResponse> => {
  const params: Record<string, unknown> = { page, per_page: perPage };
  if (status) params.status = status;
  if (platform) params.platform = platform;

  const response = await apiClient.get<ScheduledPostListResponse>(BASE_URL, { params });
  return response.data;
};

/**
 * スケジュール投稿作成
 */
export const createScheduledPost = async (
  data: ScheduledPostCreate
): Promise<ScheduledPost> => {
  const response = await apiClient.post<ScheduledPost>(BASE_URL, data);
  return response.data;
};

/**
 * スケジュール投稿詳細取得
 */
export const getScheduledPost = async (id: string): Promise<ScheduledPost> => {
  const response = await apiClient.get<ScheduledPost>(`${BASE_URL}/${id}`);
  return response.data;
};

/**
 * スケジュール投稿更新
 */
export const updateScheduledPost = async (
  id: string,
  data: ScheduledPostUpdate
): Promise<ScheduledPost> => {
  const response = await apiClient.put<ScheduledPost>(`${BASE_URL}/${id}`, data);
  return response.data;
};

/**
 * スケジュール投稿キャンセル
 */
export const cancelScheduledPost = async (id: string): Promise<ScheduledPost> => {
  const response = await apiClient.post<ScheduledPost>(`${BASE_URL}/${id}/cancel`);
  return response.data;
};

/**
 * スケジュール投稿削除
 */
export const deleteScheduledPost = async (id: string): Promise<void> => {
  await apiClient.delete(`${BASE_URL}/${id}`);
};

/**
 * 一括スケジュール作成（Business以上）
 */
export const bulkCreateScheduledPosts = async (
  data: BulkScheduleRequest
): Promise<BulkScheduleResponse> => {
  const response = await apiClient.post<BulkScheduleResponse>(`${BASE_URL}/bulk`, data);
  return response.data;
};

/**
 * スケジュール統計取得
 */
export const getScheduleStats = async (): Promise<ScheduleStats> => {
  const response = await apiClient.get<ScheduleStats>(`${BASE_URL}/stats`);
  return response.data;
};

/**
 * 今後の投稿取得
 */
export const getUpcomingPosts = async (
  days: number = 7,
  limit: number = 50
): Promise<ScheduledPostSummary[]> => {
  const response = await apiClient.get<ScheduledPostSummary[]>(`${BASE_URL}/upcoming`, {
    params: { days, limit },
  });
  return response.data;
};
