# SocialBoostAI

**AI駆動のソーシャルメディア成功アシスタント**

SocialBoostAIは、あなたのソーシャルメディアアカウントのパフォーマンスを分析し、データに基づいたヒントとAI生成コンテンツの提案でエンゲージメント向上をサポートするサービスです。

---

## ✨ 特徴

### 📊 分析機能
- フォロワー成長トラッキング
- エンゲージメント率分析
- 最もパフォーマンスの高いコンテンツの特定
- 時間帯別エンゲージメント分析
- ハッシュタグ・キーワード効果分析
- トレンドパターン検出

### 🤖 AI提案機能
- 最適な投稿時間のレコメンデーション
- トレンドに基づくコンテンツアイデア提案
- ハッシュタグ最適化
- 投稿文案の自動生成
- パーソナライズド戦略生成
- 自動返信文案生成

### 🌐 マルチプラットフォーム対応
| プラットフォーム | 状況 |
|-----------------|------|
| Twitter/X | ✅ 対応済み |
| Instagram | ✅ 対応済み |
| TikTok | ✅ 対応済み |
| YouTube | ✅ 対応済み |
| LinkedIn | ✅ 対応済み |
| クロスプラットフォーム比較 | ✅ 対応済み |

### ⚡ リアルタイム��能
- WebSocket通知（分析完了/レポート完了等）
- 分析進捗リアルタイム表示
- ダッシュボード自動更新（60秒間隔）
- 接続状態可視化

### 🚀 パフォーマンス最適化
- DBインデックス最適化
- Redisキャッシュ対応
- バックグラウンドタスク処理
- パフォーマンス監視

---

## 🛠️ 技術スタック

### バックエンド
- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **データベース**: PostgreSQL（本番）/ SQLite（開発）
- **キャッシュ**: Redis
- **ORM**: SQLAlchemy 2.0
- **マイグレーション**: Alembic

### フロントエンド
- **フレ��ムワーク**: React 18 + TypeScript
- **ビルドツール**: Vite
- **状態管理**: Zustand + React Query
- **UI**: Tailwind CSS
- **リアルタイム**: WebSocket

### API連携
- Twitter API v2 (tweepy)
- Instagram Graph API (instagrapi)
- TikTok API for Business
- YouTube Data API v3
- LinkedIn Marketing API

### インフラ
- **コンテナ**: Docker / Docker Compose
- **リバースプロキシ**: Nginx
- **決済**: Stripe

---

## 🚀 セットアップ

### Docker（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/your-org/SocialBoostAI.git
cd SocialBoostAI

# 環境変数を設定
cp .env.example .env
# .envファイルを編集

# 起動
docker-compose up -d
```

### ローカル開発

#### バックエンド

```bash
# 仮想環境を作成
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 依存関係をインストール
pip install -r requirements.txt

# データベースマイグレーション
alembic upgrade head

# 起動
uvicorn src.api.main:app --reload
```

#### フロントエンド

```bash
cd frontend

# 依存関係をインストール
npm install

# 開発サーバー起動
npm run dev
```

---

## 📁 プロジェクト構造

```
SocialBoostAI/
├── src/
│   ├── api/               # FastAPI アプリケーション
│   │   ���── routers/       # APIエンドポイント
│   │   ├── db/            # データベースモデル
│   │   ├── repositories/  # データアクセス層
│   │   ├── billing/       # Stripe課金
│   │   ├── cache/         # Redisキャッシュ
│   │   ├── tasks/         # バックグラウンドタスク
│   │   ├── websocket/     # WebSocket通知
│   │   └── middleware/    # ミドルウェア
│   ├── analysis.py        # Twitter分析ロジック
│   ├── instagram_analysis.py
│   ├── tiktok_analysis.py
│   ├── youtube_analysis.py
│   ├── linkedin_analysis.py
│   ├── cross_platform.py  # クロスプラットフォーム比較
│   ├── ai_content_generator.py  # AIコンテンツ生成
│   └── report.py          # レポート生成
├── frontend/              # React フロントエンド
│   ├── src/
│   │   ├── pages/         # ページコンポーネント
│   │   ├── components/    # 共通コンポーネント
│   │   ├── stores/        # 状態管理
│   │   └── api/           # API クライアント
│   └── public/            # 静的ファイル
├── migrations/            # Alembicマイグレーション
├── tests/                 # テストコード（582件）
├── docs/                  # ドキュメント
│   ├── DEPLOY_CHECKLIST.md
│   └── MARKETING_TEMPLATES.md
├── docker-compose.yml     # Docker Compose設定
├── docker-compose.dev.yml # 開発用設定
└── DEPLOY.md              # デプロイガイド
```

---

## 📖 API仕様

APIドキュメントは以下のURLで確認できます：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 主要エンドポイント

| エンドポイント | 説明 |
|---------------|------|
| `POST /api/v1/auth/register` | ユーザー登録 |
| `POST /api/v1/auth/login` | ログイン |
| `GET /api/v1/analysis` | 分析結果取得 |
| `POST /api/v1/analysis` | 分析実行 |
| `GET /api/v1/reports` | レポート一覧 |
| `GET /api/v1/content/generate` | AIコンテンツ生成 |
| `GET /api/v1/cross-platform/compare` | プラットフォーム比較 |
| `POST /api/v1/schedule` | 投稿スケジュール作成 |
| `GET /api/v1/schedule` | スケジュール一覧取得 |
| `POST /api/v1/email/send-weekly-report` | 週次レポートメール送信 |
| `WS /ws/{user_id}` | WebSocket接続 |

---

## 🔒 セキュリティ

- APIキーは環境変数で管理（コードにハードコードしない）
- ユーザートークンは暗号化して��存
- マルチテナント設計でユーザー間のデータを完全に隔離
- JWT認証（アクセストークン + リフレッシュトークン）
- CORS設定（本番環境では制限）
- レート制限対応
- ユーザーの承認なしに自動投稿は行いません

---

## ✅ 開発状況

### 完了済み
- [x] プロジェクト構造設計
- [x] Twitter API連携
- [x] Instagram API連携
- [x] TikTok API連携
- [x] YouTube API連携
- [x] LinkedIn API連携
- [x] クロスプラットフォーム比較機能
- [x] 基本分析機能
- [x] 高度なAIコンテンツ提案
- [x] レポート生成（HTML/コンソール）
- [x] Webダッシュボード（React）
- [x] Stripe課金機能
- [x] WebSocketリアルタイム通知
- [x] パフォーマンス最適化
- [x] SEO最適化
- [x] アクセシビリティ強化
- [x] メール通知機能（週次/月次レポート等）
- [x] 投稿スケジューリング機能（予約投稿）
- [x] Docker/Docker Compose構成
- [x] デプロイドキュメント

### 本番デプロイ準備（人間作業）
- [ ] VPS/クラウド契約
- [ ] ドメイン取得・SSL設定
- [ ] Stripe本番設定

---

## 🧪 テスト

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src

# 特定テスト
pytest tests/test_analysis.py
```

**テスト状況**: 582件全合格（2026-01-11確認）

---

## 📜 ライセンス

Proprietary - All Rights Reserved

---

## 📞 お問い合わせ

- Email: support@socialboost.ai
- Twitter: @SocialBoostAI
