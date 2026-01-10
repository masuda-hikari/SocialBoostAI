/**
 * AIコンテンツ生成 APIクライアント
 */

import api from './client';
import type {
  ABTestResponse,
  ABTestVariationRequest,
  ContentCalendarRequest,
  ContentCalendarResponse,
  ContentGenerationRequest,
  ContentGenerationSummary,
  ContentRewriteRequest,
  GeneratedContent,
  PaginatedResponse,
  TrendingContentRequest,
  TrendingContentResponse,
} from '../types';

const CONTENT_ENDPOINT = '/api/v1/content';

/**
 * コンテンツを生成
 */
export const generateContent = async (
  request: ContentGenerationRequest
): Promise<GeneratedContent> => {
  const response = await api.post<GeneratedContent>(
    `${CONTENT_ENDPOINT}/generate`,
    request
  );
  return response.data;
};

/**
 * コンテンツを別プラットフォーム向けにリライト
 */
export const rewriteContent = async (
  request: ContentRewriteRequest
): Promise<GeneratedContent> => {
  const response = await api.post<GeneratedContent>(
    `${CONTENT_ENDPOINT}/rewrite`,
    request
  );
  return response.data;
};

/**
 * A/Bテスト用バリエーションを生成
 */
export const generateABVariations = async (
  request: ABTestVariationRequest
): Promise<ABTestResponse> => {
  const response = await api.post<ABTestResponse>(
    `${CONTENT_ENDPOINT}/ab-test`,
    request
  );
  return response.data;
};

/**
 * コンテンツカレンダーを生成
 */
export const generateContentCalendar = async (
  request: ContentCalendarRequest
): Promise<ContentCalendarResponse> => {
  const response = await api.post<ContentCalendarResponse>(
    `${CONTENT_ENDPOINT}/calendar`,
    request
  );
  return response.data;
};

/**
 * トレンドを活用したコンテンツを生成
 */
export const generateTrendingContent = async (
  request: TrendingContentRequest
): Promise<TrendingContentResponse> => {
  const response = await api.post<TrendingContentResponse>(
    `${CONTENT_ENDPOINT}/trending`,
    request
  );
  return response.data;
};

/**
 * 生成履歴を取得
 */
export const getGenerationHistory = async (
  page: number = 1,
  perPage: number = 20
): Promise<PaginatedResponse<ContentGenerationSummary>> => {
  const response = await api.get<PaginatedResponse<ContentGenerationSummary>>(
    `${CONTENT_ENDPOINT}/history`,
    {
      params: { page, per_page: perPage },
    }
  );
  return response.data;
};

/**
 * 生成履歴を削除
 */
export const deleteGenerationHistory = async (
  generationId: string
): Promise<void> => {
  await api.delete(`${CONTENT_ENDPOINT}/history/${generationId}`);
};
