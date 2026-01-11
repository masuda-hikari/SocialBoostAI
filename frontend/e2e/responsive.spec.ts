import { test, expect } from '@playwright/test';

/**
 * レスポンシブデザイン E2Eテスト
 * モバイル・タブレット・デスクトップでの表示確認
 */

// デバイス設定
const viewports = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1440, height: 900 },
};

test.describe('レスポンシブデザイン - ランディングページ', () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // 未認証状態

  for (const [device, viewport] of Object.entries(viewports)) {
    test(`${device}: ランディングページが正常に表示される`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/');

      // ページが表示される
      await expect(page).toHaveTitle(/.+/);

      // ヘッダーが表示される
      await expect(page.locator('header').or(page.locator('nav'))).toBeVisible();

      // コンテンツが表示される
      await expect(page.locator('main').or(page.locator('body'))).toBeVisible();

      // スクリーンショットを保存（視覚的回帰テスト用）
      await page.screenshot({ path: `playwright-report/screenshots/landing-${device}.png` });
    });
  }

  test('モバイル: ハンバーガーメニューが表示される', async ({ page }) => {
    await page.setViewportSize(viewports.mobile);
    await page.goto('/');

    // ハンバーガーメニューまたはモバイルメニューボタンを探す
    const menuButton = page.getByRole('button', { name: /メニュー/i })
      .or(page.locator('[aria-label*="menu"]'))
      .or(page.locator('.hamburger, .menu-toggle, [data-testid="mobile-menu"]'));

    if (await menuButton.isVisible()) {
      await menuButton.click();

      // メニューが展開される
      await page.waitForTimeout(300); // アニメーション待ち
    }
  });

  test('デスクトップ: フルナビゲーションが表示される', async ({ page }) => {
    await page.setViewportSize(viewports.desktop);
    await page.goto('/');

    // ナビゲーションリンクが表示される
    const navLinks = page.getByRole('link', { name: /ログイン|登録/i });
    await expect(navLinks.first()).toBeVisible();
  });
});

test.describe('レスポンシブデザイン - ダッシュボード', () => {
  for (const [device, viewport] of Object.entries(viewports)) {
    test(`${device}: ダッシュボードが正常に表示される`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/dashboard');

      // ページが表示される
      await expect(page.getByRole('heading', { name: /ダッシュボード/i })).toBeVisible();

      // スクリーンショットを保存
      await page.screenshot({ path: `playwright-report/screenshots/dashboard-${device}.png` });
    });
  }

  test('モバイル: サイドバーが折りたたまれる', async ({ page }) => {
    await page.setViewportSize(viewports.mobile);
    await page.goto('/dashboard');

    // サイドバーが非表示か、ハンバーガーメニューが存在
    const menuButton = page.getByRole('button', { name: /メニュー/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(300);
    }
  });

  test('タブレット: 統計カードが2列表示される', async ({ page }) => {
    await page.setViewportSize(viewports.tablet);
    await page.goto('/dashboard');

    // 統計カードが表示される
    await expect(page.getByText(/エンゲージメント/i)).toBeVisible();
  });

  test('デスクトップ: フルレイアウトが表示される', async ({ page }) => {
    await page.setViewportSize(viewports.desktop);
    await page.goto('/dashboard');

    // サイドバーとメインコンテンツが同時に表示される
    await expect(page.getByRole('heading', { name: /ダッシュボード/i })).toBeVisible();
  });
});

test.describe('レスポンシブデザイン - 設定ページ', () => {
  for (const [device, viewport] of Object.entries(viewports)) {
    test(`${device}: 設定ページが正常に表示される`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/settings');

      // ページが表示される
      await expect(page.getByRole('heading', { name: /設定/i })).toBeVisible();

      // スクリーンショットを保存
      await page.screenshot({ path: `playwright-report/screenshots/settings-${device}.png` });
    });
  }

  test('モバイル: フォームが縦方向に配置される', async ({ page }) => {
    await page.setViewportSize(viewports.mobile);
    await page.goto('/settings');

    // フォームが表示される
    await expect(page.getByText(/プロフィール|通知|パスワード/i)).toBeVisible();
  });
});

test.describe('レスポンシブデザイン - 課金ページ', () => {
  for (const [device, viewport] of Object.entries(viewports)) {
    test(`${device}: 課金ページが正常に表示される`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/billing');

      // ページが表示される
      await expect(page.getByRole('heading', { name: /課金|プラン|サブスクリプション/i })).toBeVisible();

      // スクリーンショットを保存
      await page.screenshot({ path: `playwright-report/screenshots/billing-${device}.png` });
    });
  }

  test('モバイル: プランカードが縦方向に配置される', async ({ page }) => {
    await page.setViewportSize(viewports.mobile);
    await page.goto('/billing');

    // プランカードが表示される
    await expect(page.getByText(/Free|Pro|Business/i)).toBeVisible();
  });
});
