/**
 * 利用規約ページ
 */
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function TermsPage() {
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
          <h1 className="text-3xl font-bold text-gray-900 mb-8">利用規約</h1>
          <p className="text-gray-600 mb-8">最終更新日: 2026年1月8日</p>

          <div className="prose prose-gray max-w-none space-y-8">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第1条（適用）
              </h2>
              <p className="text-gray-600 leading-relaxed">
                本規約は、SocialBoostAI（以下「本サービス」）の利用に関する条件を定めるものです。
                本サービスの利用者（以下「ユーザー」）は、本規約に同意の上、本サービスを利用するものとします。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第2条（定義）
              </h2>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>「本サービス」とは、SocialBoostAIが提供するソーシャルメディア分析・最適化サービスを指します。</li>
                <li>「ユーザー」とは、本規約に同意し本サービスを利用する個人または法人を指します。</li>
                <li>「コンテンツ」とは、ユーザーが本サービスを通じて投稿、送信、または表示するテキスト、画像、その他のデータを指します。</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第3条（アカウント登録）
              </h2>
              <ol className="list-decimal pl-6 text-gray-600 space-y-2">
                <li>ユーザーは、本サービスの利用にあたり、真実かつ正確な情報を登録するものとします。</li>
                <li>登録情報に変更があった場合、ユーザーは速やかに情報を更新するものとします。</li>
                <li>アカウントの管理責任はユーザーにあり、第三者による不正使用についても責任を負うものとします。</li>
              </ol>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第4条（サービス内容）
              </h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                本サービスは以下の機能を提供します。
              </p>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>ソーシャルメディアアカウントのエンゲージメント分析</li>
                <li>投稿パフォーマンスの可視化</li>
                <li>最適投稿時間の提案</li>
                <li>AIによるコンテンツ提案</li>
                <li>レポート生成</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第5条（料金および支払い）
              </h2>
              <ol className="list-decimal pl-6 text-gray-600 space-y-2">
                <li>本サービスには無料プランおよび有料プランがあります。</li>
                <li>有料プランの料金は、サービス上に表示された金額とします。</li>
                <li>料金の支払いは、クレジットカードによる月額課金とします。</li>
                <li>一度支払われた料金は、法令に定める場合を除き、返金いたしません。</li>
              </ol>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第6条（禁止事項）
              </h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                ユーザーは、本サービスの利用にあたり、以下の行為を行ってはなりません。
              </p>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>法令または公序良俗に反する行為</li>
                <li>犯罪行為に関連する行為</li>
                <li>本サービスのサーバーまたはネットワークの機能を妨害する行為</li>
                <li>他のユーザーまたは第三者の知的財産権、プライバシー権を侵害する行為</li>
                <li>本サービスの運営を妨害するおそれのある行為</li>
                <li>不正アクセス、スパム行為</li>
                <li>連携するソーシャルメディアプラットフォームの規約に違反する行為</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第7条（サービスの停止・変更）
              </h2>
              <ol className="list-decimal pl-6 text-gray-600 space-y-2">
                <li>当社は、システムのメンテナンス、天災、その他やむを得ない事由により、事前の通知なくサービスを停止することがあります。</li>
                <li>当社は、サービス内容を変更または終了する場合、合理的な期間を設けて事前に通知するものとします。</li>
              </ol>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第8条（免責事項）
              </h2>
              <ol className="list-decimal pl-6 text-gray-600 space-y-2">
                <li>当社は、本サービスの利用により生じた損害について、当社に故意または重大な過失がある場合を除き、責任を負いません。</li>
                <li>本サービスが提供する分析結果やAI提案は参考情報であり、その正確性、完全性を保証するものではありません。</li>
                <li>ユーザーの投稿内容に起因する問題について、当社は一切の責任を負いません。</li>
              </ol>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第9条（解約）
              </h2>
              <ol className="list-decimal pl-6 text-gray-600 space-y-2">
                <li>ユーザーは、アカウント設定画面からいつでもサブスクリプションを解約できます。</li>
                <li>解約後も、支払い済みの期間終了まで本サービスを利用できます。</li>
                <li>当社は、ユーザーが本規約に違反した場合、事前の通知なくアカウントを停止または削除できるものとします。</li>
              </ol>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第10条（規約の変更）
              </h2>
              <p className="text-gray-600 leading-relaxed">
                当社は、必要に応じて本規約を変更することがあります。
                重要な変更がある場合は、サービス上で通知するものとします。
                変更後に本サービスを継続して利用した場合、変更後の規約に同意したものとみなします。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                第11条（準拠法・管轄）
              </h2>
              <p className="text-gray-600 leading-relaxed">
                本規約の解釈にあたっては、日本法を準拠法とします。
                本サービスに関して紛争が生じた場合には、東京地方裁判所を第一審の専属的合意管轄裁判所とします。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                お問い合わせ
              </h2>
              <p className="text-gray-600 leading-relaxed">
                本規約に関するお問い合わせは、以下までご連絡ください。
              </p>
              <p className="text-gray-600 mt-2">
                メール:{' '}
                <a
                  href="mailto:legal@socialboostai.com"
                  className="text-primary-600 hover:underline"
                >
                  legal@socialboostai.com
                </a>
              </p>
            </section>
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
