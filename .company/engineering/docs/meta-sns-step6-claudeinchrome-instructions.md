---
title: Meta SNS自動投稿セットアップ Step6 — ClaudeInChrome向け作業指示書（Graph API Explorer でトークン取得）
created: 2026-04-21
assignee: ClaudeInChrome (Chrome拡張で動作するClaude)
status: ready
estimated_time: 10-15分
prerequisite: Step5 完了済（ユースケース「Threads API」+「ページのすべてを管理」追加済）
---

# Meta SNS自動投稿セットアップ Step6 作業指示書（ClaudeInChrome 用）

あなたは Chrome 上で動作する Claude（ClaudeInChrome）です。Meta Graph API Explorer でアクセストークンを取得し、結果を報告してください。

## 背景（1分で把握）

- Step5 完了: アプリ `YN Factory SNS Poster`（App ID: **1747727225992867**）に投稿系ユースケース追加済
  - ① Threads API にアクセス
  - ② ページのすべてを管理（FB Page + Instagram Graph API 公開を内包）
- 今回 Step6: Graph API Explorer で **短期 User Access Token** と **Page Access Token** を取得する
- 次の Step7 で長期トークン化、Step8 で `.env` 保存 という流れ

## 既知のアセット情報

| 項目 | 値 |
|---|---|
| App ID | 1747727225992867 |
| ビジネスポートフォリオ ID | 1654828215887196 |
| Facebook ページ | YN Factory 出版プロデュース |
| FB ページ ID | 1015019845037766 |
| Instagram | @nakada_yuichi |
| IG Business Account ID | 17841477801881765 |

## 事前チェック（重要）

開始前に以下を確認してください。**Instagram がビジネスアカウントでないと `instagram_content_publish` が使えません**。

### チェック A: Instagram プロアカウントの種別

1. スマホ or Web で Instagram を開く（@nakada_yuichi）
2. プロフィール → 「プロフィールを編集」 → 「アカウントの種類」
3. 種別を確認:
   - ✅ **ビジネス** → OK、そのまま進む
   - ⚠️ **クリエイター** → 「ビジネスに切替」を推奨（切替後も UI は ほぼ同じ）
   - ❌ **個人** → プロアカウントに切替が必要

⚠️ もしビジネスでない場合は **一旦停止してオーナーに報告**。ビジネスへの切替はオーナー判断が必要です。

## メインタスク

### Step 6-1: Graph API Explorer を開く

1. 以下にアクセス: **https://developers.facebook.com/tools/explorer/**
2. 画面上部・右側のドロップダウン「**Meta App**」で **`YN Factory SNS Poster`** を選択
   - 選択肢が他のアプリになっている場合、プルダウンから探して切り替える
3. 隣の「**User or Page**」ドロップダウンは **`User Token`** を選ぶ（Page Token はここでは選ばない）

### Step 6-2: 必要な権限（Permissions）を全て追加

「Add a Permission」検索ボックスで以下を **1 つずつ** 検索 → チェック ON にする。**全 10 件**必須。

**Facebook Page 系（5個）:**
- `pages_show_list`
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_manage_metadata`
- `business_management`

**Instagram 系（2個）:**
- `instagram_basic`
- `instagram_content_publish`

**Threads 系（3個、threads_* は別カテゴリに出る可能性あり）:**
- `threads_basic`
- `threads_content_publish`
- `threads_manage_insights`（あれば ON）

検索結果に出ない権限がある場合 → そのまま進めて報告時に記録。後で申請し直せる。

### Step 6-3: Generate Access Token

1. 画面右下の **「Generate Access Token」** 青ボタンをクリック
2. ポップアップで Facebook ログイン確認（既にログイン済ならスキップされる場合あり）
3. **「以下の権限を〇〇に付与します」ダイアログ** が出たら:
   - 各権限を確認し、**全て許可** を選ぶ
   - Instagram / Threads の追加同意画面が出たら **全て許可**
   - Facebookページ選択画面が出たら「**YN Factory 出版プロデュース**」にチェック
4. 完了後、テキストボックスに長い文字列（短期 User Access Token）が表示される

### Step 6-4: User Access Token の確認

1. 表示されたトークン（`EAAX...` で始まる文字列）を **丸ごとコピー**
2. トークンボックス横の **「i」アイコン**（Debug Info）をクリック → `accesstoken/debugger` が別タブで開く
3. 有効期限（Expires）、App ID、User ID、権限リストを確認
4. 権限リストに Step 6-2 で選んだ権限が全て表示されているか確認

### Step 6-5: Page Access Token の取得

User Access Token ではなく Facebook Page 投稿に使う専用トークンを取得します。

1. Graph API Explorer に戻る
2. 検索バー（`GET /me`）に以下を入力: `me/accounts`
3. **「Submit」** 青ボタンをクリック
4. レスポンス JSON に `data` 配列が表示される
5. `data` 配列の中から `"name": "YN Factory 出版プロデュース"` のオブジェクトを探す
6. そのオブジェクトの `access_token` 値が **Page Access Token** → コピー
7. 同じオブジェクトの `id` 値（= FB ページID）を確認（`1015019845037766` と一致するはず）

### Step 6-6: Instagram Business Account ID の確認

1. Graph API Explorer の入力欄に: `{FB_PAGE_ID}?fields=instagram_business_account`
   - 実際の値: `1015019845037766?fields=instagram_business_account`
2. Submit クリック
3. レスポンスに `"instagram_business_account": {"id": "17841477801881765"}` が返ることを確認

### Step 6-7: Threads 用トークンの取得（可能なら）

Threads API は別フローの場合があります。Graph API Explorer で `threads_basic` `threads_content_publish` 権限を付けた User Token でとりあえず OK。もし追加設定が必要と判明したら報告のみでOK（後続ステップで対応）。

動作確認: Graph API Explorer で `me?fields=id,name` （graph.threads.net エンドポイント用に切替が必要かも）を試みる。エラーなら「Threads は別フロー」とメモ。

## エラー・例外の扱い

| 状況 | 対処 |
|---|---|
| `instagram_content_publish` で「ビジネス認証が必要」と出る | IG アカウントがビジネスになっていない可能性。事前チェック A に戻る |
| Page Access Token が `me/accounts` で取れない | ユーザーがページ管理者権限を持っていない可能性。報告 |
| Threads 権限が検索に出ない | そのまま進め、報告事項に記録 |
| ポップアップがブロックされる | ブラウザのポップアップ許可設定を確認、再試行 |
| トークンが短すぎる/空 | 一度ログアウト → 再ログイン → やり直し |

## 禁止事項

- ❌ 取得したトークンを **公開ページ・外部サービス・SNS にペースト** しない
- ❌ スクショに生トークン文字列全体を **鮮明に写さない**（先頭10文字程度は可）
- ❌ App Secret の再生成・削除・他アプリ操作は行わない
- ❌ トークンをブラウザのブックマークや履歴 URL に埋め込まない

## 完了後の報告フォーマット

**重要:** トークン本体は **ファイル保存** して、報告メッセージには **先頭10文字 + `...` のみ** 記載してください。

### ① トークンファイルの保存場所

以下のパスに保存してください（ClaudeInChrome が書込可能なら）:
```
G:/マイドライブ/YNFactory-cc/.company/engineering/sns-credentials/step6-tokens-2026-04-21.txt
```

ファイル内容（テンプレート）:
```
# Meta SNS Step6 取得トークン — 2026-04-21
# 短期トークン（1時間有効）— 後日 Step7 で長期化する

APP_ID=1747727225992867
USER_ACCESS_TOKEN_SHORT=<ここに User Access Token を丸ごと>
USER_TOKEN_EXPIRES=<Debug で確認した有効期限>

FB_PAGE_ID=1015019845037766
FB_PAGE_NAME=YN Factory 出版プロデュース
PAGE_ACCESS_TOKEN=<ここに Page Access Token を丸ごと>

IG_BUSINESS_ACCOUNT_ID=17841477801881765
IG_USERNAME=nakada_yuichi

# Threads 関連（取得できた場合のみ）
THREADS_USER_ID=<取得できれば>
THREADS_ACCESS_TOKEN=<取得できれば>

# 付与された権限リスト
PERMISSIONS=pages_show_list,pages_manage_posts,...
```

ファイル保存が不可能な場合 → オーナーに直接貼り付けて返す（機密扱いなので慎重に）。

### ② 報告メッセージ（オーナー向け）

```markdown
## Meta SNS Step6 完了報告

### 取得トークン（プレビューのみ、本体は保存ファイル参照）
- User Access Token: `EAAX1234aB...` （保存ファイルに全体あり）
- Page Access Token: `EAAX5678cD...` （同上）
- Threads Token: 取得可 / 取得不可（別フロー必要）

### 付与された権限
- pages_show_list, pages_manage_posts, pages_read_engagement, pages_manage_metadata, business_management
- instagram_basic, instagram_content_publish
- threads_basic, threads_content_publish, threads_manage_insights
（取得できなかった権限があれば明記）

### 確認できたID
- FB Page ID: 1015019845037766 ✅
- IG Business Account ID: 17841477801881765 ✅
- Threads User ID: [値 or 未取得]

### トークン有効期限
- User Token: [YYYY-MM-DD HH:MM]（約1時間後が普通）

### 保存ファイル
- G:/マイドライブ/YNFactory-cc/.company/engineering/sns-credentials/step6-tokens-2026-04-21.txt
  （保存できなかった場合はここに直接記載）

### 困ったこと・不明点
- [あれば記載]

### 所要時間
- XX分
```

## 完了したら次は Step7

オーナー側の Claude（ターミナル）が Step7（長期トークン化）のコマンド手順を提示します。
長期化は短期 User Access Token を使って https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token... を叩くだけの API コールなので ClaudeInChrome 不要です（ターミナル側で完結）。

---

**開始時の最初のアクション:** 事前チェック A（Instagram ビジネスアカウント種別確認）を実施してください。
