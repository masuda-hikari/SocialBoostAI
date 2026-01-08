/**
 * Instagram分析API
 */
import apiClient from './client';
import type {
  InstagramAnalysis,
  InstagramAnalysisRequest,
  PaginatedResponse,
} from '../types';

// Instagram分析一覧取得
export const getInstagramAnalyses = async (
  page: number = 1,
  perPage: number = 20
): Promise<PaginatedResponse<InstagramAnalysis>> => {
  const response = await apiClient.get<PaginatedResponse<InstagramAnalysis>>(
    '/api/v1/instagram/analysis',
    {
      params: { page, per_page: perPage },
    }
  );
  return response.data;
};

// Instagram分析詳細取得
export const getInstagramAnalysis = async (id: string): Promise<InstagramAnalysis> => {
  const response = await apiClient.get<InstagramAnalysis>(
    `/api/v1/instagram/analysis/${id}`
  );
  return response.data;
};

// 新規Instagram分析作成
export const createInstagramAnalysis = async (
  data: InstagramAnalysisRequest
): Promise<InstagramAnalysis> => {
  const response = await apiClient.post<InstagramAnalysis>(
    '/api/v1/instagram/analysis',
    data
  );
  return response.data;
};

// Instagram分析削除
export const deleteInstagramAnalysis = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/instagram/analysis/${id}`);
};
