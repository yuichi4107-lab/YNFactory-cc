# 品質チェックレポート（第1回）— 工程3: サンプルデータ確認・ドライラン手順整備

実施日: 2026-04-24
採点者: quality-checker

---

## サマリー

- **スコア**: 79 / 100
- **判定**: FAIL
- **完了条件充足**: 3 / 4 項目

---

## 完了条件チェック

| # | 条件 | 判定 | 備考 |
|---|---|---|---|
| 1 | `03_成果物/outputs/ebooks-manga/manga-career-restart/vol1/` の現状ファイル一覧が確認済みであること | OK | VERIFICATION.md §3 で git status を実行し、vol1 の変更が本工程起因でないことを確認・記録している |
| 2 | ドライラン A〜C の実施手順が明文化されていること | OK | README.md に手順が具体的に記載されている。ただしドライラン B・C は「手順記載のみ・未実施」であり要件定義書の「サンプル実行に必要な…手順」の観点では記載として充足 |
| 3 | サンプル実行に必要な環境変数・依存ライブラリがリストアップされていること | OK | README で `python 3.8+`・`pip install openai pillow`・`OPENAI_API_KEY` が明示されている |
| 4 | ドライランが既存 vol1 出力ファイルを破壊しないことが保証されていること（出力先の分離） | NG | 成果物の分離自体は担保できているが、`_sample-run/` 配下に Windows の `desktop.ini` が4件混入しており、「このフォルダ内のファイルのみ」という保証が厳密には崩れている |

---

## 品質スコア詳細

| # | チェック項目（工程3 の品質基準） | 配点 | 得点 | 根拠 |
|---|---|---|---|---|
| 1 | ドライラン A〜C の実施手順が具体的かつ再現可能であること | 30 | 23 | ドライラン A（`--dry-run --skip-image-check`）は手順・期待出力・成功チェックリストが揃っており再現性は高い。cwd が相対パス指定（`cd .company/...`）のため「プロジェクトルートから実行」という前提の明示が必要だが、他端末でも迷わず実行できる水準。一方ドライラン B・C は手順が記載されているにもかかわらず実際の実施と証跡がなく「再現可能な手順書」としての完成度が不十分。-7点 |
| 2 | 既存 vol1 出力が破壊されないことが手順上で保証されていること | 25 | 20 | `_sample-run/` への隔離設計・README の片付け手順・VERIFICATION.md §3 の git status 証跡と判定「問題なし」の明記は優秀。ただし `desktop.ini`（Windows Explorer が自動生成）が `characters/`・`output/`・`dryrun_job/`・`_sample-run/` の計4箇所に混入しており、「このフォルダ内のファイルのみ」という隔離の明快さを損なっている。削除方法や `.gitignore` への追記について言及がない。-5点 |
| 3 | 必要な依存ライブラリ・環境変数が網羅されていること | 20 | 18 | `openai`・`pillow`・`OPENAI_API_KEY`・`Python 3.8+` が README に記載されている。ドライランのみなら `openai` は不要（README も「ドライランのみなら不要」と正確に区別して記述）。`pytesseract`（ドライラン C で Claude 側が Step 5-C を確認する場合に必要）への言及がないが、ドライラン C が未実施のためスコープ外として許容範囲。-2点（ドライラン C の依存を未整理のまま残している） |
| 4 | ドライランの合否判定基準が明確であること（何を見て成功と判断するか） | 25 | 18 | ドライラン A の成功チェックリスト（終了コード 0・`検証 OK` 表示・`output/` に不要ファイルなし）は明確。DONE.json のサンプル形式と本番実行後の期待値も記載されている。しかし「ドライラン B・C の合否判定基準」が未整備。ドライラン B は DONE.json の `status: success`・`summary.skipped == 1` が明示されているが、**ドライラン C（Step 5-C が起動することの確認方法）の判定基準がまったく書かれていない**。-7点 |
| 合計 | | 100 | 79 | |

---

## 必須チェック項目（採点基準外・合否には影響するが配点不明のため参考扱い）

以下の項目は採点基準には配点記載がないため参考チェックとして実施する。スコアへの影響なし。

### (1) 既存 vol1 非破壊（参考チェック）

git status 確認: `manga-career-restart/vol1/` への本工程起因の変更はゼロ。
VERIFICATION.md §3 で「本工程開始前からすでに git 上で deleted（ステージ済み）」と明記しており、本工程では無関係であることが証跡付きで確認できる。**問題なし**。

### (2) 隔離性（参考チェック）

成果物は `.company/handoff/codex-image-gen/_sample-run/` 配下に収まっている。**基本的に問題なし**。ただし `desktop.ini`（246 bytes, Windows システムファイル）が計4件混入しているため、フォルダの内容が意図したファイルのみではない状態。本番利用前に要クリーンアップ。

### (3) 課金ゼロ（参考チェック）

VERIFICATION.md §1 に「API 呼び出し: なし（課金なし）」と明記・出力全文掲載。`--dry-run` + `--skip-image-check` を使用しており、スクリプトコードも `dry_run` ブロックで `return` するため API へ到達しない。**問題なし**。

### (4) ドライラン再現性（参考チェック）

`python gen_pages.py --dry-run --skip-image-check` のコマンド・期待出力・cwd が README に明示されており、他端末でも追従できる。`Path(__file__).parent` でスクリプト相対パス解決しているため cwd に依存しない設計。**問題なし（小注意: cd の前提をプロジェクトルートと明示する一文があると親切）**。

### (5) スキーマ整合（参考チェック・重要）

`manifest.schema.json` の `additionalProperties: false` + `required` フィールドを Python スクリプトで確認した結果:

- トップレベル: required 全項目あり、余分フィールドなし → **OK**
- item[1] page_001, item[2] page_002: 全 required フィールドあり、余分フィールドなし → **OK**
- item[3] page_003: required フィールドはあるが **`prompt: ""` (空文字列) でスキーマの `minLength: 1` 違反** → **NG**

`is_text_only: true` のページでも schema 上 `prompt` は `minLength: 1` 必須のため、厳密なスキーマバリデーション（`jsonschema` 等）を通すと失敗する。VERIFICATION.md §2 は手動チェックスクリプト（required フィールドの存在確認のみ）を実行しており、`minLength` 違反を見逃している。

### (6) `--skip-image-check` の副作用（参考チェック）

`--dry-run` なしの本番モードでは `args.skip_image_check` を参照するコードが `dry_run` ブロック内にのみ存在するため、**本番実行に `--skip-image-check` の副作用はゼロ**。`call_edit()` 内の画像存在チェックは独立した実装であり影響を受けない。**問題なし**。

### (7) README の明快さ（参考チェック）

Claude 側 / Codex 側の役割分担と手順順序が「Claude 側（準備フェーズ）」「Codex 側（本番確認フェーズ）」として明確に区分けされている。初見ユーザーが迷わず手順を追える構成。**良好**。

### (8) VERIFICATION.md の証跡（参考チェック）

- 出力末尾の全文: 記載あり
- git status 差分: 記載あり（§3）
- skill.md 参照 grep 結果: 記載あり（§4）
- manifest JSON チェックスクリプトの出力: 記載あり（§2）
- ただし `minLength` 違反の見落としがある（§2 チェックが不完全）

### (9) 片付け指示（参考チェック）

README 末尾に `rm -rf .company/handoff/codex-image-gen/_sample-run/` コマンドと「本番の制作物に一切影響しません」の明記あり。**問題なし**。

### (10) 残課題の明示（参考チェック）

VERIFICATION.md §5 に「本工程で `_spec/gen_pages.py` に最小限の修正を加えた」旨と変更理由・影響範囲が記述されている。ドライラン B・C が未実施であることは README の「次回の漫画化案件で使う前に…」という文脈で暗示されているが、**未実施であることと「実 API 検証は次の本番時に確認すること」という残課題の明示が VERIFICATION.md に不足している**。

### (11) `.gitkeep` の配置（参考チェック）

`characters/` に `.gitkeep` が配置されている。ただし同じフォルダに `desktop.ini` も混入しており、「ダミー PNG が混入していないか」という点では PNG 混入はないが、予期しないバイナリファイル（`desktop.ini`）が存在する。

### (12) `codex_instructions.md` への言及（参考チェック）

README・VERIFICATION.md ともに `codex_instructions.md` への言及がない。`_sample-run/` には `codex_instructions.md` を配置していないが、その理由（ドライランは manifest+スクリプトの検証のみで Codex CLI を実際に起動しないため不要）の説明もない。本番での自動生成フローへの言及もなし。

---

## 改善指示（不合格のため）

### 優先度1: ドライランの合否判定基準（得点: 18/25）

**問題**: ドライラン C（Step 5-C 戻り受け取りの確認）の実施手順と合否判定基準が未整備。README に手順箇条書きはあるが「何を見て成功と判断するか」の基準が書かれていない。

**改善方法**:
1. README の「成功条件チェックリスト」に以下を追加する:
   - ドライラン B: `output/DONE.json` が存在し `status == "success"` かつ `summary.skipped == 1` であること
   - ドライラン C: （手動で `DONE.json` を配置後）Claude の `Step 5-C` コマンドが実行でき、OCR ループが起動するコンソールログが出ること
2. または VERIFICATION.md に「ドライラン B・C は本番時に初回実施予定（残課題）」として明示的に残課題化する

### 優先度2: ドライラン A〜C の再現性（得点: 23/30）

**問題**: ドライラン B・C が手順記載のみで実施・証跡なし。特にドライラン A（実施済み）との対比で B・C が「やっていない」のか「やる必要がない」のかが不明瞭。

**改善方法**:
1. VERIFICATION.md に「ドライラン B・C: 未実施（理由: 本工程では API 呼び出しなしの検証のみを対象とした。実 API 検証は本番初回時に実施予定）」と明記する
2. README に「ドライラン A のみ事前確認済み。B・C は本番時に初回確認してください」という注記を追加する

### 優先度3: スキーマ違反（manifest.json の `page_003.prompt`）

**問題**: `manifest.schema.json` の item.prompt は `minLength: 1` 必須だが、`page_003`（`is_text_only: true`）の `prompt` が `""` (空文字列) のためスキーマ違反。VERIFICATION.md §2 のチェックスクリプトが `minLength` を検証していないため見落とされている。

**改善方法**:
以下のどちらかを選択する:
- **(A) manifest を修正**: `page_003` の `prompt` を `"（テキストページ）"` 等、1文字以上の文字列にする
- **(B) schema を修正**: `is_text_only: true` の場合は prompt が空文字列を許容するよう `oneOf` 条件を追加する（ただし schema が複雑になるため A 推奨）

VERIFICATION.md §2 のチェックスクリプトに `minLength` チェックを追加して再実行し、結果を記録することも必要。

### 優先度4: `desktop.ini` の混入（隔離性）

**問題**: Windows Explorer が自動生成した `desktop.ini`（246 bytes）が `_sample-run/`・`_sample-run/dryrun_job/`・`characters/`・`output/` の計4箇所に存在し、「検証専用ファイルのみ」という状態でなくなっている。git 管理下に入る場合に不要ファイルがコミットされるリスクもある。

**改善方法**:
1. `desktop.ini` を削除する: `find .company/handoff/codex-image-gen/_sample-run -name desktop.ini -delete`
2. プロジェクトの `.gitignore` に `desktop.ini` を追加する（または既存の `.gitignore` に記載があるか確認する）

---

## 合格までの必要作業まとめ

| 優先度 | 対応ファイル | 作業内容 | 難易度 |
|---|---|---|---|
| 1 | VERIFICATION.md | ドライラン B・C の残課題明示を追記 | 低（テキスト追記のみ） |
| 1 | README.md | ドライラン B・C の合否判定基準を追記 | 低（テキスト追記のみ） |
| 2 | dryrun_job/manifest.json | `page_003.prompt` を空文字列から 1 文字以上に修正 | 低（1行修正） |
| 2 | VERIFICATION.md §2 | `minLength` チェックを追加して再実行・結果記録 | 低（スクリプト修正＋再実行） |
| 3 | `_sample-run/` 配下 | `desktop.ini` を4件削除 | 低（コマンド1発） |

上記5点は低難度の修正のみ。次回イテレーションで85点以上は達成可能。
