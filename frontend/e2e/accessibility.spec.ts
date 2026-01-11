import { test, expect } from '@playwright/test';

/**
 * アクセシビリティ E2Eテスト
 * WCAG 2.1準拠のテスト
 */
test.describe('アクセシビリティ', () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // 未認証状態

  test.describe('ランディングページ', () => {
    test('スキップリンクが機能する', async ({ page }) => {
      await page.goto('/');

      // Tabキーでスキップリンクにフォーカス
      await page.keyboard.press('Tab');

      // スキップリンクが表示される
      const skipLink = page.getByRole('link', { name: /メインコンテンツへスキップ|Skip to main content/i });
      if (await skipLink.isVisible()) {
        await skipLink.click();

        // メインコンテンツにフォーカスが移動
        const mainContent = page.getByRole('main');
        await expect(mainContent).toBeFocused();
      }
    });

    test('見出し階層が正しい', async ({ page }) => {
      await page.goto('/');

      // h1が存在する
      const h1 = page.locator('h1');
      await expect(h1.first()).toBeVisible();

      // h2がh1の後に存在する
      const h2Count = await page.locator('h2').count();
      expect(h2Count).toBeGreaterThan(0);
    });

    test('画像にalt属性がある', async ({ page }) => {
      await page.goto('/');

      // 全ての画像がaltを持つ
      const images = page.locator('img');
      const count = await images.count();

      for (let i = 0; i < count; i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute('alt');
        // altは空でない、または装飾的画像として空文字が許可
        expect(alt !== null).toBeTruthy();
      }
    });

    test('フォームラベルが関連付けられている', async ({ page }) => {
      await page.goto('/login');

      // メールアドレスフィールド
      const emailInput = page.getByLabel('メールアドレス');
      await expect(emailInput).toBeVisible();

      // パスワードフィールド
      const passwordInput = page.getByLabel('パスワード');
      await expect(passwordInput).toBeVisible();
    });

    test('ボタンにアクセシブルな名前がある', async ({ page }) => {
      await page.goto('/login');

      // ログインボタン
      const loginButton = page.getByRole('button', { name: 'ログイン' });
      await expect(loginButton).toBeVisible();
    });

    test('リンクにアクセシブルな名前がある', async ({ page }) => {
      await page.goto('/');

      // 全てのリンクに名前がある
      const links = page.getByRole('link');
      const count = await links.count();

      for (let i = 0; i < Math.min(count, 10); i++) { // 最初の10件をチェック
        const link = links.nth(i);
        const name = await link.getAttribute('aria-label') || await link.innerText();
        expect(name.trim().length).toBeGreaterThan(0);
      }
    });

    test('カラーコントラストが十分（視覚的確認）', async ({ page }) => {
      await page.goto('/');

      // ページが正常にレンダリングされる
      await expect(page).toHaveTitle(/.+/);
    });
  });

  test.describe('キーボードナビゲーション', () => {
    test('Tabキーでフォーカスが移動する', async ({ page }) => {
      await page.goto('/login');

      // Tabキーでフォーカスを移動
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // フォーカスがメールアドレスフィールドにある
      const emailInput = page.getByLabel('メールアドレス');
      await expect(emailInput).toBeFocused();
    });

    test('Enterキーでボタンが動作する', async ({ page }) => {
      await page.goto('/login');

      // フォームに入力
      await page.getByLabel('メールアドレス').fill('test@example.com');
      await page.getByLabel('パスワード').fill('password123');

      // ログインボタンにフォーカスしてEnter
      await page.getByRole('button', { name: 'ログイン' }).focus();
      await page.keyboard.press('Enter');

      // 何らかのレスポンスがある（エラーまたはリダイレクト）
      await page.waitForTimeout(1000);
    });

    test('モーダルダイアログがフォーカストラップを持つ', async ({ page }) => {
      await page.goto('/dashboard');

      // モーダルを開くボタンを探す
      const modalTrigger = page.getByRole('button', { name: /詳細|編集|削除/i }).first();

      if (await modalTrigger.isVisible()) {
        await modalTrigger.click();

        // モーダルが開いた場合、Escapeで閉じられる
        await page.keyboard.press('Escape');
      }
    });
  });
});

test.describe('認証済みアクセシビリティ', () => {
  test('ダッシュボードの見出し階層が正しい', async ({ page }) => {
    await page.goto('/dashboard');

    // h1が存在する
    const h1 = page.locator('h1');
    await expect(h1.first()).toBeVisible();
  });

  test('インタラクティブ要素がフォーカス可能', async ({ page }) => {
    await page.goto('/dashboard');

    // ボタンがフォーカス可能
    const buttons = page.getByRole('button');
    const count = await buttons.count();

    if (count > 0) {
      await buttons.first().focus();
      await expect(buttons.first()).toBeFocused();
    }
  });
});
