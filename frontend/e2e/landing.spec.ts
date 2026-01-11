import { test, expect } from '@playwright/test';

/**
 * ランディングページ E2Eテスト
 * 未認証ユーザー向けの公開ページテスト
 */
test.describe('ランディングページ', () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // 未認証状態

  test('ページが正常に表示される', async ({ page }) => {
    await page.goto('/');

    // ヘッダーロゴが表示される
    await expect(page.getByRole('heading', { name: /SocialBoostAI/i })).toBeVisible();

    // CTAボタンが表示される
    await expect(page.getByRole('link', { name: /無料で始める/i })).toBeVisible();
  });

  test('機能セクションが表示される', async ({ page }) => {
    await page.goto('/');

    // 機能セクションが存在する
    await expect(page.getByRole('heading', { name: /機能/i })).toBeVisible();
  });

  test('料金プランセクションが表示される', async ({ page }) => {
    await page.goto('/');

    // 料金プランセクションまでスクロール
    await page.getByRole('heading', { name: /料金プラン/i }).scrollIntoViewIfNeeded();

    // 各プランが表示される
    await expect(page.getByText(/Free/i)).toBeVisible();
    await expect(page.getByText(/Pro/i)).toBeVisible();
    await expect(page.getByText(/Business/i)).toBeVisible();
  });

  test('ナビゲーションリンクが機能する', async ({ page }) => {
    await page.goto('/');

    // ログインリンクをクリック
    await page.getByRole('link', { name: /ログイン/i }).click();

    // ログインページに遷移
    await expect(page).toHaveURL(/.*login/);
  });

  test('フッターリンクが存在する', async ({ page }) => {
    await page.goto('/');

    // フッターまでスクロール
    await page.locator('footer').scrollIntoViewIfNeeded();

    // 法務ページへのリンクが存在
    await expect(page.getByRole('link', { name: /利用規約/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /プライバシーポリシー/i })).toBeVisible();
  });

  test('モバイルメニューが機能する', async ({ page }) => {
    // モバイルビューポートに設定
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // ハンバーガーメニューが表示される
    const menuButton = page.getByRole('button', { name: /メニュー/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();

      // モバイルメニューが展開される
      await expect(page.getByRole('link', { name: /ログイン/i })).toBeVisible();
    }
  });
});
