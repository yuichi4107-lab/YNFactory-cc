---
name: kdp-cover-and-metadata
description: KDP出版用の表紙画像（gpt-image-2 / 1024x1536 PNG + JPEG）と、KDPアップロード時に必要な3点メタデータ（書籍情報.md / ジャンル・キーワード.md / 書籍紹介文_HTML.html）を生成するポータブルスキル。ebook-to-manga スキルから Step 6（表紙）と Step 8（メタデータ）だけを抽出した独立版。
---

# KDP Cover & Metadata Generator

KDP（Kindle Direct Publishing）出版に必要な「表紙画像」と「3点メタデータ」だけをまとめて生成するスキル。
複数PCで使い回せるように、このフォルダ単体で完結する構成。

---

## このスキルでできること

1. **表紙画像の生成**（OpenAI gpt-image-2、`images.edit` API、2:3 縦長 1024x1536 PNG + JPEG）
   - キャラクターのリファレンス画像（PNG）を渡してマンガ調表紙を生成
   - PNG 直保存（マスター画像）
   - KDP申請用に同寸法の JPEG 版 `cover.jpg` も必ず保存
2. **KDPメタデータの生成**
   - `書籍情報.md`（タイトル / サブタイトル / 著者名 / 出版社名、各カナ・ローマ字付き）
   - `ジャンル・キーワード.md`（メインジャンル＋サブジャンル、7枠×3ワード=21キーワード）
   - `書籍紹介文_HTML.html`（KDP商品説明欄に貼り付け可能なHTML、7セクション固定構成）

---

## 前提条件

- Python 3.x（`python` コマンドで起動できること）
- `pip install openai`（`openai` パッケージ）
- 環境変数 `OPENAI_API_KEY` が設定されていること
- 表紙生成にはキャラクターのリファレンス画像（PNG）が1枚以上必要

### 他のPCでセットアップする手順

1. このフォルダ（`kdp-cover-and-metadata/`）を丸ごとコピー
   - 推奨配置: `<任意プロジェクト>/.claude/skills/kdp-cover-and-metadata/`
   - Claude Code以外のClaude（API直接利用やCodex等）でも `SKILL.md` を読み込ませれば動作する
2. `pip install openai` を実行
3. `OPENAI_API_KEY` を環境変数に設定
   - Windows: `setx OPENAI_API_KEY sk-...`
   - macOS/Linux: `export OPENAI_API_KEY=sk-...`（`~/.zshrc` や `~/.bashrc` に追記）
4. `scripts/generate_cover.py` の使い方は下記「使い方」を参照

---

## 使い方

### A. 表紙画像の生成

```bash
python scripts/generate_cover.py \
  --prompt-file path/to/cover_prompt.txt \
  --char-refs path/to/chara_main.png path/to/chara_sub.png \
  --out path/to/KDP出版用/cover.png
```

生成後、同じフォルダに JPEG 版も保存する。

```bash
sips -s format jpeg -s formatOptions 95 path/to/KDP出版用/cover.png --out path/to/KDP出版用/cover.jpg
```

macOS以外では、Pillow等で `cover.png` を RGB JPEG に変換し、寸法 1024x1536 を維持して `cover.jpg` として保存する。

オプション:

| 引数 | 必須 | 説明 |
|---|---|---|
| `--prompt-file` | ◯ | 表紙プロンプトのテキストファイル（UTF-8） |
| `--char-refs` | ◯ | キャラクターリファレンスPNGの一覧（1枚以上、複数可）|
| `--out` | ◯ | 出力先パス（拡張子は `.png`）|
| `--size` | ✗ | デフォルト `1024x1536`（2:3 縦長）|
| `--quality` | ✗ | デフォルト `high`（`low`/`medium`/`high`/`auto`）|

プロンプトの書き方は「表紙プロンプト構成」のセクションを参照。

### B. メタデータ3点の生成

`templates/` フォルダの3ファイルをコピーし、{{...}} プレースホルダを埋めるだけ。

```bash
# プロジェクトの KDP出版用 フォルダにコピー
cp templates/書籍情報.md            "<book>/KDP出版用/書籍情報.md"
cp templates/ジャンル・キーワード.md   "<book>/KDP出版用/ジャンル・キーワード.md"
cp templates/書籍紹介文_HTML.html    "<book>/KDP出版用/書籍紹介文_HTML.html"
```

各ファイルの先頭にコメントで埋め方が書いてある。

---

## 表紙プロンプト構成

`表紙プロンプト.md` の5ステップ構造をベースにする。`--prompt-file` に渡すテキストファイルは、以下のYAML風構造で書くのが推奨（自然文でも可）。

```yaml
request_type: generate_hyper_detailed_magazine_cover_with_fixed_aspect_ratio
title: "{タイトル}"
subtitle: "{サブタイトル}"
author: "{著者名}"

description: >
  添付された原稿ドキュメントファイルを分析して抽出したテキスト要素を使用して、
  圧倒的な情報量と高いデザイン密度を備えたプロ仕様の「マンガ書籍カバー」を生成する。

design_taste: >
  マンガ・コミック風の書籍カバーデザイン。
  {ジャンルに応じた色調・演出を反映}
  キャラクターを全面に配置し、マンガらしい躍動感を演出。

character: >
  {主要キャラクター2-3名の外見設定}
  キャラクター同士の関係性が伝わるポーズ・配置。

processing_steps:
  - step 1: 原稿分析とテキスト要素抽出
  - step 2: デザインムードと構図の決定
  - step 3: キャラクター配置と背景の生成（2:3アスペクト比）
  - step 4: テキストと装飾要素のレイアウト
  - step 5: キャラクター・背景とテキスト・装飾の統合

constraints:
  - 必ず日本のアニメ・マンガ調イラストで描くこと
  - 実写風・フォトリアル風は禁止
  - 文字は日本語で正確に表記すること
  - アスペクト比は厳密に 2:3（1024x1536）
```

### 絶対ルール

- **画風**: プロンプト冒頭に必ず「◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。」を含める
- **保存**: `cover.png` をマスターとして保存し、同寸法の `cover.jpg` も必ず保存する
- **サイズ**: `1024x1536`（2:3 縦長）固定

---

## メタデータ仕様

### 書籍情報.md

タイトル / サブタイトル / 著者名 / 出版社名の4項目を、それぞれ「日本語・フリガナ（カタカナ）・ローマ字」の3形式で記載する。
KDP登録フォームでこの3形式が必要になる。

出版社名のデフォルトは **YN出版**（フリガナ: ワイエヌシュッパン、ローマ字: YN Shuppan）。

### ジャンル・キーワード.md

- **メインジャンル**: KDPのカテゴリ階層から1つ
- **サブジャンル**: 関連カテゴリ
- **キーワード**: KDPは検索キーワード枠が **7枠**。各枠に **3ワード程度** をスペース区切りでまとめると合計21ワード前後で運用しやすい
- マンガ版を作る場合は必ず以下を含める: `マンガ` / `漫画` / `マンガでわかる` / `図解` / `コミック`
- 元書籍のキーワードも活用する

### 書籍紹介文_HTML.html

KDPの商品説明欄にそのまま貼り付けられるHTML。以下の固定構成で作る:

1. `<h2>` フック（読者の悩みに刺さる一文）
2. `<ul>` 共感リスト（こんな悩みはありませんか？）
3. `<h3>` + `<p>` 解決策の提示
4. `<h3>` + `<ul>` 本書で得られること
5. `<h3>` + `<ul>` こんな方におすすめ
6. `<h3>` + `<p>` CTA（行動を促す一文）
7. `<h3>` + `<ul>` 目次

KDP は `<h1>` を商品タイトルに使うため、本文中の見出しは `<h2>`/`<h3>` から始める。

---

## 出力先（推奨）

```
<book-name>/
└── KDP出版用/
    ├── cover.png                  # ← 表紙（このスキルの A で生成）
    ├── cover.jpg                  # ← KDP申請用JPEG版
    ├── 書籍情報.md                # ← このスキルの B で生成
    ├── ジャンル・キーワード.md     # ← このスキルの B で生成
    └── 書籍紹介文_HTML.html        # ← このスキルの B で生成
```

KDPダッシュボードでアップロードする際は、このフォルダ5点（+EPUB本体）をそのまま使う。表紙アップロードでは `cover.jpg` を優先する。

---

## トラブルシューティング

| 症状 | 対処 |
|---|---|
| `openai.AuthenticationError` | `OPENAI_API_KEY` が設定されていない／無効。`echo $OPENAI_API_KEY`（Windowsは `echo %OPENAI_API_KEY%`）で確認 |
| `model_not_found: gpt-image-2` | OpenAIアカウントの組織が画像モデルを許可していない。OpenAIダッシュボードで Verify Organization を完了させる |
| 表紙の文字が崩れる | プロンプトの `constraints` に「文字は日本語で正確に表記すること」を強調。それでもダメなら2-3回 retry |
| 表紙にキャラが似ない | `--char-refs` に渡すPNGを差し替え／追加。最大3枚程度まで |
| 生成画像のアスペクト比が違う | `--size 1024x1536` を明示指定（API側のデフォルトは正方形）|

---

## 参考: 元スキル

このスキルは `ebook-to-manga` スキル（8ステップパイプライン）の Step 6（表紙作成）と Step 8（メタデータ）を抽出した独立版。
フル機能版（ソース分析〜EPUB製本まで）が必要な場合は元スキルを使う。
