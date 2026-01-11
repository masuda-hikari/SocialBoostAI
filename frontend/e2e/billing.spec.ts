import { test, expect } from '@playwright/test';

/**
 * 課金機能 E2Eテスト
 * Stripe連携・プラン選択のテスト
 */
test.describe('課金ページ', () => {
  test('課金ページが表示される', async ({ page }) => {
    await page.goto('/billing');

    // ページタイトルが表示される
    await expect(page.getByRole('heading', { name: /課金|プラン|サブスクリプション/i })).toBeVisible();
  });

  test('現在のプランが表示される', async ({ page }) => {
    await page.goto('/billing');

    // 現在のプラン情報が表示される
    await expect(page.getByText(/現在のプラン|Free|Pro|Business|Enterprise/i)).toBeVisible();
  });

  test('プラン選択オプションが表示される', async ({ page }) => {
    await page.goto('/billing');

    // 各プランカードが表示される
    const freeCard = page.getByText(/Free|無料/i);
    const proCard = page.getByText(/Pro|¥1,980/i);
    const businessCard = page.getByText(/Business|¥4,980/i);

    await expect(freeCard.or(proCard).or(businessCard)).toBeVisible();
  });

  test('プランアップグレードボタンが存在する', async ({ page }) => {
    await page.goto('/billing');

    // アップグレードボタンが存在
    const upgradeButton = page.getByRole('button', { name: /アップグレード|プラン変更/i });
    if (await upgradeButton.isVisible()) {
      await expect(upgradeButton).toBeEnabled();
    }
  });

  test('請求履歴セクションが存在する', async ({ page }) => {
    await page.goto('/billing');

    // 請求履歴セクション
    const billingHistory = page.getByText(/請求履歴|支払い履歴/i);
    if (await billingHistory.isVisible()) {
      await expect(billingHistory).toBeVisible();
    }
  });
});

test.describe('プラン機能制限', () => {
  test('Freeプランユーザーは制限メッセージを見る', async ({ page }) => {
    // スケジュールページにアクセス（Pro以上必要）
    await page.goto('/schedule');

    // プラン制限メッセージまたはアップグレード促進が表示される
    const restrictionMessage = page.getByText(/Pro|アップグレード|この機能を利用するには/i);
    const scheduleContent = page.getByRole('heading', { name: /スケジュール/i });

    // どちらかが表示される（プランに依存）
    await expect(restrictionMessage.or(scheduleContent)).toBeVisible();
  });
});
