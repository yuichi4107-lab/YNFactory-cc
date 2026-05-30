---
title: GitHub誤push 漏洩シークレット ローテーション手順書
date: "2026-05-31"
severity: 中（private リポジトリ・短時間・削除済み）
status: ローテーション待ち（オーナー実行）
related:
  - .company/engineering/debug-log/2026-05-30-git-head-recovery.md
  - docs/superpowers/specs/2026-05-30-workdir-git-architecture-design.md
---

# GitHub誤push 漏洩シークレット ローテーション手順書

## 何が起きたか

2026-05-30、作業ディレクトリのGitHub軸移行作業中に、**機密を含んだコミットを GitHub private リポジトリ
`yuichi4107-lab/YNFactory-cc` に push してしまった**（Claude Code のミス）。

- リポジトリは **private**（第三者からは閲覧不可）
- push から削除まで**約数時間**（同日中にリモートリポジトリごと削除＝外部撤回済み）
- ローカル履歴は機密ゼロに再構築済み（コミット `af02a88`）

private かつ短時間・削除済みのため**実被害リスクは低い**が、GitHub に一度載った認証情報は
「漏洩したもの」として扱うのが安全側。以下をローテーション（再発行）する。

## ローテーション対象と手順

### 優先度【高】影響が大きいもの

#### 1. Stripe ライブシークレットキー（`sk_live_...`）+ Webhook シークレット（`whsec_...`）
- **影響**: 決済。最悪、不正な払い戻し・顧客データ参照。
- **手順**:
  1. https://dashboard.stripe.com → 右上が「本番」モードであることを確認
  2. Developers → API keys → Secret key の「Roll key...」（または Create secret key → 旧キー失効）
  3. 新しい `sk_live_...` を控える
  4. VPS `/opt/yn-tools/.env` の `STRIPE_SECRET_KEY=` を新キーに更新
  5. Developers → Webhooks → 該当エンドポイント（`https://tools.ynfactory.online/billing/webhook`）→
     「Roll secret」で新しい `whsec_...` を発行 → `.env` の `STRIPE_WEBHOOK_SECRET=` を更新
  6. `cd /opt/yn-tools && docker compose down && docker compose up -d`
  7. テスト決済 or `docker logs` で Webhook 受信を確認
- **注**: publishable key（`pk_live_...`）は公開前提なのでローテーション不要。

#### 2. Google OAuth クライアントシークレット（`GOCSPX-...`）
- **影響**: yn-tools の Googleログイン。悪用でOAuthなりすましの恐れ。
- **手順**:
  1. https://console.cloud.google.com → 該当プロジェクト → APIとサービス → 認証情報
  2. OAuth 2.0 クライアント ID（`191044568608-...`）を開く
  3. 「シークレットを追加」で新シークレット発行 → 旧シークレットを削除
  4. VPS `/opt/yn-tools/.env` の `GOOGLE_CLIENT_SECRET=` を更新
  5. `docker compose down && docker compose up -d` → Googleログインを実機確認
- **注**: client ID（`...apps.googleusercontent.com`）は公開情報なので変更不要。

#### 3. DBパスワード（`DB_PASSWORD`）+ アプリ秘密鍵（`SECRET_KEY` / `ENCRYPTION_KEY`）
- **影響**: yn-tools の DB・セッション・暗号化。
- **手順（DBパスワード）**:
  1. VPS で PostgreSQL のパスワード変更: `docker compose exec yn-tools-db psql -U postgres -c "ALTER USER postgres PASSWORD '<新パスワード>';"`
  2. `/opt/yn-tools/.env` の `DB_PASSWORD=` と接続文字列を新パスワードに更新
  3. `docker compose down && docker compose up -d`
- **手順（SECRET_KEY / ENCRYPTION_KEY）**:
  - `SECRET_KEY` は `python -c "import secrets; print(secrets.token_urlsafe(32))"` で生成し `.env` 更新
  - **`ENCRYPTION_KEY` は要注意**: これで暗号化したデータがあると、鍵を変えると復号不能になる。
    既存暗号化データの有無を確認してから判断（データがあるなら再暗号化が必要）。不明なら一旦保留。

#### 4. VPS root パスワード（旧値は漏洩済み・要変更）
- **影響**: サーバー全体。ConoHa APIログインとも共通。最も重大。
- **手順**:
  1. ConoHa コントロールパネル → サーバー → 該当VPS → 「VPS設定」→ rootパスワード変更
     （または SSH で `passwd root`）
  2. 新パスワードを安全な場所（パスワードマネージャ）に保管
  3. ローカルの User 環境変数を更新: PowerShell で
     `[Environment]::SetEnvironmentVariable('VPS_ROOT_PW','<新PW>','User')`
  4. ConoHa API を使う場合、API パスワードも同画面で別途再設定を検討
- **注**: 通常の運用は SSH 鍵（`~/.ssh/conoha-vps`）。パスワードは鍵消失時の復旧用。

### 優先度【低】様子見でも可（private・短時間のため）

#### 5. Telegram bot トークン（4種: kyoyaru_bot / JRA / BANEI / 競馬通知）
- **影響**: ボットなりすまし投稿。チャットIDが限定なので影響は限定的。
- **手順（必要なら）**: Telegram の @BotFather → `/revoke` → 新トークン取得 →
  該当環境変数（`TG_BOT_TOKEN` / `TG_TOKEN_JRA` / `TG_TOKEN_BANEI`）と VPS 側を更新。
- **判断**: リスク低。気になる場合のみ。

#### 6. Gemini API キー（2種）
- **影響**: ほぼなし。メモリ記録上、過去の Gemini キーは既に BAN/失効済みの可能性大。
- **手順（必要なら）**: Google AI Studio で該当キーを削除 → 新規発行 → 環境変数更新。
- **判断**: 失効済みなら対応不要。現用なら一応削除。

## ローテーション後のチェックリスト
- [ ] Stripe: 新 `sk_live` / `whsec` で決済・Webhook が通る
- [ ] Google: 新クライアントシークレットでログインできる
- [ ] DB: 新パスワードでアプリが起動・DB接続できる
- [ ] VPS: 新 root パスワードでログインできる（鍵接続も維持）
- [ ] ローカル環境変数（`VPS_ROOT_PW` 等）を新値に更新済み
- [ ] 旧値はどこにも残っていない（VPS `.env`・ローカル・GitHub）

## 再発防止（恒久）
- シークレットはコードに直書きしない。すべて `.env` / 環境変数 / シークレットマネージャ経由。
- `.gitignore` に `.env` 系・`settings.local.json` 等を網羅済み（2026-05-30 強化）。
- push 前に必ず機密スキャン（GitHub軸移行の実装計画に「Task 3 安全検証ゲート」として組込み済み）。
- 機密検出時は「commit に進まない」ことを徹底（今回の反省: ゲート出力を見て止まらなかったのが原因）。
