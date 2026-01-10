/**
 * LinkedIn分析API
 */
import apiClient from './client';
import type {
  LinkedInAnalysis,
  LinkedInAnalysisRequest,
  PaginatedResponse,
} from '../types';

// LinkedIn分析一覧取得
export const getLinkedInAnalyses = async (
  page: number = 1,
  perPage: number = 20
): Promise<PaginatedResponse<LinkedInAnalysis>> => {
  const response = await apiClient.get<PaginatedResponse<LinkedInAnalysis>>(
    '/api/v1/linkedin/analysis',
    {
      params: { page, per_page: perPage },
    }
  );
  return response.data;
};

// LinkedIn分析詳細取得
export const getLinkedInAnalysis = async (id: string): Promise<LinkedInAnalysis> => {
  const response = await apiClient.get<LinkedInAnalysis>(
    `/api/v1/linkedin/analysis/${id}`
  );
  return response.data;
};

// 新規LinkedIn分析作成
export const createLinkedInAnalysis = async (
  data: LinkedInAnalysisRequest
): Promise<LinkedInAnalysis> => {
  const response = await apiClient.post<LinkedInAnalysis>(
    '/api/v1/linkedin/analysis',
    data
  );
  return response.data;
};

// LinkedIn分析削除
export const deleteLinkedInAnalysis = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/linkedin/analysis/${id}`);
};
