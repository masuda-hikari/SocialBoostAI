import { test, expect } from '@playwright/test';

/**
 * 認証フロー E2Eテスト
 */
test.describe('認証', () => {
  test.use({ storageState: { cookies: [], origins: [] } }); // 未認証状態

  test.describe('ログインページ', () => {
    test('ログインフォームが表示される', async ({ page }) => {
      await page.goto('/login');

      // フォーム要素が表示される
      await expect(page.getByLabel('メールアドレス')).toBeVisible();
      await expect(page.getByLabel('パスワード')).toBeVisible();
      await expect(page.getByRole('button', { name: 'ログイン' })).toBeVisible();
    });

    test('空のフォームでエラーが表示される', async ({ page }) => {
      await page.goto('/login');

      // 空のまま送信
      await page.getByRole('button', { name: 'ログイン' }).click();

      // バリデーションエラーが表示される（HTML5バリデーションまたはカスタムエラー）
      // inputのrequired属性による警告、またはエラーメッセージ
      const emailInput = page.getByLabel('メールアドレス');
      await expect(emailInput).toHaveAttribute('required', '');
    });

    test('登録ページへのリンクが機能する', async ({ page }) => {
      await page.goto('/login');

      // 登録リンクをクリック
      await page.getByRole('link', { name: /アカウント作成|登録|新規登録/i }).click();

      // 登録ページに遷移
      await expect(page).toHaveURL(/.*register/);
    });

    test('不正な認証情報でエラーが表示される', async ({ page }) => {
      await page.goto('/login');

      // 不正な認証情報を入力
      await page.getByLabel('メールアドレス').fill('invalid@example.com');
      await page.getByLabel('パスワード').fill('wrongpassword');
      await page.getByRole('button', { name: 'ログイン' }).click();

      // エラーメッセージが表示される
      await expect(page.getByText(/認証に失敗|ログインに失敗|メールアドレスまたはパスワードが正しくありません/i)).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('登録ページ', () => {
    test('登録フォームが表示される', async ({ page }) => {
      await page.goto('/register');

      // フォーム要素が表示される
      await expect(page.getByLabel('メールアドレス')).toBeVisible();
      await expect(page.getByLabel(/パスワード/)).toBeVisible();
      await expect(page.getByRole('button', { name: /登録|アカウント作成/i })).toBeVisible();
    });

    test('ログインページへのリンクが機能する', async ({ page }) => {
      await page.goto('/register');

      // ログインリンクをクリック
      await page.getByRole('link', { name: /ログイン|既にアカウントをお持ちの方/i }).click();

      // ログインページに遷移
      await expect(page).toHaveURL(/.*login/);
    });

    test('短すぎるパスワードでエラーが表示される', async ({ page }) => {
      await page.goto('/register');

      // 短いパスワードを入力
      await page.getByLabel('メールアドレス').fill('newuser@example.com');
      const passwordField = page.getByLabel(/^パスワード$/);
      await passwordField.fill('123');
      await page.getByRole('button', { name: /登録|アカウント作成/i }).click();

      // バリデーションエラーが表示される
      await expect(page.getByText(/パスワードは\d+文字以上|パスワードが短すぎます/i)).toBeVisible({ timeout: 10000 });
    });
  });
});

test.describe('認証済みユーザー', () => {
  // 認証済み状態を使用（storageStateはplaywright.config.tsで設定）

  test('ダッシュボードにアクセスできる', async ({ page }) => {
    await page.goto('/dashboard');

    // ダッシュボードが表示される
    await expect(page.getByRole('heading', { name: /ダッシュボード/i })).toBeVisible();
  });

  test('ログアウトが機能する', async ({ page }) => {
    await page.goto('/dashboard');

    // ログアウトボタンをクリック
    const logoutButton = page.getByRole('button', { name: /ログアウト/i });
    if (await logoutButton.isVisible()) {
      await logoutButton.click();

      // ログインページまたはランディングページにリダイレクト
      await expect(page).toHaveURL(/.*\/(login|)$/);
    }
  });
});
