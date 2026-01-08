/**
 * 分析API
 */
import apiClient from './client';
import type { Analysis, AnalysisRequest, PaginatedResponse } from '../types';

// 分析一覧取得
export const getAnalyses = async (
  page: number = 1,
  perPage: number = 20
): Promise<PaginatedResponse<Analysis>> => {
  const response = await apiClient.get<PaginatedResponse<Analysis>>('/api/v1/analysis', {
    params: { page, per_page: perPage },
  });
  return response.data;
};

// 分析詳細取得
export const getAnalysis = async (id: string): Promise<Analysis> => {
  const response = await apiClient.get<Analysis>(`/api/v1/analysis/${id}`);
  return response.data;
};

// 新規分析作成
export const createAnalysis = async (data: AnalysisRequest): Promise<Analysis> => {
  const response = await apiClient.post<Analysis>('/api/v1/analysis', data);
  return response.data;
};

// 分析削除
export const deleteAnalysis = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/analysis/${id}`);
};
