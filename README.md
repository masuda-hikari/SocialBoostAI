# SocialBoostAI

**AI駆動のソーシャルメディア成功アシスタント**

SocialBoostAIは、あなたのソーシャルメディアアカウントのパフォーマンスを分析し、データに基づいたヒントとAI生成コンテンツの提案でガイドするAIアシスタントです。

---

## 特徴

### 分析機能
- フォロワー成長トラッキング
- エンゲージメント率分析
- 最もパフォーマンスの高いコンテンツの特定
- 時間帯別エンゲージメント分析

### AI提案機能
- 最適な投稿時間のレコメンデーション
- トレンドに基づくコンテンツアイデア提案
- ハッシュタグ最適化
- 投稿文案の自動生成

### クロスプラットフォーム対応
- Twitter/X（優先対応）
- Instagram（次期対応）
- TikTok、YouTube、LinkedIn（将来対応）

---

## 使い方

### 1. セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-org/SocialBoostAI.git
cd SocialBoostAI

# 仮想環境を作成
python -m venv venv
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .envファイルにAPIキーを設定
```

### 2. APIキーの取得

**Twitter API:**
1. [Twitter Developer Portal](https://developer.twitter.com/)でアプリを作成
2. API Key、API Secret、Access Token、Access Token Secretを取得
3. `.env`ファイルに設定

### 3. 実行

```bash
# 分析を実行
python src/main.py --analyze

# レポートを生成
python src/main.py --report
```

---

## メリット

- **データに基づく効果確定**: 推測ではなく、実際のエンゲージメントデータに基づいて投稿戦略を最適化
- **時間の節約**: AIが最適な投稿時間とコンテンツを提案することで、試行錯誤の時間を削減
- **一貫した成功**: 継続的な分析とフィードバックにより、持続的なフォロワー成長を実現

---

## 料金プラン

### Free（無料）
- 1プラットフォーム対応
- 過去7日間のデータ分析
- 基本レポート（月1回）

### Pro - ¥1,980/月
- 1プラットフォーム対応
- 過去90日間のデータ分析
- AIコンテンツ提案
- 詳細レポート（週1回）

### Business - ¥4,980/月
- 3プラットフォーム対応
- 無制限の履歴分析
- 優先サポート
- API利用可能
- リアルタイムレポート

### Enterprise - 要見積
- 無制限アカウント
- 専用サポート
- カスタム分析・機能開発

[プランを選択する](https://socialboost.ai/pricing)

---

## プロジェクト構造

```
SocialBoostAI/
├── src/
│   ├── main.py          # エントリポイント
│   ├── fetch_data.py    # ソーシャルメディアAPIからデータ取得
│   ├── analysis.py      # エンゲージメント分析ロジック
│   ├── ai_suggest.py    # AI提案機能
│   └── report.py        # レポート生成
├── config/              # 設定ファイル
├── reports/             # 生成されたレポート
├── tests/               # テストコード
└── docs/                # ドキュメント
```

---

## 技術スタック

- **言語**: Python 3.11+
- **API連携**: tweepy (Twitter), instagrapi (Instagram)
- **AI**: OpenAI GPT-4
- **分析**: pandas, matplotlib
- **データベース**: SQLite / PostgreSQL

---

## セキュリティ

- APIキーは環境変数で管理（コードにハードコードしない）
- ユーザートークンは暗号化して保存
- マルチテナント設計でユーザー間のデータを完全に隔離
- ユーザーの承認なしに自動投稿は行いません

---

## 開発状況

- [x] プロジェクト構造設計
- [ ] Twitter API連携
- [ ] 基本分析機能
- [ ] AIコンテンツ提案
- [ ] レポート生成
- [ ] Instagram対応

---

## ライセンス

Proprietary - All Rights Reserved

---

## コントリビューション

現在、内部開発フェーズのためコントリビューションは受け付けておりません。

---

## お問い合わせ

- Email: support@socialboost.ai
- Twitter: @SocialBoostAI
