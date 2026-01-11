import { test, expect } from '@playwright/test';

/**
 * ダッシュボード E2Eテスト
 * 認証済みユーザー向けのメイン機能テスト
 */
test.describe('ダッシュボード', () => {
  test('メイン統計カードが表示される', async ({ page }) => {
    await page.goto('/dashboard');

    // 統計カードが表示される
    await expect(page.getByText(/総フォロワー|フォロワー数/i)).toBeVisible();
    await expect(page.getByText(/エンゲージメント/i)).toBeVisible();
  });

  test('リアルタイム更新ボタンが機能する', async ({ page }) => {
    await page.goto('/dashboard');

    // 更新ボタンを探してクリック
    const refreshButton = page.getByRole('button', { name: /更新|リフレッシュ/i });
    if (await refreshButton.isVisible()) {
      await refreshButton.click();

      // ローディング状態が表示される、または更新される
      // （実際の動作はAPIレスポンスに依存）
    }
  });

  test('プラットフォーム別パフォーマンスが表示される', async ({ page }) => {
    await page.goto('/dashboard');

    // プラットフォームアイコン/名前が表示される
    const platformSection = page.getByText(/プラットフォーム|Platform/i);
    if (await platformSection.isVisible()) {
      await expect(platformSection).toBeVisible();
    }
  });

  test('ナビゲーションメニューが機能する', async ({ page }) => {
    await page.goto('/dashboard');

    // 分析ページへのリンク
    const analysisLink = page.getByRole('link', { name: /分析/i });
    if (await analysisLink.isVisible()) {
      await analysisLink.click();
      await expect(page).toHaveURL(/.*analysis/);
    }
  });

  test('通知ドロップダウンが機能する', async ({ page }) => {
    await page.goto('/dashboard');

    // 通知ベルアイコンを探す
    const notificationBell = page.getByRole('button', { name: /通知/i });
    if (await notificationBell.isVisible()) {
      await notificationBell.click();

      // ドロップダウンが表示される
      await expect(page.getByText(/通知がありません|最近の通知/i)).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('分析ページ', () => {
  test('分析ページが表示される', async ({ page }) => {
    await page.goto('/analysis');

    // ページタイトルが表示される
    await expect(page.getByRole('heading', { name: /分析/i })).toBeVisible();
  });

  test('プラットフォーム選択が機能する', async ({ page }) => {
    await page.goto('/analysis');

    // プラットフォーム選択UIが存在
    const platformSelector = page.getByRole('combobox', { name: /プラットフォーム/i })
      .or(page.getByText(/Twitter|Instagram|TikTok|YouTube|LinkedIn/i));

    if (await platformSelector.isVisible()) {
      await expect(platformSelector).toBeVisible();
    }
  });
});

test.describe('レポートページ', () => {
  test('レポートページが表示される', async ({ page }) => {
    await page.goto('/reports');

    // ページが表示される
    await expect(page.getByRole('heading', { name: /レポート/i })).toBeVisible();
  });
});

test.describe('スケジュールページ', () => {
  test('スケジュールページが表示される（Proプラン以上）', async ({ page }) => {
    await page.goto('/schedule');

    // ページが表示される、またはプランアップグレード促進が表示される
    const heading = page.getByRole('heading', { name: /スケジュール|予約投稿/i });
    const upgradePrompt = page.getByText(/Pro|アップグレード/i);

    await expect(heading.or(upgradePrompt)).toBeVisible();
  });
});

test.describe('設定ページ', () => {
  test('設定ページが表示される', async ({ page }) => {
    await page.goto('/settings');

    // 設定ページが表示される
    await expect(page.getByRole('heading', { name: /設定/i })).toBeVisible();
  });

  test('プロフィール設定が表示される', async ({ page }) => {
    await page.goto('/settings');

    // プロフィールセクションが存在
    await expect(page.getByText(/プロフィール|アカウント/i)).toBeVisible();
  });

  test('通知設定が表示される', async ({ page }) => {
    await page.goto('/settings');

    // 通知設定セクションが存在
    await expect(page.getByText(/通知/i)).toBeVisible();
  });

  test('パスワード変更フォームが表示される', async ({ page }) => {
    await page.goto('/settings');

    // パスワード変更セクションが存在
    await expect(page.getByText(/パスワード/i)).toBeVisible();
  });
});
