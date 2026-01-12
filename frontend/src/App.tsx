/**
 * メインアプリケーション（Lazy Loading対応、PWA対応）
 */
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import { PageLoading } from './components/LoadingSpinner';
import { PWAInstallPrompt, OfflineIndicator, PWAUpdateNotification } from './components/PWAInstallPrompt';

// 重要なページは即時読み込み（LCP最適化）
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import NotFoundPage from './pages/NotFoundPage';

// その他のページは遅延読み込み
const AdminPage = lazy(() => import('./pages/AdminPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const AnalysisPage = lazy(() => import('./pages/AnalysisPage'));
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'));
const ContentPage = lazy(() => import('./pages/ContentPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const BillingPage = lazy(() => import('./pages/BillingPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));
const TokushohoPage = lazy(() => import('./pages/TokushohoPage'));
const SchedulePage = lazy(() => import('./pages/SchedulePage'));
const OnboardingPage = lazy(() => import('./pages/OnboardingPage'));
const UsagePage = lazy(() => import('./pages/UsagePage'));

// React Query クライアント
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5分間キャッシュ
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {/* PWA: オフライン状態表示 */}
        <OfflineIndicator />

        <Suspense fallback={<PageLoading />}>
          <Routes>
            {/* 公開ルート - ランディング（即時読み込み） */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* 法的ページ（遅延読み込み） */}
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/legal/tokushoho" element={<TokushohoPage />} />

            {/* オンボーディング（認証必要、Layout不要） */}
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />

            {/* 保護されたルート（遅延読み込み） */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/comparison" element={<ComparisonPage />} />
              <Route path="/content" element={<ContentPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/billing" element={<BillingPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/usage" element={<UsagePage />} />
              <Route path="/admin" element={<AdminPage />} />
            </Route>

            {/* 404ページ */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>

        {/* PWA: インストールプロンプト */}
        <PWAInstallPrompt />

        {/* PWA: 更新通知 */}
        <PWAUpdateNotification />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
