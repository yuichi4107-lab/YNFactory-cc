---
name: ebook-deji
description: 電子書籍＋漫画化を完全自動で一気通貫生成するスキル。テーマを入力するだけで、リサーチ→原稿25,000字→挿絵約30枚→漫画化（20ページ）→最終DOCX統合まで確認なしで全自動実行。画像生成はGemini API使用。漫画はストーリー→シナリオ→コマ割り→CSV→API生成の4ステップで制作。DOCX出力はA5・Meiryo・赤太字・句点改行・漫画最大幅・空白ページなし。
---

# eBook + Manga Auto Creator（ebook-deji）

テーマ入力 → リサーチ → 原稿（25,000字）→ 挿絵（Gemini API）→ 漫画化 → 最終DOCX を**確認なし**で一気に生成。

## 最重要ルール: 完全自動進行

**Phase 0（初回セットアップ）でのみユーザー操作が必要。それ以降は一切の確認・許可なしで完走する。**

- 画像生成（Gemini API呼び出し）→ 自動
- 次の画像へ → 自動
- エラー時のリトライ → 自動
- 停止が必要なのは: **APIレート制限が解除されない場合** または **APIキーが無効な場合** のみ

## カラーモード設定（Phase 0で選択）

Phase 0でユーザーに「フルカラー」か「白黒（モノクロ）」かを選択してもらう。
選択に応じて、**すべての漫画プロンプトにカラー指示を必ず含める**。

| モード | プロンプトに追加する指示 |
|--------|----------------------|
| **フルカラー** | `IMPORTANT: This must be a FULL COLOR illustration. Use vibrant, rich colors throughout. Do NOT use grayscale, black-and-white, or monochrome. Every panel must have colorful backgrounds, colored clothing, colored hair, and colored skin tones. The final image must be fully colored like a modern digital manga/webtoon.` |
| **白黒** | `IMPORTANT: This must be a BLACK AND WHITE manga illustration. Use only grayscale tones, screen tones, and ink-style shading. No color at all. Traditional manga monochrome aesthetic.` |

**★ カラー指示は省略厳禁**: 指示がないとAIが勝手に白黒で出力することがあるため、**毎ページのプロンプトに必ず上記指示を含める**。

## 全体フロー（Phase 0以降は確認なし全自動）

```
Phase 0: 初回セットアップ（★ ここだけユーザー操作）
   │  テーマ入力 + Gemini APIキー確認（.env）
   │  キャラ参照・コマ割りテンプレフォルダ確認
   ▼
Phase 1: 参考資料の受け取り
   │  テーマ・資料を整理 → 確認なしで即Phase 2へ
   ▼
Phase 2: リサーチ
   │  5層リサーチ（YouTube/note/SNS/競合/読者の声）
   │  → 確認なしで即Phase 3へ
   ▼
Phase 3: 構成設計
   │  目次 + ビジュアルトーン設定 → 確認なしで即Phase 4へ
   ▼
Phase 4: 原稿執筆
   │  25,000字 + 画像タグ挿入 → 確認なしで即Phase 5へ
   ▼
Phase 5: 挿絵プロンプト生成
   │  manuscript_raw.md の画像タグ → Gemini API用プロンプトに変換
   │  → 確認なしで即Phase 5bへ
   ▼
Phase 5b: 挿絵画像生成（Gemini API / nanobanana-deji）
   │  画像1枚ずつ Gemini API で生成・保存
   │  → manuscript.md を生成し、確認なしで即Phase 6へ
   ▼
Phase 6: 中間DOCX変換
   │  Pandoc + 後処理 → 確認なしで即Phase 7へ
   ▼
Phase 7: 漫画化
   │  7a: 漫画ストーリー作成
   │  7b: 漫画シナリオ作成（コマ描写・セリフ・オノマトペ）
   │  7c: コマ割り割り当て（テンプレフォルダから最適テンプレを選択）
   │  7d: CSV作成（ページ番号・テンプレ名・プロンプトの3列CSV）
   │  7e: 画像生成（CSVを読み取り、Gemini APIで各ページを生成）
   │  → 確認なしで即Phase 8へ
   ▼
Phase 8: 最終DOCX統合
   │  原稿 + 挿絵 + 漫画 → final_book.docx（python-docx直接生成）
   ▼
完成！
```

## 生成物の仕様

| 項目 | 内容 |
|------|------|
| 総文字数 | 約25,000字 |
| 構成 | はじめに + 5章 + おわりに |
| 挿絵画像 | 約36枚（章ヘッダー + 本文中図解）1200x800px横長 |
| 漫画ページ | 20ページ（各章4ページ）896x1200px縦長 |
| 最終出力 | final_book.docx（A5・Meiryo・赤太字・漫画最大幅） |

## 出力先

```
output/{slug}/
├── manuscript.md             # Markdown版（挿絵画像リンク付き）
├── manuscript_raw.md         # 中間ファイル（画像タグ付き原稿）
├── manuscript.docx           # 原稿+挿絵のみのWord（中間成果物）
├── research.md               # リサーチ結果
├── image_prompts.md          # 挿絵プロンプト集
├── images/                   # 挿絵画像（Gemini APIで生成）
├── story_structure.md        # 漫画ストーリー構成
├── manga_scenario.md         # 漫画シナリオ
├── panel_templates.md        # テンプレート割り当て表
├── manga_pages.csv           # 画像生成用CSV
├── generate_manga.py         # 漫画画像生成スクリプト
├── panels/                   # 漫画ページ画像
├── build_final.py            # 最終DOCX生成スクリプト
└── final_book.docx           # ★ 最終成果物
```

---

## Phase 0: 初回セットアップ（★ ユーザー操作はここだけ）

### チェックリスト

```
□ 1. テーマ・参考資料の入力
□ 2. Gemini APIキー確認（プロジェクトルートの .env）
□ 3. キャラ参照フォルダ確認（キャラ参照/）
□ 4. コマ割りテンプレフォルダ確認（コマ割りテンプレ (896 x 1200 px)/）
```

### 0-1. テーマ入力

ユーザーに以下を聞く:

```
以下を教えてください：
1. テーマ（書籍タイトル案）:
2. 参考資料（ファイル/URL/テキスト）:
3. 特に強調したいポイント（あれば）:
4. 想定読者（あれば）:
5. 漫画のカラーモード: フルカラー / 白黒（デフォルト: フルカラー）
6. 各章の漫画ページ数: 数値で指定（デフォルト: 4ページ／章）
7. 漫画の配置位置: 章の最初 / 章末（デフォルト: 章末）
```

### 0-2. Gemini APIキー確認

```bash
ls "c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式/.env" 2>/dev/null && echo "✅ .envファイルあり" || echo "❌ .envファイルが見つかりません"
```

**キーがない場合**: `.env` に `GEMINI_API_KEY=AIzaSy...` を記述するよう案内する。

### 0-3. フォルダ確認

```bash
ls "c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式/キャラ参照/"
ls "c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式/コマ割りテンプレ (896 x 1200 px)/"
```

**全て確認できたら、以降は一切の確認なしで Phase 1 → Phase 8 まで自動進行する。**

---

## Phase 1: 参考資料の受け取り

Phase 0で受け取ったテーマ・資料を整理し、**確認なしで即Phase 2へ進む**。

| 形式 | 処理方法 |
|------|----------|
| ファイル | Read ツールで読み込み |
| URL | WebFetch で内容取得 |
| テキスト | そのまま使用 |

---

## Phase 2: 深層リサーチ

### 5層リサーチ（すべて実行）

| Layer | 対象 | 手法 |
|-------|------|------|
| 1 | YouTube専門家 | WebSearch → WebFetch |
| 2 | note専門家記事 | WebSearch → WebFetch |
| 3 | SNS/ショート動画トレンド | WebSearch |
| 4 | 市場・競合・書籍分析 | WebSearch → WebFetch |
| 5 | 読者の悩み・ニーズ | WebSearch → WebFetch |

結果を `output/{slug}/research.md` に保存 → **確認なしで即Phase 3へ**

---

## Phase 3: 構成設計（確認なし・自動進行）

1. 参考資料 + リサーチ結果から目次を自動生成
2. ビジュアルトーン設定（メインカラー、サブカラー、アクセントカラー）
3. **確認なしで即Phase 4へ**

### 目次構成

```
はじめに（1,200〜1,500字）
第1章〜第5章（各4,000〜5,000字）
おわりに（1,200〜1,500字）
```

---

## Phase 4: 原稿執筆

### 執筆ルール

- **総文字数**: 約25,000字
- **文体**: です・ます調で統一
- **画像タグ**: `<!-- [HEADER_IMAGE: ...] -->` / `<!-- [INLINE_IMAGE: ...] -->` を挿入
- **改ページ**: 各章・節の前に `\newpage`
- **表・コードブロック・ASCII図 禁止**（図解画像タグで表現）

### テキスト強調ルール（★必須・DOCXで赤太字に自動変換される）

以下のルールで `**...**` を積極的に使うこと。数値・キーワード・結論文は必ずマーク。

| 使う場面 | 例 |
|---------|-----|
| 重要な数値・パーセント | `**印税70%**`、`**3日間**`、`**800円**` |
| 章や節の核心キーワード | `**Claude Code**`、`**リスト集客**` |
| 結論・まとめの文末 | `**これが最大の強みです。**` |
| 読者への問いかけ・CTA | `**今すぐ始めてください。**` |

**目安**: 1段落に1〜2箇所。多くても3箇所まで。

#### ★ 太字の記号ルール（違反厳禁）

`**...**` の**内側**に `「」『』（）【】` などの括弧を含めてはならない。
括弧が内側にあると Markdown パーサーが太字と認識せず、アスタリスクがそのまま表示されてしまう。

```
❌ 悪い例（アスタリスクが残る）
**「Claude Code」**を使えば
**（印税70%）**という驚異的な

✅ 良い例（太字が正しく反映される）
**Claude Code**を使えば
**印税70%**という驚異的な
**リスト集客**が可能になります。
```

ルール:
- `**` の内側に括弧類（`「」『』（）【】`）を入れない
- 括弧ごと強調したい場合は、括弧を外に出して中のテキストだけを `**` で囲む

### 画像タグの挿入ルール

#### 章ヘッダー図解（各章の冒頭）
```
<!-- [HEADER_IMAGE: pattern={パターン名} | title={章タイトル} | elements={主要トピック} | description={補足}] -->
```

#### 本文中図解（各 `###` ごとに最低1枚）
```
<!-- [INLINE_IMAGE: pattern={パターン名} | title={図解タイトル} | elements={要素1,要素2,...} | description={補足}] -->
```

### 図解パターン（26種類）

| カテゴリ | パターン |
|---------|---------|
| 構造・分類 | tree, pyramid, layers, honeycomb, group |
| 流れ・変化 | flow-horizontal, flow-vertical, cycle, stairs, gantt |
| 比較・分析 | before-after, matrix, comparison-table, scale-circles, concentric, venn |
| 関係・論理 | network, radial, triangle, formula, map |
| 簡易・リスト | list-vertical, list-horizontal, list-dense |
| 特別 | illustration |

完成した原稿を `output/{slug}/manuscript_raw.md` に保存 → **確認なしで即Phase 5へ**

---

## Phase 5: 挿絵プロンプト生成

### 手順

1. `manuscript_raw.md` から全画像タグを抽出
2. 各タグを**Gemini API用プロンプト**に変換
3. `output/{slug}/image_prompts.md` に一括出力
4. **確認なしで即Phase 5bへ**

### 画像タグ → Gemini APIプロンプト変換ルール

#### 共通スタイルヘッダー（ファイル冒頭に記載）

```
共通スタイル: All images must use the SAME consistent visual style — clean flat design,
soft pastel colors, rounded shapes, modern Japanese ebook infographic aesthetic.
Color palette: primary {メインカラー}, accent {アクセントカラー}, supporting {サブカラー}.
Background: white or very light gray. Landscape orientation (3:2 ratio).
```

#### 変換形式

```markdown
=== IMAGE {N} ===
Output filename: {chX_header|chX_imgY}.png

{パターンに応じた英語プロンプト}
Japanese text elements: "{日本語テキスト}" — must be legible and well-integrated.
STYLE: {パターン固有のスタイル指示}. Landscape (3:2).
```

**日本語テキストの扱い（★最重要・違反厳禁）:**
- elements内の日本語は**絶対に英語に翻訳しない**
- プロンプト本体は英語で書いてよいが、表示テキストは日本語のまま `text reads "日本語"` の形式で埋め込む
- title も日本語のまま `Title text reads "日本語タイトル"` で指定
- 送信用プロンプトのヘッダーにも `画像内のテキストは必ず日本語で表記してください。` を追加する

---

## Phase 5b: 挿絵画像生成（Gemini API / nanobanana-deji）

### 手順

1. `image_prompts.md` を読み込む
2. 各 `=== IMAGE N ===` セクションからプロンプトとファイル名を抽出
3. nanobanana-deji の `scripts/generate.py` を使用して1枚ずつ生成
4. `output/{slug}/images/` に保存
5. 全画像生成後、`manuscript_raw.md` の画像タグを画像参照に置換 → `manuscript.md` を生成

### Pythonから呼び出す

```python
import subprocess
from pathlib import Path
from dotenv import load_dotenv

project_root = Path("c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式")
load_dotenv(project_root / ".env")
nanobanana_dir = Path("C:/Users/Tatsu/.claude/skills/nanobanana-deji")

images = [
    {"filename": "ch1_header.png", "prompt": "（プロンプト1）", "aspect": "landscape"},
    # ...
]

for img in images:
    out = (project_root / "output" / "{slug}" / "images" / img["filename"]).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["python", "scripts/generate.py",
         "--prompt", img["prompt"],
         "--output", str(out),
         "--aspect", img.get("aspect", "landscape")],
        cwd=str(nanobanana_dir),
        capture_output=True, text=True
    )
    print(f"[OK] {img['filename']}" if result.returncode == 0 else f"[ERROR] {img['filename']}: {result.stderr}")
```

### 最終原稿の組み立て

タグを画像参照に置換し `manuscript.md` として保存:

```
変換前: <!-- [HEADER_IMAGE: 説明] -->
変換後: ![第1章ヘッダー](images/ch1_header.png){ width=100% }
```

**★ エスケープ禁止**: 画像参照は `![` で始めること。`\![` だとPandocが画像として認識しない。

---

## Phase 6: 中間DOCX変換

### 実行コマンド

```bash
cd "output/{slug}"
pandoc manuscript.md -o manuscript.docx --from markdown --to docx --resource-path=. --standalone --dpi=150
```

### DOCX後処理（句点改行 + 段落間空行 + 画像前後空行）

```python
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy

doc = Document('manuscript.docx')
paras = list(doc.paragraphs)
for para in paras:
    style_name = para.style.name if para.style else ''
    text = para.text.strip()
    if style_name.startswith('Heading'):
        continue
    has_drawing = bool(
        para._element.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline') or
        para._element.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}anchor')
    )
    if has_drawing:
        p_element = para._element
        parent = p_element.getparent()
        idx = list(parent).index(p_element)
        if idx > 0:
            prev = parent[idx - 1]
            prev_runs = prev.findall(qn('w:r'))
            prev_is_empty = (len(prev_runs) == 0 and not any(child.tag.endswith('}drawing') for child in prev.iter()))
            if not prev_is_empty:
                empty_before = OxmlElement('w:p')
                parent.insert(idx, empty_before)
                idx += 1
        empty_after = OxmlElement('w:p')
        parent.insert(idx + 1, empty_after)
        continue
    if not text or style_name == 'Image Caption':
        continue
    if '。' not in text:
        p_element = para._element
        parent = p_element.getparent()
        idx = list(parent).index(p_element)
        parent.insert(idx + 1, OxmlElement('w:p'))
        continue
    sentences = [s for s in text.split('。') if s.strip()]
    if len(sentences) <= 1:
        p_element = para._element
        parent = p_element.getparent()
        idx = list(parent).index(p_element)
        parent.insert(idx + 1, OxmlElement('w:p'))
        continue
    p_element = para._element
    parent = p_element.getparent()
    idx = list(parent).index(p_element)
    new_elements = []
    for i, sentence in enumerate(sentences):
        st = sentence.strip()
        if not st: continue
        if i < len(sentences) - 1 or text.rstrip().endswith('。'):
            st += '。'
        new_p = deepcopy(p_element)
        for r in new_p.findall(qn('w:r')): new_p.remove(r)
        new_r = OxmlElement('w:r')
        if para.runs:
            rPr = para.runs[0]._element.find(qn('w:rPr'))
            if rPr is not None: new_r.append(deepcopy(rPr))
        new_t = OxmlElement('w:t')
        new_t.set(qn('xml:space'), 'preserve')
        new_t.text = st
        new_r.append(new_t)
        new_p.append(new_r)
        new_elements.append(new_p)
    new_elements.append(OxmlElement('w:p'))
    for j, new_el in enumerate(new_elements):
        parent.insert(idx + j, new_el)
    parent.remove(p_element)

doc.save('manuscript.docx')
```

→ **確認なしで即Phase 7へ**

---

## コマ割りテンプレートシステム（Phase 7で使用）

### テンプレートスキャン（Step 7c）

```bash
ls "c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式/コマ割りテンプレ (896 x 1200 px)/"
```

各テンプレ画像をReadツールで読み込み、コマ数とレイアウトを分析してカタログ化する。

### コマ数調整ルール

| コマ数 | 使う場面 | 頻度 |
|-------|---------|------|
| **1コマ** | クライマックス・印象的な場面 | 少なめ（各章0〜2回） |
| **2コマ** | 状況説明＋行動 | 中程度 |
| **3〜4コマ** | 会話、日常、感情変化 | **最も多い** |

### コマ割り選択ルール

- 同じテンプレートが2ページ連続してはならない（最低3ページ間隔）
- 直線分割と斜め分割を交互に混ぜる
- テンプレが見つからない場合はテキスト描写でレイアウト指示する

---

## Phase 7: 漫画化（確認なし全自動）

### Step 7a: 漫画ストーリー作成

`manuscript.md` を読み込み、各章の内容をもとに漫画の物語を構成する。
`output/{slug}/story_structure.md` に保存 → **確認なしで即Step 7bへ**

### Step 7b: 漫画シナリオ作成

各ページ・各コマの詳細シナリオを作成する。

```markdown
## Page 1（暫定：3〜4コマ）

### コマ1
- 情景: {場面・キャラの動き・表情・構図}
- セリフ: {キャラ名}：「{セリフ内容}」
- オノマトペ: {効果音・擬態語}
- 背景・効果: {背景の雰囲気・演出効果}
```

`output/{slug}/manga_scenario.md` に保存 → **確認なしで即Step 7cへ**

### Step 7c: コマ割り割り当て

テンプレフォルダをスキャンし、各ページに最適なテンプレートを割り当てる。
`output/{slug}/panel_templates.md` に保存 → **確認なしで即Step 7dへ**

### Step 7d: CSV作成

**ファイル名**: `output/{slug}/manga_pages.csv`

```csv
"ページ番号","使用するコマ割りテンプレ","漫画作成のプロンプト"
"1","テンプレ8","（プロンプト全文）"
"2","テンプレ5","（プロンプト全文）"
```

各ページのプロンプト構造:

```
◆【絶対最優先】キャラクター外見: {キャラ名A}は添付の{キャラ名A}.png、{キャラ名B}は添付の{キャラ名B}.pngと100%同一の外見で描画
◆【出力サイズ】2:3縦長（896x1200px）
◆【コマ構成】{テンプレ名}: {レイアウト説明（例: 上段横長・中段左右2コマ・下段横長）}
◆【作画】ビジネス漫画向け、清潔感重視、整った線画
◆【カラーモード】{フルカラー or 白黒の指示}
◆【ストーリー】
1コマ目 ({位置}): 情景: {情景} セリフ: {キャラ名}：「{セリフ}」 オノマトペ: {オノマトペ} 背景・効果: {背景効果}
2コマ目 ({位置}): ...
```

CSV生成後 → **確認なしで即Step 7eへ**

### Step 7e: 画像生成（Gemini API）

以下のスクリプトを `output/{slug}/generate_manga.py` として保存して実行:

```python
#!/usr/bin/env python3
"""漫画ページ生成: manga_pages.csv → panels/page_XX.png"""
import csv, os, time
from pathlib import Path
from dotenv import load_dotenv

project_root = Path("c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式")
load_dotenv(project_root / ".env")

from google import genai
from google.genai import types

CHAR_DIR  = project_root / "キャラ参照"
TMPL_DIR  = project_root / "コマ割りテンプレ (896 x 1200 px)"
SLUG      = "{slug}"  # ← 実際のslugに置き換える
OUT_DIR   = project_root / "output" / SLUG / "panels"
CSV_PATH  = project_root / "output" / SLUG / "manga_pages.csv"
MODEL     = "gemini-3.1-flash-image-preview"

OUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_page(page_num: int, template_name: str, prompt: str) -> bool:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY が設定されていません")
        return False

    client = genai.Client(api_key=api_key)
    parts = []

    # キャラ参照画像を添付（フォルダ内の全画像）
    for char_file in sorted(CHAR_DIR.glob("*.png")) + sorted(CHAR_DIR.glob("*.jpg")):
        data = char_file.read_bytes()
        mime = "image/jpeg" if char_file.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        parts.append(types.Part(inline_data=types.Blob(mime_type=mime, data=data)))

    # コマ割りテンプレート画像を添付
    for ext in [".jpg", ".jpeg", ".png"]:
        tmpl_file = TMPL_DIR / f"{template_name}{ext}"
        if tmpl_file.exists():
            data = tmpl_file.read_bytes()
            mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
            parts.append(types.Part(inline_data=types.Blob(mime_type=mime, data=data)))
            break
    else:
        print(f"[WARN] テンプレート画像なし: {template_name}（テキスト指示のみで生成）")

    parts.append(types.Part(text=prompt))

    output_path = OUT_DIR / f"page_{page_num:02d}.png"

    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=parts,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )
            for part in resp.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    output_path.write_bytes(part.inline_data.data)
                    size_kb = output_path.stat().st_size // 1024
                    print(f"[OK] page_{page_num:02d}.png ({size_kb} KB)")
                    return True
            print(f"[WARN] ページ{page_num}: 画像データなし (attempt {attempt+1})")
        except Exception as e:
            err_str = str(e)
            print(f"[ERROR] ページ{page_num} attempt {attempt+1}: {err_str}")
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                wait = 30 * (attempt + 1)
                print(f"  → レート制限: {wait}秒待機...")
                time.sleep(wait)
            elif attempt < 2:
                time.sleep(5)
            else:
                return False
    return False


def main():
    rows = []
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"[INFO] 合計 {len(rows)} ページを生成します")
    print(f"[INFO] 出力先: {OUT_DIR}\n")

    success = 0
    failed = []

    for row in rows:
        page_num = int(row["ページ番号"])
        template = row["使用するコマ割りテンプレ"]
        prompt = row["漫画作成のプロンプト"]

        output_path = OUT_DIR / f"page_{page_num:02d}.png"
        if output_path.exists() and output_path.stat().st_size > 10000:
            print(f"[SKIP] page_{page_num:02d}.png (既存)")
            success += 1
            continue

        print(f"[GEN] ページ{page_num:02d} ({template})...")
        ok = generate_page(page_num, template, prompt)
        if ok:
            success += 1
        else:
            failed.append(page_num)
        time.sleep(3)  # API負荷軽減

    print(f"\n[完了] 成功: {success}/{len(rows)}")
    if failed:
        print(f"[失敗] ページ番号: {failed}")

if __name__ == "__main__":
    main()
```

#### 実行方法

```bash
cd "c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式"
python "output/{slug}/generate_manga.py"
```

→ **確認なしで即Phase 8へ**

---

## Phase 8: 最終DOCX統合（python-docx・確認なし自動）

Pandocは使用しない。python-docxで直接 `final_book.docx` を生成する。

### 仕様（★固定ルール）

| 項目 | 仕様 |
|------|------|
| ページサイズ | A5（14.8×21.0cm） |
| 余白（本文） | 2.0cm |
| 余白（漫画） | 0.5cm（セクション切替） |
| フォント | Meiryo 10.5pt |
| **太字** | 赤太字（#CC2200）に自動変換 |
| 数値+単位 | 赤太字に自動変換（例: 70%、800円、3日、5万円） |
| 句点改行 | 2文以上の段落は「。」で分割して1文1段落 |
| 漫画サイズ | 最大幅5.15inch（高さ安全マージン2.5cm確保） |
| 漫画挿入 | 各章末・空白ページなし |

### build_final.py（自動生成するスクリプト）

`output/{slug}/build_final.py` として保存して実行する。

```python
#!/usr/bin/env python3
"""
Phase 8: 最終DOCX統合
・漫画: セクション切替で余白0.5cm→最大サイズ
・テキスト: **太字**→赤太字、数値自動赤太字、句点改行
"""
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

project_root = Path("c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式")
slug = "{slug}"  # ← 実際のslugに置き換える
base_dir = project_root / "output" / slug
md_path = base_dir / "manuscript.md"
panels_dir = base_dir / "panels"
out_path = base_dir / "final_book.docx"

# 章ごとの漫画ページ割り当て（Phase 7dのCSVページ数に合わせて更新）
chapter_manga_pages = {
    1: [1, 2, 3, 4],
    2: [5, 6, 7, 8],
    3: [9, 10, 11, 12],
    4: [13, 14, 15, 16],
    5: [17, 18, 19, 20],
}

NORMAL_MARGIN_CM = 2.0
MANGA_MARGIN_CM  = 0.5
TWIPS_PER_CM     = 566.929

# 漫画ページの画像幅を計算
# 高さ安全マージン2.5cmを確保してはみ出しを防ぐ
_print_w = (14.8 - MANGA_MARGIN_CM * 2) / 2.54          # 5.433 inch（幅上限）
_print_h = (21.0 - MANGA_MARGIN_CM * 2 - 2.5) / 2.54   # 6.89  inch（高さ上限・安全マージン込み）
_ratio   = 896 / 1200                                    # 漫画アスペクト比（幅/高さ）
if _print_w / _ratio <= _print_h:
    MANGA_IMG_WIDTH = _print_w
else:
    MANGA_IMG_WIDTH = _print_h * _ratio  # 高さ制限が有効 → ~5.15inch
print(f"[INFO] 漫画幅: {MANGA_IMG_WIDTH:.3f}inch ({MANGA_IMG_WIDTH*2.54:.1f}cm)")

# 本文ページ幅
CONTENT_IMG_WIDTH = (14.8 - NORMAL_MARGIN_CM * 2) / 2.54  # 4.252 inch

RED_BOLD        = RGBColor(0xCC, 0x22, 0x00)
NUMBER_PATTERN  = re.compile(
    r'\d+(?:[,，]\d+)*(?:\.\d+)?[%％円万千倍冊日件本時間分個人]+'
    r'|\d+(?:[,，]\d+)+'
)

# ----------------------------------------------------------------
# ドキュメント初期化
# ----------------------------------------------------------------
content = md_path.read_text(encoding="utf-8")
lines   = content.split("\n")

doc = Document()
sec = doc.sections[0]
sec.page_width    = Cm(14.8)
sec.page_height   = Cm(21.0)
sec.left_margin   = sec.right_margin  = Cm(NORMAL_MARGIN_CM)
sec.top_margin    = sec.bottom_margin = Cm(NORMAL_MARGIN_CM)

doc.styles['Normal'].font.name = 'Meiryo'
doc.styles['Normal'].font.size = Pt(10.5)

img_pattern = re.compile(r'!\[([^\]]*)\]\(images/([^)]+)\)(\{[^}]*\})?')
ch_pattern  = re.compile(r'^# 第(\d)章')


# ----------------------------------------------------------------
# セクション区切りヘルパー
# ----------------------------------------------------------------
def _make_sectPr(margin_cm):
    """pPrに埋め込むsectPr要素を生成"""
    sectPr = OxmlElement('w:sectPr')
    pgSz = OxmlElement('w:pgSz')
    pgSz.set(qn('w:w'), str(round(14.8 * TWIPS_PER_CM)))
    pgSz.set(qn('w:h'), str(round(21.0 * TWIPS_PER_CM)))
    sectPr.append(pgSz)
    t = round(margin_cm * TWIPS_PER_CM)
    pgMar = OxmlElement('w:pgMar')
    for attr in ('w:top','w:right','w:bottom','w:left'):
        pgMar.set(qn(attr), str(t))
    pgMar.set(qn('w:header'), '0')
    pgMar.set(qn('w:footer'), '0')
    pgMar.set(qn('w:gutter'), '0')
    sectPr.append(pgMar)
    return sectPr

def attach_section_break(para, margin_cm):
    """★ 既存の段落にsectPrを付与（空白段落を追加しない → 空白ページ防止）"""
    pPr = para._element.get_or_add_pPr()
    for existing in pPr.findall(qn('w:sectPr')):
        pPr.remove(existing)
    pPr.append(_make_sectPr(margin_cm))


# ----------------------------------------------------------------
# 見出し追加
# ----------------------------------------------------------------
def add_heading(doc, text, level):
    p = doc.add_heading(text, level=level)
    if not p.runs: return p
    p.runs[0].font.name = 'Meiryo'
    colors = {1: RGBColor(0x4A,0x6C,0xF7), 2: RGBColor(0x33,0x33,0x33), 3: RGBColor(0x55,0x55,0x55)}
    sizes  = {1: Pt(16), 2: Pt(13), 3: Pt(11)}
    p.runs[0].font.color.rgb = colors.get(level, RGBColor(0,0,0))
    p.runs[0].font.size      = sizes.get(level, Pt(11))
    return p


# ----------------------------------------------------------------
# テキスト段落追加（赤太字対応）
# ----------------------------------------------------------------
def split_by_kuten(text):
    parts = [p.strip() for p in re.split(r'(?<=。)', text) if p.strip()]
    return parts if len(parts) > 1 else [text]

def add_text_paragraph(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    bold_parts = re.split(r'\*\*(.+?)\*\*', text)
    for j, part in enumerate(bold_parts):
        if not part: continue
        if j % 2 == 1:
            run = p.add_run(part)
            run.font.name = 'Meiryo'; run.font.size = Pt(10.5)
            run.bold = True; run.font.color.rgb = RED_BOLD
        else:
            sub_parts   = NUMBER_PATTERN.split(part)
            num_matches = NUMBER_PATTERN.findall(part)
            for k, sub in enumerate(sub_parts):
                if sub:
                    run = p.add_run(sub)
                    run.font.name = 'Meiryo'; run.font.size = Pt(10.5)
                if k < len(num_matches):
                    run = p.add_run(num_matches[k])
                    run.font.name = 'Meiryo'; run.font.size = Pt(10.5)
                    run.bold = True; run.font.color.rgb = RED_BOLD
    return p


# ----------------------------------------------------------------
# セクションの行を処理
# ----------------------------------------------------------------
def process_lines(doc, lines_list):
    i = 0
    while i < len(lines_list):
        line = lines_list[i]
        if line.strip() == '\\newpage':
            doc.add_page_break(); i += 1; continue

        img_m = img_pattern.match(line.strip())
        if img_m:
            img_path = base_dir / "images" / img_m.group(2)
            if img_path.exists():
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(8)
                p.add_run().add_picture(str(img_path), width=Inches(CONTENT_IMG_WIDTH))
                cap = doc.add_paragraph(img_m.group(1))
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if cap.runs:
                    cap.runs[0].font.size = Pt(9)
                    cap.runs[0].font.color.rgb = RGBColor(0x88,0x88,0x88)
            i += 1; continue

        if   line.startswith('# '):   add_heading(doc, line[2:].strip(), 1)
        elif line.startswith('## '):  add_heading(doc, line[3:].strip(), 2)
        elif line.startswith('### '): add_heading(doc, line[4:].strip(), 3)
        elif line.strip().startswith('```'):
            i += 1
            while i < len(lines_list) and not lines_list[i].strip().startswith('```'): i += 1
        elif line.strip() not in ('---', ''):
            text = line.strip()
            if text:
                for sentence in split_by_kuten(text):
                    add_text_paragraph(doc, sentence)
        i += 1


# ----------------------------------------------------------------
# 章末漫画挿入（セクション切替で余白0.5cm・最大サイズ）
# ----------------------------------------------------------------
def add_manga_section(doc, chapter_num):
    pages = chapter_manga_pages.get(chapter_num, [])
    if not pages: return

    # ① 章の最後の段落にsectPr{2cm}を付与（空白ページを追加しない）
    attach_section_break(doc.paragraphs[-1], NORMAL_MARGIN_CM)

    # ② 漫画ページを配置（ページ間は通常の改ページ）
    for i, page_num in enumerate(pages):
        if i > 0:
            doc.add_page_break()
        img_path = panels_dir / f"page_{page_num:02d}.png"
        if img_path.exists():
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after  = Pt(0)
            p.add_run().add_picture(str(img_path), width=Inches(MANGA_IMG_WIDTH))
        else:
            doc.add_paragraph(f"[漫画ページ {page_num} なし]")

    # ③ 最後の漫画段落にsectPr{0.5cm}を付与（空白ページを追加しない）
    attach_section_break(doc.paragraphs[-1], MANGA_MARGIN_CM)

    print(f"[INFO] 第{chapter_num}章末: 漫画{pages} 幅{MANGA_IMG_WIDTH:.2f}inch ({MANGA_IMG_WIDTH*2.54:.1f}cm)")


# ----------------------------------------------------------------
# セクション分割（# 第X章 を境界に）
# ----------------------------------------------------------------
sections, current_lines, current_chapter = [], [], 0
for line in lines:
    m = ch_pattern.match(line)
    if m:
        while current_lines and current_lines[-1].strip() in ('\\newpage','','---'): current_lines.pop()
        sections.append((current_chapter, list(current_lines)))
        current_chapter = int(m.group(1)); current_lines = [line]
    else:
        current_lines.append(line)
while current_lines and current_lines[-1].strip() in ('\\newpage','','---'): current_lines.pop()
sections.append((current_chapter, list(current_lines)))


# ----------------------------------------------------------------
# 各セクション処理
# ----------------------------------------------------------------
last_was_manga = False
for idx, (chapter_num, section_lines) in enumerate(sections):
    # 漫画セクションの後はsectPrが改ページ済みなので不要
    if idx > 0 and not last_was_manga:
        doc.add_page_break()

    process_lines(doc, section_lines)

    if chapter_num in chapter_manga_pages:
        add_manga_section(doc, chapter_num)
        last_was_manga = True
    else:
        last_was_manga = False


# ----------------------------------------------------------------
# 保存
# ----------------------------------------------------------------
doc.save(str(out_path))
size_kb = out_path.stat().st_size // 1024
print(f"\n[OK] final_book.docx ({size_kb} KB) → {out_path}")
```

### 実行方法

```bash
cd "c:/Users/Tatsu/Desktop/ツール開発/電子書籍マンカ自動化-デジイナ式"
python "output/{slug}/build_final.py"
```

### 完成

`output/{slug}/final_book.docx` が最終成果物。

---

## 画像仕様

| 項目 | 挿絵 | 漫画 |
|------|------|------|
| モデル | gemini-3.1-flash-image-preview | gemini-3.1-flash-image-preview |
| サイズ | 1200x800px | 896x1200px |
| 向き | ランドスケープ (3:2) | ポートレート (2:3) |
| 生成方法 | nanobanana-deji `generate.py` | `generate_manga.py`（キャラ参照+テンプレ添付） |
| APIキー設定 | `.env` の `GEMINI_API_KEY` | 同左 |

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| `GEMINI_API_KEY が設定されていません` | `.env` ファイルに `GEMINI_API_KEY=...` を記述 |
| `モデルが見つかりません（404）` | APIキーの権限または地域制限を確認 |
| `response_mime_type` エラー | `GenerateContentConfig` から `response_mime_type` を削除（`response_modalities=["IMAGE","TEXT"]` のみ） |
| 画像データが返されない | プロンプトを短縮・シンプル化して再試行。「続けて」で再開 |
| 漫画が横長で生成される | プロンプトに「2:3縦長」「portrait 896x1200px」を明示 |
| 漫画の下部が切れる | `build_final.py` の `_print_h` に2.5cm安全マージンが入っているか確認 |
| 漫画セクション後に空白ページ | `attach_section_break()` を使い、空の段落を追加しないことを確認 |
| APIレート制限 | しばらく待ってから「続けて」と入力 |
| 太字がアスタリスクのまま残る | `**...**` の内側に `「」` 等の括弧が入っていないか確認 |
