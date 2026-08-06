# SNS自動投稿システム構築 作業手順書

## 概要

Claude CodeからSNS（X / Instagram / Facebook / Threads）への投稿を自動化する。
本手順書はPhase 1（X連携）とPhase 2（Meta系連携）に分かれる。

## 背景・目的

- コンテンツ制作（instagram-reel-producerスキル等）は既に自動化済み
- 投稿作業がブラウザ手動操作のボトルネックになっている
- API連携により Claude Code → 全SNS投稿 をワンストップで実現する

---

## Phase 1: X (Twitter) API 連携

### 1-1. X Developer Portal セットアップ【ブラウザ作業】

1. https://developer.x.com/en/portal/dashboard にアクセス
2. Xアカウントでログイン
3. Developer Agreement に同意（初回のみ）
4. **Free プラン**を選択（月1,500ポスト可能、十分）
5. プロジェクトが作成されるので、アプリ名を入力（例: `yn-auto-post`）

### 1-2. アプリの権限設定【ブラウザ作業】

1. アプリのダッシュボードで **「User authentication settings」** → 「Set up」
2. 以下を設定：
   - **App permissions**: `Read and Write` を選択
   - **Type of App**: `Web App, Automated App or Bot`
   - **Callback URL**: `http://localhost`
   - **Website URL**: `https://ynfactory.online`
3. 保存

### 1-3. APIキー取得【ブラウザ作業】

「Keys and Tokens」タブで以下の4つを取得・控える：

| キー名 | 用途 |
|--------|------|
| API Key | アプリ識別 |
| API Key Secret | アプリ認証 |
| Access Token | ユーザー認証 |
| Access Token Secret | ユーザー認証 |

> Access Token / Access Token Secret が表示されない場合は「Generate」ボタンで生成する

### 1-4. 環境変数の設定【Claude Code作業】

取得した4つの値を `.env` ファイルに保存：

```bash
# G:/マイドライブ/YNFactory-cc/.company/engineering/sns-credentials/.env
X_API_KEY=取得した値
X_API_KEY_SECRET=取得した値
X_ACCESS_TOKEN=取得した値
X_ACCESS_TOKEN_SECRET=取得した値
```

### 1-5. 投稿テスト【Claude Code作業】

curlでテスト投稿を実行：

```bash
# OAuth 1.0a署名が必要なため、Pythonスクリプトを使用
python3 scripts/post_to_x.py "テスト投稿です"
```

投稿スクリプト（作成する）:

```python
# scripts/post_to_x.py
import tweepy
import sys
import os
from dotenv import load_dotenv

load_dotenv()

client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_KEY_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
)

text = sys.argv[1] if len(sys.argv) > 1 else "Hello from YN Factory!"
response = client.create_tweet(text=text)
print(f"Posted: https://x.com/i/status/{response.data['id']}")
```

### 1-6. スキル化 or MCP化【Claude Code作業】

テスト成功後、以下のいずれかで恒久化：
- **Option A**: Claude Code スキル（`/post-sns`）として実装
- **Option B**: MCP Serverとして実装（より柔軟）

推奨はOption A（スキル）から始めて、Phase 2統合時にMCP化。

---

## Phase 2: Meta系（Instagram / Facebook / Threads）連携

### 前提条件【ブラウザ作業】

以下を先に済ませておく：

1. **Instagramをプロアカウントに切替**
   - Instagram → 設定 → アカウント → プロアカウントに切り替え
   - 「クリエイター」を選択（無料）

2. **Facebookページを作成**
   - https://www.facebook.com/pages/create
   - ページ名: 任意（例: YN Factory）
   - InstagramアカウントとFacebookページを連携

### 2-1. Meta Developer Portal セットアップ【ブラウザ作業】

1. https://developers.facebook.com/ にアクセス
2. 「マイアプリ」→「アプリを作成」
3. アプリタイプ: 「ビジネス」を選択
4. アプリ名: `yn-sns-auto`

### 2-2. 必要な権限の追加【ブラウザ作業】

アプリダッシュボードで以下の製品を追加：

- **Instagram Graph API**
- **Facebook Login**（認証用）

必要なパーミッション：
- `instagram_basic`
- `instagram_content_publish`
- `pages_manage_posts`
- `pages_read_engagement`
- `threads_basic`
- `threads_content_publish`

### 2-3. アクセストークン取得【ブラウザ + Claude Code作業】

1. Graph API Explorer（ https://developers.facebook.com/tools/explorer/ ）で短期トークン取得
2. 短期トークンを長期トークンに交換（60日有効）：

```bash
curl -s "https://graph.facebook.com/v19.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=APP_ID&\
client_secret=APP_SECRET&\
fb_exchange_token=SHORT_LIVED_TOKEN"
```

3. 長期トークンを `.env` に保存：

```bash
META_APP_ID=取得した値
META_APP_SECRET=取得した値
META_ACCESS_TOKEN=取得した長期トークン
META_IG_USER_ID=InstagramビジネスアカウントのID
META_PAGE_ID=FacebookページのID
```

### 2-4. 投稿スクリプト作成【Claude Code作業】

```python
# scripts/post_to_meta.py
# Instagram: 画像/リール投稿
# Facebook: テキスト/画像投稿
# Threads: テキスト/画像投稿
# （詳細は実装時に作成）
```

### 2-5. トークン自動更新の仕組み【Claude Code作業】

Meta長期トークンは60日で期限切れになるため、cronで定期更新：

```bash
# 50日ごとにトークンをリフレッシュ
```

---

## 最終形：統合投稿スキル

Phase 1 + Phase 2 完了後、統合スキルを作成：

```
ユーザー: 「この内容を全SNSに投稿して」

Claude Code（/post-snsスキル）:
  1. コンテンツを各SNS向けに調整
     - X: 280文字以内、ハッシュタグ
     - Instagram: 画像必須、キャプション2200文字以内
     - Facebook: 長文OK、リンク可
     - Threads: 500文字以内
  2. 各APIで投稿実行
  3. 投稿URL一覧を報告
```

---

## 作業分担

| 作業 | 担当 | 備考 |
|------|------|------|
| Developer Portal操作・キー取得 | ブラウザ作業者 | ログイン必要 |
| Instagramプロアカウント切替 | ブラウザ作業者 | スマホからも可 |
| Facebookページ作成 | ブラウザ作業者 | |
| スクリプト作成・テスト | Claude Code | API キー受領後 |
| スキル/MCP実装 | Claude Code | テスト成功後 |
| トークン更新cron設定 | Claude Code | Phase 2完了後 |

## 依存パッケージ

```bash
pip install tweepy python-dotenv requests
```

## 注意事項

- APIキー・トークンは `.env` に保存し、gitにコミットしない
- X Free プランは月1,500ポスト上限（通常運用では十分）
- Meta長期トークンは60日で期限切れ → 自動更新必須
- Instagram投稿は画像/動画が必須（テキストのみ不可）
- 各SNSの利用規約・レート制限に注意
