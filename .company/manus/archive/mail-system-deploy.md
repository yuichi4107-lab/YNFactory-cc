---
title: メール送信システム（mail-system）Renderデプロイ
priority: 高
created: 2026-03-20
type: deployment
---

# メール送信システム - Renderデプロイ指示書

## 概要

`mail-system/` フォルダにあるFlask製マルチユーザーメール送信Webアプリを Render にデプロイする。

## 前提

- Python 3.12
- Flask + SQLAlchemy + Flask-Login
- PostgreSQL（Render Free Tier）
- エントリーポイント: `run.py`（`app` オブジェクトをエクスポート）

## デプロイ手順

### Step 1: GitHubリポジトリ作成

1. `mail-system/` フォルダをGitHubリポジトリとして作成（プライベート）
2. リポジトリ名: `mail-system`
3. 以下のファイルは `.gitignore` に追加:
   ```
   __pycache__/
   *.pyc
   instance/
   *.db
   .env
   uploads/
   ```

4. 古いファイル（旧版）は含めない。新しい `app/` パッケージ構成のみをpush:
   ```
   mail-system/
   ├── run.py
   ├── config.py
   ├── requirements.txt
   ├── Procfile
   ├── .env.example
   └── app/
       ├── __init__.py
       ├── extensions.py
       ├── models.py
       ├── routes/
       │   ├── __init__.py
       │   ├── auth.py
       │   ├── main.py
       │   ├── contacts.py
       │   ├── templates_mgmt.py
       │   ├── settings.py
       │   └── history.py
       ├── services/
       │   ├── __init__.py
       │   ├── crypto.py
       │   └── email_sender.py
       ├── templates/
       │   ├── base.html
       │   ├── auth/
       │   │   ├── login.html
       │   │   └── register.html
       │   ├── main/
       │   │   ├── index.html
       │   │   ├── preview.html
       │   │   ├── bulk.html
       │   │   ├── bulk_preview.html
       │   │   └── bulk_results.html
       │   ├── contacts/
       │   │   └── list.html
       │   ├── templates_mgmt/
       │   │   ├── list.html
       │   │   └── form.html
       │   ├── settings/
       │   │   └── smtp.html
       │   └── history/
       │       └── list.html
       └── static/
           └── style.css
   ```

### Step 2: Render設定

#### 2a: PostgreSQL作成
1. Render Dashboard → New → PostgreSQL
2. Name: `mail-system-db`
3. Region: Oregon (US West)
4. Plan: Free
5. 作成後、**Internal Database URL** をコピー

#### 2b: Web Service作成
1. Render Dashboard → New → Web Service
2. GitHubリポジトリ `mail-system` を接続
3. 設定:
   - **Name**: `mail-system`
   - **Region**: Oregon
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
   - **Plan**: Free

#### 2c: 環境変数設定

以下の環境変数を設定:

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `DATABASE_URL` | (Step 2aでコピーしたInternal URL) | PostgreSQL接続文字列 |
| `SECRET_KEY` | (ランダム文字列を生成) | Flask秘密鍵 |
| `ENCRYPTION_KEY` | (下記コマンドで生成) | SMTP パスワード暗号化鍵 |

**ENCRYPTION_KEY の生成方法:**
```python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 3: デプロイ確認

1. デプロイが成功したら、URLにアクセス
2. `/auth/register` でアカウント作成が表示されることを確認
3. アカウント登録 → SMTP設定 → テスト送信 の一連の流れを確認

### Step 4: 結果報告

以下を報告:
- デプロイURL
- 動作確認結果（登録→ログイン→SMTP設定画面が表示されるか）

## 注意事項

- `.env` ファイルはGitHubにpushしない
- 旧版のファイル（`app.py`, `templates/config.yaml`, `templates/web/`, `data/`, `attachments/`）はリポジトリに含めない
- Render Free Tierは15分無操作でスリープする（初回アクセスが遅い）
