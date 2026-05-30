---
name: ebook-to-manga
description: 既存のKindle電子書籍（Markdown原稿）をマンガ形式に変換し、EPUB化してKDP出版用メタデータまで一括生成するスキル。ChatGPT Images 2.0 (gpt-image-2) 画像生成、コミクル2.0テンプレートを組み合わせた8ステップパイプライン。
---

# 電子書籍マンガ化スキル (Ebook-to-Manga Converter)

## 概要

このスキルは、既存のKindle電子書籍（Markdown原稿）をマンガ形式の電子書籍に変換する。
8ステップのパイプラインでソース分析からKDP出版準備まで一気通貫で実行する。

## 入力

- **ソースフォルダ**（必須）: ebookフォルダのパス（例: `.company/outputs/ebooks/01-worker-positive/`）。`project.md` と `manuscript/` ディレクトリを含むこと。
- **目標ページ数**（任意）: デフォルト100。範囲40-120。
- **ジャンル指定**（任意）: 作画設定の20ジャンルから指定。未指定時は書籍テーマから自動判定。
- **出力フォルダ名**（任意）: `.company/outputs/ebooks-manga/` 配下。デフォルトはソースフォルダ名。

## 前提条件

- `OPENAI_API_KEY` 環境変数が設定されていること（必須）
- `openai` Pythonパッケージがインストールされていること（必須）
- Python 3.x が `python` コマンドで利用可能なこと（Windows環境）
- `GOOGLE_AI_STUDIO_API_KEY` 環境変数（任意・レガシー。移行後別PRで整理予定）
- `google-genai` Pythonパッケージ（任意・レガシー。移行後別PRで整理予定）

## 画像生成の実行モード（HANDOFF_MODE）

本スキルは画像生成について 2 つのモードをサポートする:

- **`HANDOFF_MODE=inline`**（デフォルト・従来動作）: Codex が OpenAI API を直接呼び出す
- **`HANDOFF_MODE=codex-handoff`**: manifest を生成してハンドオフフォルダに配置し、ユーザーが別ターミナルの Codex CLI で `gen_pages.py` を実行。Codex は DONE.json を待機してから QC ループを続行

モード切替はユーザー指示で決定する。スキル開始時にモードを確認し、以降の Step 3 / Step 5 / Step 6 で同じモードを貫く。

ハンドオフ仕様の詳細: `.company/handoff/codex-image-gen/_spec/SPEC.md`

---

## 画像生成の絶対ルール

- **全ステップ共通**: 画像生成時は必ず「日本のアニメ・マンガ調イラスト」で生成すること
- 実写風・フォトリアル風の画像は禁止
- プロンプトの冒頭に必ず「◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。」を含めること
- これはキャラクターデザイン（Step 3）、ページ画像（Step 5）、表紙（Step 6）すべてに適用する

## 画像フォーマット

- **Step 5 本文ページ画像はPNG形式（.png）で保存する**（gpt-image-2 は b64_json で PNG を返すため、再エンコードによる品質劣化を避ける）
- **Step 6 表紙のみJPEG変換を行う**（KDP要件に対応するため Pillow で PNG→JPEG 変換: `img.save(path, 'JPEG', quality=92)`）
- Step 3 キャラリファレンス画像はPNG形式（変更なし）

## 分冊対応

ページ数が多い場合（目安: 80P超）は、複数巻に分冊する。

### 分冊時の出力ディレクトリ構成

```
.company/outputs/ebooks-manga/{book-name}/
├── manuscript/                     # 共通素材（全巻共有）
│   ├── シナリオ.txt
│   ├── character_defs.json
│   └── characters/
│       ├── {charA}.png ... 
├── vol1/                           # 第1巻
│   ├── panels/
│   │   └── comicle_output.csv
│   ├── pages/
│   │   ├── page_001.png ... page_NNN.png
│   └── KDP出版用/
│       ├── {タイトル} 第1巻.epub
│       └── cover.jpg
├── vol2/                           # 第2巻
│   ├── panels/
│   │   └── comicle_output.csv
│   ├── pages/
│   │   ├── page_001.png ... page_NNN.png
│   └── KDP出版用/
│       ├── {タイトル} 第2巻.epub
│       └── cover.jpg
├── ...
└── progress.json
```

### 単巻の出力ディレクトリ構成

```
.company/outputs/ebooks-manga/{book-name}/
├── project.md
├── KDP出版用/
│   ├── {タイトル}.epub
│   ├── cover.jpg
│   ├── 書籍情報.md
│   ├── ジャンル・キーワード.md
│   └── 書籍紹介文_HTML.html
├── manuscript/
│   ├── シナリオ.txt
│   ├── character_defs.json
│   └── characters/
│       ├── {charA}.png ... 
├── panels/
│   ├── comicle_output.csv
│   └── pages/
│       ├── page_001.png ... page_NNN.png
└── progress.json
```

### 標準保存ルール（全電子書籍共通）

| フォルダ | 内容 | 備考 |
|---------|------|------|
| `project.md` | プロジェクト概要 | タイトル、ターゲット、章立て、ステータス |
| `KDP出版用/` | KDPアップロードに必要な全ファイル | EPUB、表紙、書籍情報、紹介文HTML |
| `manuscript/` | 原稿・制作素材 | 章別Markdown、シナリオ、キャラ定義等 |

**書籍情報.md のフォーマット（必須）:**
```markdown
# 書籍情報

## タイトル
- **日本語**: {タイトル}
- **フリガナ**: {カタカナ}
- **ローマ字**: {ローマ字}

## サブタイトル
- **日本語**: {サブタイトル}
- **フリガナ**: {カタカナ}
- **ローマ字**: {ローマ字}

## 著者名
- **日本語**: {著者名}
- **フリガナ**: {カタカナ}
- **ローマ字**: {ローマ字}

## 出版社名
- **日本語**: YN出版
- **フリガナ**: ワイエヌシュッパン
- **ローマ字**: YN Shuppan
```

**書籍紹介文_HTML.html（必須）:**
KDP商品説明欄にそのまま貼り付けられるHTML形式。以下の構成で作成する:
1. `<h2>` フック（読者の悩みに刺さる一文）
2. `<ul>` 共感リスト（こんな悩みはありませんか？）
3. `<h3>` + `<p>` 解決策の提示
4. `<h3>` + `<ul>` 本書で得られること
5. `<h3>` + `<ul>` こんな方におすすめ
6. `<h3>` + `<p>` CTA（行動を促す一文）
7. `<h3>` + `<ul>` 目次

## 実行順序と依存関係

**フル実行時の正しい順序:**
```
Step 1（ソース分析）→ Step 2（シナリオ）→ Step 3（キャラデザ）
→ Step 4（CSV作成）→ Step 5（画像生成）→ Step 6（表紙作成）
→ Step 7（EPUB製本）→ Step 8（メタデータ）
```

**重要: Step 7（EPUB製本）は、Step 5（画像）とStep 6（表紙）の両方が完了してから実行すること。**
表紙なしでEPUBを作ると、後から表紙を差し替える手間が発生する。

## 部分実行への対応

| リクエスト | 実行ステップ | 前提条件 |
|-----------|------------|---------|
| 「○○をマンガ化して」 | Step 1-8 フル実行 | - |
| 「シナリオだけ作って」 | Step 1-2 | - |
| 「キャラデザインして」 | Step 3のみ | シナリオ必須 |
| 「コマ割りCSVを作って」 | Step 4のみ | シナリオ+キャラ必須 |
| 「画像を生成して」 | Step 5のみ | CSV必須 |
| 「表紙だけ作って」 | Step 6のみ | キャラ定義必須 |
| 「EPUBにまとめて」 | Step 7のみ | **画像+表紙の両方が必須** |
| 「メタデータだけ生成して」 | Step 8のみ | - |

---

## ワークフロー

### Step 1: ソース分析と準備

1. ソースフォルダから `project.md` を読み込み、書籍メタ情報を抽出する:
   - タイトル、サブタイトル、著者名
   - ターゲット読者
   - 章構成

2. `manuscript/` 配下の全 `.md` ファイルをファイル名順に読み込み、以下を集計する:
   - 章数、各章の行数・文字数
   - 総文字数

3. **ジャンル自動判定**: 書籍テーマ・内容から「作画設定マスタ」（後述）の20ジャンルの中で最適なものを選択する。判定基準:
   - 書籍タイトル・サブタイトルのキーワード
   - 章の内容からのテーマ推定
   - ユーザーが明示指定した場合はそちらを優先

4. 出力ディレクトリを作成する:
   ```bash
   mkdir -p ".company/outputs/ebooks-manga/{book-name}/KDP出版用"
   mkdir -p ".company/outputs/ebooks-manga/{book-name}/manuscript/characters"
   mkdir -p ".company/outputs/ebooks-manga/{book-name}/panels/pages"
   ```

5. `progress.json` を作成して進捗管理を開始する:
   ```json
   {
     "book_name": "{book-name}",
     "source_path": "{ソースパス}",
     "target_pages": 100,
     "genre": "{選択ジャンル}",
     "steps": {
       "1_source": {"status": "done"},
       "2_scenario": {"status": "pending"},
       "3_characters": {"status": "pending"},
       "4_panels": {"status": "pending"},
       "5_images": {"status": "pending", "completed": 0, "total": 0, "failed": []},
       "6_cover": {"status": "pending"},
       "7_epub": {"status": "pending"},
       "8_metadata": {"status": "pending"}
     }
   }
   ```

6. **ユーザーに提示**: ソース分析レポート（タイトル、章構成、選択ジャンル、推定ページ数）を表示し、確認を得る。

---

### Step 2: マンガ用シナリオ作成

以下のペルソナと指示に基づいて、Codexがマンガ用シナリオを作成する。

#### ペルソナ設定
- ビジネス関連の超人気売れっ子漫画シナリオライター
- どんなテーマのビジネスにおいても人気大爆発の漫画のシナリオを作成することのできる、独創的で斬新奇抜なアイディアを持っている
- 豊富な語彙力、情感豊かな表現力によってターゲット読者の心を動かし、彼らの問題を解決する類稀な能力を持っている
- 書籍テーマについての実践的なスキルを持っていて、それをもとに漫画のストーリーを書くことができる

#### シナリオ作成ルール
1. 書籍原稿の各章に沿って漫画ストーリーを作成する
2. 登場人物は**最大3人**に設定する
3. 登場人物は見分けやすいよう**年齢・性別をバラバラ**にする
   - NG例: 20代女性を2人登場させる
   - OK例: 20代女性と20代男性、または20代女性と40代男性
4. **1コマ単位の記述ではなく文章形式**で記載する
5. 章立ては書籍の章構成をそのまま踏襲する

#### 出力フォーマット例
```
「{タイトル} ～{サブタイトル}～」

プロローグ：{プロローグタイトル}
{プロローグの文章形式シナリオ}

第1章：{章タイトル}
{第1章の文章形式シナリオ}

第2章：{章タイトル}
{第2章の文章形式シナリオ}

...

エピローグ：{エピローグタイトル}
{エピローグの文章形式シナリオ}
```

#### 出力
- ファイル: `manuscript/シナリオ.txt`
- **ユーザー確認ポイント**: シナリオの内容を表示し、登場人物・ストーリー展開の確認を得る

---

### Step 3: キャラクターデザイン

シナリオの登場人物（最大3名）ごとにキャラクターデザインを生成する。

> **モード別フロー概要**
> - `inline` モード: 3-1 → 3-2-A-inline（直接生成）→ 3-3 ユーザー確認
> - `codex-handoff` モード: 3-1 → 3-2-A-codex（manifest 生成）→ 3-2-B-codex（Codex 実行依頼）→ 3-2-C-codex（DONE.json 受け取り）→ 3-3 ユーザー確認

#### 3-1. キャラクター定義の作成

シナリオから各登場人物の以下を決定し、`manuscript/character_defs.json` に保存する:
```json
{
  "{キャラA名}": "{キャラA名}: {年齢}{性別}、{髪型}、{髪色}、{体型}、{デフォルト服装の詳細}",
  "{キャラB名}": "{キャラB名}: {年齢}{性別}、{髪型}、{髪色}、{体型}、{デフォルト服装の詳細}",
  "{キャラC名}": "{キャラC名}: {年齢}{性別}、{髪型}、{髪色}、{体型}、{デフォルト服装の詳細}"
}
```

#### 3-1a. 時間経過によるキャラクターバリエーション

ストーリー中で時間が経過し、キャラクターの容姿が変化する場合（子供の成長、髪型の変化、加齢など）は、**同一キャラクターの時期別バリエーション**として別定義・別リファレンス画像を作成する。

例:
```json
{
  "ひなた（赤ちゃん期）": "ひなた: 0〜1歳の女の子、柔らかい黒髪（少なめ）、丸い大きな目、ピンクのロンパース",
  "ひなた（2歳期）": "ひなた: 2歳の女の子、短い黒髪のおかっぱ、丸い大きな目、ピンクのTシャツに白いズボン"
}
```

- キャラ名に `（時期名）` を付けて区別する
- リファレンス画像も時期ごとに別ファイルで生成する（例: `ひなた_赤ちゃん期.png`, `ひなた_2歳期.png`）
- CSVでは該当時期のリファレンス画像を参照する: `添付のひなた_2歳期.pngと100%同一の外見で描画`
- ストーリー上の時期に応じて正しいバリエーションを使い分けること

#### 3-1b. 場面別服装ルールの定義

キャラクターの服装は場面（シーン）に応じて変化させる。ストーリーの状況に合った服装を設定し、**同じシーン内ではページが変わっても服装を統一する**。

服装ルールの例:
```
■ ミサキの服装ルール
- 自宅・普段着: ボーダー柄（白と紺）のカットソーにデニムパンツ、白いスニーカー
- オフィス: 白いブラウスにグレーのタイトスカート、黒いパンプス
- 夜・就寝前: 薄いピンクのパジャマ
- 外出（カフェ等）: ベージュのカーディガン+白Tシャツ+デニム

■ ケンタの服装ルール
- 常時: グレーのTシャツにネイビーのスウェットパンツ
```

**CSVでの服装指定ルール:**
1. 各ページの `◆【補足情報】服装:` 欄で、そのシーンに合った服装を必ず明記する
2. **同じシーン（場面転換がないページ連続）では同じ服装を維持する**
3. 場面が変わったら（時間帯・場所の変化）服装も適切に切り替える
4. 夜のシーンで部屋着/パジャマ → 翌朝のシーンで普段着、のように自然に遷移させる

#### 3-2-A: キャラクタープロンプト構築（共通）

各キャラクターについて、gpt-image-2 で全身リファレンス画像を生成するためのプロンプトを組み立てる。

**画像生成プロンプトの構成**:
```
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆作画スタイル: 日本のアニメ・マンガ調イラスト、クリーンな線画、デジタル彩色、はっきりした輪郭線
{Step 1で選択したジャンルの作画設定全文}

キャラクターデザイン:
{キャラ名}: {character_defs.jsonの外見詳細}

# 補足
- 必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止
- セリフやオノマトペは入れない
- 全身の立ち姿にしてください
- 小道具を手に持たせないでください
- 白背景
```

#### 3-2-B: 生成実行（モード別）

**inline モード時（`HANDOFF_MODE=inline` またはデフォルト）:**

openai パッケージ（gpt-image-2）を使用する。

```bash
export OPENAI_API_KEY="$OPENAI_API_KEY" && python << 'PYTHON_SCRIPT'
import os, sys, base64, datetime
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai not found. Run: pip install openai")
    sys.exit(1)

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("ERROR: OPENAI_API_KEY is not set.")
    sys.exit(1)

PROMPT = """{{キャラクターデザインプロンプト}}"""
OUTPUT_DIR = r"{{出力ディレクトリ}}"
FILE_PREFIX = "{{キャラ名}}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = OpenAI(api_key=API_KEY)
try:
    result = client.images.generate(
        model="gpt-image-2",
        prompt=PROMPT,
        size="1024x1536",
        quality="high",
        n=1,
    )
except Exception as e:
    print(f"ERROR: gpt-image-2 generate failed: {e}")
    sys.exit(1)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{FILE_PREFIX}_{timestamp}.png"
filepath = os.path.join(OUTPUT_DIR, filename)
with open(filepath, "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
print(f"OK: {filepath}")
PYTHON_SCRIPT
```

- 各キャラクターを**並列実行**（`run_in_background: true`）で同時生成する
- サイズ: `size="1024x1536"`, `quality="high"`
- 保存先: `manuscript/characters/`

**codex-handoff モード時（`HANDOFF_MODE=codex-handoff`）:**

1. ジョブ ID を生成する: `{book_id}_vol{N}_step3_{YYYYMMDD_HHMMSS}`
2. ハンドオフフォルダを作成する: `.company/handoff/codex-image-gen/<job-id>/step3/`
3. `job.json` を生成する（`status: "created"`）
4. `manifest.json` を生成・保存する（`job_type: "character_ref"`）:
   ```json
   {
     "job_id": "<job-id>",
     "job_type": "character_ref",
     "model": "gpt-image-2",
     "size": "1024x1536",
     "quality": "high",
     "output_dir": "./output",
     "items": [
       {
         "id": "キャラ名",
         "output_filename": "キャラ名_YYYYMMDD_HHMMSS.png",
         "prompt": "（3-2-A で組み立てたプロンプト全文）",
         "api_call": "generate"
       }
     ],
     "retry_policy": {"max_retries": 3, "backoff_sec": 5}
   }
   ```
5. `_spec/gen_pages.py` を `step3/gen_pages.py` としてコピーする
6. `_spec/codex_instructions_template.md` をジョブ固有情報で埋めて `step3/codex_instructions.md` を生成する
7. `job.json` の status を `"ready"` に更新する
8. ユーザーに `codex_instructions.md` の内容を提示し、別ターミナルで Codex CLI を起動するよう依頼する

**3-2-C: 受け取りと後処理（codex-handoff モード時）:**

ユーザーから「Codex 完了しました」の通知を受けたら:

1. `step3/output/DONE.json` を読み込む
2. `status` フィールドを確認する（`"success"` / `"partial"` / `"failed"`）
3. `generated[]` 配列を `id` フィールドで manifest の `items` と突合する（配列順序は使わない）
4. 各 item の sha256 を実ファイルと照合して整合性を検証する
5. 生成成功した PNG ファイルを `manuscript/characters/` にコピーする（output/ 内の PNG を参照元とする）
6. 失敗した item があれば `step3_regen/manifest.json` を作成して再ハンドオフし、再度 Codex 実行を依頼する
7. 全 item が PASS したら 3-3 ユーザー確認へ進む

#### 3-3. ユーザー確認
- 生成されたキャラクター画像をReadツールで表示する
- ユーザーの承認を得てから次のステップへ進む
- 不満があれば外見設定を修正して再生成する

---

### Step 4: コマ割りCSV作成

**重要: 既存の `generate_comicle_csv.py` は使用しない。Codex自身がCSVを直接生成する。**

シナリオ + キャラクター定義 + 作画設定をもとに、コミクル用CSVを生成する。

#### CSV仕様
- **ヘッダー**: `ページ番号,使用するコマ割りテンプレ,漫画作成のプロンプト,コマ別テキストJSON`
- **目標ページ数**: 入力で指定された値（デフォルト100）
- **出力**: `panels/comicle_output.csv`

#### コマ別テキストJSON 仕様

4列目 `コマ別テキストJSON` には、後工程の Blind-OCR 比較・Pillow 合成が期待テキストを
直接参照できるよう、ページ内の全セリフ・ナレーションを JSON 配列として格納する。

**設計の注意（重要）**: この列は画像生成（Gemini）には渡さない。
OCR 判定・Pillow 合成だけが参照する。画像生成プロンプト（3列目）と内容が重複するが、
生成側に見せることで confirmation bias が生じるため意図的に分離している。

**JSON スキーマ:**
```json
[
  {"panel_id": 1, "type": "dialogue",  "speaker": "キャラ名", "text": "セリフ本文"},
  {"panel_id": 1, "type": "narration", "speaker": null,       "text": "ナレーション本文"},
  {"panel_id": 2, "type": "dialogue",  "speaker": "キャラ名", "text": "セリフ本文"},
  ...
]
```

**フィールド仕様:**

| フィールド | 型 | 許容値 | 説明 |
|---|---|---|---|
| `panel_id` | 整数 | 1 以上の整数 | コマ番号。`panel_regions.json` のキーと対応する |
| `type` | 文字列 | `"dialogue"` または `"narration"` のみ | セリフ・吹き出しは `"dialogue"`、ナレーションボックスは `"narration"` |
| `speaker` | 文字列 or null | キャラ名文字列 / `null` | `"dialogue"` 時は発話者名（例: `"ミサキ"`）、`"narration"` 時は必ず `null` |
| `text` | 文字列 | — | プロンプトの「」内セリフ・ナレーション本文と完全一致する文字列。OCR 比較の基準値 |

**対象外（含めないもの）:**
- オノマトペ（ぱぁっ / ビクッ 等）— OCR 対象外
- 背景テキスト・看板・スマホ画面等 — OCR 対象外

**複数セリフ・複数ナレーションの扱い:**
1コマ内に複数のセリフ・ナレーションがある場合は、コマ読み順（右→左）に
**別オブジェクトとして配列に追記**する（セパレータ結合は使用しない）。

例（1コマに2セリフ）:
```json
[
  {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ", "text": "えっ、本当に？"},
  {"panel_id": 1, "type": "dialogue", "speaker": "ケンタ", "text": "ああ、間違いない"}
]
```

**テキストページ（テンプレ=テキストページ）の扱い:**
- `コマ別テキストJSON` は空配列 `[]` を格納する
- `panel_id` の採番は不要（テキストページに panel_id は存在しない）
- 画像生成もスキップ対象のため、OCR 判定も実施しない

**テンプレと panel_id の対応（panel_regions.json との整合）:**

| テンプレ | コマ数 | panel_id の値 | 補足 |
|---------|--------|--------------|------|
| テンプレ1 | 1 | 1 | — |
| テンプレ2〜4 | 2 | 1, 2 | 1=上段（または右側）、2=下段（または左側） |
| テンプレ5 | 3 | 1, 2, 3 | 1=上段、2=中段、3=下段 |
| テンプレ6 | 3 | 1, 2, 3 | 1=上段、2=下段右側、3=下段左側 |
| テンプレ7 | 3 | 1, 2, 3 | 1=上段右側、2=上段左側、3=下段 |

> **テンプレ6（T6）の注意**: プロトタイプ実装（`composite_page5.py`）では
> 下段右側を `"bottom-right"`、下段左側を `"bottom-left"` というキー名で定義しているが、
> 本スキルでは panel_id=2（右側）/ panel_id=3（左側）に統一する。
> `panel_regions.json` 側も整数キー `"2"` / `"3"` で定義されているため、
> Pillow 合成スクリプトはキー名ではなく整数 panel_id で参照すること。

#### 7種類のコマ割りテンプレート

テンプレート参照画像: `G:\マイドライブ\AIC\コミクル2.0\テンプレ\テンプレ1-7.jpg`

| テンプレ | コマ数 | 構成 | 読み順 |
|---------|--------|------|--------|
| テンプレ1 | 1コマ | ページ全体を使った1コマ | — |
| テンプレ2 | 2コマ | 上下に均等2分割 | 上段→下段 |
| テンプレ3 | 2コマ | 上下2分割（上段小→下段大） | 上段→下段 |
| テンプレ4 | 2コマ | 上下2分割（上段大→下段小） | 上段→下段 |
| テンプレ5 | 3コマ | 上・中・下の3段構成 | 上→中→下 |
| テンプレ6 | 3コマ | 上段1コマ + 下段左右2コマ | 上段→下段右側→下段左側 |
| テンプレ7 | 3コマ | 上段左右2コマ + 下段1コマ | 上段右側→上段左側→下段 |

#### コマ読み順と配置ルール
- 読み順: 日本の漫画形式（**右上から左下へ**）
- 横並びのコマの場合: 必ず「右側」が先のコマ、「左側」が後のコマ
  - 例: 1コマ目＝右側、2コマ目＝左側

#### 各ページのプロンプト構造（出力フォーマット）

以下の順序と書式で記述する。コマの位置指定（右側・左側）を間違えないこと。

```
◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】キャラクター外見: [キャラ名]は添付の[ファイル名]と100%同一の外見で描画
◆【出力サイズ】9:16
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【補足情報】服装: [服装詳細]
◆【コマ構成】[テンプレ名]: [コマ数と配置の詳細]
◆【作画】[作画設定マスタから読み込んだジャンル別作画スタイル全文（省略せず100%書き写す）]
◆【ストーリー】
[各コマの詳細描写]
```

#### ストーリー部分の記述ルール

各コマについて以下を記述する:
```
Nコマ目 (位置): [シーン描写] セリフ: [セリフ内容] ナレーション: [ナレーション] オノマトペ: [オノマトペ]
```

- **シーン描写**: 誰が何をしているか具体的に記述。表情、感情表現、ポーズ、構図を詳細に描写
- **セリフ**: 形式: `［発言者］の吹き出しに「セリフの内容」`
- **ナレーション**: 四角い吹き出し（ナレーションボックス）。形式: `ナレーション: ［四角枠］テキスト内容`
  - 場面転換（「その夜——」）、状況説明、心理描写に使用する
  - ナレーションなしの場合: `ナレーション: なし`
- **背景**: シーンの感情に合わせて適切なパターンを選択
  - 水玉模様、半円、ドット模様、フラッシュエフェクト、ストライプ、グラデーション、幾何学模様など
- **オノマトペ**: ストーリーに応じて以下から選択
  - ぱぁっ / パァァ / ビクッ / ギクッ / キュン / イライラ / じーっ / ガーン / むすっ / テクテク / ダダダダ / ガチャ / チラッ

#### 原文テキストの活用（最重要）

**原稿のテキストをできるだけ忠実にCSVに反映すること。**

1. **セリフ「」は全て省略せずCSVに含める** — 原稿にあるセリフは1つも落とさない
2. **地の文はナレーションボックスとして積極的に入れる** — 場面転換・状況説明・心理描写をナレーション欄に配置
3. **テキスト密度目標: 1ページあたり約90文字**（セリフ+ナレーション合計）
4. **原稿カバー率80%以上を目指す** — CSV内のセリフ+ナレーション文字数 ÷ 原稿の全テキスト文字数

テキスト密度が低い（70字/P以下）場合はナレーションの追加が不足している。密度を計測して調整すること。

#### CSV生成時の注意事項
- キャラクター統一性を最優先とし、画像参照を厳密に適用
- コマ構成はテンプレートに完全準拠し、コマ数の変更は一切禁止
- 各ページで一貫した作画スタイルを維持
- 複数キャラクター登場時は位置関係と向きを明確に指定
- 各コマの状況説明は「誰が何をしているか」を具体的に記述
- カラーで生成すること。モノクロの生成は禁止
- **作画設定の演出欄に「ステップ図解」は入れない**（STEP1→STEP2のような図が多発するため）
- 文字列内に"ダブルクォート"を使う場合は〝〟に置き換える（CSVフォーマット崩れ防止）
- **`コマ別テキストJSON` 列のフォーマット対策（重要）**:
  - JSON 内の文字列値（`text` / `speaker` フィールド）に `"` が含まれる場合も〝〟に変換する
  - テキスト内に `,`（カンマ）が含まれる場合は、`コマ別テキストJSON` 列全体を CSV の
    標準ダブルクォートで囲む（例: `"[{""panel_id"": 1, ...}]"`）。
    ただし JSON 内で〝〟変換済みの場合はネストが崩れないため、
    **列の値全体をダブルクォートで囲む方法を推奨する**
  - `text` フィールド内に改行文字（`\n`）は使用しない。改行が必要な場合は空白区切りで1行に収める

#### 前付けページ（必須）

CSVの先頭に以下の前付けページを必ず含めること:

| ページ | テンプレ | 内容 | 全巻 | 2巻以降 |
|--------|---------|------|------|---------|
| 目次 | テキストページ | 巻タイトル＋収録話一覧＋コラム一覧 | ✅ | ✅ |
| 登場人物紹介 | テンプレ1 | キャラクターを縦に並べ全身イラスト＋名前＋一行紹介 | ✅ | ✅ |
| 前巻までのあらすじ | テキストページ | 前巻の物語要約（200-300字） | - | ✅ |

#### コラムページ

原稿にコラムがある場合、テキストページとして原文をそのまま入れる:
```
◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。
◆【コラム原文】
[原稿のコラム全文をそのまま入れる]
```
長いコラムは段落の区切りで2ページに分割する。

#### テンプレート選択の目安
- テンプレ1（1コマ）: タイトルページ、インパクトシーン、感情的クライマックスに使用。全体の15-20%
- テンプレ2-4（2コマ）: 会話シーン、対比表現に使用。全体の30-40%
- テンプレ5-7（3コマ）: ストーリー展開、場面転換に使用。全体の40-50%

#### ユーザー確認
- CSV生成後、以下を表示して確認を得る:
  - 総ページ数
  - テンプレート分布（各テンプレの使用割合）
  - 最初の3ページ、中盤の1ページ、最後の1ページのプロンプトサンプル

---

### Step 5: 画像生成（ハイブリッドQCループ）

#### 概要

A（Blind-OCR判定）と B（Pillowフォールバック）を組み合わせた
A+Bハイブリッドパイプラインで全ページのテキスト正確性を保証する。

- **A路線**: 画像生成 → Blind-OCR → プログラム比較 → PASS なら完了
- **B路線**: `max_iter` 回連続 FAIL 後に Pillow 合成フォールバックを発動し、
  CSV の `コマ別テキストJSON` から期待テキストを直接描画して 100% 正確性を保証する

この設計により「文字が描けない」ページが EPUB に混入する問題を根本排除する。

リファレンス実装: `.company/outputs/ebooks-manga/manga-career-restart/_prototype/hybrid_loop.py`（465行）

> **モード別フロー概要**
>
> - `inline` モード: 各 iter で [A-1] 直接 API 呼び出し → [A-2] Blind-OCR → [A-3] Vision-check → 判定 → PASS or 次 iter / フォールバック
> - `codex-handoff` モード: **[A-1] 画像生成部分のみ** Codex CLI にハンドオフ。[A-2] Blind-OCR・[A-3] Vision-check・[A-4] 統合判定・[A-5] フィードバック注入・フォールバック判定は**常に Codex 側で実行**する。
>   - iter 1: `step5/` に manifest を配置し Codex 起動依頼 → DONE.json 受け取り後に QC ループ実行
>   - QC FAIL で次 iter が必要な場合: `step5_regen_iter_2/` を新規作成して再ハンドオフ（`iter` フィールドを 2 に更新）
>   - max_iter 超過時: Step 5.5 フォールバック（Pillow 合成）を Codex が直接実行（モード分岐なし）

#### パラメータ

| パラメータ | 既定値 | 説明 |
|---|---|---|
| `max_iter` | `3` | FAIL 判定でフォールバックに切り替えるしきい値 |
| バッチサイズ | `10` | 1バッチあたりのページ数（並列実行単位） |
| バッチ間待機 | `5秒` | API レート制限対策 |
| 保存形式 | PNG（無損失） | gpt-image-2 は b64_json で PNG を返す。JPEG 変換なし |

`max_iter` の調整目安:
- 高精度が必要な場合: `2` に下げる（フォールバック発動率は上がるがコスト増）
- 処理速度優先の場合: `1` も可（A路線を1回だけ試して即フォールバック）

#### ループフロー（疑似コード）

プロトタイプ `hybrid_loop.py` の `def main()` を仕様化したもの。

```
CSV を読み込み、全ページリストを取得する
# character_defs.json を1回だけロードしてキャッシュ（ページごとに再読み込みしない）
char_defs = load_json("manuscript/characters/character_defs.json")

for page in pages:
    # テキストページ判定（OCR・Vision-check・フォールバック全スキップ）
    if page の コマ別テキストJSON == []:
        画像生成をスキップ（テキストページは生成不要）
        PASS として記録 → 次ページへ

    # A路線: 生成 → OCR + Vision-check → 統合判定 ループ
    current_prompt = 元の画像生成プロンプト
    converged = False
    # ページに登場するキャラを抽出（char_defs キャッシュを渡す）
    page_chars = extract_page_chars(page.prompt, char_defs)

    for iter in range(1, max_iter + 1):
        # [A-1] 画像生成（gpt-image-2）— モード分岐
        # inline モード:
        #   画像を生成し pages/page_{NNN}_iter_{iter}.png に保存（直接 API 呼び出し）
        # codex-handoff モード:
        #   step5/ または step5_regen_iter_{iter}/ に manifest.json を配置し Codex 起動依頼
        #   ユーザーから「Codex 完了しました」通知を受けてから DONE.json を読み込み
        #   id ベースで突合・sha256 検証・欠損検出を行い pages/ に png を配置してから
        #   [A-2] 以降の QC ループへ進む
        画像を生成し pages/page_{NNN}_iter_{iter}.png に保存

        # [A-2] Blind-OCR（→ Step 5-QC 参照）
        # セリフなしページ（コマ別テキストJSON == []）は OCR スキップ（自動 PASS 扱い）
        ocr_verdict = blind_ocr_and_compare(pages/page_{NNN}_iter_{iter}.png, コマ別テキストJSON)

        # [A-3] Vision-check（→ Step 5-QC 参照）
        # 画像生成が発生した全ページを対象（セリフなしページも必ず実行）
        # キャラ名リストは「名前を先に提示した上で1人ずつ YES/NO を返す」設計（確証バイアス排除）
        vision_verdict, missing_chars = vision_check(pages/page_{NNN}_iter_{iter}.png, page_chars)

        # [A-4] 統合判定: OCR PASS かつ Vision-check PASS → ページ PASS
        if ocr_verdict == PASS and vision_verdict == PASS:
            pages/page_{NNN}_iter_{iter}.png を pages/page_{NNN}.png としてコピー
            converged = True
            progress.json を更新（このページ完了）
            break

        # [A-5] FAIL 時フィードバック注入（OCR 側・Vision-check 側を個別に追記）
        current_prompt = build_feedback_prompt(元のプロンプト, ocr_verdict, vision_verdict, missing_chars)
        # OCR FAIL → ◆【前回失敗・最重要】パネル別の不一致を追記
        # Vision-check FAIL → ◆【前回失敗・最重要】欠落キャラ名を全身イラストで描くよう追記

    # B路線: max_iter 超過時フォールバック（→ Step 5.5 参照）
    # OCR FAIL / Vision-check FAIL のいずれが原因でも Step 5.5 に乗せる
    if not converged:
        fallback_reason = determine_fallback_reason(ocr_verdict, vision_verdict)
        # fallback_reason: "ocr_fail" / "vision_fail" / "both_fail"
        Step 5.5 を呼び出す（clean regen + Pillow 合成）
        pages/page_{NNN}_composited.png を pages/page_{NNN}.png にリネーム
        progress.json を fallback: true, fallback_reason: fallback_reason で更新

各バッチ完了後に progress.json を更新する
バッチ間は 5 秒待機する
```

#### 処理の流れ（詳細）

**1. ページごとに iter = 0 で開始**

CSV の全ページを 10 ページずつのバッチに分割し、各バッチ内は並列実行（`run_in_background: true`）する。

**2. テキストページ判定（空配列 → 自動 PASS）**

CSV の `コマ別テキストJSON` 列が空配列 `[]` のページはテキストページとみなす。
- 画像生成をスキップする（生成不要）
- OCR・Vision-check・フォールバック処理もすべてスキップする
- 自動的に PASS として `progress.json` に記録して次ページへ進む

**2a. character_defs.json のロードとキャッシュ**

ページループ開始前に `manuscript/characters/character_defs.json` を1回だけ読み込んでキャッシュする。
ページごとに再読み込みしない（I/O 削減）。
`extract_page_chars(prompt, char_defs)` にキャッシュ済み辞書を渡し、当該ページのキャラリストを取得する。

**3. 画像生成（プロンプト + フィードバック注入）**

各 iter の生成設定:
- `IMAGE_PROMPT`: iter=1 は CSV の `漫画作成のプロンプト`、iter=2以降はフィードバック注入済みプロンプト
- `OUTPUT_FOLDER`: `{vol_dir}/pages`（分冊時）または `panels/pages`（単巻時）
- `SIZE`: `"1024x1536"`（9:16縦長）
- `FILE_PREFIX`: `page_{ページ番号3桁ゼロ埋め}_iter_{iter}` （例: `page_039_iter_1`）
- **保存形式**: PNG（`.png`）。`base64.b64decode(result.data[0].b64_json)` をそのままバイナリ保存する
- **モデル名**: `gpt-image-2`（openai SDK。`client.images.edit` を使用）
- **参照画像**: プロンプト内の `添付の([^\s、,]+?\.png)` から抽出したキャラクターリファレンス PNG を `image=` に渡す

**codex-handoff モード時の [A-1] 手順（詳細）:**

1. **5-A: ハンドオフ準備（iter=1 の場合）**
   - ジョブ ID 生成: `{book_id}_vol{N}_step5_{YYYYMMDD_HHMMSS}`
   - ハンドオフフォルダ作成: `.company/handoff/codex-image-gen/<job-id>/step5/`
   - `job.json` 生成（`status: "created"`）
   - `manifest.json` 生成: `job_type: "page_batch"`、全ページの items を含む（`is_text_only` フラグも設定）
   - `manuscript/characters/` の PNG を `step5/characters/` にコピー
   - `_spec/gen_pages.py` を `step5/gen_pages.py` としてコピー
   - `codex_instructions.md` をテンプレから生成
   - `job.json` を `"ready"` に更新し、ユーザーに Codex 起動を依頼

2. **5-B: Codex 実行待機**
   - **推奨**: ユーザーが Codex 完了後に「Codex 完了しました」と通知する（方法A・SPEC.md §12 参照）
   - ユーザー通知受信後: `step5/output/DONE.json` を Read ツールで読み込む

3. **5-C: 受け取りと後処理（各 iter 共通）**
   - `DONE.json` の `status` 確認（`"success"` / `"partial"` / `"failed"`）
   - `generated[]` を `id` フィールドで manifest items と突合（インデックス対応は使用しない。SPEC.md §7 参照）
   - sha256 照合・欠損検出。失敗 items があれば `step5_regen_iter_{iter+1}/` を作成して再ハンドオフ
   - 成功 items の PNG を `pages/page_{NNN}_iter_{iter}.png` としてコピー
   - → [A-2] Blind-OCR へ進む（以降は inline モードと同じ）

4. **5-A（再生成 iter）**: QC FAIL ページを次 iter でハンドオフする場合
   - FAIL ページのみ抽出し、フィードバック注入済みプロンプトを `prompt` フィールドに入れた新 manifest を作成
   - ディレクトリ: `step5_regen_iter_{iter}/`（例: `step5_regen_iter_2/`）
   - `iter` フィールドを更新（`"iter": 2`）してユーザーに再度 Codex 起動を依頼

```python
import base64, re
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

# プロンプトから参照画像ファイル名を抽出
refs = re.findall(r"添付の([^\s、,]+?\.png)", IMAGE_PROMPT)
refs = list(dict.fromkeys(refs))  # 重複除去・順序維持
char_ref_files = []
for name in refs:
    p = os.path.join(CHAR_DIR, name)  # manuscript/characters/*.png
    if os.path.exists(p):
        char_ref_files.append(open(p, "rb"))

try:
    result = client.images.edit(
        model="gpt-image-2",
        image=char_ref_files[0] if len(char_ref_files) == 1 else char_ref_files,
        prompt=IMAGE_PROMPT,  # 既存プロンプト構造をそのまま使用（追加ルール挿入禁止）
        size="1024x1536",
        quality="high",
        n=1,
    )
finally:
    for f in char_ref_files:
        f.close()

out_path = f"pages/page_{NNN:03d}_iter_{iter}.png"
with open(out_path, "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
```

**4. Blind-OCR 判定（→ Step 5-QC 参照）**

生成した `pages/page_{NNN}_iter_{iter}.png` を `### Step 5-QC` の仕様に従って OCR する。
OCR は `gpt-4o`（openai、temperature=0.0）で実行し、期待テキストは一切渡さない。
セリフなしページ（`コマ別テキストJSON == []`）は OCR をスキップし、自動 PASS 扱いとする。

**5. Vision-check 判定（→ Step 5-QC 参照）**

`### Step 5-QC` の「Vision-check」仕様に従い、`pages/page_{NNN}_iter_{iter}.png` に対して
gpt-4o vision でキャラ存在チェックを実行する。
- 画像生成が発生したすべてのページ（セリフあり・セリフなし問わず）を対象とする
- セリフなしページも必ず Vision-check を実行する（OCR オートPASS の穴を塞ぐ）
- `extract_page_chars(prompt, char_defs)` で当該ページの登場キャラを絞り込み、そのキャラのみをチェックする
- テキストページ（画像生成スキップ済み）はスキップする

**6. 統合判定（OCR + Vision-check）**

`### Step 5-QC` の「OCR と Vision-check の統合判定」テーブルに従い判定する。

| ページ種別 | OCR 判定 | Vision-check 判定 | ページ確定条件 |
|---|---|---|---|
| セリフありページ | 実行 | 実行 | 両方 PASS のみ確定 |
| セリフなしページ（画像生成あり） | スキップ（自動 PASS） | 実行 | Vision-check PASS で確定 |
| テキストページ（画像生成なし） | スキップ | スキップ | 自動確定 |

両方 PASS → `pages/page_{NNN}_iter_{iter}.png` を `pages/page_{NNN}.png` としてコピーし、
このページを完了として次ページへ進む。

**7. FAIL 時: フィードバック構築 → iter += 1 → 3 に戻る**

`### Step 5-QC` の「FAIL 時のフィードバック注入（拡張版）」に従い、OCR FAIL 分と
Vision-check FAIL 分をそれぞれ個別のセクションとしてプロンプト末尾に追記する。
- OCR FAIL → `◆【前回失敗・最重要】` パネル別不一致エントリを追記
- Vision-check FAIL → `◆【前回失敗・最重要】` 欠落キャラ名リストを追記
- 両方 FAIL の場合は両セクションを併記する
次の iter の画像生成にこのプロンプトを使用する。

**8. max_iter 超過 → フォールバック（→ Step 5.5 参照）**

`max_iter` 回すべて FAIL した場合（OCR FAIL・Vision-check FAIL どちらの原因でも同様）、
`### Step 5.5` の手順で clean regen + Pillow 合成を実行する。
合成完了後、`pages/page_{NNN}_composited.png` を `pages/page_{NNN}.png` にリネームして
このページの最終成果物として確定する。
フォールバック発動理由（`fallback_reason`）を `progress.json` に記録する（→ 進捗管理セクション参照）。

#### 成果物ファイル命名

| ファイル名パターン | 生成タイミング | EPUB 向け扱い |
|---|---|---|
| `pages/page_{NNN}_iter_{N}.png` | A路線・各 iter の生成画像 | 監査用。PASS した iter の画像のみ `page_{NNN}.png` にコピーされる |
| `pages/page_{NNN}.png` | A路線で PASS したページの最終画像 | Step 7 EPUB 製本が直接参照する |
| `pages/page_{NNN}_clean.png` | B路線・clean regen 画像 | 監査用（削除不要） |
| `pages/page_{NNN}_composited.png` | B路線・Pillow 合成最終画像 | `page_{NNN}.png` にリネーム後に EPUB 製本が参照 |

> **EPUB製本（Step 7）との整合**: Step 7 は `pages/page_{NNN}.png` を収集する。
> フォールバック発動ページは `page_{NNN}_composited.png` を `page_{NNN}.png` に
> リネームして渡すこと。この運用により Step 7 の修正は不要になる。

#### 進捗管理

各バッチ完了後に `progress.json` を更新する。

```json
"5_images": {
  "status": "done",
  "completed": 100,
  "total": 100,
  "failed": [],
  "fallback_pages": [39, 52],
  "fallback_count": 2,
  "fallback_reasons": {"39": "ocr_fail", "52": "vision_fail"},
  "vision_check_failed_pages": [2, 17],
  "vision_check_pages": 95
}
```

- `failed` 配列: iter 内で最終的に PASS したページは記録しない。iter 超過してフォールバックに進んだページも最終的に合成で完了するため `failed` には記録しない
- `fallback_pages`: フォールバック（B路線）を使用したページ番号リスト
- `fallback_reasons`: フォールバック発動ページごとの発動理由。値は `"ocr_fail"` / `"vision_fail"` / `"both_fail"` のいずれか
- `vision_check_failed_pages`: Vision-check で1回以上 FAIL したページ番号リスト。最終的に PASS したページも記録する（監査用）
- `vision_check_pages`: Vision-check を実施したページ数の集計
- フォールバック発動時は `progress.json` の当該ページに `"fallback": true, "fallback_reason": "{reason}"` を追記する
- ログに `[fallback] page {NNN}: composited.png generated (reason={reason}, missing=[キャラ名])` を出力する

#### コスト試算

**単純生成コスト: $21.00/冊**

| 項目 | 単価目安 | 冊あたり |
|---|---|---|
| 画像生成（gpt-image-2）× 100P | $0.21/枚（1024x1536 high） | $21.00 |
| 単純生成合計 | — | **$21.00/冊** |

**ハイブリッドQC追加コスト: +$3.15〜$3.75/冊**

| 追加項目 | 想定 | コスト目安 |
|---|---|---|
| Blind-OCR（gpt-4o）× 平均 1.5 iter/P × 100P | 150コール | +$1.50 |
| **Vision-check（gpt-4o）× 平均 1.2 iter/P × 100P** | **120コール** | **+$0.60〜$1.20** |
| FAIL ページの追加生成（iter 2〜3 の再生成） | 難ページ約 20%、平均 2 iter | +$0.84 |
| clean regen（フォールバック発動ページ） | 約 5%/100P = 5ページ | +$0.21 |
| Pillow 合成処理 | ローカル処理（API 不使用） | $0 |
| 追加合計 | — | **+$3.15〜$3.75/冊** |

**合計: $24.15〜$24.75/冊（ハイブリッドQC込み）**（中央値: **$24.45/冊**）

※ 要件定義書のコスト試算（$34.89/冊）はバッファ込みの上限値。上表は内訳積み上げの標準見積もり。
※ Vision-check FAIL による再生成 iter が追加で発生した場合は、Vision-check コールが上記より増加する。

**max_iter 変更時のコスト試算:**

| max_iter | 期待 OCR コール数 | 期待 Vision-check コール数 | 追加コスト目安 |
|---|---|---|---|
| 1 | 100（1回のみ） | 100（1回のみ） | +$1.60〜$2.20（フォールバック多め） |
| 2 | 120〜140 | 110〜130 | +$2.60〜$3.20 |
| **3（既定）** | **130〜150** | **115〜125** | **+$3.15〜$3.75** |
| 4 | 150〜170 | 120〜135 | +$3.80〜$4.40（フォールバック率低下） |

> **注**: `max_iter=3` の追加コスト `+$3.15〜$3.75` は内訳積み上げ値。
> レート変動・iter 超過・OCR/Vision-check リトライ等のバッファを加味した安全側見積もりは工程1のコスト試算テーブル（`$34.89/冊`）を参照。

**フォールバック発動率の想定**: 全ページの約 5%（難ページ：長セリフ・複数キャラ同時発話・小さいコマ等）。
iter 3 回の反復で約 95% のページは A路線で収束する見込み（プロトタイプ実測に基づく推定）。

#### 維持される Step 4 と Step 6 の仕様

**Step 4 との接続（上流）:**
- Step 4 で生成した CSV（`panels/comicle_output.csv`）の `コマ別テキストJSON` 列が
  本ループの OCR 比較とフォールバック合成の期待テキスト源になる
- 使用するコマ割りテンプレは Step 4 の CSV `使用するコマ割りテンプレ` 列から取得する（7種）
- キャラクターリファレンス画像（`character_defs.json`）は Step 3 の成果物を引き続き使用する

**Step 6 との接続（下流）:**
- 本ステップ完了後、全ページが `pages/page_{NNN}.png` として揃っている（フォールバック発動ページはリネーム済み）
- Step 6（カバー画像生成）はこのファイル群を参照しないため影響なし
- Step 7（EPUB製本）は `pages/page_{NNN}.png` を収集するため、命名規則の一貫性が保証されていれば修正不要

---

### Step 5-QC: Blind-OCR + Vision-check 判定モジュール

Step 5 の画像生成ループ内で使用する OCR 品質判定の仕様。
工程5（Step 5 ループ全面改修）でこのサブセクションを参照してループを組む。

#### 設計原則: Confirmation Bias 排除（最重要）

**OCR プロンプトに期待テキストを絶対に含めない。**

反面教師となった実装（`vlm_dialogue_check.py`）では、期待テキストをプロンプト内に
`【期待されるセリフ・ナレーション】` として提示していた。この方式では OCR モデルが
期待値を見てから画像を解釈するため、誤字・脱字があっても「合っている」と判定する
偽陽性（confirmation bias）が発生した。

正しい設計:
- OCR は純粋な「画像 → テキスト抽出」タスクとして実行する
- OCR モデルには画像のみを渡し、「何が書かれているか読み取れ」とだけ指示する
- 期待テキストとの照合は **OCR 完了後にプログラム側（Python）で** 行う
- この分離により、OCR モデルは期待値の影響を受けず画像の実態を報告する

#### OCR 対象と対象外

**対象（必ず読み取る）:**
- 吹き出し（楕円・雲形）内の文字 → `type="dialogue"`
- ナレーションボックス（四角枠・角丸枠）内の文字 → `type="narration"`

上記は CSV の `コマ別テキストJSON` で `type="dialogue"` / `type="narration"` として
定義されたテキストに対応する。

**対象外（無視する）:**
- オノマトペ・擬音（ぱぁっ / ビクッ / ドンッ 等）
- 背景の看板・ポスター・標識
- 小物の UI・ラベル（スマホ画面・PC画面・本の表紙・商品パッケージ等）
- キャラクターの服のロゴ・ブランド表記

対象外はすべて CSV の `コマ別テキストJSON` に含めていないため、
OCR が対象外を拾っても比較対象が存在せず無視される。

**OCR の粒度: 画像全体を一括で渡す。**
コマ領域ごとにクロップして個別 OCR するのではなく、ページ全体画像を1回の API 呼び出しで処理する。
OCR モデルはページ全体から各吹き出しを自動検出し、`panel_id` と `type` を推定する。
（コマ領域の切り出しは Pillow 合成時（Step 5.5）にのみ使用する。）

#### OCR プロンプトテンプレート

モデル: `gpt-4o`（openai。テキスト専用。画像生成モデルは使用しない）
temperature: `0.0`（決定論的出力）
response_format: `{"type": "json_object"}`（JSON 以外の出力を防ぐ）
max_tokens: `4096`

```python
import base64
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

with open(image_path, "rb") as f:
    b64img = base64.b64encode(f.read()).decode()

OCR_PROMPT = """添付のマンガ画像を見て、下記の要素を画像に描かれている通り正確に読み取ってください。
推測や補完は一切せず、画像に実際に見える文字列だけを返してください。
読めない崩し字や意味不明な文字列も、見える通りに書いてください（勝手に正しい日本語に補正しない）。

対象:
- 吹き出し（楕円・雲形）内の文字 -> type="dialogue"
- ナレーションボックス（四角枠・角丸枠）内の文字 -> type="narration"

対象外（読み取らない）:
- オノマトペ・擬音
- 背景の看板・ポスター・標識
- 小物のUI・ラベル（スマホ画面・PC画面・本の表紙・商品パッケージ等）
- 服のロゴ・ブランド表記

出力形式: JSONのみ。説明文・マークダウン禁止。読み取れたテキストは改行なしで1行に連結。
{
  "bubbles": [
    {"panel_id": int, "type": "dialogue"|"narration", "detected_text": str}
  ]
}"""

response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.0,
    max_tokens=4096,
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64img}"}},
                {"type": "text", "text": OCR_PROMPT},
            ],
        }
    ],
)
ocr_result = json.loads(response.choices[0].message.content)
```

**重要**: このプロンプトには期待テキスト（CSV の `text` フィールドの値）を一切含めない。

#### 比較ロジック（決定論的）

OCR 完了後、以下の手順でプログラム側（Python）が比較を行う。

**ステップ1: テキスト正規化（両辺に適用）**
```python
import unicodedata, re

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s)  # 全角/半角統一（例: ｢→「、ｶﾅ→カナ）
    s = re.sub(r"\s+", "", s)              # 空白・改行・タブをすべて除去
    return s
```

NFKC 正規化により全角/半角の揺れを吸収する。空白・改行除去により縦書きレンダリングの
改行差異を吸収する。

**ステップ2: キーによる突き合わせ**
- 突き合わせキー: `(panel_id, type)` のペア
- OCR 結果の `bubbles` 配列を `{(panel_id, type): [detected_text, ...]}` の辞書に変換する
- CSV の `コマ別テキストJSON` 各エントリについて、同じキーの OCR バブルを検索する
- 1コマに同 type が複数ある場合（例: 2人のセリフ）は、未使用の候補の中から最初に
  正規化一致するものを採用する（used セットで重複消費を防ぐ）
- **fuzzy matching（編集距離・部分一致）は禁止。完全一致のみ有効とする。**

**ステップ3: 判定**
- 各エントリで `normalize_text(detected) == normalize_text(expected)` を評価する
- 全エントリが一致 → `match=True`
- 1エントリでも不一致 → `match=False`

#### PASS/FAIL 判定条件

**ページ単位の判定:**
- CSV の `コマ別テキストJSON` の全エントリが `match=True` → ページ **PASS**
- 1エントリでも `match=False` → ページ **FAIL** → 再生成トリガー

**テキストページの扱い:**
- CSV の `コマ別テキストJSON` が空配列 `[]` のページはテキストページとみなす
- テキストページは OCR をスキップし、自動的に **PASS** 扱いとする
- 画像生成自体もスキップ済みのため、判定処理は不要

**FAIL 時のフィードバック注入:**
FAIL の場合、次の iter の生成プロンプト末尾に以下のセクションを追記する:

```
◆【前回失敗・最重要】前回生成では以下が正しく描画されませんでした。今回は一字一句正確に描くこと:
- パネル{panel_id}の{種別}: 正「{expected}」 ⇔ 前回誤「{detected[:40]}」
```

- `種別` は `type=="dialogue"` なら「セリフ」、`type=="narration"` なら「ナレーション」
- `detected[:40]` は検出テキストの先頭40文字（長文の切り詰め）
- FAIL したエントリのみ列挙する（PASS 済みのエントリは含めない）

#### エラーハンドリング

**OCR API エラー・空レスポンス時:**
- OCR 呼び出しは最大 **2回リトライ**（合計3回試行）する
- リトライ間隔: 1秒
- 3回すべて失敗した場合は `{"bubbles": []}` を返す（空バブル扱い）
- 空バブルは比較時に「検出テキストなし」として全エントリが FAIL になる
- つまり OCR 失敗は自動的に FAIL 扱いとなり、次の iter または フォールバックに進む

**JSON パースエラー時:**
- OCR レスポンスが JSON として解析できない場合、部分修復を試みる
  （正規表現で `"bubbles": [...]` 部分を抽出して再パース）
- 修復も失敗した場合は `{"bubbles": []}` を返す（空バブル = FAIL 扱い）

**ログ出力:**
- OCR リトライ発生時は `[ocr] WARN: OCR failed after retries: {error}` をログ出力する
- 各 iter の判定結果（PASS/FAIL、FAIL したパネル番号と type）をログ出力して
  どのコマが何回 FAIL したかを追跡可能にする
  - 例: `[iter 2] FAIL: panel=2 type=dialogue expected='佐藤さん...' detected='佐藤ざん...'`
- progress.json の `failed` 配列には iter 超過して FAIL したページ番号のみ記録する
  （iter 内で最終的に PASS したページは failed に記録しない）

#### OCR と Vision-check の統合判定

**ページ単位の最終判定:**

| ページ種別 | OCR | Vision-check | ページ判定 |
|---|---|---|---|
| セリフありページ | 実行 | 実行 | どちらか一方でも FAIL → ページ FAIL |
| セリフなしページ（画像生成あり） | スキップ（期待テキスト空 = 自動 PASS） | 実行 | Vision-check FAIL → ページ FAIL |
| テキストページ（画像生成なし） | スキップ | スキップ | 自動 PASS |

- OCR と Vision-check は独立して実行する（並列 or 直後、どちらでも可）
- どちらか一方でも FAIL の場合 → ページ FAIL → 再生成トリガー
- 両方 PASS の場合のみ → ページ確定（`converged = True`）
- セリフなしページは OCR 実質スキップ（期待テキスト空のため全エントリ一致扱い）、Vision-check は必ず実行する

**FAIL 時のフィードバック注入（拡張版）:**

OCR FAIL 時は既存フォーマットそのまま:
```
◆【前回失敗・最重要】前回生成では以下が正しく描画されませんでした。今回は一字一句正確に描くこと:
- パネル{panel_id}の{種別}: 正「{expected}」 ⇔ 前回誤「{detected[:40]}」
```

Vision-check FAIL 時は以下を追記:
```
◆【前回失敗・最重要】前回生成では以下のキャラクターが描画されていませんでした。今回は必ず全身イラストで描いてください: {欠落キャラ名リスト}
```

両方 FAIL の場合は両セクションを併記する。

---

#### Vision-check: キャラ存在検証の設計原則

**目的**: 画像生成ループ内でキャラ欠落バグ（例: page_002 山田課長省略事象）を自動検出し、
再生成トリガーをかけることで全キャラが正しく描画された画像を確定する。

**confirmation bias 排除方針**:
- OCR の反面教師（期待テキストをプロンプトに含める設計）とは異なり、
  Vision-check は「このキャラクターが存在するか」を1人ずつ YES/NO で問う。
- 「全員が存在するか」をまとめて問うと、モデルが期待値に引っ張られて過剰に YES を返す
  確証バイアスが発生する恐れがある。キャラごとに個別質問することで判定精度を高める。
- システムプロンプトで「テキスト枠・名前ラベルのみの場合は NO とする」と明示し、
  「文字でキャラ名が書かれている」と「イラストが描かれている」の混同を防ぐ。

#### 対象ページ

**Vision-check を実行するページ:**
- `コマ別テキストJSON` が空配列 `[]` かつ画像生成が実行されたページ（セリフなしページ。例: 登場人物紹介ページ）
- `コマ別テキストJSON` に1件以上のエントリがあるページ（セリフありページ）

つまり、**画像生成が発生したすべてのページ**が Vision-check の対象となる。

**Vision-check をスキップするページ:**
- テキストページ（`コマ別テキストJSON` が `[]` かつ Step 5 で画像生成自体をスキップ済みのページ）
  - これらは画像ファイルが存在しないため Vision-check の対象外とする

#### キャラ名抽出ロジック

Vision-check で確認対象とするキャラ名は、当該ページのプロンプトに登場するキャラのみに絞り込む。
全キャラを毎ページチェックすると「このページには登場しないキャラ」への質問が多発し、
誤 FAIL の原因となるため、プロンプト内の記載で絞り込む設計とする。

**抽出元1: `character_defs.json`（Step 3 成果物、キャラ名マスター）**

```json
[
  {"id": "misaki", "name": "ミサキ", "appearance": "30代女性、ボブヘア、ボーダーシャツ"},
  {"id": "kenta",  "name": "ケンタ",  "appearance": "30代男性、グレーTシャツ"},
  ...
]
```

`character_defs.json` から全キャラの `name` と `appearance` を読み込み、
name → appearance のマッピング辞書を構築する。

**抽出元2: 当該ページの CSVプロンプト（`漫画作成のプロンプト` 列）の `◆【絶対最優先】キャラクター外見:` ブロック**

プロンプト内に登場するキャラ名を正規表現で抽出し、`character_defs.json` のマスターと突き合わせて
appearance 付きのキャラリストを生成する。

```python
import re

def extract_page_chars(prompt: str, char_defs: list[dict]) -> list[dict]:
    """
    プロンプトの「◆【絶対最優先】キャラクター外見:」ブロックから
    登場キャラ名を抽出し、character_defs.json の外見情報と結合して返す。

    Returns:
        [{"name": "ミサキ", "appearance": "30代女性、ボブヘア、ボーダーシャツ"}, ...]
    """
    # character_defs.json から name -> appearance マッピングを構築
    char_map = {c["name"]: c.get("appearance", "") for c in char_defs}

    # プロンプト内の「◆【絶対最優先】キャラクター外見:」ブロックを抽出
    block_match = re.search(
        r"◆【絶対最優先】キャラクター外見:\s*(.+?)(?=\n◆|\Z)",
        prompt,
        re.DOTALL,
    )
    if not block_match:
        return []

    block_text = block_match.group(1)

    # 「添付の〇〇.png」または「〇〇は添付の」パターンからキャラ名を動的抽出
    found_names = re.findall(r"添付の(.+?)\.png", block_text)
    # スペース除去・重複排除
    found_names = list(dict.fromkeys(name.strip() for name in found_names))

    result = []
    for name in found_names:
        appearance = char_map.get(name, "")
        result.append({"name": name, "appearance": appearance})
    return result
```

プロンプト内で言及されているキャラのみを Vision-check 対象とする（登場しないキャラまでチェックすると誤検出）。

#### Vision-check プロンプトテンプレート

モデル: `gpt-4o`（vision 機能）
temperature: `0.0`（決定論的出力）
response_format: `{"type": "json_object"}`

**システムプロンプト:**
```
あなたは画像品質チェッカーです。与えられたマンガ画像を分析し、
指定されたキャラクターが全身イラストとして描かれているかを1人ずつ YES または NO で判定してください。
テキスト枠・名前ラベルのみでキャラクターのイラスト本体が存在しない場合は NO としてください。
イラストが実際に画像内に描かれているかを画像の内容から判断してください。必ず JSON で返してください。
```

**ユーザープロンプト（動的生成）:**
```
以下のマンガ画像に、キャラクター{N}人 [{name_list}] がそれぞれ全身イラストとして描かれているか、
1人ずつ YES/NO で答えてください。テキスト枠のみ（名前タグのみでイラストなし）は NO とします。

出力形式（JSONのみ。説明文禁止）:
{{"vision_checks": [{{"char_name": "ミサキ", "result": "YES", "reason": "..."}}]}}
```

**Python コード例（base64 エンコード + gpt-4o Vision 呼び出し）:**

```python
import base64
import json
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def vision_check(image_path: str, page_chars: list[dict]) -> dict:
    """
    gpt-4o でキャラ存在チェックを実施する。

    Args:
        image_path: チェック対象の PNG ファイルパス
        page_chars: [{"name": "ミサキ", "appearance": "30代女性..."}, ...]

    Returns:
        {"vision_checks": [{"char_name": str, "result": "YES"|"NO", "reason": str}, ...]}
    """
    with open(image_path, "rb") as f:
        b64img = base64.b64encode(f.read()).decode("utf-8")

    n = len(page_chars)
    name_list = "、".join(c["name"] for c in page_chars)
    # キャラごとに外見補足付きの質問文を構築
    char_questions = "\n".join(
        f"- {c['name']}（{c['appearance']}）" for c in page_chars
    )

    system_msg = (
        "あなたは画像品質チェッカーです。与えられたマンガ画像を分析し、"
        "指定されたキャラクターが全身イラストとして描かれているかを1人ずつ YES または NO で判定してください。"
        "テキスト枠・名前ラベルのみでキャラクターのイラスト本体が存在しない場合は NO としてください。"
        "イラストが実際に画像内に描かれているかを画像の内容から判断してください。必ず JSON で返してください。"
    )
    user_msg = (
        f"以下のマンガ画像に、キャラクター{n}人 [{name_list}] がそれぞれ"
        f"全身イラストとして描かれているか、1人ずつ YES/NO で答えてください。"
        "テキスト枠のみ（名前タグのみでイラストなし）は NO とします。\n\n"
        f"確認対象:\n{char_questions}\n\n"
        '出力形式（JSONのみ。説明文禁止）:\n'
        '{"vision_checks": [{"char_name": "ミサキ", "result": "YES", "reason": "..."}]}'
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.0,
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64img}"},
                    },
                    {"type": "text", "text": user_msg},
                ],
            },
        ],
    )
    return json.loads(response.choices[0].message.content)
```

**レスポンス JSON スキーマ:**
```json
{
  "vision_checks": [
    {"char_name": "ミサキ", "result": "YES", "reason": "1段目に全身イラストあり"},
    {"char_name": "山田課長", "result": "NO", "reason": "テキスト枠のみ、イラストなし"}
  ]
}
```

#### 判定ロジック

```python
def vision_check_pass(vision_result: dict) -> tuple[bool, list[str]]:
    """
    Returns:
        (is_pass, missing_chars)
        - is_pass: True = Vision-check PASS、False = Vision-check FAIL
        - missing_chars: FAIL 時の欠落キャラ名リスト（PASS 時は空リスト）
    """
    checks = vision_result.get("vision_checks", [])
    missing = [c["char_name"] for c in checks if c.get("result") != "YES"]
    return (len(missing) == 0), missing
```

- 全キャラが `result: "YES"` → Vision-check **PASS**
- 1人でも `result: "NO"` → Vision-check **FAIL** → 再生成トリガー
- `vision_checks` が空配列（パースエラー等） → 全員 NO 扱い → **FAIL**

#### エラーハンドリング

**Vision-check API 失敗時:**
- Vision-check 呼び出しは最大 **2回リトライ**（合計3回試行）する
- リトライ間隔: 1秒
- 3回すべて失敗した場合は FAIL 扱いとする（安全側に倒す）
  - API 不安定による誤 FAIL のリスクより、キャラ欠落の見逃しリスクを優先して回避する

**JSON パースエラー時:**
- レスポンスが JSON として解析できない場合、部分修復を試みる
  （正規表現で `"vision_checks": [...]` 部分を抽出して再パース）
- 修復も失敗した場合は `{"vision_checks": []}` を返す（空配列 = 全員 NO 扱い = FAIL）

**ログ出力:**
- リトライ発生時: `[vision] WARN: Vision-check failed after retries: {error}`
- FAIL 検出時: `[vision] FAIL: page={NNN} missing=[山田課長, ケンタ]`
- 各 iter の判定結果: `[vision] iter_{N} char={name} result={YES/NO} reason={reason}`

---

### Step 5.5: Pillow合成フォールバック

> **モード注記**: Step 5.5 は `HANDOFF_MODE` に関わらず**常に Codex 側で直接実行**する。
> ローカル処理（Pillow）のみでハンドオフ不要。clean regen の画像生成 API 呼び出しは inline モードと同じロジックを使用する。

Step 5 で `max_iter` 回連続 FAIL したページに対して実行する、
100% 正確テキスト保証の合成モジュール。
Blind-OCR で収束しなかった場合のみ発動し、Pillow で日本語縦書きテキストを直接描画する。

#### 発動条件

- **発動トリガー**: Step 5 のハイブリッドループで `max_iter`（既定値: `3`）回連続して
  統合判定（Blind-OCR または Vision-check）が FAIL したページに対して発動する
  - Blind-OCR FAIL が原因でも、Vision-check FAIL が原因でも、同様に Step 5.5 に乗せる
- **スキップ条件**:
  - 1〜2 iter 以内に PASS したページ → Step 5.5 はスキップ（通常生成画像をそのまま採用）
  - テキストページ（`コマ別テキストJSON` が空配列 `[]`）→ 発動対象外（Step 5 でも画像生成をスキップ済み）
- **Vision-check FAIL 起因のフォールバックに関する重要注記**:
  - Pillow 合成はテキスト（吹き出し・ナレーション）の直接描画が主目的であり、**キャラ欠落の解消はできない**
  - Vision-check FAIL 起因でフォールバックを発動した場合は、Pillow 合成後も「キャラ欠落が残存している可能性」があるため、以下の運用とする:
    - `progress.json` の当該ページに `"fallback_reason": "vision_fail"` を記録する
    - 最終レポートでこのページを「手動確認対象」として報告する
  - ログ出力例: `[fallback] page {NNN}: composited.png generated (reason=vision_fail, missing=[山田課長])`
- **fallback_reason の値域**:
  - `"ocr_fail"`: OCR のみ FAIL が原因
  - `"vision_fail"`: Vision-check のみ FAIL が原因
  - `"both_fail"`: OCR と Vision-check の両方 FAIL が原因
- **パラメータ**:
  ```
  max_iter = 3        # FAIL 判定でフォールバックに切り替えるしきい値（既定値）
                       # 高精度が必要な場合は 2 に下げる、処理速度優先なら 1 も可
  ```
- **呼び出し元の責務**: Step 5 のループが iter 超過を検知したとき、
  `page_num`・`expected_items`（CSV の `コマ別テキストJSON` パース済みリスト）・
  `template_id`・`fallback_reason` を引数として本モジュールを呼び出す

---

#### 入出力仕様

**このモジュールが受け取る入力:**

| 引数 | 型 | 出所 | 説明 |
|---|---|---|---|
| `page_num` | int | Step 5 ループ | 対象ページ番号（3桁ゼロ埋め用） |
| `expected_items` | list[dict] | CSV `コマ別テキストJSON` | `[{panel_id, type, speaker, text}, ...]` の期待テキストリスト |
| `template_id` | str | CSV `使用するコマ割りテンプレ` | `"1"` 〜 `"7"` |
| `base_prompt` | str | Step 5 ループ | 元の画像生成プロンプト（clean regen の改訂元） |
| `char_refs` | list | Step 3 成果物 | キャラクターリファレンス画像のパスリスト |

**このモジュールの出力:**

| ファイル | 説明 |
|---|---|
| `pages/page_{NNN}_clean.png` | clean regen 画像（テキスト無し）。監査用に保持 |
| `pages/page_{NNN}_composited.png` | Pillow 合成済み最終画像（Step 7 EPUB製本の入力） |
| `pages/page_{NNN}_iter_*.png` | Step 5 で生成した各 iter 画像（監査用。削除不要） |

**呼び出し側（Step 5）の責務:**
- `pages/page_{NNN}_composited.png` を `pages/page_{NNN}.png` の代替として
  EPUB 製本（Step 7）に渡す
- `progress.json` の当該ページエントリを `"fallback": true` で更新する
- ログに `[fallback] page {NNN}: composited.png generated` を出力する

---

#### clean regen 手順

**目的**: テキスト・吹き出し・ナレーションボックスを一切含まない、
キャラクター + 背景のみの画像を再生成する。

**プロンプト改訂ルール（元プロンプトからの差分）:**

1. **テキスト除去ブロックを先頭近くに追加する（最重要）**:
   ```
   ◆【最重要・テキスト除去】このページには一切のテキスト・文字・セリフ・吹き出し・
   ナレーションボックス・オノマトペを描かないでください。
   - No text, no dialogue, no speech bubbles, no onomatopoeia, no narration boxes
   - 吹き出しの枠も描かないでください（後処理で合成します）
   - 擬音・効果音の文字も描かないでください
   - コマ内はキャラクター・背景・小物のみで構成してください
   ```

2. **ストーリー部分の改訂**:
   - 元プロンプトの `セリフ: ［...］の吹き出しに「...」` → 削除する
   - 元プロンプトの `ナレーション: ［四角枠］...` → 削除する
   - 代わりに構図指示のみを残す。例:
     ```
     1コマ目(上段): {キャラ名}が{シーン描写}。吹き出しは描かない。
     ```
   - `オノマトペ:` 行 → そのまま残してよい（もともと画像内テキストとして指示している場合は削除）

3. **削除しない要素**:
   - `◆【絶対最優先】アニメ・マンガ調` 等の画質指示
   - `◆【絶対最優先】キャラクター外見:` のリファレンス指示
   - `◆【補足情報】服装:` の服装指示
   - `◆【コマ構成】` のテンプレ・コマ割り指示

**参考（プロトタイプ `hybrid_loop.py` の `CLEAN_PROMPT`）:**
```python
CLEAN_PROMPT = """◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。...
◆【最重要・テキスト除去】このページには一切のテキスト・文字・セリフ・吹き出し・
ナレーションボックス・オノマトペを描かないでください。
...
◆【ストーリー・構図のみ】
1コマ目(上段・横長): 自宅。ミサキがスマホを耳に当てて緊張した表情で電話している。吹き出しは描かない。
...
"""
```

**画像生成（gpt-image-2）:**
```python
import base64, re
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

# base_prompt から参照画像ファイル名を抽出（A路線と同じロジック）
refs = re.findall(r"添付の([^\s、,]+?\.png)", base_prompt)
refs = list(dict.fromkeys(refs))  # 重複除去・順序維持
char_ref_files = []
for name in refs:
    p = os.path.join(CHAR_DIR, name)  # manuscript/characters/*.png
    if os.path.exists(p):
        char_ref_files.append(open(p, "rb"))

try:
    result = client.images.edit(
        model="gpt-image-2",
        image=char_ref_files[0] if len(char_ref_files) == 1 else char_ref_files,
        prompt=CLEAN_PROMPT,  # テキスト除去ブロック付きプロンプト（◆【最重要・テキスト除去】）
        size="1024x1536",
        quality="high",
        n=1,
    )
finally:
    for f in char_ref_files:
        f.close()

clean_path = f"pages/page_{NNN:03d}_clean.png"
with open(clean_path, "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
```

**保存**: `pages/page_{NNN}_clean.png`（PNG）

---

#### Pillow 合成フロー

**前提データの読み込み（合成開始前に必ず取得）:**

1. `panel_regions.json`（`.Codex/skills/ebook-to-manga/panel_regions.json`）から
   `template_{N}` キーでコマ領域辞書を取得する
2. `expected_items` リストを `panel_id` でグルーピングする

**描画順序（レイヤー重なりを防ぐため順序厳守）:**

```
[1] ベース画像（clean regen画像）を PIL で開き、RGBモードに変換する
    img = Image.open(clean_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)

[2] ページ全体を走査: panel_id ごとに以下を実行する
    （panel_id の昇順: 1 → 2 → 3）

  [2-a] narration（ナレーションボックス）を先に描画する
        ※ セリフ吹き出しより後ろに配置（Z順で下）
        - コマ右上隅に白い四角ボックスを配置（黒枠 width=2）
        - ボックス内に縦書きテキストを描画（右列から左列へ）

  [2-b] dialogue（セリフ吹き出し）を後に描画する
        ※ ナレーションボックスの上に重なるレイヤー
        - 白楕円 + 三角テールを描画（黒枠 width=3）
        - 楕円内に縦書きテキストを描画（右列から左列へ）
        - テール描画後、楕円との接続部に白線を上書きして境界線を消す

[3] 最終保存
    img.save(out_path, "PNG")
```

**配置アンカーの固定値（Phase 2 顔検出実装まで）:**

narration ボックス:
- 位置: コマ右上隅（`bx2 = px2 - 4`, `by1 = py1 + 4`）
- サイズ: テキスト量に応じて自動計算（パディング 10px）

dialogue 吹き出し:
- アンカー（吹き出し左上): `(0.04, 0.25)` — コマ左側・縦中央より少し上
- テール先端: `(0.40, 0.60)` — コマ中央やや下（キャラ顔の概算位置）
- サイズ: テキスト量に応じて自動計算（パディング 18px）

**はみ出し防止（必須）:**
- 吹き出し・ボックスがコマ領域外にはみ出す場合は、コマ内に収まるよう座標をシフトする
  （プロトタイプ `composite_bubble()` の clamp ロジック参照）

**参考（プロトタイプ `hybrid_loop.py` の `pillow_fallback()` 抜粋）:**
```python
def pillow_fallback(clean_image_path, expected_items, panel_regions, out_path):
    img = Image.open(clean_image_path).convert("RGB")
    W, H = img.size
    draw = ImageDraw.Draw(img)
    bubble_font  = ImageFont.truetype(FONT_BOLD, 22)
    narration_font = ImageFont.truetype(FONT_REG, 18)

    by_panel = {}
    for item in expected_items:
        by_panel.setdefault(item["panel_id"], []).append(item)

    for pid, items in by_panel.items():
        region = panel_regions[pid]
        box = (int(region[0]*W), int(region[1]*H),
               int(region[2]*W), int(region[3]*H))
        # narration 先
        for it in items:
            if it["type"] == "narration":
                composite_narration(img, draw, box, it["text"], narration_font)
        # dialogue 後
        for it in items:
            if it["type"] == "dialogue":
                composite_bubble(img, draw, box, (0.04, 0.25), (0.4, 0.6),
                                 it["text"], bubble_font)

    img.save(out_path, "PNG")
```

---

#### 縦書き描画ルール

日本語縦書き（tategaki）は1文字ずつ縦に積み上げて描画する。

**基本ルール:**
- 1文字 = 1セル（セル高さ = フォントの ascent + descent）
- 描画順序: 上から下へ（Y 増加方向）
- 複数列が必要な場合（テキストが長い場合）: 右列 → 左列の順に列を並べる
  （日本語マンガの縦書き慣習に従う）

**長音符・特殊文字の処理（回転必須）:**

以下の文字は縦書き時に90度回転して描画する（そのまま描くと横倒しになるため）:

| 文字 | 処理 |
|---|---|
| `ー`（長音符） | -90度回転 |
| `〜`（波ダッシュ） | -90度回転 |
| `…`（三点リーダ） | -90度回転 |
| `‥`（二点リーダ） | -90度回転 |

回転描画の実装（`draw_tategaki_text()` 内）:
```python
if ch in ("ー", "〜", "…", "‥"):
    tmp = Image.new("RGBA", (line_height, line_height), (0, 0, 0, 0))
    tmp_draw = ImageDraw.Draw(tmp)
    tmp_draw.text((0, 0), ch, font=font, fill="black")
    tmp = tmp.rotate(-90, expand=False)
    img.paste(tmp, (x, cur_y), tmp)     # img への直接ペースト（RGBA合成）
else:
    draw.text((x, cur_y), ch, font=font, fill="black")
cur_y += line_height + line_gap - 4    # 次の文字の Y 位置
```

**改行（列折り返し）の判定:**
- 列の最大文字数 `max_col_chars` を以下で計算:
  ```python
  # dialogue 吹き出しの場合
  max_col_chars = max(3, int(ph * 0.7 / char_h))
  # narration ボックスの場合
  max_col_chars = max(4, int(ph * 0.7 / char_h))
  ```
  （`ph` = コマの高さ in px、`char_h` = フォントの ascent + descent）
- `max_col_chars` を超えたら次の列に送る（Python の `range(0, len(text), max_col_chars)` でスライス）

**列幅の計算:**
```python
col_width = int(char_h * 1.05)   # dialogue（やや広め）
col_width = int(char_h * 1.02)   # narration（通常）
col_gap   = 5                     # dialogue 列間スペース
col_gap   = 3                     # narration 列間スペース
```

**句読点（、。）:** 通常文字として縦に積む（回転不要）。Pillow の縦書きで自然に見える。

---

#### フォント仕様

**推奨フォント（Windows 標準游ゴシック）:**

| 用途 | 変数名 | フォントファイル | フォントサイズ |
|---|---|---|---|
| セリフ吹き出し（dialogue） | `FONT_BOLD` | `YuGothB.ttc` | 22pt（プロトタイプ準拠） |
| ナレーションボックス（narration） | `FONT_REG` | `YuGothM.ttc` | 18pt（プロトタイプ準拠） |

**フォントパスの定義（スクリプト冒頭で変数化すること）:**
```python
FONT_BOLD = r"C:\Windows\Fonts\YuGothB.ttc"  # Bold: セリフ用
FONT_REG  = r"C:\Windows\Fonts\YuGothM.ttc"  # Medium/Regular: ナレーション用
```

**フォント未検出時のフォールバック（必須実装）:**
```python
try:
    bubble_font    = ImageFont.truetype(FONT_BOLD, 22)
    narration_font = ImageFont.truetype(FONT_REG,  18)
except OSError:
    # Windows 環境以外・フォントファイル欠損時は Pillow デフォルトで代替
    # 注: デフォルトフォントは日本語非対応のため、文字化けが起きる可能性がある
    # → 実運用では Windows 標準フォントが存在する環境で実行すること
    bubble_font    = ImageFont.load_default()
    narration_font = ImageFont.load_default()
    print("[WARN] YuGoth フォントが見つかりません。デフォルトフォントで代替します。")
    print("       日本語が正しく描画されない可能性があります。")
```

**フォントサイズの調整:**
- 長いセリフ（30文字超）で吹き出しがコマからはみ出す場合は、
  `max_col_chars` を増やして列を増やすか、フォントサイズを 18pt まで下げて対応する
- フォントサイズはページ画像の解像度（W×H）に依存するため、
  1080px 幅以外の画像では pt 数を比例調整することを推奨する

---

#### 出力ファイル命名

| ファイル名 | 用途 | 保持期間 |
|---|---|---|
| `pages/page_{NNN}_iter_1.png` 〜 `page_{NNN}_iter_N.png` | Step 5 で生成した各 iter 画像 | 監査用（削除不要） |
| `pages/page_{NNN}_clean.png` | clean regen 画像（テキスト無し） | 監査用（削除不要） |
| `pages/page_{NNN}_composited.png` | Pillow 合成済み最終画像 | **EPUB製本の入力として使用** |

> **EPUB製本（Step 7）との整合**: Step 7 の EPUB 生成スクリプトは `pages/page_{NNN}.png`
> を収集する。フォールバック発動ページは `pages/page_{NNN}_composited.png` を
> `pages/page_{NNN}.png` に**リネームまたはシンボリックリンク**して渡すこと。
> 命名規則を変えることで通常ページと区別しつつ、Step 7 の修正を不要にする。

**ログ記録（`progress.json` 更新）:**
```json
"5_images": {
  "status": "done",
  "completed": 100,
  "total": 100,
  "failed": [],
  "fallback_pages": [39, 52],   // フォールバックを使用したページ番号リスト
  "fallback_count": 2
}
```

---

### Step 6: 表紙作成

マンガ版の書籍表紙を生成する。

> **モード別フロー概要**
> - `inline` モード: 6-A プロンプト構築 → 6-B-inline 直接生成 → 6-C ユーザー確認
> - `codex-handoff` モード: 6-A プロンプト構築 → 6-B-codex manifest 生成・Codex 起動依頼 → 6-C-codex DONE.json 受け取り → ユーザー確認

#### 6-A: 表紙プロンプト構築（共通）

以下の手順でプロンプトを組み立てる（モード共通）。

#### 表紙プロンプトの構成

既存の `表紙プロンプト.md` の5ステップ構造をベースに、マンガ用に適応する:

```yaml
request_type: generate_hyper_detailed_magazine_cover_with_fixed_aspect_ratio
title: "マンガでわかる {元タイトル}"
subtitle: "{元サブタイトル}"
author: "{著者名}"

description: >
  添付された原稿ドキュメントファイルを分析して抽出したテキスト要素を使用して、
  圧倒的な情報量と高いデザイン密度を備えたプロ仕様の「マンガ書籍カバー」を生成する。

design_taste: >
  マンガ・コミック風の書籍カバーデザイン。
  {Step 1で選択したジャンルの作画設定の色調・演出を反映}
  キャラクターを全面に配置し、マンガらしい躍動感を演出。

character: >
  {character_defs.jsonの主要キャラクター2-3名の外見設定}
  キャラクター同士の関係性が伝わるポーズ・配置。

processing_steps:
  - step 1: 原稿分析とテキスト要素抽出
  - step 2: デザインムードと構図の決定
  - step 3: キャラクター配置と背景の生成（9:16アスペクト比）
  - step 4: テキストと装飾要素のレイアウト
  - step 5: キャラクター・背景とテキスト・装飾の統合
```

#### 6-B: 生成実行（モード別）

**inline モード時（`HANDOFF_MODE=inline` またはデフォルト）:**

gpt-image-2 で生成する。主人公キャラのリファレンス画像を `image=` に渡し、`images.edit` を使用する。

```python
import base64, glob, io, os, re
from PIL import Image
from openai import OpenAI

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# キャラクターリファレンス画像の取得
# 正規表現で添付PNG一覧から主人公キャラの画像ファイルを抽出する
# 例: character_defs.json や Step 3 で生成した chara_*.png を指定
char_ref_paths = []
# 方法A: 正規表現で添付ファイル名から抽出
char_ref_paths = re.findall(r'添付の([^\s、,]+?\.png)', COVER_PROMPT_TEXT)
# 方法B: Step 3 生成済みキャラPNGを直接指定（A が空の場合）
if not char_ref_paths:
    char_ref_paths = sorted(glob.glob(os.path.join(OUTPUT_DIR, "chara_*.png")))

char_ref_files = [open(p, "rb") for p in char_ref_paths]

result = client.images.edit(
    model="gpt-image-2",
    image=char_ref_files[0] if len(char_ref_files) == 1 else char_ref_files,
    prompt=COVER_PROMPT,
    size="1024x1536",
    quality="high",
    n=1,
)

# gpt-image-2 は b64_json で PNG バイナリを返す
# KDP要件（JPEG必須）のため Pillow で PNG→JPEG 変換して保存
img_bytes = base64.b64decode(result.data[0].b64_json)
img = Image.open(io.BytesIO(img_bytes))
cover_path = os.path.join(OUTPUT_DIR, "KDP出版用", "cover.jpg")
os.makedirs(os.path.dirname(cover_path), exist_ok=True)
img.save(cover_path, "JPEG", quality=92)
```

- サイズ: `size="1024x1536"`（9:16縦長形式）
- 品質: `quality="high"`
- 保存先: `KDP出版用/cover.jpg`（KDP要件により JPEG 形式で保存）
- **PNG→JPEG 変換**: gpt-image-2 から受け取った PNG バイナリを Pillow で JPEG に変換（quality=92）

**codex-handoff モード時（6-B-codex）:**

1. ジョブ ID 生成: `{book_id}_vol{N}_step6_{YYYYMMDD_HHMMSS}`
2. ハンドオフフォルダ作成: `.company/handoff/codex-image-gen/<job-id>/step6/`
3. `job.json` 生成（ジョブ状態管理用。`job_id` / `job_type: "cover"` / `created_at` / `status: "ready"` を記録。Step 3/5 と同一形式で SPEC.md §3 参照）
4. `manifest.json` 生成（`job_type: "cover"`）:
   - item 1件のみ: `id: "cover"`、`output_filename: "cover.png"`、`api_call: "edit"`
   - `reference_images`: 主人公キャラ PNG ファイル名（`characters/` からの相対パス）
5. `manuscript/characters/` の主人公キャラ PNG を `step6/characters/` にコピー
6. `_spec/gen_pages.py` を `step6/gen_cover.py` としてコピー
7. `codex_instructions.md` を生成してユーザーに提示、Codex 起動を依頼

**6-C: 受け取りと後処理（codex-handoff モード時）:**

1. ユーザーから「Codex 完了しました」通知を受けて `step6/output/DONE.json` を読み込む
2. `id: "cover"` の item が `status: "ok"` であることを確認する
3. sha256 照合で PNG の整合性を検証する
4. 生成された `step6/output/cover.png` を Pillow で JPEG 変換し `KDP出版用/cover.jpg` に保存する
   （inline モードと同じ PNG→JPEG 変換ロジックを適用）

#### ユーザー確認
- 表紙画像をReadツールで表示して確認を得る
- 不満があればプロンプトを修正して再生成する

---

### Step 7: 製本（EPUB化）

固定レイアウトEPUB3をPythonで直接構築する。
**Pandocでは固定レイアウトEPUBを生成できないため、`zipfile` モジュールを使用する。**

#### EPUB構造

```
mimetype                          (非圧縮)
META-INF/
  └── container.xml
OEBPS/
  ├── content.opf                 (パッケージメタデータ)
  ├── nav.xhtml                   (ナビゲーション)
  ├── style.css                   (スタイルシート)
  ├── images/
  │   ├── cover.jpg
  │   ├── page_001.png
  │   ├── page_002.png
  │   └── ...
  └── text/
      ├── cover.xhtml
      ├── page_001.xhtml          (画像ページ or テキストページ)
      ├── page_002.xhtml
      └── ...
```

#### テキストページの処理

CSVでテンプレが「テキストページ」のページは、画像ではなくHTMLテキストとしてEPUBに含める。
目次・あらすじ・コラム等がこれに該当する。テキストページ用CSSで読みやすくレンダリングする。

#### EPUB生成スクリプト

```bash
python << 'PYTHON_SCRIPT'
import zipfile
import os
import glob
import uuid
from datetime import datetime

BOOK_NAME = "{{book-name}}"
TITLE = "マンガでわかる {{元タイトル}}"
AUTHOR = "{{著者名}}"
OUTPUT_DIR = r"{{出力ディレクトリ}}"
PAGES_DIR = os.path.join(OUTPUT_DIR, "panels", "pages")
COVER_PATH = os.path.join(OUTPUT_DIR, "KDP出版用", "cover.jpg")
EPUB_PATH = os.path.join(OUTPUT_DIR, "KDP出版用", f"{BOOK_NAME}-manga.epub")

# ページ画像の収集（ソート済み）
# Step 5 は全画像を PNG (.png) で保存するため .png を対象とする
page_files = sorted(glob.glob(os.path.join(PAGES_DIR, "page_*.png")))
page_count = len(page_files)
book_id = str(uuid.uuid4())
modified = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

# --- mimetype ---
mimetype = "application/epub+zip"

# --- container.xml ---
container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

# --- style.css ---
style_css = """body { margin: 0; padding: 0; }
.page { width: 100%; height: 100%; }
.page img { width: 100%; height: 100%; object-fit: contain; }"""

# --- content.opf ---
manifest_items = [
    '    <item id="nav" href="text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
    '    <item id="style" href="style.css" media-type="text/css"/>',
    '    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
    '    <item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml"/>',
]
spine_items = ['    <itemref idref="cover"/>']

for i in range(1, page_count + 1):
    pid = f"page_{i:03d}"
    manifest_items.append(f'    <item id="{pid}" href="text/{pid}.xhtml" media-type="application/xhtml+xml"/>')
    manifest_items.append(f'    <item id="{pid}-img" href="images/{pid}.png" media-type="image/png"/>')
    spine_items.append(f'    <itemref idref="{pid}"/>')

content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">{book_id}</dc:identifier>
    <dc:title>{TITLE}</dc:title>
    <dc:creator>{AUTHOR}</dc:creator>
    <dc:language>ja</dc:language>
    <meta property="dcterms:modified">{modified}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:spread">landscape</meta>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
{chr(10).join(manifest_items)}
  </manifest>
  <spine page-progression-direction="ltr">
{chr(10).join(spine_items)}
  </spine>
</package>"""

# --- nav.xhtml ---
nav_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ja">
<head><title>{TITLE}</title></head>
<body>
<nav epub:type="toc">
  <ol>
    <li><a href="cover.xhtml">表紙</a></li>
    <li><a href="page_001.xhtml">本編</a></li>
  </ol>
</nav>
</body>
</html>"""

# --- ページXHTML生成関数 ---
def make_page_xhtml(img_path, alt_text):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="ja">
<head>
  <meta name="viewport" content="width=1080, height=1920"/>
  <link rel="stylesheet" href="../style.css"/>
  <title>{alt_text}</title>
</head>
<body>
  <div class="page"><img src="{img_path}" alt="{alt_text}"/></div>
</body>
</html>"""

# --- EPUB書き出し ---
os.makedirs(os.path.dirname(EPUB_PATH), exist_ok=True)

with zipfile.ZipFile(EPUB_PATH, 'w') as epub:
    # mimetype は非圧縮で最初に追加
    epub.writestr("mimetype", mimetype, compress_type=zipfile.ZIP_STORED)
    epub.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
    epub.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
    epub.writestr("OEBPS/text/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
    epub.writestr("OEBPS/style.css", style_css, compress_type=zipfile.ZIP_DEFLATED)

    # 表紙
    epub.write(COVER_PATH, "OEBPS/images/cover.jpg", compress_type=zipfile.ZIP_DEFLATED)
    cover_xhtml = make_page_xhtml("../images/cover.jpg", "表紙")
    epub.writestr("OEBPS/text/cover.xhtml", cover_xhtml, compress_type=zipfile.ZIP_DEFLATED)

    # 各ページ（Step 5 が page_{NNN}.png（PNG）で保存するため .png で格納）
    for i, page_file in enumerate(page_files, 1):
        pid = f"page_{i:03d}"
        epub.write(page_file, f"OEBPS/images/{pid}.png", compress_type=zipfile.ZIP_DEFLATED)
        page_xhtml = make_page_xhtml(f"../images/{pid}.png", f"ページ {i}")
        epub.writestr(f"OEBPS/text/{pid}.xhtml", page_xhtml, compress_type=zipfile.ZIP_DEFLATED)

print(f"OK: {EPUB_PATH}")
print(f"Pages: {page_count}")
print(f"Size: {os.path.getsize(EPUB_PATH) / 1024 / 1024:.1f} MB")
PYTHON_SCRIPT
```

#### EPUB仕様
- **固定レイアウト**: `rendition:layout: pre-paginated`
- **ページ方向**: `page-progression-direction: ltr`（左開き）
- **ビューポート**: `1080x1920`（9:16）
- **各ページ**: フルビューポート画像1枚

#### Step 5 ハイブリッドQCとの下流互換性

Step 5 のハイブリッドQCループは `pages/page_{NNN}.png` を最終成果物として出力する。
本 EPUB 生成スクリプトは `glob("page_*.png")` でこのファイル群を収集するため、
フォールバック発動ページも含めて追加改修なしで動作する。

| Step 5 出力パターン | EPUB に含まれるファイル | 対応方法 |
|---|---|---|
| A路線 PASS ページ | `page_{NNN}.png`（コピー済み） | そのまま収集 |
| B路線フォールバック ページ | `page_{NNN}.png`（`_composited.png` からリネーム済み） | そのまま収集 |
| 中間ファイル（`_iter_*` / `_clean` / `_composited`） | Step 5 がリネーム前に除去 | `glob` パターンに一致しないため自動除外 |

> **前提**: Step 5 の責務として、フォールバック発動ページの `page_{NNN}_composited.png` を
> `page_{NNN}.png` にリネームまたはコピーしてから本ステップを実行すること。

---

### Step 8: 電子出版用メタデータ

KDP出版に必要なメタデータを生成する。既存の `.company/outputs/ebooks/` 内のKDPメタデータ形式に準拠する。

#### 8-1. 書籍情報.md

```markdown
# 書籍情報

## タイトル
- **日本語**: マンガでわかる {元タイトル}
- **フリガナ**: {フリガナ}
- **ローマ字**: {ローマ字}

## サブタイトル
- **日本語**: {元サブタイトル}【マンガ版】
- **フリガナ**: {フリガナ}
- **ローマ字**: {ローマ字}

## 著者名
- **日本語**: {著者名}
- **フリガナ**: {フリガナ}
- **ローマ字**: {ローマ字}

## 出版社名
- **日本語**: YN出版
- **フリガナ**: ワイエヌシュッパン
- **ローマ字**: YN Shuppan
```

#### 8-2. ジャンル・キーワード.md

- メインジャンル + サブジャンルを設定
- キーワード7枠 × 3ワード = 21ワード
- マンガ固有キーワードを必ず含める: `マンガ`, `漫画`, `マンガでわかる`, `図解`, `コミック`
- 元書籍のキーワードも活用する

#### 8-3. 書籍紹介文_HTML.html

KDP商品説明欄にそのまま貼り付けられるHTML形式で作成する（必須）。
上記「標準保存ルール」の書籍紹介文_HTML.htmlフォーマットに準拠すること。

#### 出力先
- `KDP出版用/書籍情報.md`
- `KDP出版用/ジャンル・キーワード.md`
- `KDP出版用/書籍紹介文_HTML.html`

---

## 作画設定マスタ

書籍テーマに応じて、以下の20ジャンルから最適な作画設定を自動選択する。
（出典: `C:\Users\User\OneDrive - 株式会社　美建\作画設定.xlsx`）

### 恋愛ドラマ
- ジャンル: 恋愛に最適化した統一スタイル
- 作画スタイル: 現代的でクリアなアニメ調,細く滑らかな線画
- 色調: パステルカラー基調,温かみのある色彩
- 線画: 細く繊細な線,ハイライトを効果的に使用
- 演出: 桜の花びら,キラキラエフェクト,ソフトフォーカス,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 異世界バトルもの
- ジャンル: 異世界バトルものに最適化した統一スタイル
- 作画スタイル: 劇画調,筋肉質な体型表現,迫力重視
- 色調: 濃い色彩,コントラスト強め,炎や雷などの鮮やかなエフェクト
- 線画: 太く力強い線,影を多用したメリハリのある表現
- 演出: 集中線,爆発エフェクト,スピード線を多用,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### ミステリー
- ジャンル: ミステリーに最適化した統一スタイル
- 作画スタイル: リアル寄り,細密な描写,大人っぽい表現
- 色調: モノトーン基調,深い青や紫,影を効果的に使用
- 線画: 細く繊細な線,陰影を重視した立体感
- 演出: 暗い照明,逆光,不安を煽る構図,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### ビジネス
- ジャンル: ビジネスに最適化した統一スタイル
- 作画スタイル: 現実的,スーツ姿の正確な描写,清潔感重視
- 色調: 落ち着いた色調,グレー・ネイビー・白基調
- 線画: 整った線,クリーンな表現
- 演出: オフィス空間,グラフや資料の描写,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 哲学思想
- ジャンル: 哲学・思想に最適化した統一スタイル
- 作画スタイル: 抽象的表現も含む,象徴的な描写
- 色調: 落ち着いた色調,モノクロ部分も効果的に使用
- 線画: 繊細で思慮深い表現
- 演出: 思考を表現する視覚効果,メタファー的な背景,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 解説教育
- ジャンル: 解説・教育に最適化した統一スタイル
- 作画スタイル: 分かりやすく親しみやすい表現
- 色調: 明るく見やすい色調,重要部分は強調色
- 線画: はっきりとした線,読みやすさ重視
- 演出: 図解,矢印,吹き出しを多用,情報整理重視,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### ホラー
- ジャンル: ホラーに最適化した統一スタイル
- 作画スタイル: 不気味さを強調,歪んだ表現,リアルな恐怖描写
- 色調: 暗い色調,黒・赤・灰色基調,不自然な影
- 線画: 不規則で荒々しい線,ざらついた質感
- 演出: 血しぶき,暗闇,突然の視点変化,恐怖を煽る構図,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### スポーツ
- ジャンル: スポーツに最適化した統一スタイル
- 作画スタイル: 躍動感重視,筋肉や動きの正確な描写
- 色調: 鮮やかで活力ある色彩,汗や光の表現
- 線画: 力強く流れるような線,動きを強調
- 演出: スピード線,汗の飛沫,躍動感のある構図,観客の歓声,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### SF・宇宙
- ジャンル: SF・宇宙に最適化した統一スタイル
- 作画スタイル: 未来的でメカニカル,精密な機械描写
- 色調: メタリック,ネオンカラー,青・銀・黒基調
- 線画: シャープで精密な線,テクノロジー感
- 演出: ホログラム,光の粒子,宇宙空間,未来的UI表示,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 日常コメディ
- ジャンル: 日常コメディに最適化した統一スタイル
- 作画スタイル: デフォルメ表現多用,親しみやすいキャラデザイン
- 色調: 明るくポップな色彩,カラフルで楽しい雰囲気
- 線画: 柔らかく丸みのある線,表情豊かな描写
- 演出: 汗マーク,びっくりマーク,コミカルな効果音,誇張表現,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 時代劇・歴史
- ジャンル: 時代劇・歴史に最適化した統一スタイル
- 作画スタイル: 伝統的な劇画調,時代考証を重視した描写
- 色調: 落ち着いた和の色調,茶・黒・金・朱色基調
- 線画: 太く重厚な線,墨絵風の表現も取り入れる
- 演出: 桜吹雪,刀の軌跡,和風エフェクト,時代背景の細密描写,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### サスペンス・スリラー
- ジャンル: サスペンス・スリラーに最適化した統一スタイル
- 作画スタイル: 緊張感のあるリアル描写,心理的圧迫感
- 色調: 暗めの色調,赤・黒・グレー基調,不安を煽る配色
- 線画: 鋭く緊張感のある線,影を効果的に使用
- 演出: 斜めの構図,クローズアップ,時計や心拍数の視覚化,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### ファンタジー・冒険
- ジャンル: ファンタジー・冒険に最適化した統一スタイル
- 作画スタイル: 幻想的で壮大,魔法や異世界の表現
- 色調: 鮮やかで神秘的,緑・青・金・紫基調
- 線画: 流麗で装飾的な線,ファンタジー要素の細密描写
- 演出: 魔法陣,光の粒子,幻想的な背景,壮大な風景,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### グルメ・料理
- ジャンル: グルメ・料理に最適化した統一スタイル
- 作画スタイル: 料理の質感を重視,美味しそうな表現
- 色調: 暖色系中心,食欲をそそる色彩,艶や湯気の表現
- 線画: 丁寧で繊細な線,料理の細部まで描写
- 演出: 湯気,光沢,断面図,食べる瞬間の表情,キラキラエフェクト,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 青春・学園
- ジャンル: 青春・学園に最適化した統一スタイル
- 作画スタイル: 爽やかで清潔感のある表現,制服の正確な描写
- 色調: 明るく爽やかな色調,青空・白・緑基調
- 線画: クリアで整った線,若々しい表現
- 演出: 青空,校舎,桜,夕焼け,青春を象徴する背景,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### サイバーパンク
- ジャンル: サイバーパンクに最適化した統一スタイル
- 作画スタイル: 退廃的で未来的,ハイテクとローライフの融合
- 色調: ネオン,ピンク・青・紫基調,雨や夜の都市
- 線画: シャープで複雑な線,機械と人体の融合表現
- 演出: ネオンサイン,雨,ホログラム,電脳空間,都市の雑踏,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 投資
- ジャンル: 投資に最適化した統一スタイル
- 作画スタイル: 信頼感と専門性を重視,データやグラフの視覚化
- 色調: 落ち着いた色調,紺・緑・金・グレー基調,成長を示す上昇カラー
- 線画: クリアで正確な線,図表やチャートの明瞭な描写
- 演出: 株価チャート,グラフ,矢印,数字の強調,成功イメージの背景,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 副業
- ジャンル: 副業に最適化した統一スタイル
- 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現
- 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色
- 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現
- 演出: パソコン作業,スマホ,時計,収入の可視化,ステップ図解,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 趣味
- ジャンル: 趣味に最適化した統一スタイル
- 作画スタイル: 楽しさと充実感を重視,趣味の道具や活動の丁寧な描写
- 色調: 温かく楽しい色調,多彩な色彩,趣味に応じた適切な配色
- 線画: 柔らかく親しみやすい線,細部まで愛情を込めた描写
- 演出: キラキラエフェクト,笑顔,充実感の表現,趣味の道具や成果物,必要に応じて集中線,効果線,擬音などのマンガらしい演出

### 論文・学術
- ジャンル: 論文・学術に最適化した統一スタイル
- 作画スタイル: 学術的で正確な表現,研究内容の視覚化重視
- 色調: 知的で落ち着いた色調,白・青・グレー基調,アカデミックな雰囲気
- 線画: 精密で正確な線,図表やデータの明瞭な描写
- 演出: 研究データ,グラフ,数式,引用表示,論理的な構成の可視化

---

## 進捗管理

`progress.json` でパイプラインの進捗を管理する。セッション中断時の再開に使用。

```json
{
  "book_name": "01-worker-positive",
  "source_path": ".company/outputs/ebooks/01-worker-positive/",
  "target_pages": 100,
  "genre": "ビジネス",
  "steps": {
    "1_source": {"status": "done", "completed_at": "2026-03-24T10:00:00"},
    "2_scenario": {"status": "done", "characters": ["健太", "理沙", "教授"]},
    "3_characters": {"status": "done", "images": ["健太.png", "理沙.png", "教授.png"]},
    "4_panels": {"status": "done", "page_count": 100},
    "5_images": {"status": "in_progress", "completed": 40, "total": 100, "failed": [23, 67]},
    "6_cover": {"status": "pending"},
    "7_epub": {"status": "pending"},
    "8_metadata": {"status": "pending"}
  }
}
```

---

## コスト見積もり

以下は **`HANDOFF_MODE=inline`（Codex 内完結）時** の試算。

| 項目 | 枚数（100ページの場合） | 推定コスト |
|------|----------------------|-----------|
| Step 5: ページ画像（1024x1536 high, 平均1.5 iter） | 100 × 1.5 = 150 | ~$31.50 |
| Step 3: キャラリファレンス（9:16） | 2-3 | ~$0.63 |
| Step 6: 表紙（9:16） | 1 | ~$0.21 |
| Step 5-QC: Blind-OCR（gpt-4o vision × 150コール） | 150 | ~$1.50 |
| clean regen フォールバック（約5%/100P） | ~5 | ~$1.05 |
| **合計** | - | **~$34.89/冊** |

※ gpt-image-2 単価: 1024x1536 high = $0.21/枚（OpenAI 公式料金 2026-04-22 時点）
※ gpt-4o OCR: 入力トークン $2.50/1Mトークン換算、画像1枚あたり約 $0.01 相当
※ Pillow 合成フォールバックはローカル処理のためコスト $0

**`HANDOFF_MODE=codex-handoff` 時のコスト**: 同じ OpenAI API（gpt-image-2）を使うため、API 呼び出しコストは inline モードと同額。codex-handoff 特有の追加コストはなし。OCR・Vision-check（gpt-4o）は引き続き Codex 側で実行されるため、その分のコストも同様。

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| ソースフォルダが見つからない | エラー表示し、利用可能なebookフォルダを一覧する |
| APIキー未設定 | `~/.bashrc` から読み込みを試みる。それでも未設定ならセットアップ手順を表示 |
| 画像生成失敗（inline モード） | 失敗ページをログに記録し、バッチ続行。当該ページは次 iter でリトライ、max_iter 超過時は Step 5.5 フォールバックへ |
| EPUB構築エラー | エラー詳細を表示し、画像ファイルの存在を確認 |
| ページ数超過 | Step 2のシナリオを凝縮して再生成 |
| キャラ外見の不一致 | キャラ定義の詳細を強化してプロンプトを再生成 |
| **codex-handoff: DONE.json が出現しない** | Codex CLI の実行状況をユーザーに確認する。スクリプトが異常終了している可能性があるため、ターミナルのエラーメッセージを確認し `--retry-failed` または `--resume-from` で再実行するよう案内する |
| **codex-handoff: DONE.json の status が "failed"** | `generated[]` を `id` で突合して失敗 items を特定し、`step5_regen_iter_N/` または `step3_regen/` を作成して再ハンドオフする |
| **codex-handoff: sha256 不一致** | 転送中の破損の可能性があるため、該当 item を再生成対象として再ハンドオフする |
| **codex-handoff: partial（部分生成）** | `summary.failed > 0` を検出したら不足 items を新 manifest に転記して再ハンドオフする |

## 注意事項

- Windows環境では `python3` ではなく `python` を使用する
- 100枚の画像生成は約50-60分かかる（10枚並列×10バッチ、バッチ間5秒待機）
- OpenAI APIのレート制限に注意: バッチ間に5秒の待機を入れる
- 生成画像の品質にはばらつきがある: ハイブリッドQCループ（Step 5）が自動的にリトライ・フォールバック合成を行うため、手動再生成は原則不要。フォールバック発動ページは progress.json の fallback_pages で確認できる
- 固定レイアウトEPUBはKindle Unlimitedの対象外となる場合がある（KDPの最新規約を確認）
- EPUBの表示確認はKindleプレビューアで必ず行うこと

---

## E2E動作確認手順

### 目的

ハイブリッドQCパイプライン（工程1〜5の本実装成果）が実データで期待通り動作することを確認する。
Step 4 の `コマ別テキストJSON` → Step 5 の Blind-OCR 判定 → Step 5.5 の Pillow 合成フォールバック
という一連のデータフローが途切れなく機能していることを担保する。

---

### 確認項目

#### 1. CSV生成確認（Step 4）

Step 4 完了後に `panels/comicle_output.csv` を開き、以下を確認する。

- ヘッダーが 4 列（`ページ番号,使用するコマ割りテンプレ,漫画作成のプロンプト,コマ別テキストJSON`）になっていること
- テキストを含むページの `コマ別テキストJSON` 列が JSON 配列として格納されていること
  - 例: `[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ", "text": "えっ、本当に？"}]`
- テキストページの `コマ別テキストJSON` 列が空配列 `[]` になっていること
- JSON 内に生のダブルクォート（`"`）が混入していないこと（〝〟に変換済みであること）

**確認コマンド（Python）:**
```python
import csv, json

with open("panels/comicle_output.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, 1):
        raw = row.get("コマ別テキストJSON", "[]")
        # 〝〟を " に戻してパース
        normalized = raw.replace("\u301d", '"').replace("\u301f", '"')
        try:
            items = json.loads(normalized)
            print(f"page {i:03d}: OK ({len(items)} items)")
        except json.JSONDecodeError as e:
            print(f"page {i:03d}: PARSE ERROR - {e}")
```

---

#### 2. OCR判定確認（Step 5 / Step 5-QC）

Step 5 の Blind-OCR が正しく動作していることを確認する。

**確認ステップ:**

1. 生成済みページ画像（例: `pages/page_039_iter_1.png`）を使って Step 5-QC の OCR プロンプトを単体実行する
2. レスポンスが `{"bubbles": [...]}` の JSON 形式で返ること
3. OCR 結果の `detected_text` が CSV の `text` フィールドと一致（または不一致）することを確認する

**重要チェック**: プロンプトに期待テキスト（CSV の `text` フィールド値）が含まれていないこと（confirmation bias 排除）。

**サンプル確認スクリプト:**
```python
import os, json, base64
from openai import OpenAI

API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=API_KEY)

IMAGE_PATH = r"panels/pages/page_039_iter_1.png"

OCR_PROMPT = """添付のマンガ画像を見て、吹き出し（楕円・雲形）と
ナレーションボックス（四角枠）の文字を画像に見える通り正確に読み取ってください。
推測・補完禁止。

出力形式: JSONのみ。
{"bubbles": [{"panel_id": 1, "type": "dialogue"|"narration", "detected_text": "..."}]}"""

with open(IMAGE_PATH, "rb") as f:
    b64img = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="gpt-4o",
    temperature=0.0,
    max_tokens=4096,
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64img}"}},
                {"type": "text", "text": OCR_PROMPT},
            ],
        }
    ],
)
print(json.dumps(json.loads(response.choices[0].message.content), ensure_ascii=False, indent=2))
```

---

#### 3. フィードバック注入確認（Step 5 FAIL 時）

FAIL 時に次 iter のプロンプトに FAIL 内容が反映されることを確認する。

**確認方法:**

1. iter=1 で FAIL したページのログを確認する（例: `[iter 1] FAIL: panel=2 type=dialogue ...`）
2. iter=2 の生成プロンプトに以下のセクションが含まれることを確認する:
   ```
   ◆【前回失敗・最重要】前回生成では以下が正しく描画されませんでした。今回は一字一句正確に描くこと:
   - パネル2のセリフ: 正「...」 ⇔ 前回誤「...」
   ```
3. iter=2 の生成画像で当該パネルのテキストが改善されていることを目視確認する

---

#### 4. フォールバック発動確認（Step 5.5）

`max_iter` 超過時に Step 5.5 が自動発動し `_composited.png` が生成されることを確認する。

**確認ステップ:**

1. `max_iter` を一時的に `1` に設定して難ページ（例: ページ39）を単体実行する
   ```python
   # Step 5 のループ引数で max_iter=1 を指定
   max_iter = 1
   ```
2. iter=1 が FAIL した場合、Step 5.5 が発動して以下のファイルが生成されることを確認する:
   - `pages/page_039_iter_1.png`（監査用。iter=1 の生成画像）
   - `pages/page_039_clean.png`（clean regen 画像。テキストなし）
   - `pages/page_039_composited.png`（Pillow 合成済み最終画像）
3. `pages/page_039_composited.png` を `pages/page_039.png` にリネームして EPUB 入力とする

**目視確認ポイント:**
- `page_039_composited.png` に全セリフ・ナレーションが縦書きで正確に描画されていること
- 吹き出し（白楕円）とナレーションボックス（白四角）が正しい位置に配置されていること
- テキストがコマ領域（`panel_regions.json` の座標）の範囲内に収まっていること
- プロトタイプの `hybrid_run/p39_final_*.png` と比較して品質が同等以上であること

---

#### 5. progress.json確認

`progress.json` が正しく更新されていることを確認する。

**正常系（A路線 PASS の場合）:**
```json
"5_images": {
  "status": "in_progress",
  "completed": 39,
  "total": 100,
  "failed": []
}
```

**フォールバック発動時（B路線）:**
```json
"5_images": {
  "status": "done",
  "completed": 100,
  "total": 100,
  "failed": [],
  "fallback_pages": [39, 52],
  "fallback_count": 2
}
```

- `fallback_pages` リストにフォールバック発動ページが記録されていること
- A路線で最終的に PASS したページは `failed` に記録されないこと（iter 超過したページのみ fallback_pages に記録）

---

#### 6. 下流工程非破壊確認（Step 6 / Step 7 / Step 8）

ハイブリッドQCループの追加が Step 6 以降に影響を与えないことを確認する。

**Step 6（表紙作成）:**
- Step 6 は `pages/` フォルダを参照しないため影響なし
- `KDP出版用/cover.jpg` が正常に生成されることを確認する

**Step 7（EPUB製本）:**
- `panels/pages/page_{NNN}.png`（3桁ゼロ埋め）ファイルが全ページ分存在することを確認する
- フォールバック発動ページは `page_{NNN}_composited.png` → `page_{NNN}.png` へのリネームが完了していること
- `_iter_*.png` / `_clean.png` / `_composited.png` 等の中間ファイルは `page_*.png` のワイルドカードには一致しないため自動的に除外される
- EPUB 生成スクリプトが `glob("page_*.png")` で正しい枚数を収集できることを確認する

**Step 8（メタデータ）:**
- Step 8 は画像ファイルを参照しないため影響なし
- `KDP出版用/書籍情報.md` / `ジャンル・キーワード.md` / `書籍紹介文_HTML.html` が正常生成されることを確認する

---

#### 7. Vision-check 単体動作確認

**確認ステップ:**

1. セリフなしページ（例: page_002 登場人物紹介ページ）を対象として、キャラを1人意図的に欠落させた画像を用意する
   - 欠落させ方: 例えば山田課長の画像スロットを空欄またはテキスト枠のみにした画像を用意する
2. Vision-check を単体実行して `vision_check()` 関数を呼び出す
3. Vision-check が FAIL を返し、`missing_chars` に欠落キャラ名が含まれることを確認する
4. Step 5 のループで再生成がトリガーされることをログで確認する
   - 期待ログ: `[vision] FAIL: page=002 missing=[山田課長]`
   - 期待ログ: `[iter 2] 再生成開始（Vision-check FAIL: missing=[山田課長]）`

---

#### 8. OCR × Vision-check 独立性確認

**確認ステップ:**

1. セリフありページを1件選び、OCR は PASS するが Vision-check は FAIL になる人工ケースを作成する
   - 例: テキストが正確に描かれているがキャラの1人がテキスト枠のみで描かれていない画像を用意する
2. Step 5 のループで OCR 判定 → Vision-check 判定を順に実行する
3. OCR PASS / Vision-check FAIL のケースでも**ページ全体が FAIL** 判定になることを確認する
   - 期待ログ: `[ocr] iter_1 result=PASS`、`[vision] FAIL: page={NNN} missing=[...]`
   - 期待ログ: `[iter 1] ページ判定: FAIL（OCR=PASS, Vision=FAIL）→ 再生成`

---

#### 9. テキストページの自動スキップ確認

**確認ステップ:**

1. `コマ別テキストJSON` が `[]` のテキストページ（画像生成スキップ対象）を指定して Step 5 を実行する
2. 画像生成・OCR・Vision-check すべてがスキップされ、自動 PASS として `progress.json` に記録されることを確認する
   - 期待ログ: `[skip] page={NNN}: テキストページ（画像生成スキップ済み）→ 自動 PASS`

---

### 合格基準

以下をすべて満たした場合に E2E 確認完了とする。

| 確認項目 | 合格条件 |
|---|---|
| CSV生成 | `コマ別テキストJSON` 列が全ページで有効な JSON（または空配列） |
| OCR判定 | Blind-OCR が期待テキストなしで正しく読み取り PASS/FAIL を判定 |
| フィードバック注入 | FAIL 時に `◆【前回失敗・最重要】` セクションが次 iter のプロンプトに含まれる |
| フォールバック発動 | max_iter 超過時に `_composited.png` が生成される |
| progress.json | `fallback_pages` / `fallback_reasons` / `vision_check_failed_pages` が記録され、EPUB Step 7 で参照可能な状態 |
| ファイル命名 | 全ページが `pages/page_{NNN}.png` として揃っている（中間ファイルは除外） |
| EPUB生成 | Step 7 が変更なく動作し、正常な EPUB が出力される |
| KDPメタデータ | Step 8 が変更なく動作し、書籍情報・紹介文が出力される |
| 日本語テキスト | 全ページのセリフ・ナレーションが Blind-OCR PASS または Pillow 合成で 100% 正確 |
| Vision-check 単体動作 | セリフなしページでキャラ欠落を Vision-check が FAIL 検出し再生成ループが発動する |
| OCR × Vision-check 独立性 | OCR PASS / Vision-check FAIL のケースでもページ全体が FAIL 判定になる |
| テキストページスキップ | `コマ別テキストJSON == []` のページで OCR・Vision-check 両方スキップ・自動 PASS になる |
