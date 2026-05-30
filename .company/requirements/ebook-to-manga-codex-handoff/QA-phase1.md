# 品質チェックレポート（第1回）

作成日: 2026-04-24
対象工程: 工程1 — ハンドオフ仕様設計
採点者: quality-checker

---

## サマリー

- **スコア**: 95 / 100
- **判定**: PASS
- **完了条件充足**: 8 / 8 項目

---

## 完了条件チェック

| # | 条件 | 判定 | 備考 |
|---|---|---|---|
| 1 | ハンドオフフォルダの推奨レイアウトが具体的パスで定義されていること | OK | SPEC.md セクション2にフォルダツリー図と全ファイル説明を記載 |
| 2 | `manifest.json` の全フィールドが定義されていること（入力側・出力側それぞれ） | OK | manifest.schema.json（入力側）/ done.schema.json（出力側）の双方で定義 |
| 3 | Codex 側スクリプト名・配置パス・引数・環境変数が定義されていること | OK | SPEC.md セクション6・8、gen_pages.py の argparse と os.environ 参照で定義 |
| 4 | `codex_instructions.md` の内容骨子が定義されていること | OK | codex_instructions_template.md に事前確認・実行方法・完了確認・失敗時対処まで記載 |
| 5 | 完了マーカー `DONE.json` のスキーマが定義されていること | OK | done.schema.json で JSON Schema Draft 2020-12 として定義 |
| 6 | Claude Code 側の再開トリガーコマンドが定義されていること | OK | SPEC.md セクション12で方法A（手動通知）/ 方法B（ポーリング）の2方式を定義 |
| 7 | エラー時（API 失敗・部分生成・ファイル欠損）のリトライ戦略が明記されていること | OK | SPEC.md セクション10に7種別のエラーパターンと対処を定義 |
| 8 | セキュリティ方針（OPENAI_API_KEY の受け渡し）が定義されていること | OK | SPEC.md セクション11に5項目の方針を明記、gen_pages.py で実装準拠 |

---

## 品質スコア詳細

| # | チェック項目 | 配点 | 得点 | 根拠 |
|---|---|---|---|---|
| 1 | 自己完結性 — ハンドオフフォルダのみで Codex が画像生成を完遂できるか | 25 | 23 | SPEC/manifest/gen_pages.py/codex_instructions_template の4点セットが揃い、Claude への問い合わせなしに動作できる設計として完備。ただし gen_pages.py の `output_dir` が manifest の `output_dir` フィールドを読まず `script_dir / "output"` にハードコードされており、schema 上定義されたフィールドが実際には無視される設計上の不整合が存在する（-2点） |
| 2 | manifest スキーマ — 入力側・出力側が明確に定義されているか | 20 | 19 | manifest.schema.json（入力側）と done.schema.json（出力側）ともに required フィールド・型・enum・additionalProperties: false まで適切に定義。唯一の問題として sample_manifest_page_batch.json のルートに `_comment` フィールドが含まれており、manifest.schema.json の `additionalProperties: false` に違反する（バリデーターで reject される）。page_003 の item にも `_comment` あり、同様に item スキーマ違反（-1点） |
| 3 | DONE.json / 再開トリガー整合性 | 15 | 15 | gen_pages.py の `write_done_json()` が done.schema.json の全必須フィールド（job_id, completed_at, status, generated, summary）を完全に出力。status enum（"success"/"partial"/"failed"）も一致。codex_instructions_template.md に Claude への再開メッセージ例も記載。完全整合 |
| 4 | OPENAI_API_KEY セキュリティ | 15 | 15 | SPEC.md セクション11の5項目方針（書き込み禁止・.env生成禁止・env委任・os.environ のみ取得・.gitignore推奨）がすべて実装に反映。gen_pages.py は `os.environ.get("OPENAI_API_KEY")` のみで取得しハードコードなし。codex_instructions_template.md に「このフォルダ内に API キーは含まれていません」の警告文あり |
| 5 | エラーハンドリング — API 失敗・部分生成・タイムアウトの戦略 | 15 | 13 | SPEC.md セクション10で7種別のエラーを網羅的に定義。gen_pages.py で try/except・指数バックオフ（`backoff_sec * 2^attempt`）・失敗時 sys.exit(1) を実装。done.schema.json で `generated[].error`・`summary.failed`・トップレベル `errors` 配列を定義。軽微問題として `--retry-failed` 実行時の generated リストが「既存成功分の dict 結合 + 再試行結果のリスト append」になるため、manifest の items 順序と DONE.json の generated 順序が一致しない可能性がある。Claude が DONE.json を検証する際に id マッチングで対応できるため致命的ではないが、仕様として明記されていない（-2点） |
| 6 | U-4 QC担当分離 — Codex 側に OCR/Vision-check が混入していないか | 10 | 10 | SPEC.md セクション9に専用の「QC ループの担当分離」セクションあり。セクション8「Codex が行わないこと」に OCR 判定・Vision-check・Pillow 合成・QC ループが明示。gen_pages.py のモジュール docstring にも「OCR 判定・Vision-check・Pillow 合成は行わない（Claude 側の責務）」と明記。manifest.schema.json の text_items フィールド説明にも「Claude 側の QC 処理のみが参照する」と記載。完全準拠 |
| **合計** | | **100** | **95** | |

---

## 指摘事項（合格のため改善不要だが、工程2以降での注意点）

### 軽微問題1: gen_pages.py が manifest の output_dir を無視
**問題**: gen_pages.py の main() で `output_dir = script_dir / "output"` とハードコードしており、manifest.json の `output_dir` フィールドを読まない。manifest.schema.json でこのフィールドを定義しているため設計上の不整合。
**影響**: 現状は `./output` が既定値なので動作上は問題なし。ただし将来的に出力先を変更したい場合に manifest を変えても反映されない。
**推奨対処**: `output_dir = (script_dir / manifest.get("output_dir", "./output")).resolve()` に変更する。

### 軽微問題2: サンプル manifest の _comment フィールドが schema 違反
**問題**: sample_manifest_page_batch.json のルートオブジェクトと items[2]（page_003）に `_comment` フィールドが含まれているが、manifest.schema.json は `additionalProperties: false` のため、JSON Schema バリデーターで validate すると reject される。
**影響**: サンプルは動作確認用のため実害なし。ただし「サンプルが schema に準拠している」という前提で検証ツールを使った場合に混乱を招く。
**推奨対処**: `_comment` フィールドを削除するか、schema に `"_comment": { "type": "string" }` を追加して許容する（後者が実用的）。

### 軽微問題3: --retry-failed 時の generated 順序が非保証
**問題**: `--retry-failed` 実行時、`existing_generated` は dict でキャッシュした「既存成功/スキップ分」を先頭に、再試行結果を末尾に append するため、最終的な DONE.json の `generated` 配列が manifest の `items` 順序と一致しない可能性がある。
**影響**: Claude が DONE.json を検証する際に id マッチングで対応できるため致命的ではない。ただし SPEC.md に「generated 配列と manifest.items の対応は id で行う」と明記されていないため、Claude 実装側で誤った前提（インデックス対応）で処理する可能性がある。
**推奨対処**: SPEC.md セクション7（Step N-C）に「DONE.json の generated リストは manifest.items の順序と一致しない場合がある。items[].id で対応付けること」を追記する。

---

## 総評

工程1の成果物として必要な要素（フォルダ構造・manifest スキーマ・完了マーカー・Codex 指示テンプレ・Pythonスクリプト・セキュリティ方針・エラー戦略・U-4設計方針）がすべて揃っており、Codex ハンドオフ方式を実現するための仕様書として十分な品質に達している。指摘した問題はいずれも軽微であり、工程2（skill.md 改修）の実施を妨げるものではない。
