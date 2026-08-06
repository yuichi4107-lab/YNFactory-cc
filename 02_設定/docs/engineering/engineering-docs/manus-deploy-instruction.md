---
created: "2026-03-20"
topic: "営業自動化ツール Renderデプロイ指示書（Manus向け）"
type: instruction
tags: [deploy, render, manus]
---

# 営業自動化ツール デプロイ指示書

> **この指示書は Manus（AIブラウザエージェント）向けです。**
> 上から順番に実行してください。

---

## 前提情報

| 項目 | 値 |
|------|-----|
| GitHubリポジトリ | `https://github.com/yuichi4107-lab/sales-automation` |
| デプロイ先 | Render（https://render.com） |
| フレームワーク | Python / FastAPI |
| DB | PostgreSQL（Render無料プランを使用） |
| 設定ファイル | リポジトリ内の `render.yaml` に定義済み |

---

## ステップ 1: Renderアカウント作成

1. https://render.com にアクセス
2. 「Get Started for Free」をクリック
3. **「Sign up with GitHub」を選択**（GitHubアカウント連携が一番簡単）
   - GitHubアカウント: `yuichi4107-lab`
   - もしGitHubの認証画面が出たら「Authorize Render」を許可する
4. メール認証が求められたら、メールを確認して認証を完了する

---

## ステップ 2: Blueprintでデプロイ（render.yaml を使った一括セットアップ）

1. Renderダッシュボード（https://dashboard.render.com）にログイン
2. 画面上部の「**New**」ボタン → 「**Blueprint**」を選択
3. GitHubリポジトリ一覧から `yuichi4107-lab/sales-automation` を選択
   - リポジトリが見つからない場合は「Configure account」→ リポジトリへのアクセスを許可
4. Blueprint名はデフォルトのまま（`sales-automation` になるはず）
5. 「**Apply**」をクリック

> render.yaml の内容に基づいて、以下が自動作成される：
> - Webサービス（`sales-automation`）
> - PostgreSQLデータベース（`sales-automation-db`）

6. ビルドが始まるので完了まで待つ（5〜10分程度）

---

## ステップ 3: 環境変数の設定

ビルド完了後、Webサービスの設定画面で環境変数を追加する。

1. Renderダッシュボード → `sales-automation` サービスをクリック
2. 左メニューの「**Environment**」を開く
3. 以下の環境変数が自動設定されているか確認：
   - `APP_ENV` = `production` ✅
   - `DATABASE_URL` = （自動設定） ✅
   - `SECRET_KEY` = （自動生成） ✅

4. **以下を手動で追加する**（オーナーに値を確認してもらう）：

| Key | 説明 | 備考 |
|-----|------|------|
| `GOOGLE_PLACES_API_KEY` | Google Places APIキー | 企業検索機能に必要。なければ空でOK（手動入力機能は使える） |
| `SMTP_HOST` | メールサーバー | 例: `smtp.gmail.com` |
| `SMTP_PORT` | SMTPポート | 例: `587` |
| `SMTP_USER` | 送信元メールアドレス | 例: `example@gmail.com` |
| `SMTP_PASSWORD` | SMTPパスワード | Gmailの場合はアプリパスワードを使用 |

> **注意**: SMTP関連はメール送信機能を使わないなら空欄でもアプリは起動する。後から設定可能。

5. 「**Save Changes**」をクリック → 自動で再デプロイされる

---

## ステップ 4: デプロイ完了の確認

1. Renderダッシュボード → `sales-automation` サービス
2. ステータスが「**Live**」（緑色）になっていることを確認
3. 画面上部に表示されるURL（例: `https://sales-automation-xxxx.onrender.com`）をクリック
4. 初回アクセス時は **セットアップ画面** が表示される（ユーザー名・パスワード登録画面）
   - これは正常な動作。管理者アカウントの初期設定画面。
   - **ここでは登録せずに、URLだけ記録してオーナーに伝える**

---

## ステップ 5: 動作確認チェックリスト

デプロイURLにアクセスして、以下を確認：

- [ ] セットアップ画面（`/setup`）が表示される
- [ ] ページのスタイル（CSS）が正しく読み込まれている
- [ ] エラー画面（500等）が出ていない

もしエラーが出る場合：
- Renderダッシュボード → 「Logs」タブでエラー内容を確認
- よくある原因：
  - DB接続エラー → DATABASE_URLが正しく設定されているか確認
  - ビルドエラー → Playwrightのインストールに失敗していないか確認

---

## ステップ 6: 結果の報告

デプロイ完了後、以下の情報をオーナーに報告してください：

```
【デプロイ完了報告】
- デプロイURL: https://sales-automation-xxxx.onrender.com
- ステータス: Live / エラーあり
- DB: 正常接続 / エラー
- 環境変数で未設定のもの: （あれば列挙）
- エラーがある場合のログ: （あれば貼り付け）
```

---

## 補足: Renderの無料プランの注意点

- **15分間アクセスがないとスリープする** → 次のアクセス時に30秒〜1分の起動待ちが発生
- **PostgreSQL無料プランは90日で期限切れ** → 期限前に有料プランへの移行 or データバックアップが必要
- 独自ドメインの設定は有料プラン（月$7〜）が必要

---

## トラブルシューティング

### ビルドが失敗する場合
- 「Logs」タブでビルドログを確認
- `playwright install chromium --with-deps` が失敗する場合：
  - Renderの無料プランのメモリ制限に引っかかっている可能性あり
  - → Starter プラン（$7/月）にアップグレードするか、オーナーに相談

### アプリは起動するがCSSが崩れる場合
- ブラウザのキャッシュをクリアして再読み込み（Ctrl+Shift+R）

### DB接続エラー
- Renderダッシュボード → Database → 「Connection」タブで接続文字列を確認
- `DATABASE_URL` が `postgres://` で始まっていればOK（アプリ側で自動変換する）
