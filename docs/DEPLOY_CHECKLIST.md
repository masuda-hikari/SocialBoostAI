# SocialBoostAI 本番デプロイチェックリスト

## 概要

本番環境へのデプロイ前に必要な全手順をまとめたチェックリストです。
収益化開始に必要な全ステップを網羅しています。

---

## Phase 1: インフラ準備（人間作業）

### 1.1 VPS/クラウド選定・契約

- [ ] プロバイダー選定
  - 推奨: Hetzner Cloud（コスパ最良）、DigitalOcean、Vultr、さくらVPS
  - 最小スペック: 2vCPU / 4GB RAM / 40GB SSD
  - 月額目安: €8-15（約¥1,500-3,000）

- [ ] サーバー契約完了
  - OS: Ubuntu 22.04 LTS 推奨
  - リージョン: 東京/シンガポール（日本ユーザー向け）

### 1.2 ドメイン取得

- [ ] ドメイン取得（例: socialboostai.jp、socialboost.io）
  - 推奨: Cloudflare Registrar、Google Domains、お名前.com
  - 年額目安: ¥1,000-3,000

- [ ] DNS設定
  - Aレコード: `@` → サーバーIP
  - Aレコード: `api` → サーバーIP（APIサブドメイン使用時）
  - Aレコード: `www` → サーバーIP

### 1.3 SSL証明書

- [ ] Let's Encrypt設定（Traefik自動 or certbot手動）
- [ ] SSL証明書有効期限管理設定

---

## Phase 2: Stripe設定（人間作業）

### 2.1 Stripeアカウント準備

- [ ] Stripeアカウント作成/ログイン
  - https://dashboard.stripe.com/

- [ ] 本番モード有効化
  - ビジネス情報入力
  - 銀行口座連携
  - 本人確認完了

### 2.2 Product/Price作成

- [ ] Pro Plan作成
  - 商品名: SocialBoostAI Pro
  - 価格: ¥1,980/月（recurring）
  - Price ID: `price_xxxx` をメモ

- [ ] Business Plan作成
  - 商品名: SocialBoostAI Business
  - 価格: ¥4,980/月（recurring）
  - Price ID: `price_xxxx` をメモ

### 2.3 Webhook設定

- [ ] Webhook Endpoint作成
  - URL: `https://api.your-domain.com/api/v1/billing/webhook`
  - イベント選択:
    - `checkout.session.completed`
    - `customer.subscription.updated`
    - `customer.subscription.deleted`
    - `invoice.payment_failed`
  - Signing Secret: `whsec_xxxx` をメモ

### 2.4 APIキー取得

- [ ] 本番用APIキー取得
  - Secret Key: `sk_live_xxxx`
  - Publishable Key: `pk_live_xxxx`

---

## Phase 3: 外部API設定（人間作業）

### 3.1 Twitter API

- [ ] Twitter Developer Portalでアプリ作成/確認
  - https://developer.twitter.com/
- [ ] API Key / API Secret Key 取得
- [ ] Bearer Token 取得
- [ ] OAuth 2.0 Client ID / Secret 取得（ユーザー認証用）

### 3.2 OpenAI API

- [ ] OpenAI APIキー取得
  - https://platform.openai.com/api-keys
- [ ] 利用制限設定（予算上限）

---

## Phase 4: サーバー設定（自動化可能）

### 4.1 サーバー初期設定

```bash
# SSH接続
ssh root@your-server-ip

# パッケージ更新
apt update && apt upgrade -y

# Docker インストール
curl -fsSL https://get.docker.com | sh

# Docker Compose インストール
apt install docker-compose-plugin -y

# 非rootユーザー作成（推奨）
adduser deploy
usermod -aG docker deploy
```

### 4.2 リポジトリクローン

```bash
# デプロイユーザーに切替
su - deploy

# リポジトリクローン
git clone https://github.com/your-username/SocialBoostAI.git
cd SocialBoostAI
```

### 4.3 環境変数設定

```bash
cp .env.production.example .env
nano .env  # または vim .env
```

**必須設定項目**:

```env
# アプリ設定
SECRET_KEY=<openssl rand -hex 32 で生成>
DEBUG=false
CORS_ORIGINS=https://your-domain.com

# DB
POSTGRES_PASSWORD=<安全なパスワード>
DATABASE_URL=postgresql://socialboost:<password>@db:5432/socialboost

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
STRIPE_PRICE_PRO=price_xxxx
STRIPE_PRICE_BUSINESS=price_xxxx

# Twitter
TWITTER_API_KEY=xxxx
TWITTER_API_SECRET=xxxx
TWITTER_BEARER_TOKEN=xxxx

# OpenAI
OPENAI_API_KEY=sk-xxxx

# フロントエンド
VITE_API_URL=https://api.your-domain.com
```

### 4.4 デプロイ実行

```bash
# 本番起動
docker compose up -d

# DBマイグレーション
docker compose exec backend alembic upgrade head

# 動作確認
curl http://localhost:8000/health
```

---

## Phase 5: 動作確認（チェックリスト）

### 5.1 基本動作

- [ ] フロントエンド表示確認（`https://your-domain.com`）
- [ ] API疎通確認（`https://api.your-domain.com/health`）
- [ ] SSL証明書有効確認（ブラウザで鍵マーク）

### 5.2 認証機能

- [ ] ユーザー登録成功
- [ ] ログイン成功
- [ ] ログアウト成功

### 5.3 課金機能

- [ ] プラン一覧表示
- [ ] Stripe Checkoutへ遷移確認
- [ ] テスト決済成功（Stripeテストカード使用）
- [ ] Webhook受信確認（Stripeダッシュボードで確認）
- [ ] サブスクリプション反映確認

### 5.4 コア機能

- [ ] Twitter連携確認
- [ ] 分析実行成功
- [ ] レポート生成成功
- [ ] AI提案生成成功

---

## Phase 6: 監視・バックアップ設定

### 6.1 監視

- [ ] UptimeRobot / Betterstack 設定
  - ヘルスチェックURL: `https://api.your-domain.com/health`
  - 監視間隔: 5分
  - アラート先: メール/Slack

### 6.2 バックアップ

- [ ] PostgreSQLバックアップ設定

```bash
# cron設定例（毎日3時にバックアップ）
0 3 * * * docker compose exec -T db pg_dump -U socialboost socialboost > /backup/db_$(date +\%Y\%m\%d).sql
```

### 6.3 ログ管理

- [ ] ログローテーション設定
- [ ] エラーログ監視設定

---

## Phase 7: 公開準備

### 7.1 法的ページ確認

- [x] 利用規約（`/terms`）
- [x] プライバシーポリシー（`/privacy`）
- [x] 特定商取引法に基づく表記（`/legal/tokushoho`）

### 7.2 ランディングページ確認

- [x] ヒーローセクション
- [x] 機能紹介
- [x] 料金プラン
- [x] お客様の声
- [x] CTA

### 7.3 テスト決済後の本番切替

- [ ] Stripeテストモード → 本番モードに環境変数変更
- [ ] テストデータクリア（必要に応じて）

---

## 推定コスト（月額）

| 項目 | 月額 |
|------|------|
| VPS（Hetzner CX21） | €5.94（約¥1,000） |
| ドメイン（年割） | 約¥100/月 |
| Stripe手数料 | 3.6%+¥40/決済 |
| **合計（固定費）** | **約¥1,100/月** |

※ ユーザー100人（Pro: 50人、Business: 50人）の場合:
- 月額収益: ¥1,980×50 + ¥4,980×50 = ¥348,000
- Stripe手数料: 約¥16,500
- **純利益: 約¥330,000/月**

---

## 次のアクション

デプロイ完了後:

1. **初期ユーザー獲得**
   - SNS告知（Twitter/X、LinkedIn）
   - ベータユーザー募集
   - フィードバック収集

2. **SEO対策**
   - Google Search Console登録
   - サイトマップ提出
   - メタタグ最適化

3. **継続改善**
   - ユーザーフィードバック反映
   - バグ修正
   - 機能追加（Instagram対応等）

---

最終更新: 2026-01-08
