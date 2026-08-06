---
created: "2026-03-20"
topic: "YN Tools 統合ポータル 技術設計書"
type: technical-doc
tags: [saas, fastapi, google-oauth, stripe, postgresql]
---

# YN Tools 統合ポータル 技術設計書

## 概要

既存の自作Webアプリ3本（営業自動化・メール送信・GEMS/GPT配布）を統合し、共通アカウント・サブスク課金のSaaSプラットフォームとして提供する。ユーザーコミュニティ機能（評価・フィードバック・アプリリクエスト）も搭載。

### ビジネスモデル
| 項目 | 内容 |
|------|------|
| 登録 | 無料（Google認証） |
| 無料期間 | 登録から1ヶ月 |
| 有料プラン | 月額500円（全ツール利用可能） |
| 決済 | Stripe |

### 提供ツール
| ツール | 概要 | 移植元 |
|--------|------|--------|
| 営業自動化 | 企業リスト→HP巡回→CRM→メール送信 | `sales-automation/` (FastAPI) |
| メール送信 | テンプレメール一括送信・履歴管理 | `mail-system/` (Flask→FastAPI移植) |
| GEMS/GPTライブラリ | AI業務改善プロンプト100件の閲覧・DL | 新規構築（コンテンツは完成済み） |

---

## 設計・方針

### アーキテクチャ概要

```
┌──────────────────────────────────────────────────┐
│                 Frontend (Web UI)                 │
│            Jinja2 Templates + HTMX               │
│     ┌──────────────────────────────────────┐     │
│     │ 共通: ヘッダー / サイドバー / フッター   │     │
│     │ ダッシュボード / アカウント設定          │     │
│     └──────────────────────────────────────┘     │
├──────────────────────────────────────────────────┤
│                Backend (FastAPI)                  │
│                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌───────────┐ │
│  │ Auth   │ │Billing │ │ Users  │ │ Community │ │
│  │Google  │ │Stripe  │ │Profile │ │Review/    │ │
│  │OAuth   │ │Webhook │ │Plan    │ │Feedback/  │ │
│  │Session │ │Trial   │ │Mgmt   │ │Request    │ │
│  └────────┘ └────────┘ └────────┘ └───────────┘ │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │              Tools (各ツール)              │    │
│  │  ┌──────────┬──────────┬──────────────┐  │    │
│  │  │ 営業自動化│ メール送信 │ GEMS/GPT    │  │    │
│  │  │          │          │ ライブラリ    │  │    │
│  │  └──────────┴──────────┴──────────────┘  │    │
│  └──────────────────────────────────────────┘    │
├──────────────────────────────────────────────────┤
│              PostgreSQL (Render)                  │
└──────────────────────────────────────────────────┘
```

### 技術選定

| 領域 | 技術 | 選定理由 |
|------|------|---------|
| Webフレームワーク | FastAPI | 既存sales-automationと統一。非同期対応 |
| フロントエンド | Jinja2 + HTMX | 既存資産を活用。SPA不要でシンプル |
| ORM | SQLAlchemy 2.0 (async) | 既存sales-automationと統一 |
| 認証 | Authlib (Google OAuth 2.0) | Python向けOAuthライブラリの定番 |
| 課金 | Stripe Checkout + Webhook | SaaS課金の業界標準。月500円サブスク対応 |
| セッション | itsdangerous (署名付きCookie) | サーバーサイドセッション不要で軽量 |
| DB | PostgreSQL (Render) | 既存インフラ活用 |
| スクレイピング | BeautifulSoup4 + Playwright | 営業自動化から流用 |
| メール送信 | aiosmtplib | FastAPI非同期対応版 |
| CSS | Tailwind CSS (CDN) | モダンUI、レスポンシブ対応が容易 |

---

### DB設計

#### ユーザー・認証・課金

```
users
├── id (PK)
├── google_id (UNIQUE)        # Google OAuth sub
├── email (UNIQUE)
├── name
├── avatar_url                # Googleプロフィール画像
├── plan (free/pro)           # 現在のプラン
├── trial_ends_at             # 無料期間終了日（登録日+1ヶ月）
├── stripe_customer_id        # Stripe顧客ID
├── stripe_subscription_id    # StripeサブスクリプションID
├── is_active                 # アカウント有効フラグ
├── created_at
└── updated_at

payment_history
├── id (PK)
├── user_id (FK → users)
├── stripe_payment_intent_id
├── amount                    # 金額（500）
├── currency (jpy)
├── status (succeeded/failed/refunded)
├── paid_at
└── created_at
```

#### コミュニティ（評価・フィードバック・リクエスト）

```
reviews
├── id (PK)
├── user_id (FK → users)
├── tool_slug (sales/mailer/gems)  # 対象ツール
├── rating (1-5)                    # 星評価
├── comment                         # 感想コメント
├── created_at
└── updated_at

feedbacks
├── id (PK)
├── user_id (FK → users)
├── tool_slug (sales/mailer/gems/general)
├── category (bug/improvement/other)  # バグ/改善要望/その他
├── title
├── body
├── status (open/in-progress/resolved/closed)
├── admin_reply                      # 管理者からの返答
├── created_at
└── updated_at

app_requests
├── id (PK)
├── user_id (FK → users)            # 提案者
├── title                            # アプリ名/概要
├── description                      # 詳細説明
├── vote_count                       # 投票数（集計キャッシュ）
├── status (open/planned/building/released/declined)
├── admin_note                       # 管理者メモ
├── created_at
└── updated_at

app_request_votes
├── id (PK)
├── request_id (FK → app_requests)
├── user_id (FK → users)
├── created_at
└── UNIQUE(request_id, user_id)      # 1人1票
```

#### 営業自動化ツール（既存テーブルにuser_id追加）

```
companies         → + user_id (FK)
contacts          → + user_id (FK)
campaigns         → + user_id (FK)
outreach_logs     → (user_idはcompany経由)
crm_status        → (user_idはcompany経由)
```

#### メール送信ツール（Flask版から移植）

```
smtp_configs      → 既存構造 + user_id (FK → users)
email_templates   → 既存構造 + user_id (FK → users)
mail_contacts     → 既存構造 + user_id (FK → users) ※テーブル名変更（contactsと衝突回避）
send_history      → 既存構造 + user_id (FK → users)
```

#### GEMS/GPTライブラリ

```
gems_items
├── id (PK)
├── title                     # GEMS/GPT名
├── type (gem/gpt)
├── category                  # カテゴリ（業務効率化、分析、etc.）
├── description               # 説明文
├── prompt_content            # プロンプト本文
├── usage_guide               # 使い方ガイド
├── download_count            # DL数
├── created_at
└── updated_at
```

---

### 認証フロー

```
ユーザー
  │
  ├─→ [Googleでログイン] ボタンクリック
  │     │
  │     ├─→ Google OAuth 認証画面
  │     │     │
  │     │     └─→ 認可コード返却
  │     │
  │     ├─→ サーバーでトークン交換
  │     │     │
  │     │     ├─→ 新規ユーザー → users テーブルに登録
  │     │     │     plan=free, trial_ends_at=now+30日
  │     │     │
  │     │     └─→ 既存ユーザー → ログイン
  │     │
  │     └─→ セッションCookie発行 → ダッシュボードへ
  │
  └─→ 各ページアクセス時
        │
        ├─→ ミドルウェアでプラン判定
        │     │
        │     ├─→ pro → 全機能利用可
        │     ├─→ free かつ trial_ends_at > now → 全機能利用可
        │     └─→ free かつ trial_ends_at ≤ now → 課金ページへ誘導
        │
        └─→ ツールの全クエリに user_id フィルタ適用（マルチテナント）
```

### 課金フロー（Stripe）

```
無料期間終了
  │
  ├─→ ツールにアクセス
  │     │
  │     └─→ 「無料期間が終了しました。月額500円で継続利用できます」
  │           │
  │           └─→ [プランをアップグレード] ボタン
  │                 │
  │                 └─→ Stripe Checkout Session 作成
  │                       │
  │                       └─→ Stripe決済画面（カード入力）
  │                             │
  │                             ├─→ 成功 → Webhook受信
  │                             │     │
  │                             │     └─→ user.plan = "pro"
  │                             │         stripe_customer_id 保存
  │                             │         stripe_subscription_id 保存
  │                             │
  │                             └─→ キャンセル → 元の画面に戻る
  │
  Stripe月次自動課金
  │
  ├─→ 成功 → Webhook: invoice.paid → 何もしない（proのまま）
  └─→ 失敗 → Webhook: invoice.payment_failed
        │
        └─→ 猶予期間後 → customer.subscription.deleted
              │
              └─→ user.plan = "free"（ダウングレード）
```

---

### ディレクトリ構成

```
yn-tools/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPIエントリポイント
│   ├── config.py                  # 設定管理（env）
│   ├── database.py                # DB接続・セッション
│   │
│   ├── auth/                      # 認証
│   │   ├── router.py              # /login, /logout, /callback
│   │   ├── google_oauth.py        # Google OAuth ロジック
│   │   └── dependencies.py        # get_current_user, require_active_plan
│   │
│   ├── billing/                   # 課金
│   │   ├── router.py              # /billing, /checkout, /webhook
│   │   ├── stripe_service.py      # Stripe API操作
│   │   └── plan_guard.py          # プラン判定ミドルウェア
│   │
│   ├── users/                     # ユーザー管理
│   │   ├── router.py              # /account, /profile
│   │   ├── models.py              # User, PaymentHistory
│   │   └── service.py
│   │
│   ├── community/                 # コミュニティ
│   │   ├── router.py              # /reviews, /feedback, /requests
│   │   ├── models.py              # Review, Feedback, AppRequest, Vote
│   │   └── service.py
│   │
│   ├── tools/                     # 各ツール
│   │   ├── sales/                 # 営業自動化（既存移植）
│   │   │   ├── router.py
│   │   │   ├── models.py          # Company, Contact, Campaign, etc.
│   │   │   └── services/
│   │   │       ├── company_search.py
│   │   │       ├── hp_crawler.py
│   │   │       ├── bulk_crawler.py
│   │   │       ├── email_sender.py
│   │   │       └── export.py
│   │   │
│   │   ├── mailer/                # メール送信（Flask→FastAPI移植）
│   │   │   ├── router.py
│   │   │   ├── models.py          # SmtpConfig, EmailTemplate, etc.
│   │   │   └── services/
│   │   │       ├── email_sender.py
│   │   │       └── crypto.py
│   │   │
│   │   └── gems/                  # GEMS/GPTライブラリ（新規）
│   │       ├── router.py
│   │       ├── models.py          # GemsItem
│   │       └── service.py
│   │
│   ├── admin/                     # 管理者機能
│   │   ├── router.py              # /admin（ユーザー一覧、フィードバック管理）
│   │   └── service.py
│   │
│   ├── templates/                 # Jinja2テンプレート
│   │   ├── base.html              # 共通レイアウト（Tailwind）
│   │   ├── landing.html           # LP（未ログイン時トップ）
│   │   ├── dashboard.html         # ログイン後ダッシュボード
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── billing/
│   │   │   ├── pricing.html       # 料金プラン
│   │   │   └── upgrade.html       # アップグレード画面
│   │   ├── account/
│   │   │   └── profile.html
│   │   ├── community/
│   │   │   ├── reviews.html       # 評価一覧
│   │   │   ├── feedback.html      # フィードバック投稿・一覧
│   │   │   └── requests.html      # アプリリクエスト一覧+投票
│   │   ├── tools/
│   │   │   ├── sales/             # 営業自動化の画面群
│   │   │   ├── mailer/            # メール送信の画面群
│   │   │   └── gems/              # GEMS/GPTの画面群
│   │   └── admin/
│   │       └── index.html
│   │
│   └── static/
│       ├── css/style.css
│       └── js/htmx.min.js
│
├── alembic/                       # DBマイグレーション
│   └── versions/
├── tests/
├── requirements.txt
├── render.yaml
├── .env.example
└── README.md
```

---

### 画面構成

```
[未ログイン]
  / ─────────────────→ ランディングページ（サービス紹介 + 料金 + Googleログインボタン）

[ログイン後]
  /dashboard ────────→ ダッシュボード（利用可能ツール一覧 + プラン状態 + お知らせ）

  /tools/sales/* ────→ 営業自動化ツール（既存画面を移植）
  /tools/mailer/* ───→ メール送信ツール（既存画面を移植）
  /tools/gems/* ─────→ GEMS/GPTライブラリ（一覧・検索・詳細・DL）

  /community/reviews → アプリ評価一覧（ツール別タブ + 星評価 + コメント）
  /community/feedback → フィードバック（投稿フォーム + 一覧 + ステータス表示）
  /community/requests → アプリリクエスト（提案 + 投票 + ステータス）

  /account ──────────→ プロフィール・プラン管理
  /billing/upgrade ──→ プランアップグレード（Stripe Checkout）

[管理者]
  /admin ────────────→ ユーザー管理・フィードバック対応・統計
```

---

### 必要な外部サービス・API キー

| サービス | 用途 | 必要な設定 |
|---------|------|-----------|
| Google Cloud Console | OAuth 2.0 | Client ID, Client Secret, Redirect URI |
| Stripe | サブスク課金 | Secret Key, Publishable Key, Webhook Secret |
| Render | ホスティング | 既存アカウント利用 |
| SMTP (Gmail等) | メール送信ツール用 | ユーザーが各自設定 |

### 環境変数（.env）

```
# App
APP_ENV=production
SECRET_KEY=xxx
DATABASE_URL=postgresql+asyncpg://...

# Google OAuth
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=https://yn-tools.onrender.com/auth/callback

# Stripe
STRIPE_SECRET_KEY=sk_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID=price_xxx   # 月額500円の Price ID

# 営業自動化ツール用
GOOGLE_PLACES_API_KEY=xxx
SCRAPING_DELAY_SEC=2.0
```

---

## 詳細

### マルチテナント設計
- 全ツールのデータに `user_id` を付与
- クエリ時は必ず `WHERE user_id = :current_user_id` でフィルタ
- FastAPIの `Depends(get_current_user)` でユーザーを取得し、サービス層に渡す
- 他ユーザーのデータには絶対にアクセスできない設計

### プランガード
```python
# すべてのツールルーターに適用
async def require_active_plan(user = Depends(get_current_user)):
    if user.plan == "pro":
        return user
    if user.trial_ends_at and user.trial_ends_at > datetime.utcnow():
        return user
    raise HTTPException(status_code=402, detail="plan_expired")
```

### 管理者機能
- 管理者フラグ: `users.is_admin` (boolean)
- フィードバックへの返答・ステータス変更
- アプリリクエストのステータス変更
- ユーザー一覧・統計（登録数、課金率、アクティブ率）
- GEMS/GPTコンテンツの追加・編集

---

## 参考
- Authlib (Google OAuth): https://docs.authlib.org/
- Stripe Subscriptions: https://stripe.com/docs/billing/subscriptions
- FastAPI公式: https://fastapi.tiangolo.com/
- HTMX: https://htmx.org/
