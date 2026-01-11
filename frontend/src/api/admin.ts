/**
 * 管理者API関数
 */

import type {
  AdminUserDetail,
  AdminUserListResponse,
  AdminUserUpdateRequest,
  ActivityLogResponse,
  RevenueStats,
  SystemStats,
} from '../types';
import apiClient from './client';

const BASE_URL = '/api/v1/admin';

// =============================================================================
// ユーザー管理
// =============================================================================

/**
 * ユーザー一覧取得
 */
export async function getUsers(params: {
  page?: number;
  per_page?: number;
  role?: string;
  is_active?: boolean;
  search?: string;
}): Promise<AdminUserListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.append('page', String(params.page));
  if (params.per_page) searchParams.append('per_page', String(params.per_page));
  if (params.role) searchParams.append('role', params.role);
  if (params.is_active !== undefined)
    searchParams.append('is_active', String(params.is_active));
  if (params.search) searchParams.append('search', params.search);

  const queryString = searchParams.toString();
  const url = queryString ? `${BASE_URL}/users?${queryString}` : `${BASE_URL}/users`;
  const response = await apiClient.get<AdminUserListResponse>(url);
  return response.data;
}

/**
 * ユーザー詳細取得
 */
export async function getUser(userId: string): Promise<AdminUserDetail> {
  const response = await apiClient.get<AdminUserDetail>(`${BASE_URL}/users/${userId}`);
  return response.data;
}

/**
 * ユーザー更新
 */
export async function updateUser(
  userId: string,
  data: AdminUserUpdateRequest
): Promise<AdminUserDetail> {
  const response = await apiClient.put<AdminUserDetail>(`${BASE_URL}/users/${userId}`, data);
  return response.data;
}

/**
 * ユーザー削除（論理削除）
 */
export async function deleteUser(
  userId: string
): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(`${BASE_URL}/users/${userId}`);
  return response.data;
}

/**
 * パスワードリセット
 */
export async function resetUserPassword(userId: string): Promise<{
  message: string;
  temporary_password: string;
  note: string;
}> {
  const response = await apiClient.post<{
    message: string;
    temporary_password: string;
    note: string;
  }>(`${BASE_URL}/users/${userId}/reset-password`);
  return response.data;
}

// =============================================================================
// 統計
// =============================================================================

/**
 * システム統計取得
 */
export async function getSystemStats(): Promise<SystemStats> {
  const response = await apiClient.get<SystemStats>(`${BASE_URL}/stats/system`);
  return response.data;
}

/**
 * 収益統計取得
 */
export async function getRevenueStats(): Promise<RevenueStats> {
  const response = await apiClient.get<RevenueStats>(`${BASE_URL}/stats/revenue`);
  return response.data;
}

// =============================================================================
// アクティビティログ
// =============================================================================

/**
 * アクティビティログ取得
 */
export async function getActivityLog(params?: {
  page?: number;
  per_page?: number;
}): Promise<ActivityLogResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.append('page', String(params.page));
  if (params?.per_page) searchParams.append('per_page', String(params.per_page));

  const queryString = searchParams.toString();
  const url = queryString ? `${BASE_URL}/activity?${queryString}` : `${BASE_URL}/activity`;
  const response = await apiClient.get<ActivityLogResponse>(url);
  return response.data;
}
