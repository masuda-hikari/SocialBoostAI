/**
 * TikTok分析API
 */
import apiClient from './client';
import type {
  TikTokAnalysis,
  TikTokAnalysisRequest,
  PaginatedResponse,
} from '../types';

// TikTok分析一覧取得
export const getTikTokAnalyses = async (
  page: number = 1,
  perPage: number = 20
): Promise<PaginatedResponse<TikTokAnalysis>> => {
  const response = await apiClient.get<PaginatedResponse<TikTokAnalysis>>(
    '/api/v1/tiktok/analysis',
    {
      params: { page, per_page: perPage },
    }
  );
  return response.data;
};

// TikTok分析詳細取得
export const getTikTokAnalysis = async (id: string): Promise<TikTokAnalysis> => {
  const response = await apiClient.get<TikTokAnalysis>(
    `/api/v1/tiktok/analysis/${id}`
  );
  return response.data;
};

// 新規TikTok分析作成
export const createTikTokAnalysis = async (
  data: TikTokAnalysisRequest
): Promise<TikTokAnalysis> => {
  const response = await apiClient.post<TikTokAnalysis>(
    '/api/v1/tiktok/analysis',
    data
  );
  return response.data;
};

// TikTok分析削除
export const deleteTikTokAnalysis = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/tiktok/analysis/${id}`);
};
