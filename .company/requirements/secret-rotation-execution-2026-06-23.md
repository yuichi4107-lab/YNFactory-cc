---
title: 漏洩シークレット ローテーション実行計画
date: "2026-06-23"
status: in_progress
source: .company/engineering/debug-log/2026-05-31-secret-rotation-after-github-leak.md
---

# 漏洩シークレット ローテーション実行計画

## ゴール

2026-05-30 の GitHub private リポジトリ誤pushで露出扱いになった `yn-tools` 周辺の高優先シークレットを再発行し、VPS本番環境へ反映して、旧値が運用経路から外れていることを確認する。

## スコープ

対象にする:

- Stripe ライブ secret key / Webhook signing secret
- Google OAuth client secret
- `yn-tools` 本番DBパスワード
- `yn-tools` 本番 `SECRET_KEY`
- VPS root パスワード
- 反映後の本番起動確認、Stripe Webhook確認、Googleログイン確認、Git追跡対象の機密混入再チェック

今回ただちに変更しない:

- `ENCRYPTION_KEY`: 既存暗号化データの有無を確認してから判断する。変更すると復号不能になる可能性がある。
- Telegram bot token / Gemini API key: 手順書上は低優先。高優先の完了後に必要性を判断する。
- publishable key / OAuth client ID: 公開前提の識別子なので原則ローテーション不要。

## 現状確認

- 作業日: 2026-06-23(火) JST
- 手順書: `.company/engineering/debug-log/2026-05-31-secret-rotation-after-github-leak.md`
- `yn-tools/docker-compose.yml` は本番で以下を参照する:
  - `SECRET_KEY`
  - `DB_PASSWORD`
  - `GOOGLE_CLIENT_SECRET`
  - `STRIPE_SECRET_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `ENCRYPTION_KEY`
- ローカルGit作業ディレクトリ `/Users/yuichi/YNFactory-cc` の追跡対象では、危険パスと代表的シークレット値の検出は 0 件。
- このMacから `root@163.44.101.31` へのSSH鍵接続は不可。`sshpass` と `VPS_ROOT_PW` 環境変数も未設定。

## 承認が必要な操作

以下は外部サービスまたは本番環境に影響するため、実行直前にオーナーの明示承認を取る。

- Stripe ダッシュボードでの本番 secret key / webhook secret のローテーション
- Google Cloud Console での OAuth client secret 追加・旧secret削除
- VPS `/opt/yn-tools/.env` の本番値更新
- PostgreSQL 本番パスワード変更
- `docker compose down && docker compose up -d` による本番再起動
- VPS root パスワード変更

## 実行順序

### Phase 1: Stripe

1. Stripe Dashboard を本番モードで開く。
2. API secret key を新規作成または Roll key する。
3. Webhook endpoint `https://tools.ynfactory.online/billing/webhook` の signing secret を Roll する。
4. VPS `/opt/yn-tools/.env` の `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` を新値へ更新する。
5. `yn-tools` を再起動する。
6. 決済画面または Stripe Webhook ログで、新値による処理が通ることを確認する。

### Phase 2: Google OAuth

1. Google Cloud Console の該当 OAuth 2.0 Client ID を開く。
2. client secret を追加する。
3. VPS `/opt/yn-tools/.env` の `GOOGLE_CLIENT_SECRET` を新値へ更新する。
4. `yn-tools` を再起動する。
5. Googleログインが成功することを確認する。
6. 確認後、旧 client secret を削除する。

### Phase 3: DBパスワード / SECRET_KEY

1. 新しい `DB_PASSWORD` と `SECRET_KEY` を生成する。
2. 本番DBユーザー `yntools` のパスワードを変更する。
3. VPS `/opt/yn-tools/.env` の `DB_PASSWORD` / `SECRET_KEY` を新値へ更新する。
4. `yn-tools` を再起動する。
5. アプリ起動、DB接続、主要画面表示を確認する。

注意:

- `SECRET_KEY` 更新により既存セッションは無効化される可能性がある。
- `ENCRYPTION_KEY` は暗号化済みデータ確認まで変更しない。

### Phase 4: VPS root パスワード

1. ConoHa コントロールパネル、またはSSHで root パスワードを変更する。
2. 新パスワードはパスワードマネージャに保存する。
3. Mac / Windows の `VPS_ROOT_PW` 環境変数を必要に応じて更新する。
4. SSH鍵ログインが維持されること、緊急時のパスワードログイン経路が復旧できることを確認する。

## 完了条件

- [x] Stripe API secret key は新キーへ反映済み。VPS `/opt/yn-tools/.env` と app コンテナ内の末尾は `JYJ1`、Stripe API 読取確認OK、ローカルHTTP 200確認OK。
- [x] Stripe Webhook signing secret はローテーション済み。VPS `/opt/yn-tools/.env` と app コンテナ内の末尾は `xv8R`、ローカルHTTP 200確認OK。
- [x] Google OAuth は新 client secret へ反映済み。VPS `/opt/yn-tools/.env` と app コンテナ内の末尾は `uco-`、Google token endpoint で新secret受理確認OK、`/auth/google` 302確認OK、旧末尾 `u0Ne` はGoogle Cloud Console上で削除済み。
- [ ] 新DBパスワードで `yn-tools` がDB接続できる。
- [ ] 新 `SECRET_KEY` で本番アプリが起動する。
- [ ] VPS root パスワードが変更済みで、安全な保管先に保存されている。
- [ ] VPS `.env`・ローカル環境・Git追跡対象に旧値が残っていない。
- [ ] 作業結果を `.company/secretary/todos/2026-06-23.md` と HANDOFF に反映する。

## 品質基準

- 秘密値をチャット、ログ、Git管理ファイル、手順書に出さない。
- 外部サービスの不可逆操作は直前承認を取る。
- 変更は1サービスずつ行い、各Phaseで動作確認してから次へ進む。
- 失敗時は、最後に動作していた値へ戻せるよう、再発行と反映の順序を崩さない。

## 進捗メモ

- 2026-06-23 08時台: Stripe API secret key をローテーション。旧 `yntools-production` 末尾 `DkYw` はStripe上で約1時間後に期限切れ設定済み。新キー末尾 `JYJ1` をVPSへ反映し、`docker compose up -d --force-recreate app` でappコンテナ再作成済み。検証は `container_env_suffix=JYJ1`、`stripe_api_ok=true`、`local_http_code=200`。
- 途中で作成した未使用キー末尾 `suc4` は実値未取得・未使用。Stripe画面の拡張UIブロックにより自動期限切れ処理が未完了の可能性あり。Stripe画面で `suc4` を手動で期限切れにする。
- 2026-06-23 10時台: Stripe Webhook signing secret をローテーション。旧secretはStripe側で1時間後期限切れ設定済み。新secret末尾 `xv8R` をVPSへ反映し、appコンテナ再作成済み。検証は `container_env_suffix=xv8R`、`container_env_valid=true`、`local_http_code=200`。クリップボード消去済み。Stripe Webhook配送ログでの実イベント確認は未実施。
- 2026-06-23 10時台: Google OAuth client secret をローテーション。対象 OAuth client は `YN Tools` Webアプリケーション。新secret末尾 `uco-` をVPSへ反映し、appコンテナ再作成済み。検証は `container_env_suffix=uco-`、Google token endpoint が `invalid_grant` を返すことで client_id/new secret の受理を確認、`/auth/google` は302、ローカルHTTP 200。旧secret末尾 `u0Ne` はGoogle Cloud Consoleで無効化後に削除済み。クリップボード消去済み。
