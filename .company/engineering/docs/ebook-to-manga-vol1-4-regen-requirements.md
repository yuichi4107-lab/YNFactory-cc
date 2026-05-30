---
created: 2026-04-23
project: manga-career-restart
assignee: executor
status: draft
---

# 要件定義書: manga-career-restart vol1-4 全画像再生成

## ゴール

manga-career-restart vol1〜vol4（計342ページ）を最新 ebook-to-manga スキル（gpt-image-2 + Blind-OCR + Vision-check + Pillow フォールバック）で全ページ再生成し、各巻の `pages/page_{NNN}.png` が完備した状態にする。

---

## スコープ

### やること

- 工程1: 全4巻の `panels/comicle_output.csv`（3列）に、正規表現パースで4列目 `コマ別テキストJSON` を自動追記する（LLM 呼び出しなし）
- 工程2: 全4巻を順次（vol1 → vol2 → vol3 → vol4）Step 5 ハイブリッドQCループで再生成する。Blind-OCR + Vision-check 両方を機能させる。既存の旧モデル生成画像（JPG/PNG混在）は全て上書き対象とする
- 各巻の進捗を `{vol}/progress.json` で管理する

### やらないこと

- Step 2（シナリオ再作成）、Step 3（キャラ再生成）: 既存を流用
- Step 6（表紙）: 別タスク
- Step 7（EPUB製本）: 別タスク（画像再生成完了後に別途実施）
- 新規キャラ追加・話の差し替え
- `comicle_output_backup_pre_okuduke.csv` の削除（履歴として保持）
- LLM を使った Step 4 CSV 全面再生成（コスト節約のため正規表現パースで代替）

---

## 現状確認サマリー（調査済み）

| 巻 | CSVページ数 | 既存pages枚数 | 欠落ページ（旧） | CSV列数 | progress.json |
|---|---|---|---|---|---|
| vol1 | 84 | 78枚（JPG/PNG混在） | 1,33,53,82,83,84 | 3列 | あり（78完了）|
| vol2 | 78 | 73枚（JPG混在） | 1,3,35,77,78 | 3列 | なし |
| vol3 | 112 | 106枚（JPG混在） | 1,3,40,79,111,112 | 3列 | なし |
| vol4 | 68 | 62枚（JPG混在） | 1,3,35,36,67,68 | 3列 | なし |
| **合計** | **342** | — | — | — | — |

**重要**: vol1 の progress.json は旧モデル生成時のものであり、新スキルによる再生成では無効。全巻 progress.json をリセットして全ページ再生成する。

---

## 参照ファイルパス一覧

| ファイル | パス |
|---|---|
| スキル仕様 | `G:\マイドライブ\YNFactory-cc\.claude\skills\ebook-to-manga\skill.md` |
| panel_regions.json | `G:\マイドライブ\YNFactory-cc\.claude\skills\ebook-to-manga\panel_regions.json` |
| character_defs.json（全巻共用） | `G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\manuscript\character_defs.json` |
| キャラ参照画像（全巻共用） | `G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\manuscript\characters\*.png` |
| vol1 CSV | `G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol1\panels\comicle_output.csv` |
| vol2 CSV | `G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol2\panels\comicle_output.csv` |
| vol3 CSV | `G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\comicle_output.csv` |
| vol4 CSV | `G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol4\panels\comicle_output.csv` |
| ハイブリッドループ参照実装 | `G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\_prototype\hybrid_loop.py` |

---

## 工程一覧

| 工程 | 内容 | 中間成果物 | 入力 |
|---|---|---|---|
| 工程1: CSV 4列化 | 全4巻の CSV に `コマ別テキストJSON` を追記 | 4列 CSV × 4巻 + バックアップ | 既存3列 CSV × 4巻 |
| 工程2: 画像生成 | 全4巻 Step 5 ハイブリッドQCループ実行 | `pages/page_{NNN}.png` × 342ページ | 工程1の4列 CSV + キャラ参照画像 |
| 工程3: 表紙・EPUB | 別タスク（本要件定義ではスコープ外） | — | 工程2の成果物 |

---

## 工程1: CSV 4列化（全4巻）

### 概要

既存 CSV の3列目「漫画作成のプロンプト」本文から、コマごとのセリフ・ナレーションを正規表現でパースし、4列目 `コマ別テキストJSON` を生成して CSV に追記する。LLM 呼び出しは不要。

### 処理仕様

#### 入力・出力

- **入力**: `panels/comicle_output.csv`（UTF-8、3列: `ページ番号,使用するコマ割りテンプレ,漫画作成のプロンプト`）
- **出力**: 同ファイル上書き（4列目追記）
- **バックアップ**: 上書き前に `panels/comicle_output_before_4col.csv` として退避

#### ヘッダー更新

```
"ページ番号","使用するコマ割りテンプレ","漫画作成のプロンプト","コマ別テキストJSON"
```

#### テキストページの判定

`使用するコマ割りテンプレ` 列が `"テキストページ"` のページは 4列目を `[]` とする（画像生成不要ページ）。

#### コマ区切りパターン（優先順）

```python
# パターン1（主要形式）: "Nコマ目 (位置): 描写。 セリフ: ..."
PANEL_START = re.compile(r'(\d+)コマ目\s*\(([^)]+)\)[：:]')

# パターン2（位置なし）: "Nコマ目: 描写。 セリフ: ..."
PANEL_START_NOPOS = re.compile(r'(\d+)コマ目[：:]')
```

#### セリフ（dialogue）抽出パターン（優先順）

```python
# パターン1: 「[キャラ名]の吹き出しに「テキスト」」
re.compile(r'セリフ[：:]\s*\[([^\]]+)\]の吹き出しに「([^」]+)」')

# パターン2: 「[キャラ名]「テキスト」」（括弧省略形）
re.compile(r'セリフ[：:]\s*\[([^\]]+)\]「([^」]+)」')

# パターン3: 「[キャラ名]の声を出しに「テキスト」」（古い書式）
re.compile(r'セリフ[：:]\s*\[([^\]]+)\]の声を出しに「([^」]+)」')

# パターン4（複数セリフ対応）: 「[キャラ名]「テキスト」[キャラ名]「テキスト」」
#   → 上記パターンを findall で全件抽出後に順序保持

# なし判定: セリフ[:：]\s*なし
```

#### ナレーション（narration）抽出パターン

```python
# パターン1: 「ナレーション: [四角枠]テキスト」
re.compile(r'ナレーション[：:]\s*\[四角枠\](.+?)(?=\s*オノマトペ[：:]|\s*\d+コマ目|$)')

# パターン2: 「ナレーション: [ノート]テキスト」（古い書式）
re.compile(r'ナレーション[：:]\s*\[ノート\](.+?)(?=\s*オノマトペ[：:]|\s*\d+コマ目|$)')

# パターン3: 括弧なしナレーション
re.compile(r'ナレーション[：:]\s*(?!\s*なし)(.+?)(?=\s*オノマトペ[：:]|\s*\d+コマ目|$)')

# なし判定: ナレーション[:：]\s*なし
```

#### JSON スキーマ（skill.md 準拠）

```json
[
  {"panel_id": 1, "type": "dialogue",  "speaker": "キャラ名", "text": "セリフ本文"},
  {"panel_id": 1, "type": "narration", "speaker": null,       "text": "ナレーション本文"},
  {"panel_id": 2, "type": "dialogue",  "speaker": "キャラ名", "text": "セリフ本文"}
]
```

- 1コマ内に複数セリフ・ナレーションがある場合は別オブジェクトとして配列に追記
- オノマトペは含めない
- セリフもナレーションもない場合は `[]`

#### エラーハンドリング・フォールバック方針

| ケース | 対処 |
|---|---|
| パターン1〜3すべてにマッチしないセリフ行 | `[]` として処理。警告ログを出力し、該当ページ番号・プロンプト断片を `panels/parse_warnings.log` に記録 |
| ページ全体のパース失敗（例外発生） | そのページを `[]` とし、例外内容を `parse_warnings.log` に記録。処理は続行 |
| 4列目が既に存在する場合 | バックアップ後に上書き（べき等処理） |
| エンコーディング | UTF-8 固定（調査済み）。BOM なし |

### 承認ポイント

**工程1完了後**: vol1 の冒頭10ページの4列目 JSON をオーナーに提示し、パース精度を確認する。承認後に工程2へ進む。

### 完了条件チェックリスト

- [ ] 全4巻の CSV に4列目ヘッダー `コマ別テキストJSON` が追加されていること
- [ ] 各巻の `panels/comicle_output_before_4col.csv` バックアップが存在すること
- [ ] テキストページ（テンプレ=テキストページ）はすべて `[]` になっていること
- [ ] セリフありページ（少なくとも1エントリ以上）の4列目が空配列 `[]` でないこと
- [ ] vol1 冒頭10ページのサンプルをオーナーが承認していること
- [ ] `parse_warnings.log` が存在し、パース失敗ページ数が全体の 5% 未満であること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | テキストページの `[]` 設定率（全テキストページが `[]` であること） | 機能要件 | 20 |
| 2 | セリフありページのパース成功率（セリフ有ページの95%以上でdialogue/narrationが1件以上抽出されていること） | 機能要件 | 25 |
| 3 | 複数セリフページの分解正確性（1コマ内2セリフ以上のページで全セリフが別オブジェクトとして分解されていること） | 機能要件 | 20 |
| 4 | JSON スキーマ準拠（全エントリが panel_id/type/speaker/text の4フィールドを持ち、typeが dialogue/narration のみであること） | データ品質 | 15 |
| 5 | バックアップ整合性（backup CSV の行数 = 処理前の行数と一致すること） | データ品質 | 10 |
| 6 | parse_warnings.log のパース失敗率（全ページの5%未満であること） | エラーハンドリング | 10 |
| **合計** | | | **100** |

---

## 工程2: Step 5 画像生成（vol1-4 順次実行）

### 概要

工程1で4列化した CSV を入力として、vol1 → vol2 → vol3 → vol4 の順に Step 5 ハイブリッドQCループを実行する。既存の旧モデル生成画像（JPG/PNG混在）は全て新規 PNG で上書きする。

### 実行前確認事項

各巻の実行前に以下を確認する:

1. `panels/comicle_output.csv` の列数が4であること
2. `manuscript/characters/character_defs.json` が存在すること
3. `manuscript/characters/*.png`（キャラ参照画像）が存在すること
4. `pages/` ディレクトリが存在すること（なければ作成）
5. `progress.json` のリセット（新規作成 `{"completed": [], "failed": [], "fallback": []}`）

**注意**: vol1 の既存 `progress.json`（旧モデル時代の78完了記録）は削除またはリセットして全ページ再生成する。

### バッチ戦略

| パラメータ | 設定値 | 根拠 |
|---|---|---|
| バッチサイズ | 10ページ | API レート制限対策 + エラー影響範囲を限定 |
| バッチ間待機 | 5秒 | skill.md 仕様 |
| バッチ内並列 | `run_in_background: true` で10ページ並列 | 処理速度最大化 |
| max_iter | 3 | skill.md 既定値（OCR FAIL 3回でフォールバック発動） |
| モデル | gpt-image-2 | skill.md 仕様 |
| 出力サイズ | 1024x1536（9:16縦長） | skill.md 仕様 |
| 品質 | high | skill.md 仕様 |
| 出力形式 | PNG（b64_json をバイナリ保存） | skill.md 仕様 |

### 並列実行ガイドライン

1. **バッチ内並列**: 1バッチ（10ページ）内の各ページを `run_in_background: true` で並列実行する
2. **バッチ間逐次**: バッチ完了後に5秒待機してから次バッチを開始する
3. **巻間逐次**: vol1 の全バッチ完了後に vol2 を開始する（vol1 承認確認ポイントあり）
4. **A路線内逐次**: 同一ページの iter 1→2→3 は逐次実行（前 iter の結果がフィードバックになるため）

### 承認ポイント（中間確認）

- **vol1 第1バッチ（1〜10ページ）完了後**: Vision-check PASS率・OCR PASS率・実コストをオーナーに提示。承認後に vol1 残りを続行する
- **vol1 全完了後**: 最終 progress.json と実コスト実績を報告。承認後に vol2 を開始する

### ファイル命名規則

| ファイル | パス |
|---|---|
| 各イテレーション中間ファイル | `{vol}/pages/page_{NNN:03d}_iter_{iter}.png` |
| 確定ページ（PASS 後コピー） | `{vol}/pages/page_{NNN:03d}.png` |
| フォールバック確定ページ | `{vol}/pages/page_{NNN:03d}.png`（composited からリネーム） |
| 進捗管理 | `{vol}/progress.json` |

### コスト予算と中断条件

**内訳積み上げ見積もり:**

| 項目 | 単価 | 数量 | 計 |
|---|---|---|---|
| gpt-image-2 生成（1024x1536 high） | $0.21/枚 | 342ページ × 平均1.2iter | ~$86 |
| Blind-OCR（gpt-4o） | ~$0.01/コール | 342ページ × 平均1.5コール | ~$5 |
| Vision-check（gpt-4o） | ~$0.005〜0.01/コール | 342ページ × 平均1.2コール | ~$2〜$4 |
| フォールバック clean regen（5%） | $0.21/枚 | 17枚 | ~$3.5 |
| **合計（標準見積もり）** | | | **~$97〜$100** |

**予算上限**: $150（バッファ込み）

**中断条件（いずれかに該当したらオーナーに相談）:**
1. 累計コストが $120 を超過した時点
2. フォールバック発動率が 20% を超えた時点（品質問題の兆候）
3. OCR PASS率が 70% を下回るバッチが連続2バッチ発生した時点
4. Vision-check PASS率が 80% を下回るバッチが連続2バッチ発生した時点
5. API エラー（認証失敗・課金上限）が発生した時点

### progress.json 仕様

```json
{
  "completed": [2, 3, 4, ...],
  "failed": [],
  "fallback": [
    {"page": 15, "reason": "ocr_fail", "iter_count": 3}
  ],
  "stats": {
    "total_pages": 84,
    "ocr_pass_count": 0,
    "vision_pass_count": 0,
    "fallback_count": 0,
    "estimated_cost_usd": 0.0
  }
}
```

### 完了条件チェックリスト

- [ ] 全4巻の `pages/page_{NNN}.png`（テキストページを除く画像生成対象ページ）が存在すること
  - vol1: 83ページ（page_001 はテキストページ `[]` のため生成なし → 実際はCSV確認後に確定）
  - vol2: 77ページ相当
  - vol3: 111ページ相当
  - vol4: 67ページ相当
- [ ] 全ページが PNG 形式で保存されていること（JPG 不可）
- [ ] 各巻の `progress.json` が存在し、`completed` 配列に全画像生成対象ページが含まれていること
- [ ] vol1 第1バッチのオーナー承認が完了していること
- [ ] vol1 全完了後のオーナー承認が完了していること
- [ ] 累計コストが $150 未満であること
- [ ] フォールバック発動率が全ページの 20% 未満であること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 完了ページ率（全画像生成対象ページの `pages/page_{NNN}.png` 存在率が 100% であること） | 機能要件 | 30 |
| 2 | 出力形式（全ページが PNG 形式であること、JPG が混在していないこと） | 機能要件 | 15 |
| 3 | OCR PASS率（全巻合計で 85% 以上の画像生成ページが OCR PASS または フォールバック経由でテキスト正確性保証済みであること） | 品質 | 20 |
| 4 | Vision-check PASS率（全巻合計で 90% 以上のページが Vision-check PASS であること） | 品質 | 15 |
| 5 | フォールバック発動率（全ページの 20% 未満であること） | 品質 | 10 |
| 6 | 実コスト（$150 未満であること） | コスト | 10 |
| **合計** | | | **100** |

---

## 工程3: 表紙・EPUB製本（スコープ外）

本要件定義ではスコープ外。工程2完了・オーナー承認後に別途要件定義を行う。

**引き継ぎ先成果物:**
- `{vol}/pages/page_{NNN}.png`（全 342ページ相当）
- `{vol}/progress.json`（実績コスト・フォールバック記録）

---

## ループ上限

各工程とも最大5回（実行→チェック）。超過時はオーナーに相談する。

---

## 備考

### character_defs.json の構造（確認済み）

全巻共用。`manuscript/character_defs.json` にキャラ名 → 外見説明のオブジェクト形式で格納。skill.md の `extract_page_chars()` が参照する際は配列形式 `[{"id": "...", "name": "...", "appearance": "..."}]` を想定しているが、実際は `{"ミサキ": "外見説明", ...}` の辞書形式。実装時は `[{"name": k, "appearance": v} for k, v in char_defs.items()]` に変換して渡すこと。

### キャラ参照画像の場所（確認済み）

`manuscript/characters/` 配下に全巻共用で配置:
- `ミサキ.png`, `ケンタ.png`, `山田課長.png`, `ひなた_赤ちゃん期.png`, `ひなた_2歳期.png`, `タクヤ.png`

vol ごとの `manuscript/characters/` は存在しない。CSV プロンプト内の `添付の〇〇.png` は全て共通パスを参照する。

### vol1 の progress.json 取り扱い

既存 `progress.json` には旧モデル（NanoBanana2）時代の78ページ完了記録が含まれる。新スキルでの再生成では全ページを再生成するため、工程2開始前にリセット（新規作成）する。

### 既存 pages の取り扱い

各巻の `pages/` ディレクトリには旧モデル生成の JPG/PNG 混在ファイルが存在する。工程2では全ページを新規 PNG で上書きするため、既存ファイルのバックアップは不要（旧ファイルは `pages_backup_20260414/` 等で一部已にバックアップ済み）。ただし意図しない上書きを防ぐため、工程2開始前に既存 pages の枚数をログ出力して確認する。
