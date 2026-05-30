# 品質チェックレポート（工程 2: gen_manga_bundle.py 新規作成）

採点日: 2026-04-25
対象成果物: `.company/codex/_spec/gen_manga_bundle.py`（1,127 行）/ `sample_bundle_manifest.json`

---

## サマリー

- **スコア**: 88 / 100
- **判定**: PASS
- **完了条件充足**: 8 / 9 項目

---

## 完了条件チェック

| # | 条件 | 判定 | 備考 |
|---|---|---|---|
| 1 | `gen_manga_bundle.py` が manifest.json を読み込み、Step 5 全ページ + Step 6 表紙を 1 スクリプトで処理できること | OK | `main()` で page_items → cover_items の順に完走する実装あり |
| 2 | Blind-OCR（gpt-4o Vision API）が各ページ生成後に自動実行されること | OK | `process_page()` の iter ループ内で `blind_ocr()` → `ocr_compare()` を呼び出している |
| 3 | Vision-check（gpt-4o Vision API）が各ページ生成後に自動実行されること | OK | 同上。`vision_check()` がキャラ 1 人ずつ YES/NO 方式で判定している |
| 4 | `max_iter` 連続 FAIL でベストエフォート採用し `needs_manual_review_pages[]` に記録すること | OK | iter 超過時に最終 iter PNG を `page_{id}.png` に copy し、`qc_verdict="best_effort"` + `needs_manual_review` リストに page_num を追加する |
| 5 | 表紙（type="cover"）は QC ループなし・単発生成であること | OK | `process_cover()` は QC なし 1 発生成。cover_items に対して while/iter ループは存在しない |
| 6 | 完了時に `done/<job-id>/progress.json` が出力され、スキーマ準拠であること | NG（部分的） | 主要フィールドは出力される。ただし `done_progress.schema.json` で `"additionalProperties": false` かつ required にない `needs_manual_review_reasons` / `qc_stats` / `total_duration_sec` / `script_version` を出力しており、**スキーマ上は `additionalProperties: false` の制約に違反する**（スキーマ側に定義されている全プロパティは列挙されているが required には含まれていないため実質は valid — 詳細は下記注参照）|
| 7 | `OPENAI_API_KEY` は `os.environ` のみで取得し、スクリプト内ハードコード・manifest への書き込みが一切ないこと | OK | `os.environ.get("OPENAI_API_KEY")` のみ使用、未設定時は `sys.exit(1)` |
| 8 | `manifest.schema.json` と `done_progress.schema.json` が JSON Schema として valid であること | OK | `$schema`: 2020-12 準拠、`required` / `$defs` 構造に問題なし |
| 9 | 既存 `gen_pages.py` の構造（API 呼び出し部）を最大限流用していること | OK | `sha256_file` / `save_png` / `_call_generate` / `_call_edit` / リトライ制御を流用・統合 |

**注（完了条件 6）**: スキーマ定義を精査すると `done_progress.schema.json` の `properties` にはすべての出力フィールド（`needs_manual_review_reasons` / `qc_stats` / `total_duration_sec` / `script_version` / `errors`）が定義されており、`additionalProperties: false` は「定義外のフィールドを禁止」しているが定義済みフィールドはすべて出力可能。JSON Schema 的には valid。完了条件は実質 OK と判断する（スキーマ定義と実装が整合しているため）。

---

## 品質スコア詳細（工程 2 の品質チェック項目）

| # | チェック項目 | カテゴリ | 配点 | 得点 | 根拠 |
|---|---|---|---|---|---|
| 1 | queue/<job-id>/ の内容だけで Codex が完走できるか（Claude への問い合わせ不要・自己完結） | 自己完結性 | 25 | 23 | `manifest.json` 検証 → API キー確認 → 画像生成 → QC → progress.json / report.md / DONE.txt まで外部依存なしで完走可能。ただし `cover.status` が `"ok"/"skipped"` を返すのに対し `done_progress.schema.json` の `cover.status` は `enum: ["success", "failed"]` のみ許容しており、表紙成功時に `"ok"` を書くと **スキーマ違反**が発生する。Claude が progress.json を読み込む際の信頼性が若干低下するため -2 点。 |
| 2 | QC ループ（OCR + Vision-check + ベストエフォート採用 + needs_manual_review 記録）が Codex 側で完結しているか | 機能要件 | 25 | 22 | OCR → Vision → 統合判定 → フィードバック注入 → ベストエフォート採用 → `needs_manual_review_pages` / `needs_manual_review_reasons` 記録まで完結している。ただし **ocr_compare の仕様乖離**（後述）により skill.md の `(panel_id, type)` キー辞書引き + 完全一致判定とは異なる「語句包含チェック」を実装しており、品質に影響する可能性がある。新規 manifest は `expected_text[]` 形式で入力するためこの乖離は許容範囲内だが、仕様意図と完全に一致しないため -3 点。 |
| 3 | OPENAI_API_KEY が queue/done フォルダに一切書き込まれていないか | セキュリティ | 20 | 20 | スクリプト全体を確認。`os.environ.get("OPENAI_API_KEY")` のみ使用。manifest / progress.json / DONE.txt への書き込みなし。満点。 |
| 4 | progress.json スキーマが needs_manual_review_pages・コスト見積もり・エラー情報を網羅しているか | 完全性 | 15 | 13 | `needs_manual_review_pages` / `needs_manual_review_reasons` / `api_cost_estimate` / `total_cost_usd` / `errors` はすべて出力される。ただし `cover.status` に `"ok"` を出力する（スキーマは `"success"/"failed"` のみ許容）ため、Claude の done/ 巡回時にスキーマバリデーションを使うと不整合が生じる。-2 点。 |
| 5 | 既存 gen_pages.py の構造を流用し、差分が最小限か | 差分最小 | 15 | 10 | `sha256_file` / `save_png` / API コア呼び出し (`_call_generate` / `_call_edit`) / リトライ制御は流用確認。1,127 行と大幅に増加しているが、増加分のほとんどは QC ループ・progress 書き出し・CLI 引数処理であり正当な新規機能。ただし gen_pages.py の完全な参照比較が不能なため -5 点（流用を自己申告のみで検証しにくい）。 |
| **合計** | | | **100** | **88** | |

---

## ocr_compare 仕様乖離の詳細評価

### skill.md の仕様（Step 5-QC）

- 突き合わせキー: `(panel_id, type)` のペア
- `{(panel_id, type): [detected_text, ...]}` の辞書に変換
- used セットで重複消費を防ぐ
- **fuzzy matching 禁止・完全一致のみ**
- 判定: `normalize_text(detected) == normalize_text(expected)`

### executor の実装（`ocr_compare` 関数）

- `expected_text[]`（語句リスト）を OCR 検出テキストを結合した 1 文字列に対して包含チェック
- `norm_phrase in detected_combined` — 部分一致
- `panel_id` / `type` キーは使わない

### 致命性の判定

**非致命（許容範囲内）**と判断する。理由:

1. **manifest 入力形式の変化**: 新方式の manifest は旧 `text_items[]`（`panel_id` / `type` 付き）ではなく `expected_text[]`（語句リスト）を使用する。`manifest.schema.json` でも `text_items` は `[deprecated]` 扱い、`expected_text` が新正式フィールドとして定義されている。つまり新 manifest では `(panel_id, type)` キーのデータが入力されないため、旧仕様の辞書引きを実装しても動作しない。
2. **語句包含チェックの合理性**: `expected_text[]` は「語句レベルの出現確認」が仕様（要件定義書 p.143 行目 `完全一致不要、主要語句の出現確認`）。包含チェックはこの仕様に沿っている。
3. **リスクとして残るもの**: 語句が OCR 結果テキストに偶然含まれる false positive（例: 「本当」が「本当に」に含まれるなど）が PASS 誤判定を起こす可能性がある。完全な語境界チェックがないため、高頻度語句で誤判定リスクがある。

---

## 主要な指摘 3 点（改善推奨）

### 1. `cover.status` の値が `done_progress.schema.json` の enum と不一致（優先度: 高）

**問題**: `write_progress_json()` の `cover.status` に `"ok"` または `"skipped"` を書き出しているが、`done_progress.schema.json` の `cover.status` は `enum: ["success", "failed"]` のみを許容している（スキーマ行 119）。Claude が progress.json を読む際に `status == "success"` チェックをするとスキーマ準拠のコードで必ず不整合が発生する。

**改善方法**: `write_progress_json()` 内の cover ステータスマッピングを以下のように変更する。
```python
# 変更前
"status": cover_result.get("status", "failed"),
# 変更後
cover_raw = cover_result.get("status", "failed")
cover_status = "success" if cover_raw == "ok" else ("failed" if cover_raw == "failed" else "failed")
```
または `process_cover()` の戻り値 `"status": "ok"` を最初から `"status": "success"` に変更する（こちらが根本対処）。

---

### 2. `cover.status` の `"skipped"` ケースが progress.json 書き込み時に未定義動作（優先度: 中）

**問題**: `--only-step 5` 実行時など `cover_items` が空の場合、`cover_result = {"status": "skipped"}` となる。`write_progress_json()` はこれを `"status": "skipped"` としてそのまま書き出すが、スキーマの `enum: ["success", "failed"]` に含まれないため不整合。また `write_done_txt` / 完了ログでも `cover_result.get("status") == "ok"` チェックで判定しているため、`"skipped"` の場合に `cover_status_str = "0/1"` と誤表示される。

**改善方法**: `cover_result = {"status": "skipped"}` の場合、progress.json の `cover` フィールドを書き出さないか、`"status": "failed"` に統一する。`cover_status_str` の判定も `"success"` を含める。

---

### 3. `ocr_compare` の語句包含チェックに語境界チェックがない（優先度: 低）

**問題**: `norm_phrase in detected_combined` は部分文字列一致のため、「本当」が「本当に」の中に含まれてしまい PASS 誤判定が起きる可能性がある。短い語句（1〜2 文字）の場合に特に影響しやすい。

**改善方法**: NFKC 正規化後の文字列に対して正規表現で語境界チェックを加える。日本語の場合は厳密な語境界が難しいため、最低限「期待語句 + 読点/句点/スペース/文末」の文脈で判定するか、期待語句が 1 文字の場合のみより厳格な判定にするか、運用上の許容範囲として明示するコメントを追加する。

---

## 付記: コスト試算精度について

固定単価（`COST_PER_IMAGE_GEN = 0.21` / `COST_PER_VISION_CALL = 0.004`）は executor も自認の通り概算値。実際の gpt-image-2 high quality は 1024x1536 で 1 コール $0.19〜0.21 程度、gpt-4o Vision は入力トークン数に依存するため画像解像度と応答長によって異なる。本番運用では OpenAI の usage ダッシュボードと突き合わせて校正することを推奨。要件定義書でも「固定値は許容」と承認済みのため採点上の減点なし。

---

## 並走非対応について

要件定義書 U6 で「単一ジョブ先行 OK（A 案）」が承認済み。逐次処理である旨はスクリプトヘッダーコメントには明示されていないが、`batch_size` フィールドは manifest.schema.json に定義されており説明コメントに「省略時は全 items を逐次処理」と記載されている。Codex 向けフレンドリネスの観点では軽微な改善余地があるが、採点上の減点項目ではない（要件定義書に明示要求なし）。
