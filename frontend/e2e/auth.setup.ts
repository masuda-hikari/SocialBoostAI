import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

/**
 * 認証セットアップ
 * テスト用ユーザーでログインし、認証状態を保存
 */
setup('authenticate', async ({ page }) => {
  // テスト用ユーザー情報
  const testEmail = process.env.TEST_USER_EMAIL || 'test@example.com';
  const testPassword = process.env.TEST_USER_PASSWORD || 'testpassword123';

  // ログインページに移動
  await page.goto('/login');

  // ログインフォームに入力
  await page.getByLabel('メールアドレス').fill(testEmail);
  await page.getByLabel('パスワード').fill(testPassword);

  // ログインボタンをクリック
  await page.getByRole('button', { name: 'ログイン' }).click();

  // ダッシュボードにリダイレクトされることを確認
  await expect(page).toHaveURL(/.*dashboard/);

  // 認証状態を保存
  await page.context().storageState({ path: authFile });
});
