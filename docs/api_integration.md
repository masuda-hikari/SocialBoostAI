# API連携ガイド

## Twitter API v2

### 必要な認証情報

1. **Developer Portal登録**
   - [Twitter Developer Portal](https://developer.twitter.com/)にアクセス
   - アカウントを作成/ログイン
   - プロジェクトを作成

2. **APIキーの取得**
   - API Key
   - API Key Secret
   - Bearer Token
   - Access Token
   - Access Token Secret

3. **環境変数への設定**
   ```bash
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_BEARER_TOKEN=your_bearer_token
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
   ```

### 使用するエンドポイント

| エンドポイント | 用途 | レート制限 |
|--------------|------|-----------|
| GET /2/users/by/username/:username | ユーザー情報取得 | 300/15分 |
| GET /2/users/:id/tweets | ツイート取得 | 1500/15分 |

### サンプルコード

```python
from src.fetch_data import TwitterClient

client = TwitterClient()

# ユーザー情報取得
user = client.get_user_info("twitter_username")
print(f"Followers: {user.follower_count}")

# ツイート取得
tweets = client.get_user_tweets("twitter_username", days=7)
print(f"Got {len(tweets)} tweets")
```

---

## Instagram Graph API

### 必要な認証情報

1. **Facebook Developer登録**
   - [Facebook for Developers](https://developers.facebook.com/)
   - アプリを作成
   - Instagram Graph APIを追加

2. **認証フロー**
   - Instagramビジネスアカウントが必要
   - Facebookページとの連携が必要
   - OAuth 2.0で認証

3. **環境変数への設定**
   ```bash
   INSTAGRAM_ACCESS_TOKEN=your_access_token
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
   ```

### 使用するエンドポイント

| エンドポイント | 用途 |
|--------------|------|
| GET /{ig-user-id} | アカウント情報 |
| GET /{ig-user-id}/media | メディア一覧 |
| GET /{ig-media-id}/insights | インサイト取得 |

---

## OpenAI API

### 必要な認証情報

1. **OpenAI登録**
   - [OpenAI Platform](https://platform.openai.com/)
   - APIキーを発行

2. **環境変数への設定**
   ```bash
   OPENAI_API_KEY=your_api_key
   ```

### 使用するモデル

| モデル | 用途 | コスト |
|-------|------|-------|
| gpt-4 | コンテンツ生成、分析 | 高 |
| gpt-3.5-turbo | 簡易な処理 | 低 |

### サンプルコード

```python
from src.ai_suggest import AIContentSuggester

suggester = AIContentSuggester()

# コンテンツアイデア生成
ideas = suggester.suggest_content_ideas(top_posts, topic="プログラミング")

# ハッシュタグ提案
hashtags = suggester.suggest_hashtags("新しいPythonの機能について")
```

---

## レート制限対策

### 実装方法

1. **指数バックオフ**
   - 429エラー時に待機時間を増加
   - 最大待機時間を設定

2. **キャッシュ**
   - 同じリクエストの重複を避ける
   - ローカルDBにキャッシュ

3. **バッチ処理**
   - 可能な限りまとめてリクエスト
   - ユーザーごとにスケジューリング

### tweepyでの設定

```python
client = tweepy.Client(
    bearer_token=bearer_token,
    wait_on_rate_limit=True,  # 自動待機
)
```

---

## セキュリティ注意事項

### やってはいけないこと

- APIキーをソースコードに直接記載
- APIキーをログに出力
- APIキーをGitにコミット
- 不必要なスコープでの認証

### 推奨事項

- 環境変数での管理
- 定期的なキーローテーション
- 最小権限の原則
- 監査ログの記録
