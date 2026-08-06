# 要件定義書: yntools EPUBバリデーター（KDP出版前チェック）

作成日: 2026-04-29
対象プロジェクト: `yn-tools/`
ツールスラッグ: `epubcheck`
本番URL: `https://tools.ynfactory.online/tools/epubcheck/`

---

## ゴール

yntools の `/tools/epubcheck/` に KDP出版前 EPUB バリデーター（Level 2）を追加し、
課金ユーザーが EPUB ファイルをアップロードするだけで破損・規格違反・KDP特化チェックを即時実行できるようにする。

---

## スコープ

### やること

- `epubcheck` スラッグでの新規ツール実装（バリデーションロジック + ルーター + UI）
- Python 標準ライブラリ（`zipfile`）+ `lxml` による Level 2 バリデーション実装
  - **Level 1（基本）**: ZIP 構造 / mimetype / container.xml / OPF / NAV / 必須メタデータ / 画像参照切れ
  - **Level 2（KDP特化）**: 表紙画像有無+サイズ / 固定レイアウト判定 / フォント埋め込み / ファイルサイズ警告 / 画像枚数 / 文字数概算
- ファイルサイズ上限: 200MB（manga 固定レイアウト EPUB 対応）
- アップロードファイルはメモリ処理後即削除（ディスク保存なし）
- Stripe Product / Price の登録（per_tool 100円/月）
- `stripe_product_ids.json`（テスト）と `stripe_live_product_ids.json`（本番）への Price ID 追記
- `app/main.py` への router インポート + `ToolDefinition` シード追加（display_order=37）
- `app/templates/dashboard.html` のツールカード追加
- `app/templates/landing.html` のツール紹介セクション追加
- `app/templates/base.html` のヘッダーメガメニュー追加（カテゴリ: 制作・コンテンツ系）
- `app/templates/guide/epubcheck.html` の使い方ガイド新規作成
- 本番 VPS（163.44.101.31 / `/opt/yn-tools/`）への `docker compose up -d --build` デプロイ
- 動作確認: vol1 EPUB（197MB）でのバリデーション動作確認

### やらないこと

- Level 3（epubcheck.jar / Java 製公式バリデーター）の統合（次フェーズ）
- バリデーション結果の保存・履歴管理（結果は画面表示のみ）
- ユーザーごとのバリデーション回数制限・課金従量制
- EPUB の自動修復機能
- バリデーション結果の PDF / CSV エクスポート
- 複数ファイルの一括バリデーション
- EPUB2 / EPUB3 変換
- epubcheck.jar との比較・差分表示
- CI/CD パイプラインの変更

---

## 工程一覧

| 工程 | 中間成果物 | 入力 |
|---|---|---|
| 工程1: バリデーションロジック実装 | `app/tools/epubcheck/validator.py` | 本要件定義書 |
| 工程2: ルーター + アップロード UI 実装 | `app/tools/epubcheck/router.py` + `app/templates/tools/epubcheck/index.html` | 工程1の成果物 |
| 工程3: Stripe 登録 + メタデータ JSON 更新 + main.py 更新 | `stripe_*_product_ids.json` 2ファイル + `main.py` 更新 | 工程2の成果物 + Stripe ダッシュボード |
| 工程4: ダッシュボード / ランディング / ヘッダーナビ / 使い方ガイド追加 | 4テンプレート修正完了 | 工程3の成果物 |
| 工程5: 本番 VPS デプロイ + 動作確認 | `https://tools.ynfactory.online/tools/epubcheck/` で動作 | 工程4の成果物 + VPS ssh アクセス |

---

## 工程1: バリデーションロジック実装

### 配置ファイル

```
yn-tools/app/tools/epubcheck/
├── __init__.py     （空ファイル）
└── validator.py    （バリデーション本体）
```

### validator.py の設計

#### 関数シグネチャ

```python
def validate_epub(epub_bytes: bytes) -> dict:
    """
    Returns:
        {
            "summary": {"total": int, "pass": int, "warn": int, "fail": int},
            "file_size_mb": float,
            "checks": [
                {
                    "id": str,           # 例: "zip_structure"
                    "category": str,     # 例: "基本チェック"
                    "label": str,        # 例: "ZIP構造"
                    "status": "pass" | "warn" | "fail",
                    "message": str,
                    "detail": str | None  # 該当ファイル名・数値等
                }
            ]
        }
    """
```

#### チェック項目定義（Level 1 + Level 2）

**カテゴリ: 基本チェック（Level 1）**

| チェック ID | ラベル | Pass 条件 | Fail 条件 |
|---|---|---|---|
| `zip_structure` | ZIP 構造 | zipfile で開ける | 展開不可（破損） |
| `mimetype` | mimetype ファイル | 先頭・無圧縮・`application/epub+zip` | 存在しない / 圧縮あり / 内容不一致 |
| `container_xml` | container.xml | `META-INF/container.xml` が存在し OPF パスを返す | 存在しない / XML パースエラー |
| `opf_valid` | OPF 構造 | container.xml で示した OPF が存在し XML valid | ファイルなし / パースエラー |
| `metadata_title` | dc:title | OPF に `<dc:title>` が存在し空でない | 存在しない / 空文字 |
| `metadata_creator` | dc:creator | OPF に `<dc:creator>` が存在 | 存在しない |
| `metadata_language` | dc:language | OPF に `<dc:language>` が存在 | 存在しない |
| `metadata_identifier` | dc:identifier | OPF に `<dc:identifier>` が存在 | 存在しない |
| `manifest_files` | マニフェスト参照切れ | manifest の全 href が zip 内に存在 | 1件以上の href 切れ（件数を detail に記載） |
| `nav_ncx` | NAV / NCX | EPUB3: nav ドキュメント存在 / EPUB2: NCX 存在 | どちらも存在しない |

**カテゴリ: KDP 特化チェック（Level 2）**

| チェック ID | ラベル | Pass 条件 | Warn 条件 | Fail 条件 |
|---|---|---|---|---|
| `cover_image_exists` | 表紙画像 | manifest に `properties="cover-image"` または `<meta name="cover">` で指定された画像が存在 | — | 表紙画像が指定されていない |
| `cover_image_size` | 表紙サイズ | 最小辺 ≥ 1000px かつ 最大辺 ≤ 10000px | アスペクト比が 1.6:1〜1:1.6 の推奨範囲外 | 最小辺 < 1000px |
| `fixed_layout` | 固定レイアウト判定 | — | `<meta property="rendition:layout">pre-paginated</meta>` が存在する（固定レイアウトを検出・情報提供） | — |
| `font_embedded` | フォント埋め込み | manifest に font MIME（`application/font-woff2`, `application/font-woff`, `application/vnd.ms-opentype`, `font/ttf`, `font/otf` 等）が1件以上存在 | — | フォントが埋め込まれていない（warn 扱いに緩和可） |
| `file_size_warning` | ファイルサイズ | < 200MB | 50MB 以上 200MB 未満（読者の DL 負荷警告） | ≥ 200MB（KDP 制限に迫る） |
| `image_count` | 画像枚数 | — | — | 情報提供のみ（pass 固定、detail に枚数を記載） |
| `text_estimate` | 文字数概算 | — | — | 情報提供のみ（pass 固定、XHTML からテキスト抽出した概算文字数を detail に記載） |

#### セキュリティ対策

- **zipスラム（ZIP爆弾）対策**: 展開前にエントリ数（上限 10,000）と各エントリのサイズ（解凍前ヘッダー値、上限 500MB / エントリ）を確認し、超過時は即時 Fail を返す
- **パスインジェクション対策**: `zipfile.ZipFile` のエントリ名にディレクトリトラバーサル（`../` 等）が含まれる場合は Fail を返す
- **メモリ上限**: `UploadFile.read()` の段階で Python 側の読み込みサイズを確認（FastAPI 設定と二重チェック）
- **例外の完全捕捉**: 予期しない例外は全てキャッチし、ユーザーに Internal Error を返す（スタックトレース非表示）

### 完了条件

- [ ] `validator.py` が存在し、`validate_epub(bytes) -> dict` を単体でインポートできること
- [ ] Level 1 の全 10 チェック項目が実装されていること
- [ ] Level 2 の全 7 チェック項目が実装されていること
- [ ] 正常な EPUB（vol1 の 197MB ファイル）を渡したとき、`summary.fail == 0` であること
- [ ] 壊れた zip（任意バイト列）を渡したとき、`zip_structure` が Fail を返すこと
- [ ] ZIP 爆弾チェック: エントリ数 > 10,000 のとき早期 Fail を返すこと
- [ ] `lxml` のみ（または `zipfile` + `lxml`）で実装されており、`ebooklib` 等の追加依存がないこと
- [ ] `requirements.txt` に `lxml` が追加されていること（未追加の場合のみ）

### 品質チェック項目（工程1）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Level 1 全 10 チェックが正しく実装されているか（正常EPUBでFail 0、破損EPUBで対応チェックがFail） | 機能要件 | 30 |
| 2 | Level 2 全 7 チェックが正しく実装されているか（KDP特化: 表紙サイズ・フォント・サイズ警告等） | 機能要件 | 25 |
| 3 | ZIP爆弾・パスインジェクション・例外の3種セキュリティ対策が実装されているか | セキュリティ | 20 |
| 4 | 戻り値 dict のスキーマが仕様通りか（summary / checks の全フィールドが存在するか） | 機能要件 | 15 |
| 5 | `lxml` のみで依存が完結しており、外部バイナリ（Java 等）を必要としないか | 実現可能性 | 10 |
| 合計 | | | 100 |

---

## 工程2: ルーター + アップロード UI 実装

### 配置ファイル

```
yn-tools/app/tools/epubcheck/
├── __init__.py
├── validator.py          （工程1で作成済み）
└── router.py             （今工程で作成）

yn-tools/app/templates/tools/epubcheck/
└── index.html            （今工程で作成）
```

### router.py の設計

```python
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.auth.dependencies import require_tool_access
from app.users.models import User
from app.tools.epubcheck.validator import validate_epub

router = APIRouter(prefix="/tools/epubcheck", tags=["epubcheck"])
templates = Jinja2Templates(directory="app/templates")

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(require_tool_access("epubcheck"))):
    return templates.TemplateResponse(request, "tools/epubcheck/index.html", {"user": user, "page": "epubcheck"})

@router.post("/validate", response_class=JSONResponse)
async def validate(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_tool_access("epubcheck")),
):
    # サイズチェック・バリデーション実行・即時返却（ファイル保存なし）
    ...
```

- `POST /tools/epubcheck/validate`: ファイルを受け取り `validate_epub()` の結果を JSON で返す
- ファイルは `await file.read()` で bytes として読み込み、ディスクに書かない
- 200MB 超は `413 Request Entity Too Large` を返す

### index.html の設計

- `{% extends "base.html" %}` で既存レイアウトを継承
- 1画面構成:
  1. **ヘッダー**: ツール名 + 使い方ガイドへのリンク
  2. **アップロードエリア**: ドラッグ&ドロップ + クリック。EPUB ファイルのみ受け付ける。クライアント側で 200MB 超を事前チェックしてエラー表示
  3. **チェック開始ボタン**: `fetch()` で `POST /tools/epubcheck/validate` を呼ぶ
  4. **進捗インジケーター**: アップロード中・チェック中を表示
  5. **結果表示エリア**: カテゴリ別（基本チェック / KDP 特化チェック）に各項目を一覧表示
     - Pass: 緑バッジ / Warn: 黄バッジ / Fail: 赤バッジ
     - 全体サマリー（PASS N / WARN N / FAIL N）をヘッダーに表示
     - Fail / Warn 項目に具体的なメッセージと該当ファイル名を表示
  6. **再チェックボタン**: 結果表示後に別ファイルをアップロードできるようにリセット
- JavaScript は Vanilla JS のみ（外部ライブラリ追加なし）
- スタイルは Tailwind CSS（既存ツールと統一）

### 完了条件

- [ ] `GET /tools/epubcheck/` が認証済みユーザーに HTML を返すこと
- [ ] `POST /tools/epubcheck/validate` が EPUB bytes を受け取り JSON を返すこと
- [ ] 200MB 超のファイルを POST したとき 413 エラーが返ること
- [ ] EPUB 以外のファイル（.pdf / .zip 等）を選択したとき、クライアント側でエラーメッセージが表示されること
- [ ] バリデーション結果が Pass / Warn / Fail で色分けされて表示されること
- [ ] 全体サマリー（PASS N / WARN N / FAIL N）が結果上部に表示されること
- [ ] ページがモバイル表示でも崩れないこと（Tailwind レスポンシブ）
- [ ] vol1 EPUB（197MB）を実際にアップロードして結果が表示されること（ローカル動作確認）

### 品質チェック項目（工程2）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | GET / POST の両エンドポイントが仕様通りに動作するか（認証・レスポンス形式） | 機能要件 | 25 |
| 2 | ファイル保存がなく、メモリのみで処理されているか（ディスク書込みのないこと） | セキュリティ | 20 |
| 3 | UI の結果表示が Pass / Warn / Fail で正しく色分けされ、メッセージが読めるか | UI品質 | 20 |
| 4 | 200MB 超・EPUB 以外ファイルのエラーハンドリングが機能するか | エラーハンドリング | 20 |
| 5 | 既存ツール（fileconv / mdviewer 等）と UI スタイルが統一されているか | 既存コードとの一貫性 | 15 |
| 合計 | | | 100 |

---

## 工程3: Stripe 登録 + メタデータ JSON 更新 + main.py 更新

### 実施内容

#### 3-A: Stripe Product / Price 登録

Stripe ダッシュボード（またはCLI）で以下を登録する:

- **テスト環境**（stripe.com テストモード）:
  - Product 名: `EPUBバリデーター`
  - Price: 100円/月（recurring）
  - 取得した `product_id` と `price_id` を `stripe_product_ids.json` に追記

- **本番環境**（stripe.com 本番モード）:
  - 同名で登録
  - 取得した `product_id` と `price_id` を `stripe_live_product_ids.json` に追記

#### 3-B: stripe_product_ids.json への追記

```json
{
  ...（既存エントリ）,
  "epubcheck": {
    "product_id": "prod_XXXXXXXXXXXXXXXX",
    "price_id": "price_XXXXXXXXXXXXXXXX"
  }
}
```

#### 3-C: stripe_live_product_ids.json への追記

同形式で本番の ID を追記。

#### 3-D: main.py の更新

**router インポート追加**（既存の legalgen 行の直後）:
```python
from app.tools.epubcheck.router import router as epubcheck_router
```

**app.include_router 追加**（既存の `legalgen_router` 行の直後）:
```python
app.include_router(epubcheck_router)
```

**ToolDefinition シード追加**（display_order=37）:
```python
ToolDefinition(
    slug="epubcheck",
    name="EPUBバリデーター",
    description="KDP出版前の EPUB 破損・規格違反・表紙・フォントを即時チェック",
    monthly_price=100,
    display_order=37,
    icon_emoji="📚",
    stripe_product_id="prod_XXXXXXXXXXXXXXXX",  # 本番 ID
    stripe_price_id="price_XXXXXXXXXXXXXXXX",   # 本番 Price ID
),
```

### 完了条件

- [ ] `stripe_product_ids.json` に `epubcheck` エントリが追記されていること
- [ ] `stripe_live_product_ids.json` に `epubcheck` エントリが追記されていること
- [ ] `main.py` に router インポートが追加されていること
- [ ] `main.py` に `app.include_router(epubcheck_router)` が追加されていること
- [ ] `main.py` の ToolDefinition リストに `epubcheck`（display_order=37）が追加されていること
- [ ] JSON ファイルの構文エラーがないこと（`python -c "import json; json.load(open(...))"` で確認）

### 品質チェック項目（工程3）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | stripe_product_ids.json と stripe_live_product_ids.json の両方に epubcheck エントリが追加されているか | 機能要件 | 30 |
| 2 | main.py の router インポートと include_router が正しい位置に追加されているか | 機能要件 | 25 |
| 3 | ToolDefinition の全フィールド（slug / name / description / monthly_price / display_order / stripe_*）が正しく設定されているか | 機能要件 | 25 |
| 4 | JSON ファイルの構文が壊れていないか（パース確認） | 品質 | 20 |
| 合計 | | | 100 |

---

## 工程4: ダッシュボード / ランディング / ヘッダーナビ / 使い方ガイド追加

### 修正対象ファイル（4ファイル）

#### 4-A: `app/templates/dashboard.html`

既存ツールカード一覧の末尾に `epubcheck` のカードを追加:

```html
<!-- EPUBバリデーター -->
<a href="/tools/epubcheck/" class="...">
  <span class="text-2xl">📚</span>
  <div>
    <p class="font-medium text-gray-900">EPUBバリデーター</p>
    <p class="text-xs text-gray-500">KDP出版前のEPUB破損・規格違反チェック</p>
  </div>
</a>
```

#### 4-B: `app/templates/landing.html`

ツール紹介セクション（制作・コンテンツ系またはユーティリティ系）に epubcheck を追加する。
既存ツールと同じカードコンポーネントのスタイルを使う。

#### 4-C: `app/templates/base.html`

ヘッダーメガメニューの適切なカテゴリ（「制作・コンテンツ」または「ファイル・変換」）に追加:

```html
<a href="/tools/epubcheck/" class="...">
  <span>📚</span> EPUBバリデーター
</a>
```

#### 4-D: `app/templates/guide/epubcheck.html`

使い方ガイドを新規作成。既存の `guide/mdviewer.html` 等と同スタイル。
記載内容:
1. このツールでできること（KDP出版前チェックの目的）
2. 対応フォーマット（.epub / 上限 200MB）
3. チェック項目の説明（基本チェック / KDP 特化チェック）
4. 結果の読み方（Pass / Warn / Fail の意味）
5. よくある質問（Q: Warn が出た場合はどうすれば？ / Q: Level 3 との違いは？）

### 完了条件

- [ ] `dashboard.html` に epubcheck カードが追加されていること
- [ ] `landing.html` に epubcheck の紹介が追加されていること
- [ ] `base.html` のメガメニューに epubcheck リンクが追加されていること
- [ ] `guide/epubcheck.html` が新規作成されていること
- [ ] ガイドページに「使い方」「チェック項目」「結果の読み方」の3セクションが含まれていること
- [ ] `/guide/epubcheck` にアクセスして 200 OK が返ること（ローカル確認）

### 品質チェック項目（工程4）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 4ファイルすべてに epubcheck の追記・新規作成が完了しているか | 完全性 | 30 |
| 2 | 既存テンプレートの構造・スタイル（Tailwind クラス・コンポーネント）と一貫しているか | 既存コードとの一貫性 | 30 |
| 3 | ガイドページの内容が正確で、ユーザーがチェック結果の意味を理解できる記述になっているか | コンテンツ品質 | 25 |
| 4 | 追記によって既存テンプレートの HTML 構造が壊れていないか（Jinja2 ブロックの閉じ忘れ等） | 品質 | 15 |
| 合計 | | | 100 |

---

## 工程5: 本番 VPS デプロイ + 動作確認

### デプロイ手順

```bash
# 1. git push（ローカルから）
git add yn-tools/
git commit -m "feat: add epubcheck tool (EPUB validator for KDP)"
git push origin master

# 2. VPS にログイン
ssh root@163.44.101.31 -i ~/.ssh/conoha-vps

# 3. 最新コードを pull
cd /opt/yn-tools
git pull origin master

# 4. 必ず --build でリビルド（COPY 焼き込みのため restart だけでは反映されない）
docker compose up -d --build

# 5. ログ確認（起動エラーがないこと）
docker compose logs --tail=50
```

### 動作確認チェックリスト（本番環境）

| # | 確認内容 | 期待結果 |
|---|---|---|
| 1 | `https://tools.ynfactory.online/tools/epubcheck/` にアクセス | ログイン済みユーザーにツール画面が表示される |
| 2 | 未課金ユーザーでアクセス | 課金誘導ページへリダイレクト（既存の `require_tool_access` の動作） |
| 3 | vol1 EPUB（197MB）をアップロード | バリデーション結果が表示される（Fail 0 であること） |
| 4 | 200MB 超のファイルをアップロード（テスト用ダミー） | エラーメッセージが表示される（413 相当） |
| 5 | `.epub` 以外のファイルを選択 | クライアント側でエラーメッセージが表示される |
| 6 | ダッシュボード（`/dashboard`）に epubcheck カードが表示される | カードが存在し `/tools/epubcheck/` にリンクしている |
| 7 | ランディングページに epubcheck の紹介が表示される | 紹介文・アイコンが表示されている |
| 8 | ヘッダーメガメニューに epubcheck が表示される | クリックで `/tools/epubcheck/` に遷移する |
| 9 | `/guide/epubcheck` にアクセス | 使い方ガイドページが表示される |
| 10 | 既存ツール（fileconv 等）が引き続き正常動作する | 既存ツールに影響がないこと |

### テスト用 EPUB

本番 VPS での動作確認には以下のファイルを使用する:

```
ローカルパス:
03_成果物/outputs/ebooks-manga/manga-career-restart/vol1/KDP出版用/
manga-career-restart-vol1-manga_text1_5x_v3.epub
（197MB / 固定レイアウト / 画像多数 / フォント埋め込みあり）
```

このファイルを使って以下を確認する:
- 197MB のファイルが 200MB 制限以内で処理されること
- 固定レイアウト（`rendition:layout`）が Warn として検出されること
- フォント埋め込みが Pass になること
- 画像枚数・文字数概算が detail に表示されること
- 処理が 30 秒以内に完了すること（タイムアウトなし）

### 完了条件

- [ ] `docker compose up -d --build` がエラーなく完了すること
- [ ] `docker compose logs` にエラーが出力されていないこと
- [ ] 本番 URL（`https://tools.ynfactory.online/tools/epubcheck/`）が 200 OK を返すこと
- [ ] vol1 EPUB（197MB）のバリデーションが完了し、結果が画面に表示されること
- [ ] 既存ツールが影響を受けていないこと（fileconv / mdviewer 等で動作確認）
- [ ] ダッシュボード / ランディング / ヘッダーメガメニューに epubcheck が表示されていること

### 品質チェック項目（工程5）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 本番 URL でツールが課金ユーザー向けに正常動作するか（vol1 EPUBでバリデーション完了） | 機能要件 | 35 |
| 2 | 動作確認チェックリスト 10 項目すべてが合格しているか | 機能要件 | 30 |
| 3 | 既存ツールへの影響がないこと（fileconv / mdviewer 等で動作確認済みか） | 既存コードとの一貫性 | 20 |
| 4 | docker compose logs にエラーが出ていないか | 品質 | 15 |
| 合計 | | | 100 |

---

## リスクとブロッカー

### R1: メモリ枯渇（200MB × 同時複数ユーザー）

- **リスク**: 複数ユーザーが同時に 200MB EPUB をアップロードした場合、Docker コンテナのメモリが枯渇する
- **軽減策**:
  - `POST /tools/epubcheck/validate` の処理は同期的に実行し、`validate_epub()` 完了後に bytes を即時解放する（GC に依存）
  - `ulimit` / Docker の `memory` 設定で上限を設ける（既存設定を確認）
  - MVP フェーズでは同時アクセス数が少ないため許容。スケール時に非同期キューを検討
- **対応基準**: ローカル動作確認で 197MB EPUB を 2 回連続送信してもエラーが出ないこと

### R2: 悪意ある EPUB（ZIP スラム攻撃・パスインジェクション）

- **リスク**: 意図的に作成した ZIP（展開サイズ >>> 実ファイルサイズ）や `../` を含むエントリ名でサーバーへの攻撃
- **軽減策（工程1で実装）**:
  - エントリ数上限: 10,000 件超は早期 Fail
  - 各エントリの圧縮前サイズ（ヘッダー値）上限: 500MB / エントリ
  - エントリ名の `../` チェック
  - `zipfile.ZipFile` でのみ処理し、ファイルシステムに展開しない

### R3: Stripe Price ID 登録ミス

- **リスク**: テスト環境と本番環境の Price ID を取り違えると課金が機能しない
- **軽減策**:
  - `stripe_product_ids.json`（テスト）と `stripe_live_product_ids.json`（本番）を別ファイルで明確分離（既存設計）
  - 登録後に Stripe ダッシュボードで Price ID の通貨・金額・インターバルを目視確認してから JSON に記載
  - 工程3 の完了条件に「Stripe ダッシュボードで確認済み」を追加

### R4: lxml の Docker イメージへの未インストール

- **リスク**: `requirements.txt` に `lxml` が未記載の場合、コンテナ内でインポートエラー
- **軽減策**:
  - 工程1 の完了条件に `requirements.txt` 確認を含める
  - `docker compose up -d --build` 後のログで `ImportError` がないことを確認

### R5: 197MB ファイルのアップロードタイムアウト

- **リスク**: FastAPI / nginx のデフォルトタイムアウトが 197MB アップロードを拒否する可能性
- **軽減策**:
  - FastAPI の `max_upload_size` 設定を確認・調整
  - nginx のアップロード設定（`client_max_body_size`）が 200MB 以上に設定されているか確認
  - 動作確認（工程5）で実際に 197MB ファイルを送信して検証

---

## デプロイ手順（詳細）

### 前提

- VPS: ConoHa VPS / IP: 163.44.101.31
- SSH キー: `~/.ssh/conoha-vps`
- 作業ディレクトリ: `/opt/yn-tools/`
- Docker Compose: `docker compose`（v2 系）

### 手順

```bash
# [ローカル] 変更をコミット・プッシュ
cd G:/マイドライブ/YNFactory-cc
git add yn-tools/
git commit -m "feat: add epubcheck tool (EPUB validator for KDP, Level 2)"
git push origin master

# [VPS] SSH ログイン
ssh root@163.44.101.31 -i ~/.ssh/conoha-vps

# [VPS] 最新コード取得
cd /opt/yn-tools
git pull origin master

# [VPS] リビルド（--build 必須）
docker compose up -d --build

# [VPS] 起動確認
docker compose ps
docker compose logs --tail=100 | grep -E "ERROR|WARNING|epubcheck"

# [VPS] nginx の client_max_body_size 確認（必要に応じて設定変更）
# → docker compose の nginx サービス設定ファイルを確認

# [ローカル] ブラウザで確認
# https://tools.ynfactory.online/tools/epubcheck/
```

### ロールバック手順

デプロイ後に重大な問題が発生した場合:

```bash
# [VPS] 直前のイメージに戻す
cd /opt/yn-tools
git log --oneline -5  # コミット確認
git revert HEAD       # または git reset --hard <前のコミットハッシュ>
docker compose up -d --build
```

---

## 備考

### ツールスラッグの選定理由

`epubcheck`（候補1）を採用する。
`epubvalidator`（候補2）より短く、EPUB 業界では `epubcheck` が事実上の標準用語（W3C/DAISY の公式ツール名）であり、ユーザーに直感的。

### Level 3（epubcheck.jar）について

W3C 公式の `epubcheck.jar`（Java製）は最も厳密なバリデーターだが、以下の理由で次フェーズとする:
- Docker イメージに JRE を追加する必要がある（イメージサイズ増加）
- 実行がファイルI/O ベースのため、メモリ上処理との統合が複雑
- MVP で Level 2（Python 実装）で KDP 前チェックとして十分な実用価値がある

### 既存 manga EPUBとの整合

`manga-career-restart-vol1-manga_text1_5x_v3.epub`（197MB）は本ツールの最重要テストケース。
固定レイアウト・多数画像・フォント埋め込みを含む実運用ファイルであり、Level 2 全チェックの動作確認に最適。

### 各工程のループ上限

各工程は実行→品質チェック（85点以上で合格）のループを **最大5回** まで繰り返す。
5回を超えてもパスしない場合はオーナーに相談する。
