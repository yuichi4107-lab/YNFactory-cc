---
created: "2026-03-17"
topic: "営業自動化ツール 技術設計書"
type: technical-doc
tags: [python, fastapi, scraping, automation]
---

# 営業自動化ツール 技術設計書

## 概要
企業リスト生成〜営業メール送信〜CRM管理を一元化するWebアプリ。将来のSaaS化を見据え、モジュラーなアーキテクチャで設計する。

## 設計・方針

### アーキテクチャ概要
```
┌─────────────────────────────────────────┐
│              Frontend (Web UI)           │
│         Jinja2 Templates / HTMX         │
├─────────────────────────────────────────┤
│              Backend (API)              │
│           FastAPI + SQLAlchemy          │
├──────┬──────┬──────┬──────┬────────────┤
│ 企業  │ HP   │ メール │ CRM  │ ダッシュ   │
│ リスト │ 巡回  │ 送信  │ 管理  │ ボード    │
├──────┴──────┴──────┴──────┴────────────┤
│        Background Workers              │
│        Celery + Redis                  │
├─────────────────────────────────────────┤
│            Database                     │
│     SQLite (dev) / PostgreSQL (prod)    │
└─────────────────────────────────────────┘
```

### 技術選定
| 領域 | 技術 | 選定理由 |
|------|------|---------|
| Webフレームワーク | FastAPI | 非同期対応、自動API docs、SaaS化時のAPI提供が容易 |
| ORM | SQLAlchemy 2.0 | Python標準、DB切替が容易 |
| フロントエンド | Jinja2 + HTMX | SPAの複雑さを避けつつ動的UIを実現 |
| スクレイピング | BeautifulSoup4 + Playwright | Seleniumより軽量・安定。ヘッドレスブラウザ対応 |
| タスクキュー | Celery + Redis | 送信間隔制御、非同期スクレイピングに必須 |
| メール | smtplib | 標準ライブラリ、SMTP設定で柔軟対応 |
| データ出力 | openpyxl + csv | Excel/CSV両対応 |

### DB設計（主要テーブル）
```
companies
├── id (PK)
├── name
├── address
├── phone
├── website_url
├── google_maps_url
├── review_count
├── industry
├── region
├── created_at
└── updated_at

contacts
├── id (PK)
├── company_id (FK)
├── email
├── email_type (info/contact/support/other)
├── sns_instagram
├── sns_twitter
├── sns_facebook
└── extracted_at

campaigns
├── id (PK)
├── name
├── subject_template
├── body_template
├── created_at
└── status (draft/active/paused/completed)

outreach_logs
├── id (PK)
├── company_id (FK)
├── contact_id (FK)
├── campaign_id (FK)
├── type (email/form)
├── status (pending/sent/failed/replied)
├── sent_at
├── replied_at
└── notes

crm_status
├── id (PK)
├── company_id (FK)
├── status (未営業/送信済/返信あり/商談/契約)
├── score
├── memo
├── is_blacklisted
└── updated_at
```

### ディレクトリ構成（案）
```
sales-automation/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIエントリポイント
│   ├── config.py             # 設定管理
│   ├── database.py           # DB接続・セッション
│   ├── models/               # SQLAlchemyモデル
│   │   ├── company.py
│   │   ├── contact.py
│   │   ├── campaign.py
│   │   ├── outreach.py
│   │   └── crm.py
│   ├── routers/              # APIルーター
│   │   ├── companies.py
│   │   ├── scraper.py
│   │   ├── email_sender.py
│   │   ├── form_sender.py
│   │   ├── crm.py
│   │   └── dashboard.py
│   ├── services/             # ビジネスロジック
│   │   ├── company_search.py   # Google Maps等からの企業リスト取得
│   │   ├── hp_crawler.py       # HP巡回・情報抽出
│   │   ├── email_extractor.py  # メールアドレス抽出
│   │   ├── email_sender.py     # メール送信
│   │   ├── form_submitter.py   # フォーム営業
│   │   ├── scoring.py          # スコアリング
│   │   └── export.py           # CSV/Excel出力
│   ├── templates/            # Jinja2テンプレート
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── companies/
│   │   ├── campaigns/
│   │   └── crm/
│   └── static/               # CSS/JS
├── workers/
│   ├── celery_app.py
│   └── tasks.py
├── tests/
├── alembic/                  # DBマイグレーション
├── requirements.txt
├── .env.example
└── README.md
```

## 詳細

### ① 企業リスト生成
- Google Maps API または Google Places API を利用
- フォールバック: Webスクレイピング（利用規約に注意）
- 検索パラメータ: キーワード、地域、業種、件数上限

### ② HP巡回・情報取得
- TOP / Contact / About / Company ページを優先巡回
- robots.txt を尊重
- リクエスト間隔: 最低2秒（サーバー負荷考慮）

### ③ メールアドレス抽出
- 正規表現ベースの抽出 + mailto: リンク解析
- info@ / contact@ / support@ を優先的にピックアップ
- 重複排除・バリデーション

### ⑦ 営業スコアリング
- スコア算出基準（案）:
  - メールあり: +30点
  - HP あり: +20点
  - レビュー数10以上: +20点
  - SNSあり: +15点（各SNS +5点）
  - お問い合わせフォームあり: +15点

## 参考
- FastAPI公式: https://fastapi.tiangolo.com/
- Playwright Python: https://playwright.dev/python/
- 特定電子メール法 → リサーチ部署の法的調査を参照
