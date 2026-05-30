---
name: openai-image-gen
description: OpenAI gpt-image-2 (ChatGPT Images 2.0) API経由で画像を生成して保存するスキル。単一・複数枚・参照画像入力（最大10枚）・4種のサイズ（1024x1024/1024x1536/1536x1024/auto）・4段階の画質（low/medium/high/auto）に対応。
---

# OpenAI 画像生成スキル

## 概要

このスキルは、テキストプロンプト（および任意で参照画像）を入力として受け取り、OpenAI Images API（gpt-image-2 モデル / ChatGPT Images 2.0）を使って画像を生成し、指定フォルダに PNG として保存します。
単一プロンプトでの生成のほか、複数プロンプトの並列生成にも対応しています。
参照画像を指定するとキャラクター一貫性を保った画像を生成できます。

## 入力

- **画像生成プロンプト**（必須）: 生成したい画像の説明テキスト。複数枚の場合はリスト形式
- **保存フォルダ名**（任意）: `.company/outputs/` 配下のフォルダ名。未指定時は `openai-image-gen`
- **サイズ**（任意）: `1024x1024` / `1024x1536` / `1536x1024` / `auto`。未指定時は `1024x1536`
- **画質**（任意）: `low` / `medium` / `high` / `auto`。未指定時は `medium`
- **参照画像**（任意）: 参照画像ファイルパスのリスト。最大10枚、各25MB以下、PNG/JPG/WebP
- **ファイル名プレフィックス**（任意）: 出力ファイル名の先頭に付ける識別子

## 実行モード判定

スキル起動時に、入力内容から実行モードを判定する:

| モード | 条件 | 実行方法 |
|--------|------|----------|
| **generate（単一）** | プロンプト1つ・参照画像なし | Step 2 を1回実行（images.generate） |
| **edit（単一）** | プロンプト1つ・参照画像1枚以上 | Step 2 を1回実行（images.edit） |
| **並列（複数）** | プロンプトが複数 | Step 2 を各プロンプトごとに `run_in_background` で並列実行 |

## ワークフロー

### Step 1: 環境準備

1. 環境変数 `OPENAI_API_KEY` が設定されているか確認する。**未設定の場合は `~/.bashrc` から読み込みを試みる。** それでも未設定ならエラー表示して終了。

```bash
source ~/.bashrc 2>/dev/null
if [ -z "$OPENAI_API_KEY" ]; then
  echo "ERROR: 環境変数 OPENAI_API_KEY が設定されていません。"
  exit 1
fi
```

2. `openai` パッケージがインストールされているか確認し、なければインストールする。

```bash
pip install -q openai 2>/dev/null || pip install -q openai
```

### Step 2: 画像生成と保存

以下のPythonスクリプトをBashツールで実行する。変数部分はスキル実行時に適切な値に置き換えること。

- `IMAGE_PROMPT`: ユーザーから受け取った画像生成プロンプト
- `OUTPUT_FOLDER`: 保存フォルダ名（デフォルト: `openai-image-gen`）
- `SIZE`: サイズ（デフォルト: `1024x1536`）
- `QUALITY`: 画質（デフォルト: `medium`）
- `REFERENCE_IMAGES`: 参照画像パスのカンマ区切り文字列（デフォルト: 空文字）
- `FILE_PREFIX`: ファイル名プレフィックス（デフォルト: 空）
- `PROJECT_ROOT`: プロジェクトルートパス（`G:/マイドライブ/YNFactory-cc`）

**⚠️ 置換時の重要な注意事項（セキュリティ）:**
`IMAGE_PROMPT` は Python の triple-quoted string `"""..."""` の中に埋め込まれます。プロンプト本文に `"""`（連続する三重引用符）が含まれているとスクリプト構文が壊れ任意の Python コードが実行される恐れがあります。プロンプト置換前に **必ず `"""` を `'''` または `""`（二重引用符×2）に置換** してください。同様に、`REFERENCE_IMAGES` のパス文字列にも `"""` が含まれないことを確認してください。

**重要: Windows環境では `python3` ではなく `python` を使用すること。**

```bash
export OPENAI_API_KEY="$OPENAI_API_KEY" && python << 'PYTHON_SCRIPT'
import os
import sys
import base64
import datetime

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai not found. Run: pip install openai")
    sys.exit(1)

# --- 設定 ---
API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("ERROR: OPENAI_API_KEY is not set.")
    sys.exit(1)

PROMPT = """{{IMAGE_PROMPT}}"""
OUTPUT_FOLDER = "{{OUTPUT_FOLDER}}"
SIZE = "{{SIZE}}"
QUALITY = "{{QUALITY}}"
REFERENCE_IMAGES_RAW = "{{REFERENCE_IMAGES}}"
FILE_PREFIX = "{{FILE_PREFIX}}"
PROJECT_ROOT = r"{{PROJECT_ROOT}}"

# --- バリデーション ---
VALID_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}
if SIZE not in VALID_SIZES:
    print(f"ERROR: Unsupported size '{SIZE}'. Valid: {sorted(VALID_SIZES)}")
    sys.exit(1)

VALID_QUALITIES = {"low", "medium", "high", "auto"}
if QUALITY not in VALID_QUALITIES:
    print(f"ERROR: Unsupported quality '{QUALITY}'. Valid: {sorted(VALID_QUALITIES)}")
    sys.exit(1)

reference_paths = [p.strip() for p in REFERENCE_IMAGES_RAW.split(",") if p.strip()]
if len(reference_paths) > 10:
    print(f"ERROR: Too many reference images ({len(reference_paths)}). Max 10.")
    sys.exit(1)

for p in reference_paths:
    if not os.path.exists(p):
        print(f"ERROR: Reference image not found: {p}")
        sys.exit(1)
    size_bytes = os.path.getsize(p)
    if size_bytes > 25 * 1024 * 1024:
        print(f"ERROR: Reference image exceeds 25MB: {p} ({size_bytes} bytes)")
        sys.exit(1)

# --- 出力ディレクトリ作成 ---
output_dir = os.path.join(PROJECT_ROOT, ".company", "outputs", OUTPUT_FOLDER)
os.makedirs(output_dir, exist_ok=True)

# --- API呼び出し ---
client = OpenAI(api_key=API_KEY)
try:
    if reference_paths:
        # edit モード
        image_files = [open(p, "rb") for p in reference_paths]
        try:
            result = client.images.edit(
                model="gpt-image-2",
                image=image_files if len(image_files) > 1 else image_files[0],
                prompt=PROMPT,
                size=SIZE,
                quality=QUALITY,
                n=1,
            )
        finally:
            for f in image_files:
                f.close()
    else:
        # generate モード
        result = client.images.generate(
            model="gpt-image-2",
            prompt=PROMPT,
            size=SIZE,
            quality=QUALITY,
            n=1,
        )
except Exception as e:
    print(f"ERROR: API call failed: {e}")
    sys.exit(1)

# --- レスポンス処理 ---
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
prefix = f"{FILE_PREFIX}_" if FILE_PREFIX else ""
image_count = 0

for i, item in enumerate(result.data or []):
    b64 = getattr(item, "b64_json", None)
    if not b64:
        continue
    image_count += 1
    filename = f"{prefix}{timestamp}_{image_count:03d}.png"
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(b64))
        print(f"OK: {filepath}")
    except Exception as e:
        print(f"ERROR: save failed: {e}")
        sys.exit(1)

if image_count == 0:
    print("WARNING: No image in response.")
    sys.exit(1)

print(f"\n--- Result ---")
print(f"Images: {image_count}")
print(f"Dir: {output_dir}")
print(f"Mode: {'edit' if reference_paths else 'generate'}")
print(f"Size: {SIZE}, Quality: {QUALITY}")
print("--- Done ---")
PYTHON_SCRIPT
```

### Step 2b: 複数枚生成（並列実行）

複数プロンプトが指定された場合、**Step 2のBashコマンドを各プロンプトごとに `run_in_background: true` で並列起動**する。

手順:
1. 各プロンプトに対して、個別の `FILE_PREFIX`（例: `vol1`, `vol2`...）を設定する
2. 全てのBashコマンドを**1つのメッセージ内で同時に**発行する（並列実行）
3. 全タスク完了後、結果をまとめて報告する
4. **一部失敗した場合でも成功分は報告し、失敗したプロンプトと失敗理由を別枠で列挙する**（課金発生するAPIなので部分失敗を見落とさない）

例: 4枚生成の場合
- Bash(run_in_background=true): プロンプト1 → FILE_PREFIX="vol1"
- Bash(run_in_background=true): プロンプト2 → FILE_PREFIX="vol2"
- Bash(run_in_background=true): プロンプト3 → FILE_PREFIX="vol3"
- Bash(run_in_background=true): プロンプト4 → FILE_PREFIX="vol4"

### Step 3: 結果報告

生成完了後、以下の情報をユーザーに報告する:

1. 生成された全画像のファイルパス
2. 保存先フォルダのパス
3. 使用モード（generate / edit）
4. 使用サイズ・画質
5. 画像をReadツールで表示する（ユーザーに確認してもらう）

## 実行例

### 単一生成（テキストのみ）

> 「かわいい柴犬がお花畑で遊んでいるイラストを生成して」

1. プロンプト: `かわいい柴犬がお花畑で遊んでいるイラスト`
2. 保存フォルダ: `openai-image-gen`（デフォルト）
3. サイズ: `1024x1536`（デフォルト）
4. 画質: `medium`（デフォルト）
5. API呼び出し → `.company/outputs/openai-image-gen/20260421_153000_001.png` に保存

### 単一生成（参照画像あり）

> 「ミサキが公園を歩いている場面」＋ 参照画像: `ミサキ.png`

1. プロンプト: `ミサキが公園を歩いている場面`
2. 参照画像: `[ミサキ.png]`
3. モード: edit（参照画像あり）
4. API呼び出し（images.edit）→ `.company/outputs/openai-image-gen/` に保存

### 複数枚並列生成

> 「マンガ第1巻の表紙3種を生成」（3つのプロンプトがリストで渡される）

1. 3つのプロンプトを並列で同時実行
2. FILE_PREFIX: `variantA`, `variantB`, `variantC`
3. 保存フォルダ: `openai-image-gen/cover-variants`
4. 全完了後、3枚まとめて報告

## ファイル名規則

- 単一: `{timestamp}_{連番}.png`
- プレフィックス付き: `{prefix}_{timestamp}_{連番}.png`
- timestamp: `YYYYMMDD_HHMMSS`
- 連番: `001` から開始（3桁ゼロ埋め）

## 対応サイズ

| 値 | ピクセル | 用途例 |
|----|---------|--------|
| `1024x1024` | 1024×1024 | SNSアイコン、正方形素材 |
| `1024x1536` | 1024×1536 | マンガコマ、書籍カバー、縦長（デフォルト） |
| `1536x1024` | 1536×1024 | 横長バナー、YouTubeサムネイル |
| `auto` | モデル任せ | 判断を OpenAI に委ねる |

※ NanoBanana2 のような `9:16` や `4:5` 等の任意アスペクト比は非対応。

## 対応画質（料金目安: 1024x1536 1枚あたり）

| 値 | 料金目安 | 用途例 |
|----|----------|--------|
| `low` | $0.016 | テスト、ラフ、大量生成 |
| `medium` | $0.063 | 通常用途（デフォルト） |
| `high` | $0.21 | 最終版、印刷物 |
| `auto` | 不定 | OpenAI任せ |

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| `OPENAI_API_KEY` 未設定 | エラーメッセージを表示し、APIキーの取得・設定方法を案内する |
| `openai` 未インストール | `pip install openai` を自動実行する |
| 非対応サイズ | 対応一覧（4種）を表示してエラー終了 |
| 非対応画質 | 対応一覧（4種）を表示してエラー終了 |
| 参照画像ファイル不在 | パスを表示してエラー終了 |
| 参照画像が 25MB 超 | サイズを表示してエラー終了 |
| 参照画像が 10枚超 | 枚数を表示してエラー終了 |
| API 呼び出しエラー | エラー詳細を表示し、プロンプトの修正や rate limit の確認を案内 |
| レスポンスに画像なし | WARNING を表示して終了 |

## 注意事項

- APIキーは環境変数 `OPENAI_API_KEY` に事前設定が必要
- Windows環境では `python3` ではなく `python` コマンドを使用する
- モデル `gpt-image-2`（ChatGPT Images 2.0）は OpenAI の最新画像生成モデルで、画像は base64 エンコードされて返される（URL 形式は非対応）
- 生成画像はPNG形式で保存される
- 複数枚生成時はAPI呼び出しが並列で行われるため、レート制限に注意
- 料金は 1 枚ごとの課金で、サイズ・画質により変動する
- アスペクト比は 4 種のネイティブサイズのみ対応（任意比率の自動マッピングは行わない）

## 将来の拡張予定

- マスク編集（inpainting）対応
- ebook-to-manga からの呼び出し切替（設定ファイルで NanoBanana2/OpenAI を選択）
- アスペクト比の自動マッピング層（`9:16` → `1024x1536` 等）
- `n > 1` での 1 プロンプトからの複数バリアント生成
