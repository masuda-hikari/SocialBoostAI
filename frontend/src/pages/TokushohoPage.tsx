/**
 * 特定商取引法に基づく表記ページ
 */
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function TokushohoPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Link
            to="/"
            className="inline-flex items-center text-gray-600 hover:text-primary-600 transition-colors"
          >
            <ArrowLeft size={20} className="mr-2" />
            トップに戻る
          </Link>
        </div>
      </header>

      {/* コンテンツ */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-xl shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            特定商取引法に基づく表記
          </h1>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <tbody className="divide-y divide-gray-200">
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700 w-1/3">
                    販売業者
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    SocialBoostAI
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    運営責任者
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    [お問い合わせにて開示]
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    所在地
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    [お問い合わせにて開示]
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    電話番号
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    [お問い合わせにて開示]
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    メールアドレス
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    <a
                      href="mailto:support@socialboostai.com"
                      className="text-primary-600 hover:underline"
                    >
                      support@socialboostai.com
                    </a>
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    販売URL
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    https://socialboostai.com
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    販売価格
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    <ul className="list-disc pl-4 space-y-1">
                      <li>Free: 無料</li>
                      <li>Pro: 月額 1,980円（税込）</li>
                      <li>Business: 月額 4,980円（税込）</li>
                      <li>Enterprise: 別途見積</li>
                    </ul>
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    商品代金以外の必要料金
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    なし
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    支払方法
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    クレジットカード（Visa、Mastercard、American Express、JCB）
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    支払時期
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    サブスクリプション開始時および毎月の更新時
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    商品の引渡し時期
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    決済完了後、即時利用可能
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    返品・キャンセルについて
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    <p className="mb-2">
                      デジタルサービスの性質上、サービス提供開始後の返金には対応しておりません。
                    </p>
                    <p className="mb-2">
                      サブスクリプションはいつでもキャンセル可能です。
                      キャンセル後も現在の請求期間終了までサービスを利用できます。
                    </p>
                    <p>
                      ただし、サービス提供に重大な不具合があった場合は、
                      個別にご対応させていただきます。
                    </p>
                  </td>
                </tr>
                <tr>
                  <th className="text-left py-4 px-4 bg-gray-50 font-medium text-gray-700">
                    動作環境
                  </th>
                  <td className="py-4 px-4 text-gray-600">
                    <ul className="list-disc pl-4 space-y-1">
                      <li>最新版のGoogle Chrome、Firefox、Safari、Microsoft Edge</li>
                      <li>安定したインターネット接続</li>
                    </ul>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* フッター */}
      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400 text-sm">
            © 2026 SocialBoostAI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
