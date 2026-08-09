# 要件定義書: YN Tools 追加5ツール実装

作成日: 2026-04-13
対象プロジェクト: YN Tools (FastAPI + Jinja2 + SQLAlchemy)
Stripe価格: 月額100円/ツール

---

## ゴール

ランサーズ・ランサーズ・CWの発注傾向上位から選定した5ツール（求人票ジェネレーター・データクリーニング・画像一括加工・ステップメール作成・契約書自動作成）を実装し、本番VPS上で既存ツールと同一品質で稼働させる。

---

## スコープ

### やること
- 5ツールそれぞれのディレクトリ作成（`app/tools/{slug}/`）
- `router.py` / `models.py` / `service.py` の実装
- Jinja2テンプレート作成（`app/templates/tools/{slug}/`）
- `app/main.py` へのルーター登録
- `ToolDefinition` シードデータ追加（display_order 32〜36）
- Alembicマイグレーション作成・適用
- ConoHa VPS へのデプロイ（Docker Compose 再ビルド）
- Stripe本番商品・Price作成（各ツール100円/月）

### やらないこと
- 既存ツールの改修（contract等のUIは参照のみ）
- モバイルアプリ対応
- 他社APIとのWebhook連携（Stripe課金フロー変更なし）
- 多言語対応（日本語のみ）
- 管理画面での売上分析拡張

---

## 工程一覧

| 工程 | slug | 中間成果物 | 想定日数 | 入力 |
|---|---|---|---|---|
| 工程1 | jobposting | 求人票ジェネレーターが本番稼働 | 3日 | 本要件定義書 |
| 工程2 | dataclean | データクリーニングツールが本番稼働 | 3日 | 工程1完了後 |
| 工程3 | imgbatch | 画像一括加工ツールが本番稼働 | 4日 | 工程2完了後 |
| 工程4 | stepmail | ステップメール作成ツールが本番稼働 | 3日 | 工程3完了後 |
| 工程5 | legalgen | 契約書自動作成ツールが本番稼働 | 4日 | 工程4完了後 |

---

## 共通技術仕様

### ディレクトリ構成（各ツール共通）
```
app/tools/{slug}/
├── __init__.py
├── models.py       # SQLAlchemy Mapped モデル
├── router.py       # APIRouter(prefix="/tools/{slug}")
└── service.py      # AI処理・ビジネスロジック
app/templates/tools/{slug}/
└── index.html      # Jinja2テンプレート（base.html継承）
```

### 実装規約
- ルーターは `require_tool_access("{slug}")` で認証・課金チェック
- DB非同期: `AsyncSession` + `async with db.begin()`
- 月間利用回数: `get_monthly_usage` / `get_limit` / `limit_error` を使用
- AI呼び出し: `openai.AsyncOpenAI` + `gpt-4o-mini`
- Stripe商品: `ToolDefinition` シードに `stripe_product_id` / `stripe_price_id` を追加

---

## 工程1: jobposting（求人票ジェネレーター）

### ユーザーストーリー
1. 飲食店オーナーとして、業種テンプレートを選ぶだけで求人票の下書きを10分以内に作りたい。なぜなら採用担当がおらず、毎回ゼロから書くのに2時間かかるから。
2. 介護施設の管理者として、過去の求人票を一覧から選んで再利用したい。なぜなら毎月同じポジションの求人を出すため、毎回入力するのが非効率だから。
3. 建設会社の総務担当として、Indeed・タウンワーク・ハローワーク向けのフォーマットで求人票をコピペできる状態で出力してほしい。なぜなら各媒体のテキスト制限に合わせて手動で書き直す手間を省きたいから。

### 画面構成

```
/tools/jobposting/          ← ダッシュボード（履歴一覧・新規作成ボタン）
/tools/jobposting/new       ← 新規作成フォーム（業種選択→詳細入力→生成）
/tools/jobposting/{id}      ← 生成結果表示・編集・コピー・再生成
```

#### 画面遷移
1. ダッシュボード → 「新規作成」ボタン → new
2. new: 業種テンプレート選択 → フォーム自動補完 → 生成実行 → 結果ページへリダイレクト
3. 結果ページ: テキスト編集 → 保存（PATCH /api/{id}） → コピーボタン

### 主要機能の詳細仕様

#### 業種テンプレート（9種）
| slug | 業種名 |
|---|---|
| restaurant | 飲食店ホール・キッチン |
| care | 介護職・ヘルパー |
| construction | 建設・土木作業員 |
| office | 一般事務・経理 |
| engineer | ITエンジニア |
| retail | 販売員・レジスタッフ |
| driver | 配送ドライバー |
| medical | 医療事務・クリニックスタッフ |
| other | その他（自由入力） |

#### 入力フォーム項目
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| industry_template | select | 必須 | 業種テンプレートslug |
| job_title | text | 必須 | 職種名（例: ホールスタッフ） |
| company_name | text | 必須 | 会社・店舗名 |
| location | text | 必須 | 勤務地（例: 東京都新宿区） |
| salary_type | select | 必須 | 時給/日給/月給/年収 |
| salary_min | number | 必須 | 最低給与 |
| salary_max | number | 任意 | 最高給与 |
| work_hours | text | 必須 | 勤務時間（例: 10:00〜22:00のうちシフト制） |
| holidays | text | 任意 | 休日・休暇 |
| qualifications | textarea | 任意 | 応募資格・経験 |
| benefits | textarea | 任意 | 待遇・福利厚生 |
| pr_points | textarea | 任意 | アピールポイント（3点まで） |
| target_format | select | 必須 | 出力フォーマット（Indeed / タウンワーク / ハローワーク / 汎用） |

#### AI処理仕様
- 入力フォームデータを構造化してGPT-4o-miniに渡す
- 出力は以下セクションで構成（Markdown形式でDB保存、表示時はプレーンテキスト変換）:
  - 【仕事内容】
  - 【応募資格】
  - 【給与】
  - 【勤務時間】
  - 【待遇・福利厚生】
  - 【会社・店舗PR】
  - 【応募方法】
- フォーマット別の文字数制限をシステムプロンプトで指定（Indeed: 各項目500字以内 / タウンワーク: 全体2000字以内 / ハローワーク: 定型ヘッダー付き / 汎用: 制限なし）

### DBモデル

```python
# app/tools/jobposting/models.py

class JobPosting(Base):
    __tablename__ = "jobposting_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(200))          # 保存名（例: 「ホールスタッフ_2026-04」）
    industry_template: Mapped[str] = mapped_column(String(30))
    job_title: Mapped[str] = mapped_column(String(200))
    company_name: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(200))
    salary_type: Mapped[str] = mapped_column(String(20))
    salary_min: Mapped[int] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_hours: Mapped[str] = mapped_column(String(300))
    holidays: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits: Mapped[str | None] = mapped_column(Text, nullable=True)
    pr_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_format: Mapped[str] = mapped_column(String(30))   # indeed / taunt / hello / general
    generated_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI生成結果
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)     # ユーザー編集後
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

### APIエンドポイント

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---|---|---|---|---|
| GET | /tools/jobposting/ | ダッシュボード | - | HTML（履歴一覧） |
| GET | /tools/jobposting/new | 作成フォーム | - | HTML |
| POST | /tools/jobposting/api/generate | AI生成 | Form（全フィールド） | JSON `{id, generated_text}` |
| GET | /tools/jobposting/{id} | 結果・編集画面 | - | HTML |
| POST | /tools/jobposting/api/{id}/save | テキスト保存 | JSON `{edited_text}` | JSON `{ok}` |
| POST | /tools/jobposting/api/{id}/regenerate | 再生成 | JSON `{field_overrides}` | JSON `{generated_text}` |
| DELETE | /tools/jobposting/api/{id} | 削除 | - | JSON `{ok}` |

### UIの要件
- ダッシュボード: カード形式で過去の求人票一覧（タイトル・業種・作成日・コピーボタン）
- 作成フォーム: 業種テンプレート選択時にJSで推奨テキストを各フィールドにプリセット
- 結果画面: 左カラム=入力内容サマリ、右カラム=生成テキスト（contenteditable div）
- コピーボタン: クリックでクリップボードにコピー、「コピーしました！」フラッシュ表示
- 既存ツールデザイン踏襲: `bg-white rounded-xl shadow p-6`、青系アクセントカラー

### 完了条件
- [ ] `/tools/jobposting/` にアクセスするとダッシュボードが表示されること
- [ ] 9種の業種テンプレートが選択でき、選択後にフォームにデフォルト値が入ること
- [ ] フォーム送信後にGPT-4o-miniが求人票テキストを生成し結果画面に表示されること
- [ ] 生成結果が4フォーマット（Indeed/タウンワーク/ハローワーク/汎用）で出力されること
- [ ] 結果テキストをコピーボタンでクリップボードにコピーできること
- [ ] 過去の求人票が一覧に表示され、再編集・再生成・削除ができること
- [ ] Stripe商品が本番に作成され、`ToolDefinition` に登録されていること
- [ ] VPSでDockerコンテナが正常起動し、本番URLでアクセスできること
- [ ] 月間利用回数制限が機能すること

### 品質チェック項目（jobposting）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 9種の業種テンプレートが選択でき、フォームにデフォルト値がセットされること | 機能要件 | 20 |
| 2 | AI生成が実行でき、4フォーマット全てで出力されること | 機能要件 | 25 |
| 3 | 生成結果の保存・再編集・削除が正常動作すること | 機能要件 | 15 |
| 4 | 未認証/未課金ユーザーが `/tools/jobposting/` にアクセスした場合にリダイレクトされること | セキュリティ | 15 |
| 5 | 月間利用上限に達した場合にエラーメッセージが表示されること | エラーハンドリング | 10 |
| 6 | コピーボタンが機能し、フラッシュメッセージが表示されること | UI/UX | 5 |
| 7 | 既存ツール（contract等）と同一のデザインパターンを踏襲していること | 可読性・一貫性 | 5 |
| 8 | Alembicマイグレーションが正常に適用され、テーブルが存在すること | インフラ | 5 |
| **合計** | | | **100** |

---

## 工程2: dataclean（データクリーニングツール）

### ユーザーストーリー
1. 営業部門の担当者として、顧客名簿CSVの重複・表記揺れを自動で検出・統一したい。なぜなら毎月手作業で数時間かけているクリーニング作業をゼロにしたいから。
2. マーケティング担当として、クリーニング前後の差分を画面で確認してからダウンロードしたい。なぜなら意図しない変更が含まれていると顧客データに悪影響が出るから。
3. 中小企業の経営者として、電話番号・郵便番号・日付のフォーマットを一括統一したい。なぜなら既存のExcelシートに複数の記法が混在していて困っているから。

### 画面構成

```
/tools/dataclean/           ← ダッシュボード（処理履歴一覧）
/tools/dataclean/new        ← ステップUI（ステップ1〜4）
/tools/dataclean/{id}/result ← 差分プレビュー・ダウンロード
```

#### ステップUI（/tools/dataclean/new）
- **ステップ1: ファイルアップロード** — CSV/Excelドラッグ&ドロップ → プレビュー表示（先頭10行・カラム一覧）
- **ステップ2: クリーニング設定** — チェックボックスで処理を選択
- **ステップ3: 実行確認** — 設定内容サマリ表示 → 「実行」ボタン
- **ステップ4: 完了** — 変更件数サマリ → 結果ページへ

### 主要機能の詳細仕様

#### クリーニング処理オプション
| オプション slug | 処理内容 |
|---|---|
| dedup | 重複行削除（全列一致 or キー列指定） |
| fullhalf | 全角英数字・記号を半角に統一 |
| phone | 電話番号フォーマット統一（ハイフン付き: 000-0000-0000） |
| postal | 郵便番号フォーマット統一（ハイフン付き: 000-0000） |
| date | 日付フォーマット統一（YYYY/MM/DD） |
| whitespace | 前後の空白・改行削除 |
| empty_col | 空白列削除 |
| name_normalize | 名前の表記揺れ統一（株式会社/（株）等） |

#### 処理仕様
- ファイルアップロード: 最大10MB、CSV（UTF-8/Shift-JIS自動判定）/ xlsx対応
- データフレーム処理: `pandas` を使用
- 差分検出: 変更前後のセル値を行単位で比較し、変更セル数・変更行数をカウント
- 差分プレビュー: HTMLテーブルで変更セルをハイライト（黄色背景）表示（最大100行）
- ダウンロード: CSV（UTF-8 BOM付き）またはExcel形式

#### AI補助（name_normalize オプション）
- 会社名の表記揺れ統一のみGPT-4o-miniを使用（「(株)」→「株式会社」等のルールは固定ロジック、AIは曖昧な揺れを判定）

### DBモデル

```python
# app/tools/dataclean/models.py

class DataCleanJob(Base):
    __tablename__ = "dataclean_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    row_count_before: Mapped[int] = mapped_column(Integer, default=0)
    row_count_after: Mapped[int] = mapped_column(Integer, default=0)
    col_count: Mapped[int] = mapped_column(Integer, default=0)
    changed_cells: Mapped[int] = mapped_column(Integer, default=0)
    options_applied: Mapped[str] = mapped_column(String(500))   # JSON配列文字列
    output_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # サーバー側一時ファイルパス
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/done/error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### APIエンドポイント

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---|---|---|---|---|
| GET | /tools/dataclean/ | ダッシュボード | - | HTML |
| GET | /tools/dataclean/new | ステップUI | - | HTML |
| POST | /tools/dataclean/api/upload | ファイルアップロード | multipart/form-data（file） | JSON `{job_id, columns, preview_html, row_count, encoding}` |
| POST | /tools/dataclean/api/{job_id}/execute | クリーニング実行 | JSON `{options: [...], dedup_key_col?: str}` | JSON `{changed_cells, row_before, row_after, redirect_url}` |
| GET | /tools/dataclean/{job_id}/result | 差分プレビュー | - | HTML |
| GET | /tools/dataclean/api/{job_id}/download | クリーン済みファイルDL | Query `format=csv|xlsx` | FileResponse |
| DELETE | /tools/dataclean/api/{job_id} | ジョブ削除（ファイルも） | - | JSON `{ok}` |

### UIの要件
- ステップインジケーター（1→2→3→4）を画面上部に表示（現在ステップをアクティブ表示）
- プレビューテーブル: 先頭10行をScrollable tableで表示、カラム名はヘッダーに固定
- 差分プレビュー: 変更セルを `bg-yellow-100` でハイライト、変更行数・セル数をバッジで表示
- 処理オプション: カード形式のチェックボックスグループ（アイコン付き）

### 完了条件
- [ ] CSVファイル（UTF-8/Shift-JIS）とExcelファイルのアップロードが成功すること
- [ ] プレビューが先頭10行で表示されること
- [ ] 8種のクリーニングオプションが全て機能すること
- [ ] 差分プレビューで変更セルが黄色ハイライトされること
- [ ] CSV（UTF-8 BOM）とExcel形式でダウンロードできること
- [ ] 10MBを超えるファイルで適切なエラーが表示されること
- [ ] 処理履歴が一覧に表示されること
- [ ] VPSで稼働し、Stripe商品が登録されていること

### 品質チェック項目（dataclean）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | CSV（UTF-8/Shift-JIS両対応）とExcelのアップロード・プレビューが正常動作すること | 機能要件 | 20 |
| 2 | 8種のオプション処理が全て正しく動作すること（重複削除・フォーマット統一等） | 機能要件 | 25 |
| 3 | 差分プレビューで変更セルがハイライトされ、変更件数が正確に表示されること | 機能要件 | 15 |
| 4 | CSV/Excel両形式でダウンロードでき、文字化けがないこと（UTF-8 BOM確認） | データ品質 | 15 |
| 5 | 10MB超ファイル・空ファイル・不正形式ファイルでエラーが適切に表示されること | エラーハンドリング | 10 |
| 6 | アップロードした一時ファイルが削除後にサーバーに残らないこと | セキュリティ | 10 |
| 7 | ステップインジケーターが現在位置を正しく表示すること | UI/UX | 5 |
| **合計** | | | **100** |

---

## 工程3: imgbatch（画像一括加工ツール）

### ユーザーストーリー
1. SNS担当者として、1枚の画像を複数のSNS推奨サイズに一括リサイズして全部まとめてダウンロードしたい。なぜなら毎回Canvaで手動リサイズするのに30分かかっているから。
2. ECショップ運営者として、商品画像の背景を一括で除去したい。なぜなら毎回デザイナーに依頼すると1枚500円〜かかるから。
3. AI画像生成を使っているクリエイターとして、生成した画像を指定フォーマット（WebP/JPG）に一括変換してサイズ最適化したい。なぜなら画像ファイルが大きすぎてWebに使えないから。

### 画面構成

```
/tools/imgbatch/            ← ダッシュボード（バッチ処理履歴）
/tools/imgbatch/new         ← 処理設定画面（アップロード+設定）
/tools/imgbatch/{batch_id}/result ← 結果プレビュー・ZIPダウンロード
```

### 主要機能の詳細仕様

#### 対応処理モード
| モード | 処理内容 | ライブラリ |
|---|---|---|
| resize_preset | SNSプリセットサイズへリサイズ | Pillow |
| resize_custom | 指定サイズ（W×H）へリサイズ | Pillow |
| format_convert | フォーマット変換（JPG/PNG/WebP/AVIF） | Pillow |
| bg_remove | 背景除去 | rembg |
| crop_center | 中央クロップ（指定アスペクト比） | Pillow |
| optimize | ファイルサイズ最適化（品質調整） | Pillow |

#### SNSプリセット一覧
| プリセット名 | サイズ (W×H) | 対象 |
|---|---|---|
| instagram_post | 1080×1080 | Instagram 投稿 |
| instagram_story | 1080×1920 | Instagram ストーリー |
| instagram_reel | 1080×1920 | Instagram リール |
| x_post | 1200×675 | X（旧Twitter）投稿 |
| facebook_post | 1200×628 | Facebook 投稿 |
| youtube_thumb | 1280×720 | YouTube サムネイル |
| ogp | 1200×630 | OGP / SNSシェア用 |
| line_timeline | 1040×1040 | LINE タイムライン |
| tiktok | 1080×1920 | TikTok |

#### ファイルアップロード仕様
- ドラッグ&ドロップ対応（JSのDragEvent API使用）
- 同時アップロード最大20枚、1ファイル最大20MB
- 対応入力形式: JPG / PNG / WebP / AVIF / GIF（静止画のみ）
- 入力後にサムネイルグリッドプレビュー表示

#### 処理・出力仕様
- 処理はサーバーサイドで同期実行（最大20枚 × 複数プリセットで最大60秒タイムアウト）
- 出力ファイル命名: `{元ファイル名}_{プリセット名または処理名}.{拡張子}`
- 複数ファイル出力時はZIPアーカイブにまとめてダウンロード
- 単一ファイル出力時は直接ダウンロード可能

#### rembg実装方針
- `rembg` PyPIパッケージ（u2netモデル）を使用
- モデルファイルは初回処理時に自動ダウンロード（`~/.u2net/`）
- Docker環境では初回起動スクリプトでプリダウンロード
- API費用ゼロ

### DBモデル

```python
# app/tools/imgbatch/models.py

class ImgBatchJob(Base):
    __tablename__ = "imgbatch_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    mode: Mapped[str] = mapped_column(String(30))             # resize_preset / bg_remove 等
    preset_names: Mapped[str | None] = mapped_column(String(500), nullable=True)  # JSON配列
    custom_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custom_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_format: Mapped[str | None] = mapped_column(String(10), nullable=True)  # jpg/png/webp
    input_file_count: Mapped[int] = mapped_column(Integer, default=0)
    output_file_count: Mapped[int] = mapped_column(Integer, default=0)
    zip_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/processing/done/error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### APIエンドポイント

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---|---|---|---|---|
| GET | /tools/imgbatch/ | ダッシュボード | - | HTML |
| GET | /tools/imgbatch/new | 処理設定画面 | - | HTML |
| POST | /tools/imgbatch/api/upload | 画像アップロード | multipart（files[]） | JSON `{job_id, file_count, preview_urls}` |
| POST | /tools/imgbatch/api/{job_id}/process | 処理実行 | JSON `{mode, presets?, custom_w?, custom_h?, output_format?}` | JSON `{output_count, redirect_url}` |
| GET | /tools/imgbatch/{job_id}/result | 結果プレビュー | - | HTML（サムネイルグリッド） |
| GET | /tools/imgbatch/api/{job_id}/download | ZIPダウンロード | - | FileResponse（ZIP） |
| DELETE | /tools/imgbatch/api/{job_id} | ジョブ削除 | - | JSON `{ok}` |

### UIの要件
- アップロードエリア: 点線ボーダー・中央に雲アイコン「ここに画像をドロップ or クリックして選択」
- アップロード後: 4列グリッドでサムネイル表示（各サムネイルにファイル名・サイズ表示）
- モード選択: タブ切り替え（リサイズ / フォーマット変換 / 背景除去 / クロップ / 最適化）
- プリセット選択: チェックボックスカード（プリセット名・サイズ・対象SNSアイコン）
- 結果画面: Before/Afterサムネイル比較（背景除去時は市松模様背景でα確認）

### 完了条件
- [ ] ドラッグ&ドロップで最大20枚アップロードでき、サムネイルが表示されること
- [ ] SNS9プリセット全てでリサイズが正しいサイズ（W×H）で出力されること
- [ ] カスタムサイズ指定でリサイズができること
- [ ] JPG/PNG/WebP/AVIF フォーマット変換が機能すること
- [ ] 背景除去（rembg）が実行でき、背景が透明なPNGが出力されること
- [ ] 複数出力ファイルがZIPにまとめてダウンロードできること
- [ ] 20MB超ファイルでエラーが表示されること
- [ ] VPSで稼働し、Stripe商品が登録されていること

### 品質チェック項目（imgbatch）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | ドラッグ&ドロップで複数画像アップロードとサムネイルプレビューが機能すること | 機能要件 | 15 |
| 2 | SNS9プリセット全てで正確なW×Hサイズにリサイズされること | 機能要件 | 20 |
| 3 | JPG/PNG/WebP形式変換が正常動作すること | 機能要件 | 10 |
| 4 | rembgによる背景除去が実行でき、出力PNGのα値が正しいこと | 機能要件 | 20 |
| 5 | 複数ファイル出力時にZIPが正常に生成されダウンロードできること | 機能要件 | 10 |
| 6 | 20枚・各20MBの大量処理で60秒以内に完了するか、適切なタイムアウト処理があること | パフォーマンス | 10 |
| 7 | アップロード一時ファイル・ZIPがダウンロード後に削除されること（ストレージ保護） | セキュリティ | 10 |
| 8 | rembgモデルがVPS上に事前配置され、初回から動作すること | インフラ | 5 |
| **合計** | | | **100** |

---

## 工程4: stepmail（ステップメール作成ツール）

### ユーザーストーリー
1. EC事業者として、新規購入者向けの3通ステップメールシリーズを1回の操作で一括生成したい。なぜなら1通ずつ別々に依頼・確認するのに時間がかかりすぎるから。
2. セミナー講師として、集客目的のステップメール（全5通）のシナリオ構成から文章まで自動提案してほしい。なぜなら文章が得意でなく、毎回5万円でライターに外注しているから。
3. コンサルタントとして、作成したステップメールを個別に編集し、全体を一括コピーしてMailchimpに貼り付けられる状態で出力してほしい。なぜなら自社メール配信ツールに手動で入力する必要があるから。

### 画面構成

```
/tools/stepmail/            ← ダッシュボード（シリーズ一覧）
/tools/stepmail/new         ← シリーズ作成フォーム
/tools/stepmail/{series_id} ← シリーズ詳細（全通表示・個別編集）
```

### 主要機能の詳細仕様

#### ビジネス目的テンプレート（8種）
| slug | 目的 | 推奨通数 |
|---|---|---|
| new_customer | 新規顧客ウェルカム | 3〜5通 |
| cart_abandon | カート放棄リカバリ | 3通 |
| seminar | セミナー集客 | 5通 |
| product_launch | 商品ローンチ | 7通 |
| repeat | リピート促進 | 3通 |
| nurture | リード育成（教育コンテンツ） | 5〜10通 |
| onboarding | SaaSオンボーディング | 5通 |
| free_input | 自由設定 | 任意 |

#### 入力フォーム項目
| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| business_purpose | select | 必須 | ビジネス目的（上記8種） |
| product_name | text | 必須 | 商品・サービス名 |
| target_audience | text | 必須 | ターゲット（例: 30代女性フリーランス） |
| step_count | number | 必須 | 通数（3〜10の整数） |
| tone | select | 必須 | トーン（フォーマル/カジュアル/ビジネス） |
| cta_url | url | 任意 | CTAリンク先URL |
| seller_name | text | 任意 | 送信者名（例: 山田太郎） |
| extra_info | textarea | 任意 | 追加情報（強み・USP等） |

#### AI生成仕様
- **1回のAPI呼び出し**でシリーズ全通を一括生成（文脈を保持するため）
- システムプロンプトにシリーズ全体の構成戦略を組み込む（1通目=信頼構築、中盤=教育、最終通=CTA強化等）
- 出力形式: JSON配列（通数分のオブジェクト）
  ```json
  [
    {
      "step": 1,
      "subject": "件名テキスト",
      "preheader": "プレヘッダーテキスト（40字以内）",
      "body": "本文テキスト（Markdown形式）",
      "cta_text": "CTAボタン文言"
    },
    ...
  ]
  ```
- 生成後、各通をDBに個別レコードとして保存

#### 個別編集仕様
- 各通の件名・本文・CTAを直接編集可能（textarea）
- 「この通だけ再生成」ボタン: 前後の通の内容を文脈として渡して再生成
- 編集内容はAUTO-SAVE（変更2秒後に自動的にPATCHリクエスト）

### DBモデル

```python
# app/tools/stepmail/models.py

class StepMailSeries(Base):
    __tablename__ = "stepmail_series"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(200))           # シリーズ名
    business_purpose: Mapped[str] = mapped_column(String(30))
    product_name: Mapped[str] = mapped_column(String(200))
    target_audience: Mapped[str] = mapped_column(String(300))
    step_count: Mapped[int] = mapped_column(Integer)
    tone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/generated
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class StepMailItem(Base):
    __tablename__ = "stepmail_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(Integer, index=True)  # FK to stepmail_series.id
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    step_number: Mapped[int] = mapped_column(Integer)            # 1始まり
    subject: Mapped[str] = mapped_column(String(300))
    preheader: Mapped[str | None] = mapped_column(String(100), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    cta_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

### APIエンドポイント

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---|---|---|---|---|
| GET | /tools/stepmail/ | ダッシュボード | - | HTML（シリーズ一覧） |
| GET | /tools/stepmail/new | 作成フォーム | - | HTML |
| POST | /tools/stepmail/api/generate | シリーズ一括生成 | Form（全フィールド） | JSON `{series_id, items: [...]}` |
| GET | /tools/stepmail/{series_id} | シリーズ詳細 | - | HTML（全通アコーディオン） |
| PATCH | /tools/stepmail/api/item/{item_id} | 個別通の保存 | JSON `{subject, preheader, body, cta_text}` | JSON `{ok}` |
| POST | /tools/stepmail/api/item/{item_id}/regenerate | 1通だけ再生成 | JSON `{context_prev?, context_next?}` | JSON `{subject, body, ...}` |
| DELETE | /tools/stepmail/api/series/{series_id} | シリーズ削除 | - | JSON `{ok}` |
| GET | /tools/stepmail/api/series/{series_id}/export | 全通一括テキスト出力 | Query `format=text|json` | PlainText or JSON |

### UIの要件
- シリーズ詳細画面: アコーディオン形式で各通を表示（通番バッジ・件名・プレヘッダー・本文・CTA）
- 編集エリア: textarea（件名100px固定・本文300px・文字数カウンター付き）
- AUTO-SAVE: 変更後2秒で自動保存、「保存済み ✓」インジケーター表示
- 「全通コピー」ボタン: 全通を「=== 第1通 ===\n件名:...\n本文:...\n\n=== 第2通 ===...」形式でクリップボードコピー
- ダッシュボード: シリーズカード（目的アイコン・タイトル・通数バッジ・作成日）

### 完了条件
- [ ] 8種のビジネス目的テンプレートが選択でき、推奨通数が自動セットされること
- [ ] 一括生成が1回のAPIコールで実行され、全通が生成・保存されること
- [ ] 各通の件名・本文・CTAが個別編集でき、AUTO-SAVEが機能すること
- [ ] 「1通だけ再生成」が前後の文脈を保持して実行されること
- [ ] 「全通コピー」ボタンで全通をプレーンテキスト形式でコピーできること
- [ ] シリーズ一覧に過去の全シリーズが表示されること
- [ ] VPSで稼働し、Stripe商品が登録されていること

### 品質チェック項目（stepmail）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 8種のビジネス目的テンプレート選択が機能し、推奨通数がセットされること | 機能要件 | 10 |
| 2 | シリーズ全通が1回のAPI呼び出しで一括生成され、文脈の連続性があること（1通目→最終通の流れが自然であること） | 機能要件 | 30 |
| 3 | 個別通の編集・AUTO-SAVEが機能し、再読み込み後も内容が保持されること | 機能要件 | 15 |
| 4 | 「1通だけ再生成」が前後文脈を保持して実行されること | 機能要件 | 15 |
| 5 | 「全通コピー」で全通が分かりやすいフォーマットでコピーされること | 機能要件 | 10 |
| 6 | 10通生成時のGPT-4o-mini呼び出しが60秒以内に完了すること（またはストリーミング対応） | パフォーマンス | 10 |
| 7 | 既存ツールと一貫したデザインパターンが適用されていること | 可読性・一貫性 | 10 |
| **合計** | | | **100** |

---

## 工程5: legalgen（契約書・利用規約自動作成ツール）

### ユーザーストーリー
1. フリーランスデザイナーとして、業務委託契約書を案件ごとに5分以内に生成したい。なぜなら毎回弁護士に依頼すると3万円かかり、案件規模と釣り合わないから。
2. スタートアップのCEOとして、スタッフとのNDA（秘密保持契約書）を自社ロゴ入りWordファイルで出力したい。なぜなら外部にすぐ送れる完成形ドキュメントが必要だから。
3. ECサイト運営者として、利用規約・プライバシーポリシーをまとめて生成したい。なぜなら自社サービスに適した内容で、法的に最低限の記載事項が揃っているものが必要だから。

### 画面構成

```
/tools/legalgen/            ← ダッシュボード（作成済み文書一覧）
/tools/legalgen/new         ← 文書種別選択・入力フォーム
/tools/legalgen/{doc_id}    ← 生成結果・編集・ダウンロード
```

### 主要機能の詳細仕様

#### 対応契約書種別（7種）
| slug | 文書名 | 主な入力項目 |
|---|---|---|
| commission | 業務委託契約書 | 委託者/受託者名・業務内容・報酬・期間・知財 |
| nda | NDA（秘密保持契約書） | 当事者名・目的・期間・対象情報の範囲 |
| sale | 売買契約書 | 売主/買主・商品・金額・引渡・瑕疵担保 |
| tos | 利用規約 | サービス名・運営者・禁止事項・免責 |
| privacy | プライバシーポリシー | 事業者名・取得情報・利用目的・問い合わせ先 |
| employment | 雇用契約書 | 雇用者/被雇用者・業務・給与・勤務地・期間 |
| rent | 賃貸借契約書 | 貸主/借主・物件・賃料・期間・敷金 |

#### 入力フォーム（共通 + 種別固有）

共通フィールド:
| フィールド | 型 | 説明 |
|---|---|---|
| doc_type | select | 文書種別（上記7種） |
| party_a_name | text | 甲（第一当事者）の名称 |
| party_b_name | text | 乙（第二当事者）の名称 |
| effective_date | date | 契約日（効力発生日） |
| governing_law | text | 準拠法（デフォルト: 日本法） |
| jurisdiction | text | 合意管轄（デフォルト: 東京地方裁判所） |

種別固有フィールドはJSで動的に表示切替（doc_type選択変更時）。

#### AI生成仕様
- GPT-4o-miniに入力情報を渡し、完全な日本語契約書本文を生成
- 出力形式: Markdown（見出し/条項番号付き）
- 各文書種別ごとに「最低限含めるべき条項リスト」をシステムプロンプトに埋め込む
- 免責文言（必須）: 生成文書の冒頭に以下を自動挿入
  ```
  ※ 本文書はAIによって自動生成されたものであり、法的助言ではありません。
  実際の法的効力を担保するには、弁護士等の専門家にご確認ください。
  ```

#### ダウンロード形式
- **Word（docx）**: `python-docx` で生成（見出し・条項番号付き体裁）
- **PDF**: `WeasyPrint` または `pdfkit` で生成（日本語フォント対応: Noto Sans JP）
- テキスト編集後にダウンロードした場合は編集後テキストを使用

#### contract（チェッカー）との連携
- 結果画面の下部に「この契約書をリスクチェックする」ボタンを表示
- クリック時: 生成テキストをセッション経由で `/tools/contract/` の入力欄に渡してリダイレクト

### DBモデル

```python
# app/tools/legalgen/models.py

class LegalDocument(Base):
    __tablename__ = "legalgen_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    doc_type: Mapped[str] = mapped_column(String(30))          # commission/nda/sale/tos/privacy/employment/rent
    title: Mapped[str] = mapped_column(String(300))            # 自動生成（例: 「業務委託契約書_株式会社ABC_2026-04」）
    party_a_name: Mapped[str] = mapped_column(String(200))
    party_b_name: Mapped[str] = mapped_column(String(200))
    effective_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    input_params: Mapped[str] = mapped_column(Text)            # 全入力パラメータJSON
    generated_text: Mapped[str] = mapped_column(Text)          # AI生成結果（Markdown）
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # ユーザー編集後
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

### APIエンドポイント

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---|---|---|---|---|
| GET | /tools/legalgen/ | ダッシュボード | - | HTML（文書一覧） |
| GET | /tools/legalgen/new | 作成フォーム | - | HTML |
| POST | /tools/legalgen/api/generate | 契約書生成 | Form（全フィールド） | JSON `{doc_id, preview_html}` |
| GET | /tools/legalgen/{doc_id} | 結果・編集画面 | - | HTML |
| PATCH | /tools/legalgen/api/{doc_id} | テキスト保存 | JSON `{edited_text}` | JSON `{ok}` |
| GET | /tools/legalgen/api/{doc_id}/download | ファイルDL | Query `format=docx|pdf` | FileResponse |
| POST | /tools/legalgen/api/{doc_id}/regenerate | 再生成 | JSON `{}` | JSON `{generated_text}` |
| DELETE | /tools/legalgen/api/{doc_id} | 削除 | - | JSON `{ok}` |

### UIの要件
- 文書種別選択: アイコン付きカードグリッド（7種、クリックで選択・フォーム動的切替）
- 結果画面: 左カラム=入力サマリ、右カラム=生成テキスト（リッチテキストエリア or contenteditable）
- 免責文言バナー: 黄色背景の警告ボックスを文書上部に常時表示（非表示にできない）
- ダウンロードボタン: Word / PDF の2ボタン（アイコン付き）
- 「リスクチェックする」ボタン: 結果画面下部に青色ボタン（既存contractツールへ遷移）
- ダッシュボード: 文書種別バッジ（色分け）・タイトル・両当事者名・作成日

### 完了条件
- [ ] 7種の契約書種別が選択でき、種別ごとに固有フィールドが動的に表示されること
- [ ] AI生成が実行され、最低限の条項が含まれた日本語契約書が出力されること
- [ ] 免責文言が生成文書の冒頭に必ず挿入されること（編集しても冒頭に残ること）
- [ ] Word（docx）形式でダウンロードでき、日本語が文字化けしていないこと
- [ ] PDF形式でダウンロードでき、日本語が正常に表示されること
- [ ] 「リスクチェックする」ボタンがcontractツールに生成テキストを渡して遷移すること
- [ ] 過去の文書が一覧表示され、再編集・再生成・削除ができること
- [ ] VPSで稼働し、Stripe商品が登録されていること

### 品質チェック項目（legalgen）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 7種の文書種別で生成が実行でき、種別ごとに適切な条項構成が出力されること | 機能要件 | 25 |
| 2 | 免責文言が生成文書の冒頭に常に含まれ、ユーザーが削除できない（あるいは再挿入される）こと | 機能要件 | 15 |
| 3 | Word（docx）ダウンロードで日本語が文字化けせず、条項番号付き体裁が整っていること | 機能要件 | 15 |
| 4 | PDF ダウンロードで日本語が正常に表示されること | 機能要件 | 10 |
| 5 | contractツールへの連携ボタンが機能し、テキストが正しく渡されること | 機能要件 | 10 |
| 6 | 未認証/未課金ユーザーのアクセスが拒否されること | セキュリティ | 10 |
| 7 | 生成AIが架空の法的助言（「この契約は有効です」等）を断定的に述べていないこと | 情報の正確性 | 10 |
| 8 | 既存ツールと一貫したデザイン・ファイル構成であること | 可読性・一貫性 | 5 |
| **合計** | | | **100** |

---

## 全工程共通: デプロイ完了条件

各工程の本番稼働には以下が全て満たされていること:

- [ ] `app/main.py` にルーターがインポート・登録されていること
- [ ] `ToolDefinition` シードデータに新ツールが追加されていること（display_order連番）
- [ ] Alembicマイグレーションファイルが作成され、本番DBに適用されていること
- [ ] Stripe本番環境に商品（Product）と月額100円のPrice（recurring/month）が作成されていること
- [ ] ConoHa VPSで `docker-compose up --build -d` が成功していること
- [ ] 本番URLで `/tools/{slug}/` にアクセスし、ログイン後にページが正常表示されること

---

## 備考

### 依存パッケージ（追加が必要なもの）
```
pandas>=2.2          # dataclean
openpyxl>=3.1        # dataclean（Excel読み書き）
rembg>=2.0           # imgbatch（背景除去）
Pillow>=10.0         # imgbatch（画像処理）
python-docx>=1.1     # legalgen（Word出力）
WeasyPrint>=61       # legalgen（PDF出力）
```
※ これらを `requirements.txt` に追加すること。rembgは初回起動時にu2netモデルをDL（約170MB）するため、Docker build時にプリDLするスクリプトを追加推奨。

### Stripe商品登録方針
- 本番Stripe dashboard または Stripe CLIで手動作成し、IDを `ToolDefinition` シードに記入
- 価格: 100円/月（recurring）、通貨: JPY

### セキュリティ共通事項
- アップロードファイルは `/tmp/` または `uploads/` 配下に保存し、処理完了後24時間以内に削除
- ユーザーのファイルは `user_id` ディレクトリ以下に隔離（他ユーザーのファイルにアクセスできないこと）
- ダウンロードAPIは `require_tool_access` で認証チェック必須
