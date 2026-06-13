---
title: Meta SNS自動投稿セットアップ Step6 — ClaudeInChrome向け作業指示書（Graph API Explorer でトークン取得）
created: 2026-04-21
updated: 2026-06-09
assignee: ClaudeInChrome (Chrome拡張で動作するClaude)
status: ready
estimated_time: 20-30分
prerequisite: Step5 初回完了済。ただし Developer Console の use case 権限 Customize/Add が未完了のため、Graph API Explorer の前に必ず Step 6-0 を実施する
---

# Meta SNS自動投稿セットアップ Step6 作業指示書（ClaudeInChrome 用）

あなたは Chrome 上で動作する Claude（ClaudeInChrome）です。Meta Developer Console と Graph API Explorer でアクセストークン取得準備を行い、結果を報告してください。

## 背景（1分で把握）

- Step5 完了: アプリ `YN Factory SNS Poster`（App ID: **1747727225992867**）に投稿系ユースケース追加済
  - ① Threads API にアクセス
  - ② ページのすべてを管理（FB Page + Instagram Graph API 公開を内包）
- 2026-05-06時点のブロッカー: Graph API Explorer の権限追加ドロップダウンに `business_management` `pages_show_list` しか表示されなかった
- 原因: use case を追加しただけで、Developer Console 側の個別権限が Customize/Add されていない
- 今回 Step6: まず Developer Console で必要権限を Add し、その後 Graph API Explorer で **短期 User Access Token** と **Page Access Token** を取得する
- 次の Step7 で長期トークン化、Step8 で `.env` 保存 という流れ

参考URL（確認用）:
- Instagram Graph API: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media
- Facebook Pages API: https://developers.facebook.com/docs/pages-api/posts/
- Threads API: https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions

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

### Step 6-0: Developer Console で use case 権限を Customize/Add する（最優先）

Graph API Explorer に行く前に、必ず Meta Developer Console 側で個別権限が追加済みか確認してください。
ここを飛ばすと、Graph API Explorer の「Add a Permission」に必要権限が出ません。

1. 以下を開く:
   **https://developers.facebook.com/apps/1747727225992867/use_cases/**
2. 表示中のアプリが **`YN Factory SNS Poster` / App ID `1747727225992867`** であることを確認
3. use case 一覧で **「ページのすべてを管理」** または Facebook Page / Instagram 投稿に関係する use case を開く
4. **Customize** / **カスタマイズ** / **設定** に入り、以下の権限を **Add / 追加 / Request access** する
   - `pages_show_list`
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_manage_metadata`
   - `business_management`
   - `instagram_basic`
   - `instagram_content_publish`
   - 2026-06-09実測メモ: Page系use case内にInstagram権限が出ない場合は、use case一覧の「ユースケースを追加」→「コンテンツ管理」→「Instagramでメッセージとコンテンツを管理」を追加する。その後、Instagram use caseのFacebookログイン設定で「Add required content permissions」を実行し、Graph API Explorerを再読み込みすると `instagram_basic` / `instagram_content_publish` が候補に出る。
5. use case 一覧に戻り、**「Threads APIにアクセス」** を開く
6. **Customize** / **カスタマイズ** / **設定** に入り、以下の権限を **Add / 追加 / Request access** する
   - `threads_basic`
   - `threads_content_publish`
   - `threads_manage_insights`（表示される場合）
7. 各権限の状態が **Added / 追加済 / Requested / 申請中** のいずれかになったことを確認

注意:
- 権限が見つからない場合は、権限名・表示中の use case 名・画面上のエラーメッセージを記録して報告する
- 別アプリへ切り替えない
- App Secret 再生成、本番モード切替、アプリ削除、ビジネス認証フォーム入力は行わない
- Facebook Login / Instagram Basic Display（旧API）を新規追加する判断はしない

### Step 6-1: Graph API Explorer を開く

1. 以下にアクセス: **https://developers.facebook.com/tools/explorer/**
2. 画面上部・右側のドロップダウン「**Meta App**」で **`YN Factory SNS Poster`** を選択
   - 選択肢が他のアプリになっている場合、プルダウンから探して切り替える
3. 隣の「**User or Page**」ドロップダウンは **`User Token`** を選ぶ（Page Token はここでは選ばない）

### Step 6-2: 必要な権限（Permissions）を全て追加

「Add a Permission」検索ボックスで以下を **1 つずつ** 検索 → チェック ON にする。
Facebook Page / Instagram の7件は必須、Threads の3件は取得できれば追加する。

**Facebook Page 系（5個）:**
- `pages_show_list`
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_manage_metadata`
- `business_management`

**Instagram 系（2個）:**
- `instagram_basic`
- `instagram_content_publish`
  - 2026-06-09実測メモ: Developer Console側の説明では `instagram_content_publishing` と表示される場合があるが、Graph API Explorerで選択できた権限名は `instagram_content_publish`。

**Threads 系（3個、threads_* は別カテゴリに出る可能性あり）:**
- `threads_basic`
- `threads_content_publish`
- `threads_manage_insights`（あれば ON）

検索結果に出ない権限がある場合:
- まず Step 6-0 に戻り、その権限が Developer Console 側で Add 済みか確認
- Step 6-0 済みでも出ない場合は、出ない権限名・選択中のアプリ名・Graph API Explorer のカテゴリ表示を記録して報告
- Facebook Page と Instagram の必須権限が欠けている場合は、トークン生成まで進めず停止して報告
- Threads 権限だけが出ない場合は、Facebook Page / Instagram のトークン取得を優先し、Threads は別フロー候補として報告

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

Threads API は Facebook Page / Instagram Graph API と別フローになる場合があります。
Graph API Explorer で `threads_basic` `threads_content_publish` 権限を付けた User Token が取得できるか確認し、取得できなければ無理に突破しないでください。
公式フローでは `graph.threads.net` の OAuth / long-lived token を使う場面があるため、取得不可なら「Threads は別フロー必要」と報告して Step7 以降で扱います。

動作確認: Graph API Explorer で `me?fields=id,name` （graph.threads.net エンドポイント用に切替が必要かも）を試みる。エラーなら「Threads は別フロー」とメモ。

## エラー・例外の扱い

| 状況 | 対処 |
|---|---|
| Graph API Explorer に `business_management` `pages_show_list` しか出ない | Step 6-0 未完了。Developer Console の use case Customize/Add に戻る |
| `pages_manage_posts` `pages_read_engagement` `pages_manage_metadata` が出ない | Facebook Page 系 use case の権限追加不足。Step 6-0 に戻る |
| `instagram_basic` `instagram_content_publish` が出ない | Instagram / Page 投稿系 use case の権限追加不足。Step 6-0 に戻る |
| `threads_basic` `threads_content_publish` が出ない | Threads use case の権限追加不足、または Threads 別フロー。Step 6-0 確認後、未解決なら報告 |
| `instagram_content_publish` で「ビジネス認証が必要」と出る | IG アカウントがビジネスになっていない可能性。事前チェック A に戻る |
| Page Access Token が `me/accounts` で取れない | ユーザーがページ管理者権限を持っていない可能性。報告 |
| Threads 権限が検索に出ない | Step 6-0 を確認後、未解決なら「Threads は別フロー必要」として報告 |
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
G:/マイドライブ/YNFactory-cc/.company/engineering/sns-credentials/step6-tokens-2026-06-09.txt
```

ファイル内容（テンプレート）:
```
# Meta SNS Step6 取得トークン — 2026-06-09
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

ファイル保存が不可能な場合 → 生トークンをチャットへ貼らず、作業を止めて「安全な保存先が必要」と報告する。

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
- G:/マイドライブ/YNFactory-cc/.company/engineering/sns-credentials/step6-tokens-2026-06-09.txt
  （保存できなかった場合は「保存不可。安全な保存先が必要」と記載）

### 困ったこと・不明点
- [あれば記載]

### 所要時間
- XX分
```

## 完了したら次は Step7

オーナー側の Claude（ターミナル）が Step7（長期トークン化）のコマンド手順を提示します。
長期化は短期 User Access Token を使って `https://graph.facebook.com/{API_VERSION}/oauth/access_token?grant_type=fb_exchange_token...` を叩く API コールなので ClaudeInChrome 不要です（ターミナル側で完結）。API_VERSION は Step7 実施時に確認します。

---

## 2026-06-09 実行結果メモ

- Graph API ExplorerでPage + Instagram必須権限を選択し、オーナー承認後に短期User Access Tokenを生成済み。
- User Tokenから `me/accounts` を確認し、`YN Factory 出版プロデュース` のPage Access Tokenを取得済み。
- 保存先: `.company/engineering/sns-credentials/step6-tokens-2026-06-09.txt`（権限 `600`）
- 付与確認済み権限: `business_management`, `instagram_basic`, `instagram_content_publish`, `pages_manage_metadata`, `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
- 確認済みID: FB Page `1015019845037766` / IG Business Account `17841477801881765`
- Threads権限はGraph API Explorer候補に出なかったため、Threads Tokenは別フローで扱う。
- Step7（長期トークン化）と `.env` 反映は、外部API呼び出し・本番反映に当たるため直前承認後に実施する。
- Step7用スクリプト: `scripts/meta_step7_long_lived_token.py`
  - `APP_SECRET` が `.company/engineering/sns-credentials/step6-tokens-2026-06-09.txt` または環境変数に存在する場合のみ長期化APIを呼ぶ。
  - `APP_SECRET` が無い場合は `missing_app_secret` で安全停止し、トークン全文は表示しない。
  - 2026-06-09時点ではMeta Developer ConsoleのBasic Settingsページがブラウザ安全ポリシーでブロックされたため、App Secretはオーナーが手動コピーし、ローカル保存ファイルへ追加した。
  - 初回Step7実行時は短期User Tokenが期限切れだったため、Graph API Explorerで短期User Tokenを再発行し、直後に長期化した。
- Step7完了結果:
  - 長期User Token期限: `2026-08-07T22:20:23Z`
  - `me/accounts` 読み取りOK: `YN Factory 出版プロデュース` / `1015019845037766`
  - Page Token読み取りOK: `instagram_business_account.id = 17841477801881765`
  - 期待権限7件の欠落なし。
- `.env` 反映:
  - `.company/engineering/sns-credentials/.env` にMeta系キーを反映済み。
  - 認証情報ディレクトリは `.gitignore` で除外済み。
- 投稿スクリプト:
  - `scripts/post_to_meta.py` はFacebook Page / Instagram本番投稿処理を実装済み。
  - 本番投稿は `--publish-approved` 必須。Instagramは公開HTTPS画像URL必須。
  - Threads本番投稿はToken別フロー確定後に対応。

---

**開始時の最初のアクション:** 事前チェック A（Instagram ビジネスアカウント種別確認）を実施してください。
