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

- **`HANDOFF_MODE=inline`**（デフォルト・従来動作）: Claude Code が OpenAI API を直接呼び出す
- **`HANDOFF_MODE=codex-handoff`**: Claude が `.company/codex/queue/<job-id>/` にバンドル（manifest.json + characters/ + gen_manga_bundle.py + TASK.md）を 1 回投入するだけで、Step 5（本文全ページ）と Step 6（表紙）が **Codex 側で QC ループ込みで自律完走**する。Claude の介在は queue 投入時と done/ 受け取り時の 2 回のみ（fire-and-forget 方式）

モード切替はユーザー指示で決定する。スキル開始時にモードを確認し、以降の Step 5 / Step 6 で同じモードを貫く。
Step 3（キャラデザイン）は HANDOFF_MODE に関わらず常に Claude Code が inline で実行する。

ハンドオフ仕様の詳細: `.company/codex/_spec/SPEC.md`

---

## 画像生成の絶対ルール

- **全ステップ共通**: 画像生成時は必ず「日本のアニメ・マンガ調イラスト」で生成すること
- 実写風・フォトリアル風の画像は禁止
- プロンプトの冒頭に必ず「◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。」を含めること
- これはキャラクターデザイン（Step 3）、ページ画像（Step 5）、表紙（Step 6）すべてに適用する

## 画像フォーマット

- **Step 5 本文ページ画像はPNG形式（.png）で保存する**（gpt-image-2 は b64_json で PNG を返すため、再エンコードによる品質劣化を避ける）
- **Step 6 表紙も PNG のまま保存する**（Pillow 等の再エンコードは使わない。KDP は PNG 表紙も受理する）
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
│       └── cover.png
├── vol2/                           # 第2巻
│   ├── panels/
│   │   └── comicle_output.csv
│   ├── pages/
│   │   ├── page_001.png ... page_NNN.png
│   └── KDP出版用/
│       ├── {タイトル} 第2巻.epub
│       └── cover.png
├── ...
└── progress.json
```

### 単巻の出力ディレクトリ構成

```
.company/outputs/ebooks-manga/{book-name}/
├── project.md
├── KDP出版用/
│   ├── {タイトル}.epub
│   ├── cover.png
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

以下のペルソナと指示に基づいて、Claudeがマンガ用シナリオを作成する。

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

> Step 3 は HANDOFF_MODE に関わらず常に Claude Code が inline で実行する（キャラ参照画像は Step 5-A で queue/<job-id>/characters/ にコピーして Codex に渡す）。
> フロー: 3-1 → 3-2-A（直接生成）→ 3-3 ユーザー確認

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

#### 3-1b. 場面別服装ルールの定義（outfit_id 参照方式）

キャラクターの服装は場面（シーン）に応じて変化させる。ストーリーの状況に合った服装を設定し、**同じシーン内ではページが変わっても服装を統一する**。

服装管理は `character_defs.json` に `outfit_presets` オブジェクトを追加する方式を使用する。CSV側は `outfit_id` 列でプリセットを参照し、`gen_manga_bundle.py` 等が `character_defs.json` を読んで description を展開する。

##### outfit_presets の仕様

**outfit_id の命名規則**: `{キャラ名snake_case}_{シーン略称}`（例: `misaki_casual`, `misaki_work_home`）

**1キャラあたり2〜4プリセット推奨**（多すぎると管理コスト増）

**各プリセットのフィールド**: `character`（キャラ名）、`description`（服装詳細文字列）、`scenes`（適用シーン例の配列）

**character_defs.json の拡張例:**
```json
{
  "キャラ定義（既存）": "...",
  "outfit_presets": {
    "misaki_casual": {
      "character": "ミサキ",
      "description": "ボーダー柄（白と紺）のカットソーにデニムパンツ、白いスニーカー（自宅・外出の普段着）",
      "scenes": ["自宅", "外出", "カフェ", "公園"]
    },
    "misaki_work_home": {
      "character": "ミサキ",
      "description": "グレーのスウェット上下、素足（在宅作業・深夜集中タイム）",
      "scenes": ["在宅作業", "深夜", "早朝"]
    }
  }
}
```

**CSVでの服装指定ルール:**
1. CSV の `outfit_id` 列（5列目）に、そのページで適用するプリセットIDを記載する（例: `misaki_casual`）
2. **同じシーン（場面転換がないページ連続）では同じ outfit_id を維持する**
3. 場面が変わったら（時間帯・場所の変化）適切な outfit_id に切り替える
4. 夜のシーンで部屋着/パジャマ → 翌朝のシーンで普段着、のように自然に遷移させる
5. テキストページの `outfit_id` は空文字 `""` を格納する

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

Step 3 は HANDOFF_MODE に関わらず常に Claude Code が inline で実行する。このブロックは参照不要。
Step 5-A のバンドル投入時に、`manuscript/characters/` の生成済み PNG を `queue/<job-id>/characters/` にコピーして Codex に渡す。

**3-2-C: 受け取りと後処理:**

inline 生成のため不要。生成完了後そのまま 3-3 ユーザー確認へ進む。

#### 3-3. ユーザー確認
- 生成されたキャラクター画像をReadツールで表示する
- ユーザーの承認を得てから次のステップへ進む
- 不満があれば外見設定を修正して再生成する

---

### Step 4: コマ割りCSV作成

**重要: 既存の `generate_comicle_csv.py` は使用しない。Claude自身がCSVを直接生成する。**

シナリオ + キャラクター定義 + 作画設定をもとに、コミクル用CSVを生成する。

#### CSV仕様
- **ヘッダー**: `ページ番号,使用するコマ割りテンプレ,漫画作成のプロンプト,コマ別テキストJSON,outfit_id`
- **目標ページ数**: 入力で指定された値（デフォルト100）
- **出力**: `panels/comicle_output.csv`

#### コマ別テキストJSON 仕様

4列目 `コマ別テキストJSON` には、後工程の Blind-OCR 比較が期待テキストを
直接参照できるよう、ページ内の全セリフ・ナレーションを JSON 配列として格納する。

5列目 `outfit_id` には、そのページで適用する服装プリセットIDを格納する。
テキストページは空文字 `""` を格納する（`gen_manga_bundle.py` 等が `character_defs.json` の
`outfit_presets` を参照して description を展開する）。

**設計の注意（重要）**: この列は画像生成（Gemini）には渡さない。
OCR 判定だけが参照する。画像生成プロンプト（3列目）と内容が重複するが、
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
| `panel_id` | 整数 | 1 以上の整数 | コマ番号（読み順：右→左 / 上→下の順に採番） |
| `type` | 文字列 | `"dialogue"` または `"narration"` のみ | セリフ・吹き出しは `"dialogue"`、ナレーションボックスは `"narration"` |
| `speaker` | 文字列 or null | キャラ名文字列 / `null` | `"dialogue"` 時は発話者名（例: `"ミサキ"`）、`"narration"` 時は必ず `null` |
| `text` | 文字列 | — | プロンプトの「」内セリフ・ナレーション本文と完全一致する文字列。OCR 比較の基準値。**1コマあたり平均50字程度を目安**（soft limit、超過率10%未満が望ましい） |

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

**テンプレと panel_id の対応:**

| テンプレ | コマ数 | panel_id の値 | 補足 |
|---------|--------|--------------|------|
| テンプレ1 | 1 | 1 | — |
| テンプレ2〜4 | 2 | 1, 2 | 1=上段（または右側）、2=下段（または左側） |
| テンプレ5 | 3 | 1, 2, 3 | 1=上段、2=中段、3=下段 |
| テンプレ6 | 3 | 1, 2, 3 | 1=上段、2=下段右側、3=下段左側 |
| テンプレ7 | 3 | 1, 2, 3 | 1=上段右側、2=上段左側、3=下段 |

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
◆【出力サイズ】2:3
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

#### 1コマあたりの文字数目安（50字 soft limit）

1コマあたりのセリフ＋ナレーション合計は **平均50字程度を目安** とする。

- **hard limit ではない**（長セリフの多少超過は許容する）
- **超過率10%未満**（50字超過コマ数 / 全コマ数 < 10%）を望ましい水準とする
- 1ページあたりのテキスト密度目標（約90文字）と合わせて確認すること
- 50字を大幅に超える長セリフは、自然な切れ目で次コマに分割することを優先する
- 1コマ30字以下の旧 hard limit は廃止（過剰なコマ分割を抑制し、ページ数の自然な圧縮を狙う）

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

#### 後付けページ（必須）

CSVの末尾（本編終了後）に以下の後付けページを必ず以下の順序で含めること:

| 順序 | ページ | テンプレ | 内容 | 全巻 |
|------|--------|---------|------|------|
| 1 | 著者紹介 | テキストページ | 著者プロフィール（肩書き＋経歴＋連絡先） | ✅ |
| 2 | **CTA（固定）** | **画像ページ（固定アセット）** | **`.claude/skills/ebook-to-manga/assets/cta.png` を全巻共通で必ず差し込む** | ✅ |
| 3 | 奥付 | テキストページ（colophon） | 書名／著者／発行所／発行日／著作権表示 | ✅ |

> **CTA画像の固定運用**: CTAページは全巻共通の固定画像（`.claude/skills/ebook-to-manga/assets/cta.png`、1024×1536 PNG）を使用する。CSVには載せず、Step 7（EPUB製本）で著者紹介ページ直後・奥付ページ直前に必ず spine に挿入する。差し替えはこのアセットファイル自体を更新することで全巻に反映される。

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

Blind-OCR 判定と Vision-check を組み合わせた QC ループで全ページのテキスト正確性を高める。
`max_iter` 回連続 FAIL 時は最後の iter 画像をベストエフォートとして採用し、手動レビュー対象として記録する。

- **A路線**: 画像生成 → Blind-OCR → プログラム比較 → PASS なら完了
- **max_iter 超過時**: 最後の iter 画像 `pages/page_{NNN}_iter_{max_iter}.png` を `pages/page_{NNN}.png` にリネームして採用。`progress.json` の `needs_manual_review_pages` / `needs_manual_review_reasons` に記録し、最終レポートで手動確認対象として列挙する。

リファレンス実装: `.company/outputs/ebooks-manga/manga-career-restart/_prototype/hybrid_loop.py`（465行）

> **モード別フロー概要**
>
> - `inline` モード: 各 iter で [A-1] 直接 API 呼び出し → [A-2] Blind-OCR → [A-3] Vision-check → 判定 → PASS or 次 iter / ベストエフォート採用
> - `codex-handoff` モード: Claude が `.company/codex/queue/<job-id>/` にバンドル（Step 5 全ページ + Step 6 表紙）を 1 回投入するだけで完了。[A-1]〜[A-5] を含む QC ループ全体が **Codex 側で自律完走**する。Claude は `done/<job-id>/progress.json` を受け取って後処理するのみ（本セクションのループ疑似コードは inline 専用）。

#### パラメータ

| パラメータ | 既定値 | 説明 |
|---|---|---|
| `max_iter` | `1`（`--qc full` 時の推奨値は `3`） | OCR/Vision-check FAIL 時の再生成試行回数。デフォルト `1` は iter_1 で完結（QC オフ時のシンプルモード前提） |
| バッチサイズ | `10` | 1バッチあたりのページ数（並列実行単位） |
| バッチ間待機 | `5秒` | API レート制限対策 |
| 保存形式 | PNG（無損失） | gpt-image-2 は b64_json で PNG を返す。JPEG 変換なし |
| `--strict-ocr` | `false` | OCR 比較を完全一致モードに固定（fuzzy matching を無効化） |
| `--qc` | `off` | QC モード。`off` / `lite` / `full` の3択（後述） |

#### `--qc` フラグの3モード

| 値 | 動作 | 対応する運用ケース |
|---|---|---|
| `off`（デフォルト） | QC なし。画像生成のみ実行（iter_1 採用）。Blind-OCR・Vision-check ともにスキップ。**`max_iter` の設定値によらず iter_1 で完結する** | 現在の本番運用（iter_1 シンプルモード）。画像品質が安定しており再生成不要なケース |
| `lite` | Vision-check のみ実行。Blind-OCR スキップ。キャラ欠落のみ検出 | キャラ欠落（page_002 山田課長省略事象等）が懸念されるが OCR 厳密性は不要なケース |
| `full` | Blind-OCR（正規化強化・fuzzy matching 対応版）+ Vision-check（緩和版）両方実行 | 高品質が必要な書籍向けの従来 QC（緩和版）。`max_iter=3` 推奨 |

**運用ガイダンス**:
- 通常運用（vol1-4 の本番生成等）: `--qc off` + `max_iter 1`（実質 QC なし）
- キャラ欠落のみ警戒: `--qc lite` + `max_iter 1` または `2`
- 完全品質保証: `--qc full` + `max_iter 3` + `--strict-ocr`（必要に応じて）

`max_iter` の調整目安:
- デフォルト `1`: 現在の本番運用モード（iter_1 シンプルモード、QC オフ前提）。再生成リトライなし
- `2`: `--qc lite` または `--qc full` 利用時の中間設定。1回のリトライ余地を持たせる
- `3`: `--qc full` の高品質モードでの推奨値。OCR/Vision-check FAIL 時に最大2回リトライ
- `max_iter > 3`: 推奨外。コストが大幅増加する割に品質改善の見返りが乏しい

> **注**: `--qc off` 時は max_iter の値に関わらず iter_1 で完結する（QC なしのため
> PASS 条件が常に満たされる）。max_iter=2 以上が意味を持つのは `--qc lite` または
> `--qc full` 使用時のみ。

#### ループフロー（疑似コード）

プロトタイプ `hybrid_loop.py` の `def main()` を仕様化したもの。

```
CSV を読み込み、全ページリストを取得する
# character_defs.json を1回だけロードしてキャッシュ（ページごとに再読み込みしない）
char_defs = load_json("manuscript/characters/character_defs.json")

# QC モード判定
qc_mode = args.qc  # "off" | "lite" | "full"
strict_ocr = args.strict_ocr  # True | False

for page in pages:
    # テキストページ判定（OCR・Vision-check・フォールバック全スキップ）
    if page の コマ別テキストJSON == []:
        画像生成をスキップ（テキストページは生成不要）
        PASS として記録 → 次ページへ

    # A路線: 生成 → QC → 統合判定 ループ
    current_prompt = 元の画像生成プロンプト
    converged = False
    # ページに登場するキャラを抽出（char_defs キャッシュを渡す）
    page_chars = extract_page_chars(page.prompt, char_defs)

    for iter in range(1, max_iter + 1):
        # [A-1] 画像生成（gpt-image-2）— inline モード専用
        # codex-handoff モード時はこの疑似コード全体が Codex 側で完結するため省略
        画像を生成し pages/page_{NNN}_iter_{iter}.png に保存

        # [A-2] Blind-OCR（qc_mode == "full" のときのみ実行）
        # セリフなしページ（コマ別テキストJSON == []）は OCR スキップ（自動 PASS 扱い）
        if qc_mode == "full":
            ocr_verdict = blind_ocr_and_compare(pages/page_{NNN}_iter_{iter}.png, コマ別テキストJSON, strict=strict_ocr)
        else:
            ocr_verdict = PASS  # スキップ時は自動 PASS

        # [A-3] Vision-check（qc_mode == "lite" or "full" のときのみ実行）
        # キャラ名リストは「名前を先に提示した上で1人ずつ YES/NO を返す」設計（確証バイアス排除）
        if qc_mode in ("lite", "full"):
            vision_verdict, missing_chars = vision_check(pages/page_{NNN}_iter_{iter}.png, page_chars)
        else:
            vision_verdict = PASS  # スキップ時は自動 PASS

        # [A-4] 統合判定: qc_mode == "off" のときは無条件 PASS（iter_1 採用）
        # qc_mode != "off" の場合: OCR PASS かつ Vision-check PASS → ページ PASS
        if ocr_verdict == PASS and vision_verdict == PASS:
            pages/page_{NNN}_iter_{iter}.png を pages/page_{NNN}.png としてコピー
            converged = True
            progress.json を更新（このページ完了）
            break

        # [A-5] FAIL 時フィードバック注入（qc_mode != "off" の場合のみ）
        if qc_mode != "off":
            current_prompt = build_feedback_prompt(元のプロンプト, ocr_verdict, vision_verdict, missing_chars)
            # OCR FAIL → ◆【前回失敗・最重要】パネル別の不一致を追記
            # Vision-check FAIL → ◆【前回失敗・最重要】欠落キャラ名をバストアップ・クローズアップ以上のイラストで描くよう追記

    # max_iter 超過時: ベストエフォート採用（案A）
    if not converged:
        最後の iter 画像 pages/page_{NNN}_iter_{max_iter}.png を pages/page_{NNN}.png にリネーム
        progress.json に page_num を needs_manual_review_pages[] に追加
        review_reason = determine_review_reason(ocr_verdict, vision_verdict)
        # review_reason: "ocr_fail" / "vision_fail" / "both_fail"
        progress.json に needs_manual_review_reasons{page_num: review_reason} で記録
        ログに [needs_review] page {NNN}: best-effort accepted (reason=review_reason, missing=[...]) を出力

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
- `SIZE`: `"1024x1536"`（2:3縦長）
- `FILE_PREFIX`: `page_{ページ番号3桁ゼロ埋め}_iter_{iter}` （例: `page_039_iter_1`）
- **保存形式**: PNG（`.png`）。`base64.b64decode(result.data[0].b64_json)` をそのままバイナリ保存する
- **モデル名**: `gpt-image-2`（openai SDK。`client.images.edit` を使用）
- **参照画像**: プロンプト内の `添付の([^\s、,]+?\.png)` から抽出したキャラクターリファレンス PNG を `image=` に渡す

**codex-handoff モード時の Step 5-A（バンドル投入）:**

1. ジョブ ID 生成: `{book_id}_vol{N}_{YYYYMMDD_HHMMSS}`（Step 5 と Step 6 を同一 job-id で扱う）
2. `.company/codex/queue/<job-id>/` を作成
3. `manifest.json` を `task_type: "manga_bundle"` 形式で生成:
   - `items[]` に **全本文ページ** (`type: "page"`) と **表紙** (`type: "cover"`) を含める
   - `qc_policy: {max_iter: 1, qc_mode: "off", ocr_model: "gpt-4o", vision_check: false, strict_ocr: false}`
   - （`--qc full` 時は `{max_iter: 3, qc_mode: "full", ocr_model: "gpt-4o", vision_check: true, strict_ocr: false}` を指定）
   - `cover_config: {cover_ref_character_id: "<主人公キャラID>", size: "1024x1536"}`
4. `manuscript/characters/` の PNG を `queue/<job-id>/characters/` にコピー
5. `panels/comicle_output.csv` を `queue/<job-id>/csv/comicle_output.csv` にコピー
6. `.company/codex/_spec/gen_manga_bundle.py` を `queue/<job-id>/gen_manga_bundle.py` にコピー
7. `.company/codex/_template.md` を流用して `queue/<job-id>/TASK.md` を生成（job-id / book_id / vol を埋め込む）
8. ユーザーに以下を提示:
   ```
   queue/<job-id>/ を配置しました。別ターミナルで以下を実行してください:
     cd .company/codex/queue/<job-id>
     python gen_manga_bundle.py
   完了したら「Codex 完了しました」と教えてください。
   ```

**codex-handoff モード時の Step 5-C（done 受取）:**

> 注: fire-and-forget 方式のため、queue 投入から done 受取までの間 Claude 側の能動操作は不要。
> ユーザーから「Codex 完了しました」通知を受けた時点で以下を実行する。

ユーザーから「Codex 完了しました」の通知を受けたら:

1. `.company/codex/done/<job-id>/progress.json` を読み込む
2. `status` フィールドを確認:
   - `"success"`: 全ページ PASS（ベストエフォート採用含む）
   - `"partial"`: 一部失敗あり（failed 項目を確認）
   - `"failed"`: 大多数失敗（ユーザーに報告して再投入判断）
3. `done/<job-id>/pages/page_{NNN}.png` を書籍側 `panels/pages/page_{NNN}.png` にコピー
4. `done/<job-id>/cover.png` を `KDP出版用/cover.png` にコピー
5. `needs_manual_review_pages[]` が空でない場合、書籍側 `progress.json` に転記 + ユーザーに手動確認を促す
6. 書籍側 `progress.json` の Step 5 / Step 6 を `done` に更新
7. `done/<job-id>/` を `.company/codex/archive/<job-id>/` に移動
8. Step 7（EPUB 化）へ進む

なお、codex-handoff モードでは QC ループ（Blind-OCR・Vision-check・ベストエフォート採用）はすべて Codex 側で実行され、結果が `progress.json` の `needs_manual_review_pages` に反映される。

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

**8. max_iter 超過 → ベストエフォート採用**

`max_iter` 回すべて FAIL した場合（OCR FAIL・Vision-check FAIL どちらの原因でも同様）、
最後の iter 画像 `pages/page_{NNN}_iter_{max_iter}.png` を `pages/page_{NNN}.png` にリネームして
このページの最終成果物として確定する（ベストエフォート採用）。
`progress.json` の `needs_manual_review_pages[]` に当該ページ番号を追加し、
`needs_manual_review_reasons{page_num}` に `"ocr_fail"` / `"vision_fail"` / `"both_fail"` を記録する（→ 進捗管理セクション参照）。
ログに `[needs_review] page {NNN}: best-effort accepted (reason=..., missing=[...])` を出力する。

#### 成果物ファイル命名

| ファイル名パターン | 生成タイミング | EPUB 向け扱い |
|---|---|---|
| `pages/page_{NNN}_iter_{N}.png` | 各 iter の生成画像 | 監査用。PASS した iter の画像は `page_{NNN}.png` にコピー、max_iter 超過時は最後の iter 画像を `page_{NNN}.png` にリネーム |
| `pages/page_{NNN}.png` | Step 5 の最終画像（PASS 時は収束 iter、FAIL 超過時は最後の iter をベストエフォート採用） | Step 7 EPUB 製本が直接参照する |

> **EPUB製本（Step 7）との整合**: Step 7 は `pages/page_{NNN}.png` を収集する。
> この運用により Step 7 の修正は不要になる。

#### 進捗管理

各バッチ完了後に `progress.json` を更新する。

```json
"5_images": {
  "status": "done",
  "completed": 100,
  "total": 100,
  "failed": [],
  "needs_manual_review_pages": [39, 52],
  "needs_manual_review_reasons": {"39": "ocr_fail", "52": "vision_fail"},
  "vision_check_failed_pages": [2, 17],
  "vision_check_pages": 95
}
```

- `failed` 配列: iter 内で最終的に PASS したページは記録しない。iter 超過してベストエフォート採用になったページも最終的に完了するため `failed` には記録しない
- `needs_manual_review_pages`: max_iter 超過によりベストエフォート採用となったページ番号リスト（手動確認が必要なページ）
- `needs_manual_review_reasons`: 手動確認対象ページごとの理由。値は `"ocr_fail"` / `"vision_fail"` / `"both_fail"` のいずれか
- `vision_check_failed_pages`: Vision-check で1回以上 FAIL したページ番号リスト。最終的に PASS したページも記録する（監査用）
- `vision_check_pages`: Vision-check を実施したページ数の集計
- max_iter 超過時は `needs_manual_review_pages[]` にページ番号を追加し、`needs_manual_review_reasons{}` に `"<page>": "ocr_fail"|"vision_fail"|"both_fail"` を記録する（上記フィールド仕様参照）
- ログに `[needs_review] page {NNN}: best-effort accepted (reason={reason}, missing=[キャラ名])` を出力する

#### コスト試算

**3モード別 1ページあたりコスト**:

| モード | 画像生成 | Blind-OCR | Vision-check | 合計 / ページ | 100P 冊あたり |
|---|---|---|---|---|---|
| `--qc off`（simple） | $0.21 | スキップ | スキップ | ~$0.21 | ~$21 |
| `--qc lite` | $0.21 | スキップ | $0.01-$0.02（avg 1-2 iter） | ~$0.22-$0.23 | ~$22-$23 |
| `--qc full`（緩和版） | $0.21〜$0.24（再生成発動時） | $0.01-$0.02（avg 1-2 iter） | $0.01-$0.02（avg 1-2 iter） | ~$0.25-$0.28 | ~$27 |

**前提・根拠**:
- `gpt-image-2`: $0.21/枚（1024x1536, high）
- gpt-4o Vision 単価: 約 $0.005-$0.01/コール（画像 + 短いテキスト）
- `--qc full` の再生成発動率: 緩和版（Vision-check「全身」条件撤廃済み）により 10-20% 想定
- `--qc lite` は Vision-check のみ実行のため OCR コールなし

**max_iter による期待コスト変動**:

| max_iter | --qc lite | --qc full |
|---|---|---|
| 1 | ~$0.22 | ~$0.24 |
| 2 | ~$0.23 | ~$0.26 |
| 3 | ~$0.23（PASS 後即停止） | ~$0.28 |

#### 維持される Step 4 と Step 6 の仕様

**Step 4 との接続（上流）:**
- Step 4 で生成した CSV（`panels/comicle_output.csv`）の `コマ別テキストJSON` 列が
  本ループの Blind-OCR 比較の期待テキスト源になる
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
（コマ領域の切り出し機能は現在未使用。将来の手動レビューツール用に保持。）

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

    # 三点リーダ統一: … (U+2026) / ‥ (U+2025) / ... → ...（ASCII 3文字）
    s = s.replace("…", "...").replace("‥", "...")

    # ダッシュ統一: — (U+2014) / ― (U+2015) → -（ASCII ハイフン）
    # 注: 長音記号 ー (U+30FC) は日本語の音引きとして使われるため対象外
    s = s.replace("—", "-").replace("―", "-")

    # 引用符正規化: 〝 (U+301D) / 〟 (U+301F) / " (U+201C) / " (U+201D) → " (ASCII)
    # 注: 「」『』 は日本語括弧として保持（正規化対象外）
    s = s.replace("〝", '"').replace("〟", '"')
    s = s.replace("“", '"').replace("”", '"')

    # 波ダッシュ統一: 〜 (U+301C) / ～ (U+FF5E) → ~（ASCII チルダ）
    # ※ NFKC で ～ → ~ になるが、〜 (U+301C) は NFKC 対象外なので明示変換
    s = s.replace("〜", "~").replace("～", "~")

    s = re.sub(r"\s+", "", s)              # 空白・改行・タブをすべて除去
    return s
```

NFKC 正規化により全角/半角の揺れを吸収する。さらに三点リーダ・ダッシュ・引用符・
波ダッシュの各種異体字を ASCII に統一し、OCR の軽微な文字種差異を吸収する。
空白・改行除去により縦書きレンダリングの改行差異も吸収する。

> **設計補足 - ダッシュと長音記号の識別について**
> `ー`（U+30FC、カタカナ長音符）はセリフ内で「えーっ」「そーだ」のように使われる。
> ダッシュ（`—`/`―`）はナレーションや区切りで使われる。
> 文字コード上は異なるため、`ー` を統一対象から外し `—` と `―` のみハイフンに寄せる設計とする。

### 正規化例（page_005 実データ相当）

| 種別 | 期待テキスト | OCR 検出テキスト | 正規化前 一致 | 正規化後 一致 |
|---|---|---|---|---|
| 三点リーダ | `そう…なんだ` | `そう...なんだ` | × | ○ |
| ダッシュ | `だから――話を聞いて` | `だから--話を聞いて` | × | ○ |
| 引用符 | `"おはよう"` | `"おはよう"` | × | ○ |
| 波ダッシュ | `えーっと～` | `えーっと〜` | × | ○ |
| キャラ名（完全一致維持） | `ミサキ「行こう」` | `ミサ「行こう」` | × | × （fuzzy 対象外、完全一致必須） |
| 引用符（〝〟系） | `〝こんにちは〟` | `"こんにちは"` | × | ○ |
| 「」括弧（保持） | `「行こう」` | `「行こう」` | ○ | ○ |

**ステップ2: キーによる突き合わせ**
- 突き合わせキー: `(panel_id, type)` のペア
- OCR 結果の `bubbles` 配列を `{(panel_id, type): [detected_text, ...]}` の辞書に変換する
- CSV の `コマ別テキストJSON` 各エントリについて、同じキーの OCR バブルを検索する
- 1コマに同 type が複数ある場合（例: 2人のセリフ）は、未使用の候補の中から最初に
  正規化一致するものを採用する（used セットで重複消費を防ぐ）
- **fuzzy matching の方針**: デフォルトでは Levenshtein 編集距離 2 以内を PASS 扱いとする（OCR の軽微な誤読を吸収）。`--strict-ocr` フラグ指定時は従来の完全一致モードに戻す。
- **キャラ名・固有名詞の完全一致維持**: `character_defs.json` の `name` フィールド値が expected テキストに含まれる場合は fuzzy 対象外とし、完全一致で判定する（誤字を看過しないため）。

> **設計補足 - 距離=2 の根拠**
> - 距離=1: OCR は1文字誤読が頻出するため緩すぎず、軽微なノイズ吸収に必要
> - 距離=2: 「佐藤さん」→「佐藤ざん」（1字）+「佐藤さん。」→「佐藤ざん」（2字、句読点欠落）等、実運用で観測される典型的な誤読範囲をカバー
> - 距離=3 以上: 全く別の単語が一致してしまうリスクが高まる（例: 「ミサキ」と「ササキ」が距離2で一致する境界事例があるため、距離2で打ち止め）
> 距離2 はキャラ名等の重要語句を完全一致モードで保護した上での「セリフ本文の許容上限」として設定している。

**fuzzy matching 参考実装（ピュア Python）:**
```python
def fuzzy_match(detected: str, expected: str, max_distance: int = 2) -> bool:
    """
    編集距離 max_distance 以内で一致と判定する。
    キャラ名・固有名詞を含む場合は呼び出し側で完全一致判定に切り替えること。
    """
    # 簡易実装（Levenshtein 距離）
    if detected == expected:
        return True
    if abs(len(detected) - len(expected)) > max_distance:
        return False
    # DP で編集距離計算（n*m）
    n, m = len(detected), len(expected)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if detected[i-1] == expected[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      # 削除
                dp[i][j-1] + 1,      # 挿入
                dp[i-1][j-1] + cost  # 置換
            )
    return dp[n][m] <= max_distance


def is_match(detected: str, expected: str, char_names: list, strict: bool = False) -> bool:
    """
    OCR 比較の総合判定。
    - キャラ名（char_names）が expected に含まれる場合は完全一致必須
    - strict=True 時は fuzzy 無効
    - それ以外は編集距離 2 以内を PASS
    """
    norm_detected = normalize_text(detected)
    norm_expected = normalize_text(expected)
    contains_char_name = any(name in expected for name in char_names)
    if strict or contains_char_name:
        return norm_detected == norm_expected
    return fuzzy_match(norm_detected, norm_expected, max_distance=2)
```

> **ライブラリ依存について**: `python-Levenshtein` 等の外部ライブラリは使用しない。上記の DP 実装（ピュア Python）で十分な精度を確保できる。

**ステップ3: 判定**
- 各エントリで `is_match(detected, expected, char_names, strict)` を評価する
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
◆【前回失敗・最重要】前回生成では以下のキャラクターが描画されていませんでした。今回は必ずバストアップ・クローズアップ以上のイラストで描いてください（顔のみでも可）: {欠落キャラ名リスト}
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
- **判定基準（緩和後）**: 「全身イラストとして描かれているか」ではなく「バストアップ・クローズアップ・顔のみを含めて画像内に描かれているか」を判定する。
  テキスト枠・名前ラベルのみは引き続き NO とする。

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
指定されたキャラクターがバストアップ・クローズアップを含めて画像内に描かれているかを1人ずつ YES または NO で判定してください（顔だけでも YES とします）。
テキスト枠・名前ラベルのみでキャラクターのイラスト本体が存在しない場合は NO としてください。
イラストが実際に画像内に描かれているかを画像の内容から判断してください。必ず JSON で返してください。
```

**ユーザープロンプト（動的生成）:**
```
以下のマンガ画像に、キャラクター{N}人 [{name_list}] がそれぞれイラストとして描かれているか（バストアップ・クローズアップ・顔のみも YES とします）、
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
        "指定されたキャラクターがバストアップ・クローズアップを含めて画像内に描かれているかを1人ずつ YES または NO で判定してください（顔だけでも YES とします）。"
        "テキスト枠・名前ラベルのみでキャラクターのイラスト本体が存在しない場合は NO としてください。"
        "イラストが実際に画像内に描かれているかを画像の内容から判断してください。必ず JSON で返してください。"
    )
    user_msg = (
        f"以下のマンガ画像に、キャラクター{n}人 [{name_list}] がそれぞれ"
        f"イラストとして描かれているか（バストアップ・クローズアップ・顔のみも YES とします）、1人ずつ YES/NO で答えてください。"
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
    {"char_name": "ミサキ", "result": "YES", "reason": "1段目にバストアップイラストあり"},
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

### Step 6: 表紙作成

マンガ版の書籍表紙を生成する。

> **モード別フロー概要**
> - `inline` モード: 6-A プロンプト構築 → 6-B-inline 直接生成 → 6-C ユーザー確認
> - `codex-handoff` モード: Step 6 表紙は Step 5-A のバンドルに `type: "cover"` の item として統合済みのため、独立した Step 6-A / 6-B / 6-C の操作は不要。Step 5-C（done 受取）の中で表紙 PNG も一括して受け取る。

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
  - step 3: キャラクター配置と背景の生成（2:3アスペクト比）
  - step 4: テキストと装飾要素のレイアウト
  - step 5: キャラクター・背景とテキスト・装飾の統合
```

#### 6-B: 生成実行（モード別）

**inline モード時（`HANDOFF_MODE=inline` またはデフォルト）:**

gpt-image-2 で生成する。主人公キャラのリファレンス画像を `image=` に渡し、`images.edit` を使用する。

```python
import base64, glob, os, re
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
# PNG のまま保存する（KDP は PNG 表紙も受け付けるため、画質劣化を避ける）
img_bytes = base64.b64decode(result.data[0].b64_json)
cover_path = os.path.join(OUTPUT_DIR, "KDP出版用", "cover.png")
os.makedirs(os.path.dirname(cover_path), exist_ok=True)
with open(cover_path, "wb") as f:
    f.write(img_bytes)
```

- サイズ: `size="1024x1536"`（2:3縦長形式）
- 品質: `quality="high"`
- 保存先: `KDP出版用/cover.png`（PNG のまま保存。Pillow 等の再エンコードは使わない）

**codex-handoff モード時（Step 6 全体）:**

Step 6-A のバンドルに表紙 item（`type: "cover"`）を Step 5-A で一括投入済みのため、Step 6-B-codex / 6-C-codex の独立した操作は不要。
`done/<job-id>/cover.png` は Step 5-C（done 受取）の中で `KDP出版用/cover.png` にコピーされる。

もし Step 6 単独で再生成が必要な場合は、新 job-id で `manifest.json` の `items[]` に `type: "cover"` のみ 1 件を含めて投入する（--only-step 6 相当の動作）。

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
  ├── fonts/
  │   ├── NotoSansJP-Regular.otf  (日本語ゴシック・埋め込み)
  │   └── NotoSansJP-Bold.otf
  ├── images/
  │   ├── cover.png
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
目次・あらすじ・コラム・著者紹介・奥付等がこれに該当する。テキストページ用CSSで読みやすくレンダリングする。

**改ページルール（必須）**: 各テキストページは表示行数が**最大20行**に収まるよう要素単位（h2/h3/p/subtitle）で折り返し行数を推定し、20行を超える場合は新しいXHTMLファイル（`page_NNN.xhtml`, `page_NNNb.xhtml`, `page_NNNc.xhtml` ...）に分割する。見出し（h2/h3）が末尾孤立しないよう、次の本文も同ページに入らない場合は見出しごと次ページへ送る orphan 回避を実装する。viewport 1024×1536 + 1.5倍フォントの条件では、p=42pxで1行63px、利用可能高さ約1444pxで20行≈1260pxとなり安全に収まる。

**改ページ実装例**: `C:\tmp\repaginate_vol1.py` を参照（`visual_lines()` で要素別の行数推定、`paginate()` で20行バジェットの貪欲パッキング）。

#### CTA固定ページ（後付け）

著者紹介ページの直後・奥付ページの直前に、全巻共通の固定CTA画像を spine に挿入する。

- **アセット**: `.claude/skills/ebook-to-manga/assets/cta.png`（1024×1536 PNG、全巻共通固定）
- **spine ID**: `page_cta`
- **挿入位置**: `... → page_NNN（著者紹介） → page_cta → page_NNN+1（奥付） → ...`
- **xhtml 生成**: 通常の画像ページと同じ `<div class="page"><img src="../images/page_cta.png" alt="ページ CTA"/></div>`
- **manifest 登録**: `<item id="page_cta" .../>` と `<item id="page_cta-img" href="images/page_cta.png" .../>` の2エントリ

```python
# CTA固定ページの挿入（著者紹介の直後・奥付の直前）
SKILL_DIR = os.path.expanduser("~/.claude/skills/ebook-to-manga")  # または相対パスでスキル位置を解決
CTA_IMAGE = os.path.join(SKILL_DIR, "assets", "cta.png")

# spine 構築時に著者紹介→CTA→奥付の順で追加
# spine.append(("page_NNN_author", "text"))   # 著者紹介
spine.append(("page_cta", "image_cta"))       # CTA固定
# spine.append(("page_NNN_colophon", "text")) # 奥付

# manifest 登録
manifest_items.append('    <item id="page_cta" href="text/page_cta.xhtml" media-type="application/xhtml+xml"/>')
manifest_items.append('    <item id="page_cta-img" href="images/page_cta.png" media-type="image/png"/>')

# EPUB書き込み
with open(CTA_IMAGE, "rb") as f:
    cta_data = f.read()
epub.writestr("OEBPS/images/page_cta.png", cta_data, compress_type=zipfile.ZIP_DEFLATED)
epub.writestr("OEBPS/text/page_cta.xhtml", make_image_xhtml("page_cta", "CTA"), compress_type=zipfile.ZIP_DEFLATED)
```

> **差し替えはアセットを更新するだけ**: CTAデザインを変更したい場合は `.claude/skills/ebook-to-manga/assets/cta.png` を新しい1024×1536 PNGで上書きする。次回以降のEPUBビルドで全巻に自動反映される。

#### フォント埋め込み（必須）

**端末（特にKindle）にインストールされたCJKフォントは中国語字形にフォールバックすることがあるため、
日本語ゴシックフォント（Noto Sans JP）を必ずEPUB内に埋め込むこと。**

- フォント取得元: `https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf`（Bold同様）
- ライセンス: SIL Open Font License（再配布可・商用利用可・KDP出版可）
- EPUB内パス: `OEBPS/fonts/NotoSansJP-{Regular,Bold}.otf`
- ZIP格納時は `ZIP_STORED`（既圧縮のため再圧縮しない）
- `style.css` の `@font-face` で参照、`font-family` の先頭に `"Noto Sans JP"` を指定
- `content.opf` の manifest に `media-type="application/vnd.ms-opentype"` で登録

#### テキストページCSS（標準サイズ）

テキストページのフォントサイズは「画像ページの読みやすさ」と揃えるため以下を標準とする
（オリジナル比1.5倍。さらに調整したい場合は本文・見出しを比例して変更）:

| クラス | 用途 | font-size |
|---|---|---|
| `.text-page` | 本文（目次・コラム・著者紹介等） | 42px |
| `.text-page h2` | 大見出し | 54px |
| `.text-page h3` | 小見出し | 45px |
| `.text-page .subtitle` | サブタイトル・肩書き | 33px |
| `.colophon` | 奥付本文 | 45px |
| `.colophon h2` | 奥付見出し | 54px |

#### EPUB生成スクリプト

```bash
python << 'PYTHON_SCRIPT'
import zipfile
import os
import glob
import uuid
import urllib.request
from datetime import datetime

BOOK_NAME = "{{book-name}}"
TITLE = "マンガでわかる {{元タイトル}}"
AUTHOR = "{{著者名}}"
OUTPUT_DIR = r"{{出力ディレクトリ}}"
PAGES_DIR = os.path.join(OUTPUT_DIR, "panels", "pages")
COVER_PATH = os.path.join(OUTPUT_DIR, "KDP出版用", "cover.png")
EPUB_PATH = os.path.join(OUTPUT_DIR, "KDP出版用", f"{BOOK_NAME}-manga.epub")

# --- Noto Sans JP フォントを取得（キャッシュ） ---
FONT_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "noto-sans-jp")
os.makedirs(FONT_CACHE, exist_ok=True)
FONT_URLS = {
    "NotoSansJP-Regular.otf": "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/NotoSansJP-Regular.otf",
    "NotoSansJP-Bold.otf":    "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/NotoSansJP-Bold.otf",
}
font_paths = {}
for fname, url in FONT_URLS.items():
    fpath = os.path.join(FONT_CACHE, fname)
    if not os.path.exists(fpath) or os.path.getsize(fpath) < 1_000_000:
        urllib.request.urlretrieve(url, fpath)
    font_paths[fname] = fpath

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
# Noto Sans JP を埋め込み、テキストページは1.5倍サイズで読みやすくレンダリング
style_css = """@charset "UTF-8";
@font-face {
  font-family: "Noto Sans JP";
  font-weight: normal;
  font-style: normal;
  src: url("fonts/NotoSansJP-Regular.otf") format("opentype");
}
@font-face {
  font-family: "Noto Sans JP";
  font-weight: bold;
  font-style: normal;
  src: url("fonts/NotoSansJP-Bold.otf") format("opentype");
}
html, body { margin: 0; padding: 0; width: 100%; height: 100%; background-color: #ffffff; }
.page { width: 100%; height: 100%; position: relative; text-align: center; }
.page img { display: block; height: 100%; width: auto; max-width: 100%; margin: 0 auto; }
.text-page {
  padding: 3% 5%;
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
  font-size: 42px;
  line-height: 1.5;
  color: #333;
  box-sizing: border-box;
}
.text-page h2 { font-size: 54px; margin: 0 0 12px 0; border-bottom: 2px solid #ddd; padding-bottom: 6px; }
.text-page h3 { font-size: 45px; margin-top: 14px; margin-bottom: 6px; }
.text-page p { margin: 5px 0; text-indent: 1em; }
.text-page .subtitle { font-size: 33px; color: #666; font-style: italic; margin-bottom: 12px; text-indent: 0; }
.colophon {
  padding: 5% 7%;
  font-family: "Noto Sans JP", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif;
  font-size: 45px;
  line-height: 1.5;
  color: #333;
}
.colophon h2 { font-size: 54px; margin: 14px 0 6px 0; border-bottom: 2px solid #ddd; padding-bottom: 4px; }
.colophon h2:first-child { margin-top: 0; }
.colophon p { margin: 4px 0; text-indent: 0; }
"""

# --- content.opf ---
manifest_items = [
    '    <item id="nav" href="text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
    '    <item id="style" href="style.css" media-type="text/css"/>',
    '    <item id="font-noto-regular" href="fonts/NotoSansJP-Regular.otf" media-type="application/vnd.ms-opentype"/>',
    '    <item id="font-noto-bold" href="fonts/NotoSansJP-Bold.otf" media-type="application/vnd.ms-opentype"/>',
    '    <item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>',
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

    # フォント埋め込み（既圧縮なので ZIP_STORED で格納）
    for fname, fpath in font_paths.items():
        epub.write(fpath, f"OEBPS/fonts/{fname}", compress_type=zipfile.ZIP_STORED)

    # 表紙
    epub.write(COVER_PATH, "OEBPS/images/cover.png", compress_type=zipfile.ZIP_DEFLATED)
    cover_xhtml = make_page_xhtml("../images/cover.png", "表紙")
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

#### Step 5 QCループとの下流互換性

Step 5 の QC ループは `pages/page_{NNN}.png` を最終成果物として出力する。
本 EPUB 生成スクリプトは `glob("page_*.png")` でこのファイル群を収集するため、
ベストエフォート採用ページも含めて追加改修なしで動作する。

| Step 5 出力パターン | EPUB に含まれるファイル | 対応方法 |
|---|---|---|
| PASS ページ | `page_{NNN}.png`（収束 iter からコピー済み） | そのまま収集 |
| ベストエフォート採用ページ | `page_{NNN}.png`（最後の iter 画像からリネーム済み） | そのまま収集 |
| 中間ファイル（`_iter_*`） | `glob` パターンに一致しないため自動除外 | 対応不要 |

> **前提**: Step 5 の責務として、全ページの `page_{NNN}.png` が揃ってから本ステップを実行すること。

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

### モード別 100ページ冊あたりコスト

| QC モード | 画像生成 | OCR | Vision-check | 合計 / 100P 冊 |
|---|---|---|---|---|
| `--qc off`（simple、本番運用デフォルト） | $21.00 | - | - | **~$21** |
| `--qc lite` | $21.00 | - | $1.50-$2.00 | **~$22-$23** |
| `--qc full`（緩和版） | $21.00-$24.00 | $1.50-$2.50 | $1.50-$2.50 | **~$27** |

### 補足
- `gpt-image-2`: $0.21/枚（1024x1536, high）
- gpt-4o Vision: $0.01/コール想定
- `--qc full` の再生成発動率は緩和版で 10-20% 想定（旧版「全身」条件で 30-50% 発動 → 緩和版で大幅減）
- `HANDOFF_MODE=codex-handoff` でも同じ OpenAI API を使うため、画像生成 API コストは inline モードと同額。codex-handoff 時の OCR・Vision-check コストも同様に発生。実測値は `done/<job-id>/progress.json` の `api_cost_estimate` フィールドに記録される。

---

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| ソースフォルダが見つからない | エラー表示し、利用可能なebookフォルダを一覧する |
| APIキー未設定 | `~/.bashrc` から読み込みを試みる。それでも未設定ならセットアップ手順を表示 |
| 画像生成失敗（inline モード） | 失敗ページをログに記録し、バッチ続行。当該ページは次 iter でリトライ、max_iter 超過時はベストエフォート採用 |
| EPUB構築エラー | エラー詳細を表示し、画像ファイルの存在を確認 |
| ページ数超過 | Step 2のシナリオを凝縮して再生成 |
| キャラ外見の不一致 | キャラ定義の詳細を強化してプロンプトを再生成 |
| **codex-handoff: done/<job-id>/progress.json が出現しない** | Codex CLI の実行状況をユーザーに確認する。スクリプトが異常終了している可能性があるため、ターミナルのエラーメッセージを確認し `gen_manga_bundle.py` を再実行するよう案内する。また `OPENAI_API_KEY` が Codex 側ターミナルの環境変数として設定されているか確認する |
| **codex-handoff: progress.json の status が "failed"** | `.company/codex/done/<job-id>/progress.json` の `errors[]` を確認し、ユーザーに通知する。新 job-id で queue に再投入するか手動対応を促す |
| **codex-handoff: needs_manual_review_pages が多数** | ユーザーに該当ページ番号リストを提示して手動確認を案内する。再生成が必要な場合は新 job-id で該当ページのみを manifest に含めて再投入する |
| **codex-handoff: partial（部分生成）** | `progress.json` の `status: "partial"` を検出したら不足 items を確認し、ユーザーに通知する。新 job-id で不足分のみを manifest に含めて再投入する |

## 注意事項

- Windows環境では `python3` ではなく `python` を使用する
- 100枚の画像生成は約50-60分かかる（10枚並列×10バッチ、バッチ間5秒待機）
- OpenAI APIのレート制限に注意: バッチ間に5秒の待機を入れる
- 生成画像の品質にはばらつきがある: QCループ（Step 5）が自動的にリトライを行う。max_iter 超過ページはベストエフォート採用となり、progress.json の needs_manual_review_pages で確認できる
- 固定レイアウトEPUBはKindle Unlimitedの対象外となる場合がある（KDPの最新規約を確認）
- EPUBの表示確認はKindleプレビューアで必ず行うこと

---

## E2E動作確認手順

### 目的

`ebook-to-manga` スキルの3つの QC モード（`--qc off`/`lite`/`full`）と OCR 緩和、Pillow 合成非発動を検証する。

### 確認項目（4ケース）

#### ケース1: iter_1 シンプルモード基本動作（`--qc off`）

**確認内容**: `--qc off` で画像生成のみが完走し、QC API（OCR/Vision-check）が一切呼ばれないこと。これが現在の本番運用モード（iter_1 シンプルモード）である。

**手順**:
1. テスト用 ebook（vol1 manuscript の page_001-005）を `_e2e_test/` にコピー
2. Step 5 を `--qc off` + `max_iter 1` で実行
   ```bash
   python scripts/run_step5.py --source _e2e_test/ --qc off --max-iter 1
   ```
3. 確認:
   - `pages/page_001.png` 〜 `pages/page_005.png` が生成されていること
   - `progress.json` の `vision_check_pages` が `0` であること
   - `progress.json` の `ocr_pages` が `0` であること
   - 標準出力ログに `[ocr]` `[vision]` プレフィックスのログが含まれないこと

**期待結果**: 5枚の PNG が iter_1 のままで `pages/` に確定。QC API コスト = $0。

---

#### ケース2: lite モードでのキャラ欠落検出（`--qc lite`）

**確認内容**: `--qc lite` で page_002 相当（複数キャラ登場ページ）のキャラ欠落を Vision-check が検出し、FAIL → 再生成 → PASS のループが発動すること。

**手順**:
1. テスト用 ebook の page_002 に「ミサキ・ケンタ・山田課長」3人登場を指定
2. Step 5 を `--qc lite` + `max_iter 2` で実行
   ```bash
   python scripts/run_step5.py --source _e2e_test/ --qc lite --max-iter 2
   ```
3. 人工的にキャラ欠落を起こすため、テスト用フィクスチャを作成:
   ```bash
   # _e2e_test/manuscript/csv/page_002.csv の「漫画作成のプロンプト」列をバックアップ後、
   # 「山田課長」「添付の山田課長.png」記述を sed で一時除去
   cp _e2e_test/manuscript/csv/page_002.csv _e2e_test/manuscript/csv/page_002.csv.bak
   sed -i 's/山田課長[、。]*//g; s/添付の山田課長\.png//g' _e2e_test/manuscript/csv/page_002.csv
   ```
   （テスト後は `cp page_002.csv.bak page_002.csv` で復元する）
4. 確認:
   - iter_1 で Vision-check が FAIL を返すこと（`missing_chars=["山田課長"]`）
   - iter_2 で再生成され Vision-check が PASS すること
   - `progress.json` の `vision_check_failed_pages` に page_002 が記録されること
   - `progress.json` の `ocr_pages` が `0`（OCR スキップ済み）であること

**期待結果**: page_002 が iter_2 で確定。Vision-check ログに FAIL → 再生成 → PASS の流れが残る。

---

#### ケース3: OCR 緩和（三点リーダ差異吸収）の単体確認

**確認内容**: `normalize_text()` が三点リーダ・ダッシュ・引用符・波ダッシュの差異を吸収して PASS 判定すること。fuzzy matching が編集距離 2 以内で PASS すること。

**手順**:
1. 単体テストスクリプトを実行
   ```python
   from skills.ebook_to_manga.qc import normalize_text, fuzzy_match, is_match

   # 三点リーダ
   assert normalize_text("そう…なんだ") == normalize_text("そう...なんだ")
   # ダッシュ
   assert normalize_text("だから――話を聞いて") == normalize_text("だから--話を聞いて")
   # 引用符
   assert normalize_text('“おはよう”') == normalize_text('"おはよう"')
   # 波ダッシュ
   assert normalize_text("えーっと～") == normalize_text("えーっと〜")
   # 長音記号は保持
   assert normalize_text("えーっと") != normalize_text("えっと")
   # fuzzy matching（編集距離 1）
   assert fuzzy_match("佐藤さん", "佐藤ざん", max_distance=2) == True
   # キャラ名完全一致モード
   assert is_match("ミサ「行こう」", "ミサキ「行こう」", char_names=["ミサキ", "ケンタ"]) == False
   # strict モード
   assert is_match("そう…なんだ", "そう...なんだ", char_names=[], strict=True) == False
   print("[ocr-test] all assertions passed")
   ```
2. 全アサーションが PASS することを確認

**期待結果**: 標準出力に `[ocr-test] all assertions passed` が出力される。

---

#### ケース4: Pillow 合成が発動しない回帰確認

**確認内容**: skill.md と関連スクリプトに Pillow 合成フォールバック関連の記述・コードが存在しないこと。

**手順**:
1. skill.md 全文に対して以下の grep を実行し、ヒットしないことを確認:
   ```bash
   grep -n "Step 5\.5" .claude/skills/ebook-to-manga/skill.md      # → 0件
   grep -n "Pillow.*合成|Pillow.*オーバーレイ|Pillow.*fallback" .claude/skills/ebook-to-manga/skill.md  # → 0件
   grep -n "fallback_pages|fallback_reasons|fallback_count" .claude/skills/ebook-to-manga/skill.md  # → 0件
   grep -n "panel_regions\.json" .claude/skills/ebook-to-manga/skill.md  # → 0件
   ```
2. 関連スクリプト（`hybrid_loop.py` 等）にも `from PIL import` / `Image.open` 等の合成系コードが存在しないことを目視確認

**期待結果**: 上記 grep がすべて 0 件。Pillow 合成は完全撤廃済み。

---

### 最終チェックリスト

- [ ] ケース1（`--qc off` シンプルモード）: 画像5枚生成 + QC API 0コール
- [ ] ケース2（`--qc lite` キャラ欠落検出）: page_002 で FAIL → 再生成 → PASS
- [ ] ケース3（OCR緩和単体テスト）: 全アサーション PASS
- [ ] ケース4（Pillow 合成非発動回帰）: 全 grep 0件
- [ ] `progress.json` フィールド: `vision_check_pages` / `vision_check_failed_pages` / `needs_manual_review_pages` / `ocr_pages`（廃止: `fallback_pages` 等）
