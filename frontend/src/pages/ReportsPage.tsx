/**
 * レポートページ
 */
import { useState } from 'react';
import { FileText, Calendar, RefreshCw } from 'lucide-react';

export default function ReportsPage() {
  const [reportType, setReportType] = useState<'weekly' | 'monthly'>('weekly');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    // TODO: レポート生成API呼び出し
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsGenerating(false);
    alert('レポート生成機能は開発中です');
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">レポート</h1>
        <p className="text-gray-600">パフォーマンスレポートを生成・ダウンロード</p>
      </div>

      {/* レポート生成フォーム */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">新規レポート生成</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              レポートタイプ
            </label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="reportType"
                  value="weekly"
                  checked={reportType === 'weekly'}
                  onChange={(e) =>
                    setReportType(e.target.value as 'weekly' | 'monthly')
                  }
                  className="mr-2"
                />
                <span>週次レポート</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="reportType"
                  value="monthly"
                  checked={reportType === 'monthly'}
                  onChange={(e) =>
                    setReportType(e.target.value as 'weekly' | 'monthly')
                  }
                  className="mr-2"
                />
                <span>月次レポート</span>
              </label>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="btn-primary flex items-center"
          >
            {isGenerating ? (
              <>
                <RefreshCw size={16} className="mr-2 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <FileText size={16} className="mr-2" />
                レポート生成
              </>
            )}
          </button>
        </div>
      </div>

      {/* レポート履歴（モック） */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">レポート履歴</h3>
        <div className="text-center py-12 text-gray-500">
          <FileText size={64} className="mx-auto mb-4 opacity-50" />
          <p>レポートはまだありません</p>
          <p className="text-sm mt-2">上のフォームからレポートを生成してください</p>
        </div>

        {/* TODO: レポート一覧テーブル */}
        {/*
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-gray-500 border-b">
              <th className="pb-3 font-medium">タイプ</th>
              <th className="pb-3 font-medium">期間</th>
              <th className="pb-3 font-medium">作成日</th>
              <th className="pb-3 font-medium">アクション</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b">
              <td className="py-3">週次レポート</td>
              <td className="py-3 text-sm text-gray-500">2024/01/01 - 2024/01/07</td>
              <td className="py-3 text-sm text-gray-500">2024/01/08</td>
              <td className="py-3">
                <button className="btn-outline text-sm py-1 px-2 flex items-center">
                  <Download size={14} className="mr-1" />
                  ダウンロード
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        */}
      </div>

      {/* 機能説明 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-start">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Calendar className="text-blue-600" size={24} />
            </div>
            <div className="ml-4">
              <h4 className="font-medium text-gray-900">週次レポート</h4>
              <p className="text-sm text-gray-600 mt-1">
                過去7日間のパフォーマンスを分析。投稿数、エンゲージメント、最適投稿時間などを含みます。
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-start">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Calendar className="text-purple-600" size={24} />
            </div>
            <div className="ml-4">
              <h4 className="font-medium text-gray-900">月次レポート</h4>
              <p className="text-sm text-gray-600 mt-1">
                過去30日間の詳細分析。トレンド、成長率、前月比較などを含みます。
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
