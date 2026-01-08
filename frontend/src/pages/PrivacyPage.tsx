/**
 * プライバシーポリシーページ
 */
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function PrivacyPage() {
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
            プライバシーポリシー
          </h1>
          <p className="text-gray-600 mb-8">最終更新日: 2026年1月8日</p>

          <div className="prose prose-gray max-w-none space-y-8">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                はじめに
              </h2>
              <p className="text-gray-600 leading-relaxed">
                SocialBoostAI（以下「当社」）は、お客様の個人情報の保護を重要視しています。
                本プライバシーポリシーでは、当社がどのような情報を収集し、どのように使用、保護するかについて説明します。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                1. 収集する情報
              </h2>
              <h3 className="text-lg font-medium text-gray-800 mb-2">
                1.1 お客様が提供する情報
              </h3>
              <ul className="list-disc pl-6 text-gray-600 space-y-2 mb-4">
                <li>アカウント情報（メールアドレス、パスワード）</li>
                <li>プロフィール情報（ユーザー名）</li>
                <li>支払い情報（Stripeを通じて処理。当社はクレジットカード番号を直接保存しません）</li>
                <li>ソーシャルメディア連携情報（アクセストークン）</li>
              </ul>

              <h3 className="text-lg font-medium text-gray-800 mb-2">
                1.2 自動的に収集される情報
              </h3>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>アクセスログ（IPアドレス、ブラウザ情報）</li>
                <li>サービス利用状況（閲覧ページ、操作履歴）</li>
                <li>Cookie情報</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                2. 情報の利用目的
              </h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                収集した情報は、以下の目的で利用します。
              </p>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>サービスの提供・運営</li>
                <li>ユーザー認証・アカウント管理</li>
                <li>サブスクリプション・課金処理</li>
                <li>ソーシャルメディアデータの分析・レポート生成</li>
                <li>サービスの改善・新機能開発</li>
                <li>お問い合わせへの対応</li>
                <li>利用規約違反の調査</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                3. 情報の共有
              </h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                当社は、以下の場合を除き、お客様の個人情報を第三者に提供しません。
              </p>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>お客様の同意がある場合</li>
                <li>法令に基づく開示要請があった場合</li>
                <li>サービス提供に必要な業務委託先への提供（機密保持契約締結済み）</li>
                <li>合併、買収等の事業承継に伴う場合</li>
              </ul>

              <h3 className="text-lg font-medium text-gray-800 mb-2 mt-6">
                利用している外部サービス
              </h3>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>Stripe（決済処理）</li>
                <li>OpenAI（AI分析機能）</li>
                <li>Twitter/X（ソーシャルメディア連携）</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                4. データのセキュリティ
              </h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                当社は、お客様の情報を保護するために以下の対策を講じています。
              </p>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>通信の暗号化（SSL/TLS）</li>
                <li>パスワードのハッシュ化保存</li>
                <li>アクセストークンの暗号化保存</li>
                <li>アクセス制御・権限管理</li>
                <li>定期的なセキュリティ監査</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                5. データの保持期間
              </h2>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>アカウント情報: アカウント削除まで</li>
                <li>分析データ: プランに応じた期間（Free: 7日、Pro: 90日、Business以上: 無制限）</li>
                <li>アクセスログ: 90日間</li>
                <li>請求関連情報: 法令に基づき7年間</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                6. お客様の権利
              </h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                お客様は以下の権利を有します。
              </p>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>個人情報へのアクセス・閲覧</li>
                <li>個人情報の訂正・更新</li>
                <li>アカウントの削除（データの消去）</li>
                <li>データのエクスポート</li>
              </ul>
              <p className="text-gray-600 leading-relaxed mt-4">
                これらの権利行使については、設定画面または下記お問い合わせ先にご連絡ください。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                7. Cookieの使用
              </h2>
              <p className="text-gray-600 leading-relaxed mb-4">
                当社は、以下の目的でCookieを使用します。
              </p>
              <ul className="list-disc pl-6 text-gray-600 space-y-2">
                <li>ログイン状態の維持</li>
                <li>サービスのパーソナライズ</li>
                <li>利用状況の分析</li>
              </ul>
              <p className="text-gray-600 leading-relaxed mt-4">
                ブラウザの設定でCookieを無効にすることができますが、一部の機能が利用できなくなる場合があります。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                8. 子供のプライバシー
              </h2>
              <p className="text-gray-600 leading-relaxed">
                本サービスは18歳未満の方を対象としていません。
                18歳未満の方の個人情報を故意に収集することはありません。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                9. ポリシーの変更
              </h2>
              <p className="text-gray-600 leading-relaxed">
                当社は、必要に応じて本プライバシーポリシーを変更することがあります。
                重要な変更がある場合は、サービス上で通知するものとします。
                変更後も継続して本サービスを利用した場合、変更後のポリシーに同意したものとみなします。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                10. お問い合わせ
              </h2>
              <p className="text-gray-600 leading-relaxed">
                本プライバシーポリシーに関するお問い合わせは、以下までご連絡ください。
              </p>
              <p className="text-gray-600 mt-2">
                メール:{' '}
                <a
                  href="mailto:privacy@socialboostai.com"
                  className="text-primary-600 hover:underline"
                >
                  privacy@socialboostai.com
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
