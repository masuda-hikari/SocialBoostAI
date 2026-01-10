/**
 * 404 エラーページ
 * ユーザーフレンドリーな404ページ
 */
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Search, HelpCircle } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* 404イラスト */}
        <div className="mb-8">
          <div className="text-9xl font-bold text-primary-200">404</div>
          <div className="mt-2 text-2xl font-semibold text-gray-900">
            ページが見つかりません
          </div>
          <p className="mt-4 text-gray-600">
            お探しのページは存在しないか、移動した可能性があります。
          </p>
        </div>

        {/* アクションボタン */}
        <div className="space-y-4">
          <Link
            to="/"
            className="btn-primary w-full inline-flex items-center justify-center"
          >
            <Home size={20} className="mr-2" aria-hidden="true" />
            ホームに戻る
          </Link>

          <div className="flex gap-4">
            <button
              onClick={() => window.history.back()}
              className="btn-outline flex-1 inline-flex items-center justify-center"
            >
              <ArrowLeft size={20} className="mr-2" aria-hidden="true" />
              前のページ
            </button>
            <Link
              to="/login"
              className="btn-outline flex-1 inline-flex items-center justify-center"
            >
              <Search size={20} className="mr-2" aria-hidden="true" />
              ログイン
            </Link>
          </div>
        </div>

        {/* ヘルプリンク */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            問題が解決しない場合は、
            <a
              href="mailto:support@socialboostai.com"
              className="text-primary-600 hover:text-primary-700 underline"
            >
              サポートにお問い合わせ
            </a>
            ください。
          </p>
        </div>

        {/* よく使うリンク */}
        <div className="mt-8">
          <h3 className="text-sm font-medium text-gray-700 mb-4">
            <HelpCircle size={16} className="inline mr-1" aria-hidden="true" />
            よく使うページ
          </h3>
          <div className="flex flex-wrap justify-center gap-2">
            <Link
              to="/"
              className="text-sm text-primary-600 hover:text-primary-700 px-3 py-1 bg-primary-50 rounded-full"
            >
              トップページ
            </Link>
            <Link
              to="/login"
              className="text-sm text-primary-600 hover:text-primary-700 px-3 py-1 bg-primary-50 rounded-full"
            >
              ログイン
            </Link>
            <Link
              to="/register"
              className="text-sm text-primary-600 hover:text-primary-700 px-3 py-1 bg-primary-50 rounded-full"
            >
              新規登録
            </Link>
            <Link
              to="/terms"
              className="text-sm text-primary-600 hover:text-primary-700 px-3 py-1 bg-primary-50 rounded-full"
            >
              利用規約
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
