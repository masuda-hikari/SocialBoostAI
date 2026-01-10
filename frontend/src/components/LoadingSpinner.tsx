/**
 * ローディングスピナーコンポーネント
 * lazy loadingのSuspense用フォールバック
 */

interface LoadingSpinnerProps {
  /** 表示サイズ */
  size?: 'sm' | 'md' | 'lg';
  /** フルスクリーン表示 */
  fullScreen?: boolean;
  /** メッセージ */
  message?: string;
}

export default function LoadingSpinner({
  size = 'md',
  fullScreen = false,
  message = '読み込み中...',
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  const content = (
    <div className="flex flex-col items-center justify-center gap-4" role="status" aria-live="polite">
      <div
        className={`${sizeClasses[size]} border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin`}
        aria-hidden="true"
      />
      <span className="text-gray-600 text-sm">{message}</span>
      <span className="sr-only">{message}</span>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        {content}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center py-12">
      {content}
    </div>
  );
}

/**
 * ページローディング用コンポーネント
 * Suspenseのフォールバックとして使用
 */
export function PageLoading() {
  return <LoadingSpinner fullScreen message="ページを読み込み中..." />;
}
