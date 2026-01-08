/**
 * 認証API
 */
import apiClient from './client';
import type { User, TokenResponse, LoginRequest, RegisterRequest } from '../types';

// ログイン
export const login = async (data: LoginRequest): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', data);
  return response.data;
};

// ユーザー登録
export const register = async (data: RegisterRequest): Promise<User> => {
  const response = await apiClient.post<User>('/api/v1/auth/register', data);
  return response.data;
};

// ログアウト
export const logout = async (): Promise<void> => {
  await apiClient.post('/api/v1/auth/logout');
  localStorage.removeItem('access_token');
};

// 現在のユーザー情報取得
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/api/v1/users/me');
  return response.data;
};
