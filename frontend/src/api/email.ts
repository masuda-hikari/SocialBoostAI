/**
 * メール通知API
 */
import apiClient from './client';

// 型定義
export interface EmailStatus {
  enabled: boolean;
  message: string;
}

export interface EmailPreferences {
  weekly_report: boolean;
  monthly_report: boolean;
  analysis_complete: boolean;
  engagement_alerts: boolean;
  billing_notifications: boolean;
  updated_at: string;
}

export interface EmailPreferencesUpdate {
  weekly_report?: boolean;
  monthly_report?: boolean;
  analysis_complete?: boolean;
  engagement_alerts?: boolean;
  billing_notifications?: boolean;
}

export interface SendTestEmailRequest {
  template_type: 'welcome' | 'analysis_complete' | 'weekly_report' | 'engagement_alert';
}

export interface SendTestEmailResponse {
  success: boolean;
  message: string;
}

/**
 * メール送信状態を取得
 */
export async function getEmailStatus(): Promise<EmailStatus> {
  const response = await apiClient.get('/email/status');
  return response.data;
}

/**
 * メール通知設定を取得
 */
export async function getEmailPreferences(): Promise<EmailPreferences> {
  const response = await apiClient.get('/email/preferences');
  return response.data;
}

/**
 * メール通知設定を更新
 */
export async function updateEmailPreferences(
  preferences: EmailPreferencesUpdate
): Promise<EmailPreferences> {
  const response = await apiClient.put('/email/preferences', preferences);
  return response.data;
}

/**
 * テストメールを送信
 */
export async function sendTestEmail(
  templateType: SendTestEmailRequest['template_type']
): Promise<SendTestEmailResponse> {
  const response = await apiClient.post('/email/test', {
    template_type: templateType,
  });
  return response.data;
}

/**
 * 週次レポートメールを送信（Pro以上）
 */
export async function sendWeeklyReportEmail(): Promise<SendTestEmailResponse> {
  const response = await apiClient.post('/email/send-weekly-report');
  return response.data;
}
