# SocialBoostAI デプロイガイド

## 前提条件

- Docker 24.0+
- Docker Compose 2.20+
- ドメイン（本番環境用）
- 以下のAPIキー:
  - Twitter API v2
  - OpenAI API
  - Stripe API

## クイックスタート（開発環境）

```bash
# 1. 環境変数設定
cp .env.production.example .env
# .env を編集して必要な値を設定

# 2. 開発環境起動
docker compose -f docker-compose.dev.yml up -d

# 3. アクセス
# フロントエンド: http://localhost:5173
# バックエンドAPI: http://localhost:8000
# APIドキュメント: http://localhost:8000/docs
```

## 本番環境デプロイ

### 1. 環境変数設定

```bash
cp .env.production.example .env
```

必須項目を設定:
- `SECRET_KEY`: `openssl rand -hex 32` で生成
- `POSTGRES_PASSWORD`: 安全なパスワード
- Stripe関連キー（Stripeダッシュボードから取得）
- Twitter API関連キー
- OpenAI APIキー

### 2. Stripe設定

Stripeダッシュボードで以下を設定:

1. **Products作成**:
   - Pro Plan: ¥1,980/月
   - Business Plan: ¥4,980/月

2. **Webhook Endpoint設定**:
   - URL: `https://api.your-domain.com/api/v1/billing/webhook`
   - イベント:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_failed`

3. **Price IDを.envに設定**:
   ```
   STRIPE_PRICE_PRO=price_xxxx
   STRIPE_PRICE_BUSINESS=price_xxxx
   ```

### 3. 起動

```bash
# 基本構成（Traefik なし）
docker compose up -d

# Traefik付き（リバースプロキシ）
docker compose --profile with-traefik up -d
```

### 4. データベースマイグレーション

```bash
docker compose exec backend alembic upgrade head
```

### 5. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# APIドキュメント
open http://localhost:8000/docs
```

## 構成

```
┌─────────────────────────────────────────────────────┐
│                    Traefik (オプション)              │
│                    (リバースプロキシ)                │
└────────────────┬──────────────────┬────────────────┘
                 │                  │
        ┌────────▼────────┐ ┌──────▼──────┐
        │   Frontend      │ │   Backend   │
        │   (Nginx)       │ │   (FastAPI) │
        │   Port: 80      │ │   Port: 8000│
        └─────────────────┘ └──────┬──────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
             ┌──────▼──────┐ ┌────▼────┐ ┌───────▼───────┐
             │  PostgreSQL │ │  Redis  │ │ External APIs │
             │  Port: 5432 │ │  :6379  │ │ (Twitter等)   │
             └─────────────┘ └─────────┘ └───────────────┘
```

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `docker compose up -d` | 起動 |
| `docker compose down` | 停止 |
| `docker compose logs -f backend` | バックエンドログ |
| `docker compose exec backend alembic upgrade head` | DBマイグレーション |
| `docker compose exec backend pytest` | テスト実行 |

## トラブルシューティング

### DBに接続できない

```bash
# DBの状態確認
docker compose logs db

# 接続テスト
docker compose exec backend python -c "from src.api.db import engine; print(engine.url)"
```

### Stripeイベントが受信されない

1. Webhook URLが正しいか確認
2. `STRIPE_WEBHOOK_SECRET`が正しいか確認
3. Stripeダッシュボードでイベント履歴を確認

### フロントエンドがAPIに接続できない

1. `VITE_API_URL`が正しいか確認
2. CORSが許可されているか確認
3. ネットワーク設定を確認

## 本番チェックリスト

- [ ] SECRET_KEYをランダム文字列に変更
- [ ] DEBUG=false に設定
- [ ] HTTPS設定（Traefik/Nginx）
- [ ] Stripe本番キーに変更
- [ ] バックアップ設定（PostgreSQL）
- [ ] ログローテーション設定
- [ ] 監視設定（Uptime等）
