---
created: "2026-04-22"
updated: "2026-04-23"
author: requirements-definer
status: draft
---

# 要件定義書: ebook-to-manga スキル — gpt-image-2 全面移行

## ゴール

`skill.md`（1926行、8ステップパイプライン）の画像生成エンジンを NanoBanana2（`gemini-2.5-flash-image` / Google AI Studio API）から gpt-image-2（OpenAI API）に全面切替し、縦書きテキスト描画の安定化とモデル一本化を実現する。

---

## スコープ

### やること

- `skill.md` 内の全 API 呼び出しコード（Step 3 / Step 5 / Step 5.5 clean regen / Step 6）を gpt-image-2 に切替
- 環境変数・パッケージ依存の変更（前提条件セクションの書き換え）
- プロンプト構造（`◆【コマ構成】`〜`◆【ストーリー】`）はそのまま維持する（追加ルールは加えない）
- Step 5 の画像生成 API コール部分（A路線・B路線 clean regen ともに）の書き換え
- Step 5-QC の OCR モデルを gpt-4o（`gpt-4o`、OpenAI API）へ変更
- コスト試算セクションの数値更新
- 前提条件・エラーハンドリングセクションの更新
- E2E動作確認手順の更新
- 保存形式を PNG に変更（gpt-image-2 は b64_json で PNG を返す）

### やらないこと

- Step 1（ソース分析）・Step 2（シナリオ）・Step 4（CSV作成）・Step 7（EPUB製本）・Step 8（メタデータ）のロジック変更
- Blind-OCR 判定の廃止（残存する。OCR モデルを gpt-4o に変更するのみ）
- Pillow 合成フォールバックの廃止（残存する。gpt-image-2 でも保険として維持）
- 既存の vol1/vol2 生成済みデータの再生成（別案件）
- GOOGLE_AI_STUDIO_API_KEY の即時削除（併存とし、移行後に別 PR で整理）
- google-genai パッケージの即時アンインストール（同上）
- EPUB 固定レイアウト構造・テキストページ処理の変更

---

## 要判断ポイントと結論

### 0. プロンプトへの追加ルール（縦書き・枠配置）の要否

**結論: 追加ルールは加えない。既存のプロンプト構造をそのまま維持する**

理由:
- vol1 p045 のテスト生成において、以下の追加ルールを挿入すると「文字数と枠サイズの不一致」など新たな問題が発生することが判明した
  - セリフ吹き出し内は縦書き必須ルール
  - ナレーション四角枠内は横書きルール
  - ナレーション枠オーバーレイ配置ルール（コマ幅40%×高50%以内等）
- gpt-image-2 は既存の `［四角枠］` 記法だけでも適切に処理できる
- 追加ルールを入れない方がトータルの品質が安定する

方針:
- `◆【コマ構成】`〜`◆【ストーリー】` の既存プロンプト構造をそのまま使用する
- テキスト方向・枠配置に関する追加ブロックは一切挿入しない

---

### 1. ハイブリッドQC（Blind-OCR）の継続有無

**結論: 残存・継続する（OCR モデルを gpt-4o に変更）**

理由:
- gpt-image-2 は日本語描画が大幅改善されたが、「誤字・文字見切れ」の 100% 保証はない
- Blind-OCR の設計目的（確認バイアス排除 + プログラム側完全一致判定）はモデル依存でなく普遍的
- 廃止した場合、FAIL ページが EPUB に混入するリスクが復活する
- コスト的には gpt-4o OCR 追加分でも削減効果あり（後述コスト試算参照）

OCR モデルの変更方針:
- 現行: `gemini-2.5-flash`（Google AI Studio API）
- 変更後: `gpt-4o`（OpenAI API）
- これにより API を OpenAI に完全一本化できる
- gpt-4o の vision 機能は OCR に十分な精度を持つ

### 2. Pillow 合成フォールバックの継続有無

**結論: 残存・継続する（変更なし）**

理由:
- gpt-image-2 でも「長セリフ・複数キャラ同時発話・小さいコマ」での文字崩れは残存し得る
- Pillow 合成はローカル処理（コスト $0）のため残すデメリットがない
- max_iter 超過時の最終手段として「文字品質の床」を担保する設計は継続価値がある

### 3. 環境変数・パッケージの扱い

**結論: 併存方式（即時削除はしない）**

- `OPENAI_API_KEY`: 必須（新規追加）
- `GOOGLE_AI_STUDIO_API_KEY`: 必須から「任意（レガシー）」に降格して記載
- `openai` パッケージ: 必須（新規追加）
- `google-genai` パッケージ: 「任意（レガシー）」に降格して記載
- 削除タイミング: vol1/vol2 の再生成移行完了後に別 PR で整理

### 4. 保存形式: PNG vs JPEG

**結論: PNG（変更あり）**

gpt-image-2 は `b64_json` で PNG バイナリを返す。JPEG に変換する場合は Pillow で再エンコードが必要だが、変換コストと品質劣化が生じるため PNG のまま保存する。

影響範囲:
- Step 5 生成ファイルの拡張子: `.jpg` → `.png`
- Step 7 EPUB 製本スクリプトの `glob` パターン: `page_*.jpg` → `page_*.png`（Step 7 も修正対象に追加）
- Step 3 キャラリファレンス: すでに `.png`（変更なし）
- 既存スキルの「全画像 JPEG で保存」ルールを「Step 5/6 は PNG、既存データは JPEG」に修正

### 5. gpt-image-2 の API 呼び出し方式

**結論: 常に `client.images.edit`（参照画像付き）を使用**

理由:
- Step 3/5/6 すべてでキャラクターリファレンス画像を参照する設計になっている
- `images.generate` は参照画像なしのケースのみ（Step 3 の初回生成でキャラ未存在時のみ使用）

パラメータ仕様:
```python
client.images.edit(
    model="gpt-image-2",
    image=files[0] if len(files) == 1 else files,  # 最大10枚まで
    prompt=PROMPT,
    size="1024x1536",   # 9:16相当の縦長形式
    quality="high",
    n=1,
)
```

---

## コスト試算（移行後）

### Step 3 + Step 5 + Step 6（100ページ本）

| 項目 | 旧（NanoBanana2） | 新（gpt-image-2） |
|---|---|---|
| 画像生成単価 | $0.04〜0.07/枚 | $0.21/枚（1024x1536 high） |
| Step 5: 100枚 × 平均 1.5 iter | ~$7.00 | ~$31.50 |
| Step 3: キャラリファレンス 2〜3枚 | ~$0.18 | ~$0.63 |
| Step 6: 表紙 1枚 | ~$0.06 | ~$0.21 |
| Blind-OCR（gpt-4o vision）× 150コール | ~$1.00 | ~$1.50（gpt-4o input） |
| clean regen（フォールバック 約5%/100P） | ~$0.35 | ~$1.05 |
| **合計目安** | **~$8.60/冊** | **~$34.89/冊（約4.1倍）** |

※ gpt-image-2 単価: 1024x1536 high = $0.21/枚（OpenAI 公式料金 2026-04-22 時点）
※ gpt-4o OCR: 入力トークン $2.50/1Mトークン換算、画像1枚あたり約 $0.01 相当

コスト増加への対応方針（スコープ外だが記録）:
- max_iter=1〜2 に下げてフォールバック許容度を上げる（コスト削減方向）
- quality="medium" に下げる（単価 $0.07/枚、約33%削減）
- 上記は別案件として検討

---

## 工程一覧

| 工程 | 変更対象セクション | 中間成果物 | 入力 |
|---|---|---|---|
| 工程1: 前提条件・グローバル設定の書き換え | 前提条件・画像生成絶対ルール・コスト試算 | 非コード記述変更 | 現行 skill.md |
| 工程2: Step 3（キャラリファレンス生成）の書き換え | Step 3 セクション（行 258〜386） | gpt-image-2 呼び出しコードに変換済みのセクション | 工程1の成果物 |
| 工程3: Step 5（画像生成ループ・A路線）の書き換え | Step 5 セクション（行 579〜783）、Step 5-QC（行 786〜937） | A路線生成コード + OCR モデル変更済み | 工程2の成果物 |
| 工程4: Step 5.5（Pillow フォールバック clean regen）の書き換え | Step 5.5 セクション（行 940〜1241） | clean regen の API コード変更済み | 工程3の成果物 |
| 工程5: Step 6（表紙）の書き換え | Step 6 セクション（行 1243〜1287） | gpt-image-2 呼び出しコードに変換済み | 工程4の成果物 |
| 工程6: Step 7・エラーハンドリング・E2E確認手順の更新 | Step 7（glob パターン）、エラーハンドリング表、E2E確認手順 | 整合性の取れた完成形 skill.md | 工程5の成果物 |

---

## 工程1: 前提条件・グローバル設定の書き換え

### 対象行（現行 skill.md）

- 行 3: `description` の `NanoBanana2画像生成` 記述
- 行 22〜24: `前提条件` セクション（環境変数・パッケージ）
- 行 35〜37: `画像フォーマット`（PNG/JPEG の記述変更）
- 行 1700〜1708: コスト試算テーブル
- 行 1724〜1727: 注意事項（Gemini API レート制限の記述）

### 完了条件

- [ ] `前提条件` セクションが `OPENAI_API_KEY` 必須・`openai` パッケージ必須に変更されていること
- [ ] `GOOGLE_AI_STUDIO_API_KEY` と `google-genai` が「任意（レガシー）」として残存していること
- [ ] `画像フォーマット` セクションが PNG 方針（gpt-image-2 が b64_json/PNG を返す）に更新されていること
- [ ] コスト試算テーブルが gpt-image-2 の単価（$0.21/枚）で更新されていること
- [ ] `skill.md` の冒頭 `description` フィールドが gpt-image-2 ベースの記述に変更されていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | OPENAI_API_KEY 必須・openai パッケージ必須への変更が正確か | 機能要件 | 30 |
| 2 | GOOGLE_AI_STUDIO_API_KEY/google-genai が削除でなく「任意」として残存しているか | リスク管理 | 25 |
| 3 | 保存形式（PNG方針）の記述が矛盾なく更新されているか | 整合性 | 25 |
| 4 | コスト試算の数値が gpt-image-2 単価に基づいて正確に計算されているか | 正確性 | 20 |
| 合計 | | | 100 |

---

## 工程2: Step 3（キャラリファレンス生成）の書き換え

### 対象行（現行 skill.md）

- 行 314: `NanoBanana2で全身リファレンス画像を生成する` という記述
- 行 333〜374: bash/Python スクリプトブロック全体（`google-genai` → `openai` に置換）
- 行 357: `model="gemini-2.5-flash-image"` の呼び出し
- 行 377〜379: 並列実行・アスペクト比・保存先の記述

### 変更仕様

```python
# 変更前
from google import genai
from google.genai import types
client = genai.Client(api_key=GOOGLE_AI_STUDIO_API_KEY)
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    ...
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="9:16"),
    ),
)
image.save(filepath)  # PNG保存（拡張子はそのまま .png）

# 変更後
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
result = client.images.generate(  # キャラ初回生成は参照画像なし → generate
    model="gpt-image-2",
    prompt=PROMPT,
    size="1024x1536",
    quality="high",
    n=1,
)
# b64_json → PNG ファイル保存
import base64
with open(filepath, "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
```

縦書きルールはキャラリファレンスには不要（「セリフやオノマトペは入れない」指示があるため）。アニメ・マンガ調の絶対最優先プロンプトはそのまま維持。

### 完了条件

- [ ] Step 3 の bash/Python コードブロックが openai パッケージを使った gpt-image-2 呼び出しに変更されていること
- [ ] `GOOGLE_AI_STUDIO_API_KEY` の参照が Step 3 コードから除去されていること
- [ ] サイズが `size="1024x1536"`, `quality="high"` になっていること
- [ ] 保存が `base64.b64decode(result.data[0].b64_json)` 経由の PNG 保存になっていること
- [ ] `run_in_background: true` の並列実行指示が維持されていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | openai パッケージ経由の gpt-image-2 呼び出しが正確に記述されているか | 機能要件 | 35 |
| 2 | b64_json デコード → PNG 保存のコードが正確か | 機能要件 | 25 |
| 3 | Google AI Studio 依存（google-genai import、API_KEY 参照）が Step 3 コードから除去されているか | 整合性 | 20 |
| 4 | 並列実行・保存先ディレクトリ等の周辺仕様が維持されているか | 整合性 | 10 |
| 5 | コードに構文エラー・論理エラーがないか | 可読性 | 10 |
| 合計 | | | 100 |

---

## 工程3: Step 5（画像生成ループ・A路線）+ Step 5-QC の書き換え

### 対象行（現行 skill.md）

- 行 625: `[A-1] 画像生成（gemini-2.5-flash-image）` コメント
- 行 670〜675: 生成設定詳細（ASPECT_RATIO, モデル名等）
- 行 680: OCR モデル `gemini-2.5-flash` の記述
- 行 831〜856: Step 5-QC OCR プロンプトテンプレート（モデル指定部分）

### 変更仕様

**A-1 画像生成（A路線）:**

```python
# 変更前: gemini-2.5-flash-image
# 変更後: gpt-image-2（openai）
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# 参照画像ありの場合（通常）
result = client.images.edit(
    model="gpt-image-2",
    image=char_ref_files if len(char_ref_files) > 1 else char_ref_files[0],
    prompt=IMAGE_PROMPT,  # 既存のプロンプト構造をそのまま使用（追加ルールなし）
    size="1024x1536",
    quality="high",
    n=1,
)
# b64_json → PNG 保存
with open(f"page_{NNN}_iter_{iter}.png", "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
```

プロンプト構造は既存の `◆【コマ構成】`〜`◆【ストーリー】` をそのまま維持する。テキスト方向・枠配置に関する追加ブロックは挿入しない（vol1 p045 のテスト生成で追加ルールが逆効果と判明）。

**Step 5-QC OCR モデル変更:**

```python
# 変更前: gemini-2.5-flash（google-genai）
# 変更後: gpt-4o（openai）
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
```

**ファイル拡張子:** `.jpg` → `.png`（全ファイル命名規則を更新）

### 完了条件

- [ ] A路線の画像生成コードが gpt-image-2（openai）に変更されていること
- [ ] 既存のプロンプト構造がそのまま維持され、追加ルールが挿入されていないこと
- [ ] Step 5-QC の OCR モデル指定が `gpt-4o`（openai）に変更されていること
- [ ] OCR のレスポンス処理が `response.choices[0].message.content` 経由に変更されていること
- [ ] ファイル命名規則が `.jpg` → `.png` に更新されていること
- [ ] バッチサイズ・待機時間・max_iter 等のパラメータが維持されていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | gpt-image-2 の images.edit 呼び出しが正確に記述されているか | 機能要件 | 35 |
| 2 | 既存プロンプト構造が維持され、追加ルールが挿入されていないか | 整合性 | 20 |
| 3 | Step 5-QC の OCR が gpt-4o（openai chat completions）に正確に変更されているか | 機能要件 | 25 |
| 4 | ファイル命名・拡張子の更新が一貫しているか | 整合性 | 10 |
| 5 | 既存のハイブリッドループフロー（max_iter、PASS/FAIL判定、フィードバック注入）が維持されているか | 整合性 | 10 |
| 合計 | | | 100 |

---

## 工程4: Step 5.5（Pillow フォールバック clean regen）の書き換え

### 対象行（現行 skill.md）

- 行 1024〜1036: clean regen スクリプト内の gemini 呼び出し部分
- 行 1036: `pages/page_{NNN}_clean.jpg` → `.png` への命名変更

### 変更仕様

clean regen の画像生成 API も gpt-image-2 に変更する。clean regen は「テキスト除去ブロック付きプロンプト」を使って画像のみを再生成するもので、参照画像（キャラリファレンス）は引き続き使用する。

```python
# 変更前: gemini-2.5-flash-image
# 変更後: gpt-image-2
result = client.images.edit(
    model="gpt-image-2",
    image=char_ref_files if len(char_ref_files) > 1 else char_ref_files[0],
    prompt=CLEAN_PROMPT,  # テキスト除去ブロック付きプロンプト
    size="1024x1536",
    quality="high",
    n=1,
)
# b64_json → PNG 保存
with open(f"page_{NNN}_clean.png", "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
```

Pillow 合成処理自体（吹き出し・テキスト描画）は変更なし。合成出力ファイルも `.png` に変更。

### 完了条件

- [ ] clean regen の API 呼び出しが gpt-image-2（openai）に変更されていること
- [ ] `page_{NNN}_clean.jpg` → `page_{NNN}_clean.png`、`page_{NNN}_composited.jpg` → `page_{NNN}_composited.png` に変更されていること
- [ ] Pillow 合成処理のコード（テキスト描画部分）が変更されていないこと
- [ ] 保存コマンドが `img.save(out_path, "JPEG", quality=92)` から PNG 保存（`img.save(out_path, "PNG")` または PIL PNG 形式）に変更されていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | clean regen の gpt-image-2 呼び出しが正確か | 機能要件 | 35 |
| 2 | ファイル拡張子が `.png` に統一されているか | 整合性 | 25 |
| 3 | Pillow 合成コードが変更されていないこと（変更禁止） | 整合性 | 25 |
| 4 | 保存コードが PNG 形式に変更されているか | 機能要件 | 15 |
| 合計 | | | 100 |

---

## 工程5: Step 6（表紙生成）の書き換え

### 対象行（現行 skill.md）

- 行 1279: `NanoBanana2で生成` の記述
- 行 1280: `アスペクト比: 9:16` の記述（gpt-image-2 では `size="1024x1536"` に変換）
- 行 1281: 保存先 `cover.jpg`（PNG に変更 → `cover.png` または JPEG 変換の選択）

### 方針決定: 表紙は JPEG 変換を行う

KDP（Kindle Direct Publishing）の表紙要件は JPEG を推奨。Pillow で PNG → JPEG 変換を行う。

```python
import base64, io
from PIL import Image

result = client.images.edit(
    model="gpt-image-2",
    image=char_ref_files,
    prompt=COVER_PROMPT,
    size="1024x1536",
    quality="high",
    n=1,
)
img_bytes = base64.b64decode(result.data[0].b64_json)
img = Image.open(io.BytesIO(img_bytes))
cover_path = os.path.join(OUTPUT_DIR, "KDP出版用", "cover.jpg")
img.save(cover_path, "JPEG", quality=92)
```

### 完了条件

- [ ] Step 6 の実行手順が gpt-image-2 呼び出しに変更されていること
- [ ] 表紙のみ PNG → JPEG 変換が明示されていること（KDP 要件対応）
- [ ] 追加プロンプトルール（テキスト方向・枠配置）が表紙プロンプトに混入していないこと
- [ ] `size="1024x1536"`, `quality="high"` が指定されていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Step 6 の gpt-image-2 呼び出しが正確か | 機能要件 | 35 |
| 2 | 表紙の PNG→JPEG 変換が明示されているか | 機能要件 | 30 |
| 3 | 追加プロンプトルール（テキスト方向・枠配置）が表紙プロンプトに混入していないか | 整合性 | 20 |
| 4 | KDP 出力先パス・ファイル名が維持されているか | 整合性 | 15 |
| 合計 | | | 100 |

---

## 工程6: Step 7・エラーハンドリング・E2E確認手順の整合更新

### 対象行（現行 skill.md）

- 行 1341: `glob(os.path.join(PAGES_DIR, "page_*.jpg"))` → `"page_*.png"` に変更
- 行 1711〜1730: エラーハンドリング・注意事項セクション（Gemini API → OpenAI API 言及変更）
- 行 1733〜1926: E2E動作確認手順（OCR 単体テストコード内の gemini 呼び出し → gpt-4o 変更）

### 完了条件

- [ ] Step 7 の `glob` パターンが `"page_*.png"` に変更されていること（表紙 cover.jpg のみ別途処理のため除外）
- [ ] エラーハンドリング・注意事項で Gemini API 固有の言及が OpenAI API に変更されていること
- [ ] E2E 確認手順の OCR テストコードが gpt-4o（openai）呼び出しに変更されていること
- [ ] `skill.md` 全体を通して `gemini-2.5-flash-image`・`GOOGLE_AI_STUDIO_API_KEY`（必須として記載）・`google-genai` の残存が 0 件であること（任意/レガシーとして明記されているものは除く）
- [ ] `skill.md` 全体を通してファイル拡張子 `.jpg` への参照が cover.jpg と既存データへの言及のみになっていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Step 7 の glob パターンが .png に変更されているか | 機能要件 | 25 |
| 2 | 全体を通して Google API 必須参照の完全除去ができているか | 整合性 | 30 |
| 3 | E2E 確認手順のテストコードが gpt-4o に変更されているか | 機能要件 | 20 |
| 4 | 変更点とスコープ外（維持すべき箇所）の境界が明確か | リクエスト一致 | 15 |
| 5 | 全工程の変更内容に矛盾・抜け漏れがないか（整合性最終確認） | 整合性 | 10 |
| 合計 | | | 100 |

---

## 動作確認手順（移行後テスト案）

### 方法1: 単ページ煙テスト（推奨・低コスト）

既存 vol1 の p045（ナレーション四角枠が含まれる難ページ）1 枚で動作確認。

```bash
# Step 5 相当の呼び出しを単体実行
python 03_成果物/outputs/openai-image-gen/vol1-sample/generate_v2_vertical.py
# 出力: 03_成果物/outputs/openai-image-gen/vol1-sample/v2/p045_*.png
# 目視確認: テキスト描画・コマ構成が正常であること
```

コスト: $0.21（1枚）

### 方法2: Step 5-QC OCR 単体テスト

上記で生成した p045.png に対して gpt-4o OCR を実行し、Blind-OCR 判定が PASS になることを確認。

コスト: ~$0.01（OCR 1回）

### 方法3: 新規書籍の vol1 冒頭10ページ E2E テスト

Step 3 → Step 5（10ページ分）→ Step 5-QC の一連フローを新規データで実行。

コスト: ~$3.50（10ページ × $0.21 + キャラ2枚 + OCR）

推奨: 方法1 + 方法2 で機能確認後、方法3 で実運用確認。

---

## リスク評価

| リスク | 影響度 | 発生確率 | 対策 |
|---|---|---|---|
| コスト急増（約4倍）でオーナーの使用抑制 | 高 | 低〜中 | 初回のみ quality=medium で試験、承認後 high に変更 |
| gpt-image-2 API 障害（OpenAI 側の障害） | 高 | 低 | google-genai を「任意・レガシー」として残すことで緊急時は NanoBanana2 に手動切り戻し可 |
| Blind-OCR（gpt-4o）の判定精度低下 | 中 | 低 | gpt-4o は vision 機能が成熟しており、マンガ OCR には十分な精度。FAIL → Pillow フォールバックで担保 |
| .jpg → .png 変更による Step 7 glob 漏れ | 高 | 中 | 工程6 の完了条件で明示的に検証 |
| 既存 vol1/vol2 の page_*.jpg と新規 page_*.png の混在 | 低 | 確実 | 既存データは再生成しないため影響なし（Step 7 は vol 別に glob を実行するため混在しない） |
| gpt-image-2 の max 参照画像数制限（10枚） | 低 | 低 | 現行もキャラ最大3枚。制限超過しない |

---

## 備考

- **gpt-image-2 の正式名称**: `gpt-image-2`（2026-04-21 リリース。`gpt-image-1`・`gpt-image-1.5`・`chatgpt-image-latest` は別モデル）
- **openai-image-gen スキル（`.claude/skills/openai-image-gen/SKILL.md`）との関係**: 現行は `gpt-image-1.5` を使用。ebook-to-manga は独立して `gpt-image-2` を使用する（スキル間の依存なし）
- **Google AI Studio API 残存の正当性**: vol1/vol2 の既存成果物はすべて NanoBanana2 で生成されており、再生成タイミングまでは `GOOGLE_AI_STUDIO_API_KEY` が .env に残る必要がある。即時削除はデータ依存性の観点でリスクがある
- **Organization Verification**: gpt-image-2（および `chatgpt-image-latest`）の使用には OpenAI Organization Verification が必要。2026-04-22 に認証済み（HANDOFF.md 参照）
- **参照実装**: `03_成果物/outputs/openai-image-gen/vol1-sample/generate_v2_vertical.py` が本 skill.md 変更の実装参考として使用可能（API 呼び出しパターン・b64_json デコード処理確認済み）。ただし追加プロンプトルール（縦書き・枠配置）はこのファイルに含まれているが、2026-04-23 の方針決定により skill.md への反映は行わない
