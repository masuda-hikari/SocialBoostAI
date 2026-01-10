/**
 * 進捗バーコンポーネント
 *
 * 分析の進捗状態を表示
 */
import { useNotificationStore } from '../stores/notificationStore';

interface ProgressBarProps {
  analysisId: string;
}

export function ProgressBar({ analysisId }: ProgressBarProps) {
  const { progressStates } = useNotificationStore();
  const progress = progressStates.get(analysisId);

  if (!progress) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg p-3 shadow-sm border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">{progress.status}</span>
        <span className="text-sm text-gray-500">{progress.progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-primary-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress.progress}%` }}
        />
      </div>
    </div>
  );
}

/**
 * アクティブな進捗バーリスト
 */
export function ActiveProgressBars() {
  const { progressStates } = useNotificationStore();

  if (progressStates.size === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 w-80">
      {Array.from(progressStates.values()).map((progress) => (
        <div
          key={progress.analysisId}
          className="bg-white rounded-lg p-4 shadow-lg border animate-in slide-in-from-right duration-300"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-900">分析中...</span>
            <span className="text-sm text-primary-600 font-medium">{progress.progress}%</span>
          </div>
          <div className="text-xs text-gray-500 mb-2">{progress.status}</div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default ProgressBar;
