---
name: ebook-from-theme
description: テーマ入力だけでゼロから電子書籍本文を制作するフロントオーケストレーター。5層Webリサーチ→指定文字数（15,000/25,000/35,000字）の原稿（画像タグ付き）→挿絵をcodeximageキュー方式でCodexに委任→ebook-to-mangaが期待するproject.md＋manuscript/形式へ橋渡しするまでを一気通貫で実行する。
allowed-tools: Read, Write, Edit, Bash, Glob, WebSearch, WebFetch
---

# ebook-from-theme: テーマ起点電子書籍制作オーケストレーター

テーマを受け取り、Phase 0〜4 の順に実行して `.company/outputs/ebooks/{slug}/` に成果物を生成し、最後に `ebook-to-manga` スキルへの引き渡し案内を出力する。

---

## Phase 0: 制作開始前の5項目一括質問

スキル起動直後、リサーチや原稿作成を始める前に、以下の5項目をまとめて提示してユーザーの回答を待つ。

```text
電子書籍と漫画を作成する前に、以下の5項目を選択してください。

項目1
テーマ
A. 依頼文のテーマで進める（推奨）
B. 依頼文のテーマを少し広げて進める
C. 依頼文のテーマを絞り込んで進める
D. 別テーマを指定する

項目2
カラーモード
A. フルカラー（推奨）
B. 白黒

項目3
キャラクター設定
A. 全部お任せ（推奨）
B. 主人公だけ自分で用意
C. 全員自分で用意

項目4
1章あたりの漫画ページ数
A. 4ページ（推奨）
B. 3ページ
C. 5ページ

項目5
漫画の配置位置
A. 章末（推奨）
B. 章頭

項目6
本文の文字数
A. 25,000字（推奨）
B. 15,000字
C. 35,000字

回答例:
1A、2A、3A、4A、5A、6A
```

**回答処理ルール:**
- 未回答の項目のみ短く再質問する。
- ユーザーが「お任せ」「推奨で」「デフォルトで」と回答した場合は以下の推奨値を使う:
  - カラーモード: フルカラー
  - キャラクター設定: 全部お任せ
  - 1章あたりの漫画ページ数: 4ページ
  - 漫画の配置位置: 章末
  - 本文の文字数: 25,000字
- 選択値を変数として記録し、Phase 4 の `ebook-to-manga` 引き渡し案内に引き継ぐ。

---

## Phase 1: 5層リサーチ

Phase 0 の確定テーマでリサーチを実行し、以下2ファイルを出力する。

**出力パス:**
- `.company/outputs/ebooks/{slug}/_research/research.md`
- `.company/outputs/ebooks/{slug}/_research/meta.json`

### Step 1-0: slug 生成とディレクトリ作成

テーマから slug を生成する（例: 「言語化力」→ `gengo-ryoku`、「AI活用術」→ `ai-katsuyo`）。

```bash
mkdir -p ".company/outputs/ebooks/{slug}/_research"
mkdir -p ".company/outputs/ebooks/{slug}/_images_source/images"
mkdir -p ".company/outputs/ebooks/{slug}/manuscript"
```

### Step 1-1: 5層リサーチ（全層実行）

| Layer | 対象 | クエリ例 |
|-------|------|---------|
| 1 | YouTube専門家・解説動画 | `{テーマ} 解説 コツ site:youtube.com` |
| 2 | note専門家記事 | `{テーマ} note.com` |
| 3 | SNS/Xトレンド | `{テーマ} Twitter OR X 話題` |
| 4 | 市場・競合書籍 | `{テーマ} 本 おすすめ Amazon` |
| 5 | 読者の悩み・ニーズ | `{テーマ} できない 悩み 初心者` |

各層で WebSearch → 上位3件を WebFetch で詳細取得する。

### Step 1-2: research.md 生成

```markdown
# リサーチ結果: {テーマ}

## メタ情報
- テーマ: {テーマ}
- サブタイトル: {サブタイトル}
- 想定読者: {想定読者}
- 生成日: {日付}

## Layer 1: YouTube専門家の知見
...

## Layer 2: note記事の知見
...

## Layer 3: SNSトレンド
...

## Layer 4: 市場・競合分析
...

## Layer 5: 読者の悩み・ニーズ
...

## 総合まとめ
### 読者が本当に求めていること
### 差別化ポイント
### 重要キーワード
```

### Step 1-3: meta.json 生成

```json
{
  "slug": "{slug}",
  "title": "{タイトル}",
  "subtitle": "{サブタイトル}",
  "target_reader": "{想定読者}",
  "key_points": ["{ポイント1}", "{ポイント2}", "{ポイント3}"],
  "color_theme": {
    "primary": "#2D5BE3",
    "accent": "#FF8C42",
    "sub": "#00B4D8"
  }
}
```

`color_theme` はテーマの雰囲気・Phase 0 カラーモード選択に合わせて自動設定する。白黒選択時は `primary: "#333333"`, `accent: "#666666"`, `sub: "#999999"` を基本値とする。

---

## Phase 2: 原稿執筆（指定文字数・画像タグ付き）

**入力:** `_research/research.md`、`_research/meta.json`、Phase 0 項目6で選択した本文文字数

**出力パス:**
- `.company/outputs/ebooks/{slug}/_images_source/manuscript_raw.md`

### Step 2-1: 構成設計（目次自動生成）

Phase 0 項目6で選択した文字数に応じて、リサーチ結果から目次を生成する（いずれも全5章構成）:

| 選択文字数 | はじめに | 各章（×5章） | おわりに | 合計目安 |
|-----------|---------|------------|---------|---------|
| 15,000字 | 800〜1,000字 | 2,400〜2,800字 | 800〜1,000字 | 約15,000字 |
| 25,000字（推奨） | 1,200〜1,500字 | 4,000〜5,000字 | 1,200〜1,500字 | 約25,000字 |
| 35,000字 | 1,500〜2,000字 | 5,600〜6,400字 | 1,500〜2,000字 | 約35,000字 |

### Step 2-2: 原稿執筆ルール

- 文体: です・ます調で統一
- 1セクション（`###`）ごとに最低1枚の画像タグを挿入
- 章冒頭には必ず `HEADER_IMAGE` 画像タグを挿入
- 表・コードブロック・ASCII図は禁止（図解は画像タグで表現）
- 各章・節の前に `\newpage` を挿入

### Step 2-3: 画像タグ挿入形式

**章ヘッダー（各章冒頭）:**
```
<!-- [HEADER_IMAGE: pattern=illustration | title={章タイトル} | elements={主要トピック} | description={補足}] -->
```

**本文中図解（###ごと）:**
```
<!-- [INLINE_IMAGE: pattern={パターン名} | title={図解タイトル} | elements={要素1,要素2,...} | description={補足}] -->
```

**図解パターン（26種類）:**

| カテゴリ | パターン |
|---------|---------|
| 構造・分類 | tree, pyramid, layers, honeycomb, group |
| 流れ・変化 | flow-horizontal, flow-vertical, cycle, stairs, gantt |
| 比較・分析 | before-after, matrix, comparison-table, scale-circles, concentric, venn |
| 関係・論理 | network, radial, triangle, formula, map |
| 簡易・リスト | list-vertical, list-horizontal, list-dense |
| 特別 | illustration |

**完了条件:** 総文字数が Phase 0 で選択した文字数（±10%）。画像タグは文字数に比例した枚数（15,000字→18枚以上 / 25,000字→30枚以上 / 35,000字→42枚以上）。

---

## Phase 3: 挿絵生成（codeximageキュー方式）

**重要: 画像生成はAPI直叩きせず、必ず codeximageキュー方式で Codex に委任する。**

### Step 3-1: 画像タグ抽出とプロンプト変換

`manuscript_raw.md` から全画像タグを抽出し、以下のルールで生成プロンプトに変換する。

#### 共通スタイル指示（全画像に適用）

```
Clean flat design infographic, soft pastel colors, rounded shapes,
modern Japanese ebook illustration aesthetic.
Color palette: primary {meta.jsonのprimary}, accent {accent}, sub {sub}.
Background: white. {向き}.
All text in the image must be in Japanese (日本語).
Kindle電子書籍本文用。実在企業ロゴ・商標ロゴ禁止。日本語テキストは大きく短く読みやすく。PNGとして保存。
```

#### HEADER_IMAGE → 章ヘッダー横長（3:2 = 1536x1024px）

```
Chapter header illustration for Japanese ebook.
Large text reads "{章タイトル}" in bold Japanese.
VISUAL: {elements と description から構成}
STYLE: Flat design, chapter header, landscape (3:2 ratio, 1536x1024px).
```

#### INLINE_IMAGE → パターン別変換

**サイズ選択ロジック:**
- デフォルト: 横長 3:2（1536x1024）
- 正方形（1024x1024）: list-vertical / pyramid / radial で要素が見やすい場合
- 縦長（1024x1536）: layers / list-vertical で要素数が多い場合

**★ 重要: 日本語テキストは絶対に英語に翻訳しない**
- `elements` 内の日本語 → `text reads "日本語のまま"` の形式で埋め込む
- title も `Title text reads "日本語タイトル"` で指定

| パターン | プロンプト構造 |
|---------|--------------|
| before-after | Left panel "Before" with text reads "{要素1}", right panel "After" with text reads "{要素2}" |
| flow-horizontal | Horizontal flow diagram with arrows: text reads "{要素1}" → text reads "{要素2}" → ... |
| stairs | Step-by-step staircase diagram, each step text reads "{要素N}" |
| radial | Central circle text reads "{タイトル}", surrounding nodes each text reads "{要素N}" |
| comparison-table | Card comparison layout, headers text reads "{要素1}" vs text reads "{要素2}" |
| cycle | Circular cycle diagram with nodes text reads "{要素N}" |
| pyramid | Triangle pyramid, top text reads "{要素1}", middle "{要素2}", base "{要素3}" |
| list-vertical | Vertical checklist, each item text reads "{要素N}" |
| tree | Tree/hierarchy diagram, root text reads "{タイトル}", branches text reads "{要素N}" |
| layers | Layered stack diagram, each layer text reads "{要素N}" |
| illustration | Flat illustration depicting: {description} |
| その他 | パターン名に応じた構図。タイトル・要素は text reads "日本語" 形式で指定 |

### Step 3-2: ジョブフォルダ作成

現在日付を確認し、以下のパスにジョブフォルダを作成する:

```
.company/codex/queue/{slug}-ebook-images_{YYYYMMDD}_{連番}/
├── manifest.json
├── TASK.md
└── START_HERE.md
```

**連番ルール:** `01` から始め、同日に複数ジョブがあれば `02`, `03` と増やす。

#### manifest.json の形式（items配列型）

**この manifest は chatgpt55-ebook-diagrams 実例の items 配列型に準拠する。** `prompt_file`（別txtファイル参照方式）は使わない。`prompt` を各 item に直接埋め込む方式を採用する。`common_requirements` は chatgpt55 型には存在しないため使わない（共通要件は TASK.md の完了条件に記載する）。

```json
{
  "job_id": "{slug}-ebook-images_{YYYYMMDD}_{連番}",
  "created_at": "{ISO8601日時}",
  "generation_mode": "chatgpt_plus_image_generation_manual_codex",
  "book_title": "{meta.jsonのtitle}",
  "source_image_plan": ".company/outputs/ebooks/{slug}/_images_source/manuscript_raw.md",
  "final_image_dir": ".company/outputs/ebooks/{slug}/_images_source/images",
  "aspect_ratio": "3:2",
  "expected_count": {画像タグ総数},
  "items": [
    {
      "id": "{filename_stem}",
      "type": "diagram|illustration|header",
      "filename": "{filename}.png",
      "prompt": "{変換済みプロンプト（日本語テキストは text reads 形式）。Kindle電子書籍本文用。実在企業ロゴ・商標ロゴ禁止。日本語テキストは大きく短く読みやすく。PNGとして保存。}",
      "insert_file": "{挿入先章ファイル名（例: 00_はじめに.md）}",
      "purpose": "{この画像が果たす役割}",
      "description": "{画像タグのdescriptionを日本語で}",
      "target_output": ".company/outputs/ebooks/{slug}/_images_source/images/{filename}.png",
      "done_output": ".company/codex/done/{job_id}/pages/{filename}.png"
    }
  ],
  "quality_checks": [
    "全{N}ファイルがPNGとして保存されている",
    "ファイル名がitems配列と完全一致している",
    "画像内の日本語テキストが破綻していない",
    "実在ロゴや商標が含まれていない",
    "電子書籍本文として違和感のないシンプルな図解・挿絵になっている"
  ]
}
```

#### TASK.md の形式

実例ジョブ `chatgpt55-ebook-diagrams_20260504_2237` の形式に準拠する:

```markdown
# {title} 本文挿絵生成ジョブ

## ゴール

Codex経由の画像生成を使い、電子書籍 `{title}` の本文用画像{N}点を作成する。

## スコープ

- 生成対象: `manifest.json` の `items` {N}件
- 画像形式: PNG
- 画像比率: 横長3:2 基本（パターンにより正方形・縦長あり）
- 出力先:
  - 一時完了: `.company/codex/done/{job_id}/pages/`
  - 最終配置: `.company/outputs/ebooks/{slug}/_images_source/images/`
- API・NanoBanana・Gemini画像生成は使わない

## 完了条件

- `manifest.json` の `items` 全{N}点が生成されている
- ファイル名が本文Markdownの画像タグ参照名と一致している
- 日本語テキストが大きく読みやすい
- 実在企業ロゴを含まない
- 電子書籍本文に入れても違和感のないシンプルな図解・挿絵になっている
- `progress.json`、`report.md`、`DONE.txt` を done フォルダに作成する

## 品質基準

85点以上で合格。

採点観点:
- ファイル名一致: 20点
- 本文内容との対応: 20点
- 視認性・読みやすさ: 20点
- 日本語安全表現: 20点
- 電子書籍内での統一感: 20点
```

#### START_HERE.md の形式

実例ジョブ `somatid-ebook-images_20260504_01` の形式に準拠する:

```markdown
# START HERE

このジョブは、Codex経由の画像生成で電子書籍本文用画像{N}点を作成するためのハンドオフです。

## 目的

`{title}` の本文内に差し込む図解・挿絵を、APIキーを使わず Codex 経由で生成します。

## 入力

- `manifest.json`: {N}点分の生成指示（プロンプト・ファイル名・出力先を含む）

## 出力先（done_output）

生成したPNGは manifest.json の各 item の `done_output` に記載されたパスへ保存してください。

**Windowsフルパス（実行時にプロジェクトの絶対パスを記入すること）:**
`{Windowsフルパス}\.company\codex\done\{job_id}\pages\`

## 作業順

1. `manifest.json` を開き `items` を上から順に読む
2. 各 item の `prompt` を使って画像を1点ずつ生成する
3. `done_output` に記載されたファイル名でPNG保存する
4. 全{N}点が揃ったら品質チェックする（`quality_checks` 参照）
5. `report.md` と `DONE.txt` と `progress.json` をこのdoneフォルダに作成する

## 注意

- NanoBanana/Gemini/APIは使用しない
- 実在企業ロゴは入れない
- 日本語文字は短く、大きく、読みやすくする
- 画像内の細かい長文は避ける
- 日本語が崩れる場合は文字量を減らしてアイコン・線・カード配置で表現する
```

### Step 3-3: Codex 実行の依頼とウェイト

ジョブフォルダ作成後、以下のメッセージでユーザーに Codex 実行を依頼し、完了通知を待つ:

```
.company/codex/queue/{job_id}/ を配置しました。

別セッション（Codex/ChatGPT）で以下を実行してください:
1. .company/codex/queue/{job_id}/START_HERE.md を開く
2. manifest.json の items を順に処理して画像を生成する
3. 完了後「Codex完了しました」と教えてください

生成画像の保存先: .company/codex/done/{job_id}/pages/
```

**ここで一時停止する。「Codex完了しました」通知を受けるまで Phase 3 後続処理に進まない。**

### Step 3-4: 完了後の画像受け取り

「Codex完了しました」通知を受けたら:

1. `.company/codex/done/{job_id}/pages/` の PNG を確認する
2. 全点が揃っていれば `.company/outputs/ebooks/{slug}/_images_source/images/` にコピーする:
   ```bash
   cp ".company/codex/done/{job_id}/pages/"*.png ".company/outputs/ebooks/{slug}/_images_source/images/"
   ```
3. `progress.json` を確認し、`needs_manual_review_pages` があれば日本語が崩れているページをユーザーに報告する

### Step 3-5: manuscript.md 生成

`manuscript_raw.md` の画像タグを実画像リンクに置換して `manuscript.md` を生成する:

```
<!-- [HEADER_IMAGE: ...] --> → ![{章タイトル}](images/{filename}.png)
<!-- [INLINE_IMAGE: ...] --> → ![{図解タイトル}](images/{filename}.png)
```

**出力パス:** `.company/outputs/ebooks/{slug}/_images_source/manuscript.md`

---

## Phase 4: ebook-to-manga へのブリッジ

`meta.json` + `manuscript.md` を `ebook-to-manga` スキルが期待する入力形式に変換する。

**出力パス:**
- `.company/outputs/ebooks/{slug}/project.md`
- `.company/outputs/ebooks/{slug}/manuscript/` 配下に章別 .md ファイル

### Step 4-1: project.md 生成

`ebook-to-manga` の Step 1（ソース分析）が読み込む形式に準拠:

```markdown
# 電子書籍プロジェクト

## テーマ
{meta.jsonのtitle}が示すテーマの概要

## ターゲット
{meta.jsonのtarget_reader}

## タイトル・サブタイトル・著者名
タイトル: {meta.jsonのtitle}
サブタイトル: {meta.jsonのsubtitle}
著者名: {テーマ・内容・読者層に合った著者名（ペンネーム）を自動生成。ユーザーが著者名を指定した場合のみその値を使う}

## 章立て

はじめに
{はじめにの概要（1〜2文）}

第1章：{第1章タイトル}
{第1章の概要（1〜2文）}

第2章：{第2章タイトル}
{第2章の概要（1〜2文）}

第3章：{第3章タイトル}
{第3章の概要（1〜2文）}

第4章：{第4章タイトル}
{第4章の概要（1〜2文）}

第5章：{第5章タイトル}
{第5章の概要（1〜2文）}

おわりに
{おわりにの概要（1〜2文）}
```

**著者名は固定しない（お任せ）。テーマ・読者層に合うペンネームを自動生成する。ユーザーが著者名を明示指定した場合のみその値を使う。**

### Step 4-2: manuscript/ フォルダに章別 .md を生成

`manuscript.md` をファイル名順に読まれる形式で章別に分割して保存する。ファイル名は `ebook-to-manga` の Step 1 で読み込まれる順序を保証するため、ゼロ埋め連番プレフィックスを付ける:

```
.company/outputs/ebooks/{slug}/manuscript/
├── 00-はじめに.md
├── 第1章_{タイトル}.md
├── 第2章_{タイトル}.md
├── 第3章_{タイトル}.md
├── 第4章_{タイトル}.md
├── 第5章_{タイトル}.md
└── 06-おわりに.md
```

**注記:** ebook-to-manga Step 1 はファイル名順（辞書順）に原稿を読み込む。実例 `01-worker-positive` と同一の命名規則（`00-はじめに` / `第N章_タイトル` / `06-おわりに`）に揃えれば既存運用と一致する。

各ファイルの内容は `manuscript.md` から該当章を抜き出したもの（画像リンク含む）。

### Step 4-3: 引き渡し案内の出力

ブリッジ完了後、以下の情報を含む引き渡し案内を出力する:

```
ebook-to-manga でマンガ化できる状態になりました。

【ソースフォルダ】
.company/outputs/ebooks/{slug}/

【ebook-to-manga 起動時の引数情報】
- ソースフォルダ: .company/outputs/ebooks/{slug}/
- 目標ページ数: {Phase0選択章数} × {Phase0選択ページ数/章} = {合計}ページ
- カラーモード: {Phase0で選択した値（フルカラー/白黒）}
- キャラクター設定: {Phase0で選択した値}
- 漫画の配置位置: {Phase0で選択した値（章末/章頭）}
- ジャンル指定: 未指定（自動判定）

次のステップ:
/ebook-to-manga を起動し、ソースフォルダとして上記パスを指定してください。
```

自動連鎖はしない。手動でユーザーが `ebook-to-manga` を起動する。

---

## 実行フロー早見表

```
Phase 0: 5項目一括質問 → 回答待ち
    ↓ 回答確定
Phase 1: 5層リサーチ → research.md + meta.json
    ↓
Phase 2: 原稿執筆 → manuscript_raw.md（Phase0選択文字数・画像タグは文字数に比例）
    ↓
Phase 3-1〜2: 画像タグ→プロンプト変換 → ジョブフォルダ作成（manifest.json/TASK.md/START_HERE.md）
    ↓
Phase 3-3: ユーザーに Codex 実行依頼 → 完了通知待ち
    ↓ 「Codex完了しました」
Phase 3-4〜5: 画像コピー → manuscript.md 生成
    ↓
Phase 4-1〜2: project.md + manuscript/章別.md 生成
    ↓
Phase 4-3: ebook-to-manga 引き渡し案内を出力
```

---

## 制約（厳守）

- インラインAPI直叩き（`client.images.generate` 等）を一切記述・実行しない
- 著者名は固定しない。お任せ（自動生成）を既定とし、ユーザー指定があればそれを優先する
- `HANDOFF_MODE=codex-handoff` や `.company/handoff/codex-image-gen/_spec/SPEC.md` は実在しないため参照・依存しない
- `ebook-to-manga` skill.md は変更しない
- ターミナルへの大量出力禁止（CLAUDE.md ターミナル出力制限準拠）
