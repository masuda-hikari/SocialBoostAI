import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2Eテスト設定
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // テストディレクトリ
  testDir: './e2e',

  // テスト完了まで待機
  fullyParallel: true,

  // CIではリトライを有効化
  retries: process.env.CI ? 2 : 0,

  // 並列ワーカー数
  workers: process.env.CI ? 1 : undefined,

  // レポーター
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'playwright-report/results.json' }],
    ['list'],
  ],

  // グローバル設定
  use: {
    // ベースURL
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',

    // トレース記録
    trace: 'on-first-retry',

    // スクリーンショット
    screenshot: 'only-on-failure',

    // ビデオ記録
    video: 'on-first-retry',

    // タイムアウト
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // テストタイムアウト
  timeout: 60000,

  // ブラウザ設定
  projects: [
    // セットアップ（ログイン状態を保存）
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Chromium
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Firefox（CIのみ）
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Safari（CIのみ）
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // モバイル Chrome
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // モバイル Safari
    {
      name: 'mobile-safari',
      use: {
        ...devices['iPhone 12'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  // ローカル開発サーバー
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
