/**
 * YouTube分析API
 */
import apiClient from './client';
import type {
  YouTubeAnalysis,
  YouTubeAnalysisRequest,
  PaginatedResponse,
} from '../types';

// YouTube分析一覧取得
export const getYouTubeAnalyses = async (
  page: number = 1,
  perPage: number = 20
): Promise<PaginatedResponse<YouTubeAnalysis>> => {
  const response = await apiClient.get<PaginatedResponse<YouTubeAnalysis>>(
    '/api/v1/youtube/analysis',
    {
      params: { page, per_page: perPage },
    }
  );
  return response.data;
};

// YouTube分析詳細取得
export const getYouTubeAnalysis = async (id: string): Promise<YouTubeAnalysis> => {
  const response = await apiClient.get<YouTubeAnalysis>(
    `/api/v1/youtube/analysis/${id}`
  );
  return response.data;
};

// 新規YouTube分析作成
export const createYouTubeAnalysis = async (
  data: YouTubeAnalysisRequest
): Promise<YouTubeAnalysis> => {
  const response = await apiClient.post<YouTubeAnalysis>(
    '/api/v1/youtube/analysis',
    data
  );
  return response.data;
};

// YouTube分析削除
export const deleteYouTubeAnalysis = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/youtube/analysis/${id}`);
};
