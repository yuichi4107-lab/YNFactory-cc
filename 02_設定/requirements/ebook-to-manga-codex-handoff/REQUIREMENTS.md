> **【この要件定義は 2026-04-25 に fire-and-forget 型に切替のため superseded。新要件は `02_設定/requirements/ebook-to-manga-codex-fire-and-forget/REQUIREMENTS.md` を参照】**

# 要件定義書: ebook-to-manga Codex ハンドオフ方式への移行

作成日: 2026-04-24
対象スキル: `.claude/skills/ebook-to-manga/skill.md`

---

## ゴール

ebook-to-manga パイプラインの画像生成工程（Step 3 / Step 5 / Step 5.5 / Step 6）を
Claude Code 内完結から「ハンドオフフォルダ経由で別ターミナルの Codex CLI に委託」する方式へ移行し、
Claude Code は前処理・後処理（OCR 検証・Pillow 合成・EPUB化）に専念できる構成にする。

---

## スコープ

### やること

- ハンドオフフォルダの構造設計（フォルダレイアウト・manifest スキーマ・命名規則）
- skill.md の Step 3 / Step 5 / Step 5.5 / Step 6 を「ハンドオフ準備」と「戻り受け取り」に分離する改修仕様
- Codex 側が実行する Python スクリプト群の仕様定義（ファイル名・引数・環境変数）
- ユーザーが Codex CLI に渡す指示テンプレート文（ `codex_instructions.md` の内容仕様）
- 完了マーカー（`DONE.json`）のスキーマ定義
- Claude Code 側の「再開トリガー」の呼び出し仕様
- エラー・部分生成時のリトライ戦略

### やらないこと

- Codex CLI 本体の動作変更・設定変更
- OCR 検証ロジック（Step 5-QC）の刷新（既存ロジックを維持）
- Pillow 合成フォールバック（Step 5.5）のロジック変更
- EPUB フォーマット（Step 7）の変更
- KDP メタデータ（Step 8）の変更
- Step 1 / Step 2 / Step 4 の変更
- CI/CD や自動デプロイの整備

---

## ユーザー確認事項（要承認）

以下の設計判断について、実装前にユーザーの意思決定が必要です。

| # | 確認事項 | 選択肢 | 推奨案 |
|---|---|---|---|
| U-1 | 既存の Claude 内完結版を残すか？ | A) 削除して新方式のみ / B) フラグ切り替えで両方維持 | **B案推奨**（`HANDOFF_MODE=true` 環境変数で切り替え。既存ロジックをフォールバックとして保持） |
| U-2 | Codex 側スクリプトの言語・SDK | A) 既存 openai Python SDK をそのまま流用 / B) 新規スクリプト作成 | **A案推奨**（skill.md に記載済みのコードを直接 Codex スクリプトとして配置） |
| U-3 | ハンドオフフォルダの配置先 | A) `.company/handoff/codex-image-gen/<job-id>/` / B) 出力フォルダ直下の `_handoff/` サブディレクトリ | **A案推奨**（一元管理しやすく、複数ジョブの並走に対応） |
| U-4 | Step 5 の OCR/Vision-check QC ループを誰が回すか（最重要設計判断） | A) Codex 側でループを回し、PASS した画像のみ Claude に返す / B) Claude 側が QC を担当し、FAIL 時は Codex へ再ハンドオフ / C) Codex は pure 生成のみ、QC は全部 Claude | **C案推奨**（関心の分離が明確。Codex = 生成専用、Claude = OCR/Vision-check/Pillow 合成。Codex 側の複雑化を防ぐ） |
| U-5 | ジョブ管理: 単一ジョブのみか複数並走対応か | A) 単一ジョブのみ（シンプル） / B) 複数ジョブ並走（job-id 管理） | **B案推奨**（フォルダ名に job-id を含める設計にしておく。起動時は 1 ジョブでも後から拡張容易） |

---

## 工程一覧

| 工程 | 中間成果物 | 入力 |
|---|---|---|
| 工程1: ハンドオフ仕様設計 | フォルダ構造仕様・manifest スキーマ・Codex 指示テンプレ | ユーザー確認済み回答 + skill.md 現状 |
| 工程2: skill.md 改修 | 改修済み skill.md（Step 3/5/5.5/6 の分離） | 工程1の成果物 |
| 工程3: サンプルデータ準備・動作確認仕様 | テスト計画書 + サンプルデータ配置手順 | 工程2の成果物 + 既存 manga-career-restart/vol1/ |

---

## 工程1: ハンドオフ仕様設計

### 完了条件

- [ ] ハンドオフフォルダの推奨レイアウトが具体的パスで定義されていること
- [ ] `manifest.json` の全フィールドが定義されていること（入力側・出力側それぞれ）
- [ ] Codex 側スクリプト名・配置パス・引数・環境変数が定義されていること
- [ ] `codex_instructions.md`（ユーザーが Codex に渡す指示テンプレ）の内容骨子が定義されていること
- [ ] 完了マーカー `DONE.json` のスキーマが定義されていること
- [ ] Claude Code 側の再開トリガーコマンドが定義されていること
- [ ] エラー時（API 失敗・部分生成・ファイル欠損）のリトライ戦略が明記されていること
- [ ] セキュリティ方針（OPENAI_API_KEY の受け渡し）が定義されていること

### 品質チェック項目（工程1）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | ハンドオフフォルダの情報だけで Codex が自己完結して画像生成できるか（Claude へ問い合わせ不要） | 設計・機能要件 | 25 |
| 2 | manifest スキーマが入力側（Claude→Codex）と出力側（Codex→Claude）で明確に定義されているか | 設計・完全性 | 20 |
| 3 | `DONE.json` / `DONE.txt` 等の完了マーカーが定義され、Claude の再開トリガーと整合しているか | 設計・整合性 | 15 |
| 4 | OPENAI_API_KEY を Claude が Codex に渡さず、Codex 側の env のみで解決する方針が明記されているか | セキュリティ | 15 |
| 5 | エラー（API 失敗・部分生成・タイムアウト）の検出・リトライ・フォールバック戦略が明記されているか | エラーハンドリング | 15 |
| 6 | U-4（QC ループの担当分離）の設計判断が仕様に反映されているか | 設計・方針 | 10 |
| 合計 | | | 100 |

---

## 工程2: skill.md 改修

### 改修対象セクション

#### Step 3（キャラリファレンス画像生成）の分離

**現状**: Claude Code が直接 `client.images.generate` を呼び出して PNG を生成・保存。

**変更後**:
- `Step 3-A: ハンドオフ準備`（Claude が実行）
  - キャラクター定義 JSON の確定
  - Step 3 用 manifest.json の生成（生成すべきキャラ名・プロンプト・サイズ・出力命名規則）
  - ハンドオフフォルダ `handoff/<job-id>/step3/` の作成と配置
  - `codex_instructions.md` の自動生成
- `Step 3-B: Codex ハンドオフ待機`（ユーザーが Codex CLI を起動）
  - Claude は `DONE.json` の出現を確認するまで待機
- `Step 3-C: 戻り受け取り`（Claude が実行）
  - `DONE.json` の検証（全キャラ画像の存在確認）
  - `manuscript/characters/` への画像コピー
  - ユーザー確認（Step 3-3 既存フロー）

#### Step 5（本文ページ画像生成）の分離

**現状**: Claude が 10ページ/バッチ×並列実行で `client.images.edit` を呼び出す。ハイブリッド QC ループ（OCR + Vision-check）も Claude が回す。

**変更後**（U-4 の C 案採用前提）:
- `Step 5-A: ハンドオフ準備`（Claude が実行）
  - CSV の全ページ情報を step5_manifest.json に変換
  - キャラリファレンス PNG（`manuscript/characters/`）をハンドオフフォルダにコピー
  - バッチ分割情報（batch_size=10）をマニフェストに記載
  - `gen_pages.py`（生成専用スクリプト）をハンドオフフォルダに配置
  - `codex_instructions.md` の自動生成（バッチ実行手順含む）
- `Step 5-B: Codex ハンドオフ待機`（ユーザーが Codex CLI を起動）
  - Codex は `gen_pages.py` を実行し、全ページ `page_{NNN}_iter_1.png` を生成・保存
  - 完了後 `DONE.json` を出力
- `Step 5-C: 戻り受け取り + QC ループ`（Claude が実行）
  - 生成済み画像を取り込み、**既存の Blind-OCR + Vision-check ループ（Step 5-QC）を Claude 側で実行**
  - FAIL ページは Codex への再ハンドオフ（`step5_regen/` サブフォルダ）または Pillow フォールバック（Step 5.5）へ

#### Step 5.5（Pillow 合成フォールバック）

変更なし。Step 5-C の一部として Claude が実行する（U-4 C 案）。
clean regen が必要な場合のみ、対象ページを `step5_regen/` としてミニハンドオフ。

#### Step 6（カバー画像生成）の分離

**現状**: Claude が `client.images.edit` を呼び出す（単一画像）。

**変更後**:
- `Step 6-A: ハンドオフ準備`（Claude が実行）
  - step6_manifest.json の生成（カバープロンプト・参照キャラ PNG・サイズ・出力命名）
  - `gen_cover.py` をハンドオフフォルダに配置
  - `codex_instructions.md` 生成
- `Step 6-B: Codex ハンドオフ待機`
- `Step 6-C: 戻り受け取り`
  - `cover.png` → `cover.jpg`（Pillow で PNG→JPEG 変換は Claude 側で実行）
  - ユーザー確認

### 完了条件

- [ ] Step 3 が 3-A / 3-B / 3-C のサブステップに分離されていること
- [ ] Step 5 が 5-A / 5-B / 5-C のサブステップに分離されていること
- [ ] Step 5-QC（OCR + Vision-check + Pillow 合成）が Claude 側（Step 5-C）に残っていること
- [ ] Step 6 が 6-A / 6-B / 6-C のサブステップに分離されていること
- [ ] U-1 の選択（フラグ切り替え）が反映されていること（`HANDOFF_MODE` 環境変数による分岐）
- [ ] 各サブステップの「入力」「処理」「出力」が明確に記述されていること
- [ ] 変更しないステップ（Step 1/2/4/7/8）が影響を受けないこと（後方互換）
- [ ] ハンドオフフォルダ構造の具体的パスが skill.md 内に図として記載されていること

### 品質チェック項目（工程2）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Step 3/5/6 の各サブステップの境界が明確で、Claude/Codex それぞれの責務が混在していないか | 設計・整合性 | 20 |
| 2 | Step 5-QC（OCR・Vision-check・Pillow）が Claude 側に正しく留まり、Codex への責務漏れがないか | 機能要件 | 20 |
| 3 | `HANDOFF_MODE` 環境変数フラグによる既存フォールバックが正しく分岐されているか | 後方互換 | 15 |
| 4 | ハンドオフフォルダへの配置物（manifest/スクリプト/参照画像）が各ステップで完全に列挙されているか | 完全性 | 15 |
| 5 | 変更しない Step 1/2/4/7/8 の記述に不要な修正・影響が発生していないか | 差分最小 | 15 |
| 6 | skill.md の日本語・構造スタイルが既存セクションと一貫しているか（命名・箇条書き・コードブロック） | 可読性 | 15 |
| 合計 | | | 100 |

---

## 工程3: サンプルデータ準備・動作確認仕様

### サンプルデータ流用方針

既存出力 `03_成果物/outputs/ebooks-manga/manga-career-restart/vol1/` を使用する。

- `manuscript/characters/` に既存のキャラリファレンス PNG が存在する場合 → Step 3 ハンドオフのドライランに使用
- `panels/comicle_output.csv` が存在する場合 → Step 5 ハンドオフのドライランに使用
- 実際の API 呼び出しは最小限（1〜3 ページのサンプル生成のみ）

### テスト計画の範囲

- ドライラン A: ハンドオフフォルダの生成確認（API 呼び出しなし）
  - Claude が Step 5-A を実行し、`handoff/<job-id>/step5/` の内容を検証
  - manifest.json・gen_pages.py・codex_instructions.md が正しく生成されること
- ドライラン B: Codex スクリプト単体実行（API 呼び出しあり、1 ページのみ）
  - ユーザーが手動で `gen_pages.py --pages 1` を実行し、`page_001_iter_1.png` を生成
  - `DONE.json` が正しく出力されること
- ドライラン C: Claude 側の戻り受け取り（Step 5-C）の確認
  - `DONE.json` を手動配置し、OCR + Vision-check ループが起動することを確認

### 完了条件

- [ ] `03_成果物/outputs/ebooks-manga/manga-career-restart/vol1/` の現状ファイル一覧が確認済みであること
- [ ] ドライラン A〜C の実施手順が明文化されていること
- [ ] サンプル実行に必要な環境変数・依存ライブラリ（openai, pillow, pytesseract 等）がリストアップされていること
- [ ] ドライランが既存の vol1 出力ファイルを破壊しないことが保証されていること（出力先の分離）

### 品質チェック項目（工程3）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | ドライラン A〜C の実施手順が具体的かつ再現可能であること | 再現性 | 30 |
| 2 | 既存 vol1 出力が破壊されないことが手順上で保証されていること | 安全性 | 25 |
| 3 | 必要な依存ライブラリ・環境変数が網羅されていること | 完全性 | 20 |
| 4 | ドライランの合否判定基準が明確であること（何を見て成功と判断するか） | 検証可能性 | 25 |
| 合計 | | | 100 |

---

## ハンドオフフォルダ設計（工程1 の先行定義）

### 推奨フォルダレイアウト

```
.company/handoff/codex-image-gen/
└── <job-id>/                         # 例: manga-career-restart_vol1_20260424_143000
    ├── job.json                      # ジョブ全体のメタ情報（書名・vol・ステップ種別・作成日時）
    │
    ├── step3/                        # Step 3: キャラリファレンス画像生成
    │   ├── manifest.json             # 生成指示（キャラ名・プロンプト・サイズ）
    │   ├── gen_characters.py         # Codex が実行する生成スクリプト
    │   ├── codex_instructions.md     # ユーザーが Codex CLI に渡す指示テンプレ
    │   └── output/                   # Codex が画像を書き出す場所
    │       └── DONE.json             # Codex が生成完了後に出力する完了マーカー
    │
    ├── step5/                        # Step 5: 本文ページ画像生成（純粋生成のみ）
    │   ├── manifest.json             # 全ページ情報（ページ番号・プロンプト・テンプレ・文字情報）
    │   ├── characters/               # キャラリファレンス PNG（manuscript/characters/ からコピー）
    │   │   ├── ミサキ_20260424_120000.png
    │   │   └── ケンタ_20260424_120001.png
    │   ├── gen_pages.py              # Codex が実行する生成スクリプト
    │   ├── codex_instructions.md     # ユーザーが Codex CLI に渡す指示テンプレ
    │   └── output/                   # Codex が画像を書き出す場所
    │       ├── page_001_iter_1.png
    │       ├── page_002_iter_1.png
    │       └── DONE.json             # 全ページ生成完了後に出力
    │
    ├── step5_regen/                  # Step 5 QC FAIL ページの再生成（OCR/Vision-check FAIL 時）
    │   ├── manifest.json             # FAIL ページのみ（ページ番号・フィードバック注入済みプロンプト）
    │   ├── characters/               # step5/ からシンボリックリンクまたはコピー
    │   ├── gen_pages.py              # step5/ と同じスクリプト（またはシンボリックリンク）
    │   ├── codex_instructions.md
    │   └── output/
    │       └── DONE.json
    │
    └── step6/                        # Step 6: カバー画像生成
        ├── manifest.json             # カバー生成指示（プロンプト・参照キャラ・サイズ）
        ├── characters/               # 主人公キャラ PNG（step5/characters/ からコピー）
        ├── gen_cover.py              # Codex が実行する生成スクリプト
        ├── codex_instructions.md
        └── output/
            ├── cover.png             # Codex が出力（PNG 形式）
            └── DONE.json
```

### job.json スキーマ

```json
{
  "job_id": "manga-career-restart_vol1_20260424_143000",
  "book_id": "manga-career-restart",
  "vol": 1,
  "step": "step5",
  "created_at": "2026-04-24T14:30:00+09:00",
  "source_dir": "03_成果物/outputs/ebooks-manga/manga-career-restart/vol1",
  "total_pages": 100,
  "status": "pending"
}
```

### manifest.json スキーマ（Step 5 用）

#### 入力側（Claude → Codex）

```json
{
  "job_id": "manga-career-restart_vol1_20260424_143000",
  "step": "step5",
  "model": "gpt-image-2",
  "size": "1024x1536",
  "quality": "high",
  "batch_size": 10,
  "characters_dir": "./characters",
  "output_dir": "./output",
  "pages": [
    {
      "page_num": 1,
      "template": "template_3",
      "prompt": "◆【絶対最優先】...",
      "text_items": [
        {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ", "text": "えっ、本当に？"}
      ],
      "char_refs": ["ミサキ_20260424_120000.png"],
      "is_text_only": false
    }
  ]
}
```

#### 出力側（Codex → Claude）: DONE.json

```json
{
  "job_id": "manga-career-restart_vol1_20260424_143000",
  "step": "step5",
  "completed_at": "2026-04-24T16:45:00+09:00",
  "total_pages": 100,
  "generated_pages": 98,
  "skipped_pages": [5, 23],
  "failed_pages": [],
  "files": [
    {"page_num": 1, "path": "output/page_001_iter_1.png", "status": "ok"},
    {"page_num": 2, "path": "output/page_002_iter_1.png", "status": "ok"}
  ],
  "errors": []
}
```

### codex_instructions.md テンプレート骨子（Step 5 用）

```markdown
# 画像生成タスク: [書名] vol[N] Step 5

## あなたのタスク

このフォルダ内の `gen_pages.py` を実行して、マンガ本文ページの画像を生成してください。

## 事前確認

1. Python 環境に openai ライブラリがインストール済みであること
   `pip install openai pillow`
2. 環境変数 `OPENAI_API_KEY` が設定済みであること
   `export OPENAI_API_KEY="your-key-here"`

## 実行方法

```bash
cd /path/to/handoff/<job-id>/step5
python gen_pages.py
```

## 実行内容

- `manifest.json` の全ページを読み込み、OpenAI `gpt-image-2` で画像生成します
- 生成画像は `output/page_NNN_iter_1.png` として保存されます
- 全ページ完了後、`output/DONE.json` に完了マーカーを書き出します
- `is_text_only: true` のページはスキップします（テキストページ）

## 完了の確認

`output/DONE.json` が存在し、`generated_pages` の値が期待するページ数と一致することを確認してください。

## 注意事項

- OPENAI_API_KEY はこのフォルダ内には含まれていません。ご自身の環境変数から読み込んでください
- 生成には約 50〜60 分かかります（100ページの場合）
- バッチ間に 5 秒の待機が入ります（API レート制限対策）
```

### セキュリティ方針

- Claude Code は `OPENAI_API_KEY` を **ハンドオフフォルダに書き込まない**（`.env` ファイル生成も禁止）
- キー解決は Codex CLI を起動するターミナルの環境変数（`export OPENAI_API_KEY=...`）に完全委任
- `gen_pages.py` は `os.environ["OPENAI_API_KEY"]` でのみキーを取得する実装とする
- `codex_instructions.md` に「ご自身の環境変数から読み込んでください」と明示する

### エラー・部分生成時のリトライ戦略

| エラー種別 | 検出方法 | 対処 |
|---|---|---|
| API 呼び出し失敗（1ページ） | `gen_pages.py` 内の try/except、`DONE.json` の `errors` フィールド | `gen_pages.py --retry-failed` で失敗ページのみ再実行。最大 3 回まで |
| 部分生成（DONE.json の generated_pages < total_pages） | Claude が DONE.json を検証時に検出 | `step5_regen/` を作成して不足ページのみ再ハンドオフ |
| DONE.json が存在しない（Codex 中断） | Claude の待機タイムアウト（設定値: 120 分） | ユーザーへ通知し手動確認を促す |
| ファイル名の命名規則違反（`page_NNN_iter_1.png` 以外） | Claude の検証スクリプトで名前パターン照合 | 自動リネームを試みる。不明なファイルはスキップし `DONE.json` の `errors` に記録 |
| QC FAIL ページ（OCR FAIL / Vision-check FAIL） | Claude が Step 5-C で OCR + Vision-check を実行 | `max_iter=3` まで `step5_regen/` 経由で再ハンドオフ。超過時は Pillow フォールバック（Step 5.5） |

---

## 備考

### 設計思想: 関心の分離

```
[Claude Code]                     [Codex CLI（別ターミナル）]
  Step N-A: 準備・manifest 生成
  → フォルダを書き出す
                                    ← ユーザーが起動
                                    Step N-B: 純粋な画像生成のみ
                                    → output/ に PNG を書き出す
                                    → DONE.json を出力
  Step N-C: QC・検証・続き工程
  ← DONE.json を検出して再開
```

Claude は「何を生成すべきか」の設計（manifest）と「生成後の品質保証」（OCR/Vision-check）に集中する。
Codex は「API を叩いて PNG を書く」純粋な実行役に徹する。

### コスト試算への影響

この方式変更はコスト構造に影響しない（同一 API・同一モデルを使用）。
`$24.45/冊`（ハイブリッド QC 込み）の見積もりはそのまま有効。

### step5_regen の反復上限

`step5_regen/` による再ハンドオフは最大 `max_iter=3` 回まで（skill.md の既定値に準拠）。
3 回超過時は該当ページを Pillow 合成フォールバック（Step 5.5）で処理する。
これにより「EPUB に文字化けページが混入する」問題は引き続き根本排除される。

### 既存プロトタイプの活用

`03_成果物/outputs/ebooks-manga/manga-career-restart/_prototype/hybrid_loop.py`（465 行）の
画像生成コードは `gen_pages.py` のベースとして流用可能。
`main()` から API 呼び出し部分のみを抜き出し、OCR/Vision-check ループを除去したものが `gen_pages.py` となる。
