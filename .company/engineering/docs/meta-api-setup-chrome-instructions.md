# Meta API セットアップ指示（Claude in Chrome用）

Facebookにはログイン済みです。Instagramはプロアカウント、Facebookページも作成済みです。
以下の手順でMeta APIのアプリ作成とトークン取得を行ってください。

---

## Phase 1: アプリ作成と基本設定

### Step 1: Meta Developer Portal にアクセス

https://developers.facebook.com/ を開いて、「マイアプリ」に進んでください。

### Step 2: アプリを作成

既に `yn-sns-auto` というアプリがあれば Step 3 に進んでください。なければ：

1. 「アプリを作成」をクリック
2. ユースケースを聞かれたら「その他（Other）」を選択
3. アプリタイプは「ビジネス（Business）」を選択
4. アプリ名: `yn-sns-auto`
5. 連絡先メールアドレス: 自分のメールアドレスを入力
6. 「アプリを作成」をクリック

### Step 3: 必要な製品を追加

アプリダッシュボードで以下の製品を追加してください：

1. 「製品を追加」から **「Instagram Graph API」** を探して「設定」をクリック
2. 同様に **「Facebook Login」** を探して「設定」をクリック
3. 同様に **「Threads API」** を探して「設定」をクリック（Use cases から追加する場合もあります）

### Step 4: アプリID と App Secret を取得

1. 左メニューの「設定」→「ベーシック」を開く
2. 以下の2つの値をメモ：
   - **アプリID (App ID)**
   - **App Secret**（「表示」をクリックして表示）

---

## Phase 2: アクセストークンとID取得

### Step 5: Graph API Explorer でトークン取得

1. https://developers.facebook.com/tools/explorer/ を開く（Graph API Explorer）
2. 右上の「アプリ」ドロップダウンで `yn-sns-auto` を選択
3. 「権限を追加」で以下を **全て** 追加：

**Instagram用:**
- `instagram_basic`
- `instagram_content_publish`

**Facebook用:**
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_show_list`

**Threads用:**
- `threads_basic`
- `threads_content_publish`

4. 「アクセストークンを取得」をクリック
5. Facebookログインの許可画面が出たら **全て許可**
6. 表示された **短期アクセストークン** をコピー

> 注意: このトークンは約1時間で失効します。Step 8 で長期トークンに交換します。

### Step 6: FacebookページID を取得

Graph API Explorer の入力欄に以下を入力して「送信」をクリック：

```
GET /me/accounts
```

レスポンスの `data` 配列の中にある `id` が **FacebookページID** です。
複数ページがある場合は、投稿先にしたいページの `id` を選んでください。
同時に、そのページの `access_token`（ページアクセストークン）もメモしてください。

### Step 7: Instagram ビジネスアカウントID を取得

Graph API Explorer で以下を実行（`PAGE_ID` は Step 6 で取得した値に置き換え）：

```
GET /PAGE_ID?fields=instagram_business_account
```

レスポンスの `instagram_business_account.id` が **InstagramビジネスアカウントID** です。

---

## Phase 3: Threads API セットアップ

### Step 7.5: Threads ユーザーID を取得

Graph API Explorer で以下を実行：

```
GET /me?fields=id,name
```

レスポンスの `id` が **Threads ユーザーID**（= Facebook ユーザーID）です。

> Threads API は Instagram アカウントと紐づいているため、
> Instagram プロアカウントが設定済みであれば Threads API も利用可能です。
> Threads アプリ自体にもログインしておいてください。

### Threads API の権限確認

Step 5 で `threads_basic` と `threads_content_publish` を追加済みであることを確認してください。
もし権限リストに Threads 系が表示されない場合：

1. アプリダッシュボードに戻る
2. 左メニュー「ユースケース」をクリック
3. 「Threads API」のユースケースを追加
4. 再度 Graph API Explorer でトークンを取得し直す

---

## Phase 4: 長期アクセストークンの取得

### Step 8: 短期トークンを長期トークンに交換

Graph API Explorer の入力欄に以下を入力して「送信」：

```
GET /oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN
```

- `APP_ID`: Step 4 で取得したアプリID
- `APP_SECRET`: Step 4 で取得した App Secret
- `SHORT_LIVED_TOKEN`: Step 5 で取得した短期トークン

レスポンスの `access_token` が **長期ユーザーアクセストークン**（60日間有効）です。

### Step 9: 長期ページアクセストークンの取得

Step 8 で取得した長期ユーザートークンを使って以下を実行：

```
GET /me/accounts?access_token=LONG_LIVED_USER_TOKEN
```

レスポンスの各ページの `access_token` が **長期ページアクセストークン**（無期限）です。

> Facebook ページへの投稿にはこのページトークンを使います。
> Instagram・Threads への投稿には Step 8 のユーザートークンを使います。

---

## Phase 5: 動作確認

### Step 10: Threads テスト投稿

Graph API Explorer で以下を実行してテスト投稿します：

**ステップ1 — コンテナ作成:**
```
POST /THREADS_USER_ID/threads?media_type=TEXT&text=Meta API テスト投稿です。自動投稿システム構築中。&access_token=LONG_LIVED_USER_TOKEN
```

レスポンスの `id` をコピー。

**ステップ2 — 公開:**
```
POST /THREADS_USER_ID/threads_publish?creation_id=上でコピーしたID&access_token=LONG_LIVED_USER_TOKEN
```

Threads アプリで投稿が表示されていれば成功です。確認後、テスト投稿は削除してOKです。

### Step 11: Facebook テスト投稿

```
POST /PAGE_ID/feed?message=Meta API テスト投稿です。自動投稿システム構築中。&access_token=LONG_LIVED_PAGE_TOKEN
```

Facebook ページで投稿が表示されていれば成功です。

### Step 12: Instagram テスト投稿（画像必須）

Instagram はテキストのみ投稿ができないため、テスト画像が必要です。
以下の公開画像URLを使ってテストします：

**ステップ1 — メディア作成:**
```
POST /IG_BUSINESS_ACCOUNT_ID/media?media_type=IMAGE&image_url=https://tools.ynfactory.online/static/og-image.png&caption=Meta API テスト投稿 🔧&access_token=LONG_LIVED_USER_TOKEN
```

レスポンスの `id` をコピー。

**ステップ2 — 公開:**
```
POST /IG_BUSINESS_ACCOUNT_ID/media_publish?creation_id=上でコピーしたID&access_token=LONG_LIVED_USER_TOKEN
```

Instagram で投稿が表示されていれば成功です。

> Instagram の image_url は **公開アクセス可能なURL** である必要があります。
> もし `tools.ynfactory.online` の OG画像が使えない場合は、適当な公開画像URLに変えてください。

---

## Phase 6: 結果の報告

取得した以下の値を全て報告してください：

```
App ID: xxxxxxxxxx
App Secret: xxxxxxxxxx
Long-Lived User Token: xxxxxxxxxx
Long-Lived Page Token: xxxxxxxxxx
Facebook Page ID: xxxxxxxxxx
Instagram Business Account ID: xxxxxxxxxx
Threads User ID: xxxxxxxxxx

テスト結果:
- Threads テスト投稿: OK / NG
- Facebook テスト投稿: OK / NG
- Instagram テスト投稿: OK / NG
```

---

## トラブルシューティング

### 「Threads API の権限が表示されない」
- アプリダッシュボード → 「ユースケース」→ Threads API を追加してから再試行

### 「Instagram投稿でエラー」
- Instagram アカウントが **プロアカウント（ビジネス or クリエイター）** であることを確認
- Instagram アカウントが **Facebook ページと紐づけ** されていることを確認
- `image_url` が公開URLであることを確認（認証不要でブラウザからアクセスできるURL）

### 「権限が足りないエラー (OAuthException)」
- Graph API Explorer でトークンを再取得し、全ての権限にチェックが入っていることを確認
- 再取得後、Step 8 の長期トークン交換もやり直す

### 「ページトークンが取得できない」
- Facebook ページの管理者権限があることを確認
- `pages_show_list` 権限が付与されていることを確認

以上です。全ステップ完了したら報告してください。スクリプト開発に進みます。
