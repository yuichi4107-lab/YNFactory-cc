---
title: Meta SNS自動投稿セットアップ Step5 — ClaudeInChrome向け作業指示書
created: 2026-04-21
assignee: ClaudeInChrome (Chrome拡張で動作するClaude)
status: ready
estimated_time: 10-20分
---

# Meta SNS自動投稿セットアップ Step5 作業指示書（ClaudeInChrome 用）

あなたは Chrome 上で動作する Claude（ClaudeInChrome）です。以下のブラウザ作業を完遂し、結果を報告してください。

## 背景（1分で把握）

- オーナーは Instagram / Facebook Page / Threads への自動投稿システムを構築中
- Meta for Developers にアプリ `YN Factory SNS Poster`（App ID: **1747727225992867**）は作成済み
- Step1〜4 までは完了（FBページ作成／IG-FB連携／アプリ作成／ビジネスポートフォリオ紐付け）
- **今回のゴール（Step5）**: アプリに「投稿系ユースケース」を 3 つ追加し、必要な API 権限を有効化する

## 前提確認

開始前に、Meta for Developers にログイン済みであることを確認してください。未ログインなら:
- URL: https://developers.facebook.com/
- 右上「ログイン」→ オーナーの Facebook アカウントでログイン

対象アカウントはオーナー個人（`nakada_yuichi` ビジネスポートフォリオ所有者）です。

## メインタスク

### Step 5-1: アプリダッシュボードを開く

1. 以下の URL に直接アクセス:
   **https://developers.facebook.com/apps/1747727225992867/**
2. ページタイトルに「YN Factory SNS Poster」と表示されていることを確認
3. 左サイドバーに「ユースケース（Use cases）」「設定」等のメニューが見える

### Step 5-2: ユースケース追加画面を開く

1. 画面上部または左サイドバーの以下いずれかをクリック:
   - **「+ ユースケースを追加」** / **「+ Add use cases」** ボタン
   - 左メニューの **「ユースケース」** → 右上の追加ボタン
2. ユースケース選択モーダル/ページが開く

### Step 5-3: 3 つのユースケースを追加する

以下の 3 つを **必ず全て** 追加してください。UIの表記ゆれがあるため、含まれるキーワードで判断してください。

#### ユースケース ①: Instagram 投稿系

- **左サイドバーのフィルタ**: 「コンテンツ管理」 or 「Content Management」を選択
- **選ぶもの**: 名前に **「Instagram」** を含み、「コンテンツ公開」「投稿」「Content publish」等の語があるもの
  - 想定される表記例:
    - 「Instagram API でメッセージと投稿を管理」
    - 「Instagram Graph API を使用してコンテンツを公開」
    - 「Access the Instagram API to publish content」
- クリック → 詳細ページ → 「**カスタマイズ（Customize）**」or 「**追加（Add）**」ボタン押下
- **権限（Permissions）画面で以下を ON にする**:
  - `instagram_basic`
  - `instagram_content_publish`
  - `pages_show_list`
  - `pages_read_engagement`
  - `business_management`（任意だが推奨）
  - （他に `instagram_manage_comments` 等が表示されたら全て ON でOK）

#### ユースケース ②: Facebook Page 投稿系

- 同じ「コンテンツ管理」フィルタ内
- **選ぶもの**: 名前に **「Facebookページ」** or **「Facebook Page」** を含み、「投稿」「管理」「content」等があるもの
  - 想定される表記例:
    - 「Facebook ページのコンテンツを管理」
    - 「Manage Facebook Page content」
- 追加 →  **権限画面で以下を ON**:
  - `pages_manage_posts`
  - `pages_manage_metadata`
  - `pages_read_engagement`
  - `pages_show_list`
  - `publish_to_groups`（表示されなければ不要）

#### ユースケース ③: Threads 投稿系

- 同じ「コンテンツ管理」フィルタ内
- **選ぶもの**: 名前に **「Threads」** を含むもの
  - 想定される表記例:
    - 「Threads API を使用してコンテンツを公開」
    - 「Access the Threads API」
- 追加 → **権限画面で以下を ON**:
  - `threads_basic`
  - `threads_content_publish`
  - `threads_manage_insights`（あれば推奨）
  - `threads_manage_replies`（あれば推奨）

### Step 5-4: 追加結果の確認

1. 左サイドバー「ユースケース」一覧に追加した 3 件が全て表示されているか確認
2. 各ユースケースをクリックし、権限リストに「状態: Added / 追加済」または「Requested（申請中）」が表示されていることを確認

## エラー・例外の扱い

| 状況 | 対処 |
|---|---|
| ユースケース名が指示書と違う | 「Instagram」「Facebook Page / ページ」「Threads」のキーワードがあれば選んでOK。確信が持てなければ候補を報告して指示待ち |
| 権限名が指示書と違う | 類似名を ON（例: `instagram_business_basic` なら ON）。不明なら報告 |
| 「ビジネス認証が必要」と出た | その権限はスキップ。報告事項に記載 |
| 「Facebook ログインを追加してください」等のダイアログ | **キャンセル**。今回は Facebook Login は設定しない |
| モーダルが閉じる/遷移が想定外 | ページを戻って再試行。3 回失敗したら停止して報告 |
| ログインセッション切れ | 再ログイン後に続行 |

## 禁止事項

- ❌ アプリの**削除・本番モード切替・App Secret 再生成** は絶対に行わない
- ❌ **別のアプリ**（App ID が 1747727225992867 以外）を操作しない
- ❌ 支払い情報やビジネス認証フォームは触らない（指示外）
- ❌ Facebook Login / Instagram Basic Display（旧API）は追加しない

## 完了後の報告フォーマット

作業完了後、以下の形式でオーナーに報告してください:

```markdown
## Meta SNS Step5 完了報告

### 追加したユースケース
1. [ユースケース正式名称①（コピペ）] — 状態: 追加済 / 申請中
2. [ユースケース正式名称②（コピペ）] — 状態: 追加済 / 申請中
3. [ユースケース正式名称③（コピペ）] — 状態: 追加済 / 申請中

### 有効化した権限（ユースケース別）
**Instagram:**
- [権限名①] — 状態
- ...

**Facebook Page:**
- [権限名①] — 状態
- ...

**Threads:**
- [権限名①] — 状態
- ...

### スクリーンショット
[各ユースケース詳細画面 + 権限一覧のスクショを添付]

### 困ったこと・不明点
- [あれば記載]

### 備考
- 所要時間: XX分
- 特記事項: [もしあれば]
```

## 報告先

- オーナー本人（直接返信）
- または作業メモとして `G:/マイドライブ/YNFactory-cc/.company/secretary/inbox/2026-04-21-meta-sns-step5-result.md` に保存

## 完了したら次は Step6

Step5 完了の報告を受けたら、オーナー側の Claude（ターミナル側）が Step6（Graph API Explorer で短期トークン取得）のコマンド手順を提示します。ClaudeInChrome は Step6 以降も継続する場合は別指示書を待ってください。

---

**開始時の最初のアクション:** Meta for Developers にログイン済みかを確認し、上記 URL にアクセスしてください。
