# 要件定義書: ebook-to-manga Codex fire-and-forget 型への再設計

作成日: 2026-04-25
対象スキル: `.claude/skills/ebook-to-manga/skill.md`
設計方針: Genspark Claw パターン（キュー型 fire-and-forget）
旧要件定義: `.company/requirements/ebook-to-manga-codex-handoff/REQUIREMENTS.md`（superseded）

---

## ゴール

ebook-to-manga パイプラインの画像生成工程（Step 5: 本文ページ + Step 6: 表紙）を、
Claude がキュー投入した後は Codex が自律的に「画像生成 + QC ループ + ベストエフォート採用」を完走し、
`done/<job-id>/` に成果物を書き出すまで Claude の介在を不要にする fire-and-forget 型に再設計する。

---

## スコープ

### やること

- フォルダ構造の新設（`.company/codex/{queue,in-progress,done,archive}/` — Genspark 流儀に統一）
- `.company/codex/CLAUDE.md` の新設（Genspark の `.company/genspark/CLAUDE.md` を雛形に運用ルールを記述）
- `_template.md` 作成（Codex 向けタスク指示書の雛形）
- `_spec/` 配下の SPEC.md を新方式（フォルダ遷移・QC 責任 Codex 側）に更新
- `gen_manga_bundle.py`（仮称）の仕様定義: Step 5 本文全ページ + Step 6 表紙を 1 バンドルで処理し、QC ループ（OCR + Vision-check + ベストエフォート採用）を Codex 側で完結
- `manifest.json` スキーマをバンドル型に拡張（Step 5 + Step 6 両方の item を含む）
- `done/<job-id>/progress.json` の出力スキーマ定義（`needs_manual_review_pages` 含む）
- skill.md の Step 5/6 `codex-handoff` 節を fire-and-forget 方式に書き換え（5-A / 5-B 削除 / 5-C / Step 6 節）
- skill.md のディレクトリパス参照を新フォルダ構造（`.company/codex/`）に更新
- 旧要件定義書（`ebook-to-manga-codex-handoff/REQUIREMENTS.md`）冒頭への superseded バナー追記

### やらないこと

- Step 1 / Step 2 / Step 3 / Step 4 / Step 7 / Step 8 の Claude 側ロジックの変更
- Step 3 キャラ参照画像の生成ロジック変更（Step 3 は引き続き inline または別ハンドオフで先行実施）
- 古い `.company/handoff/codex-image-gen/` フォルダの物理削除（後述 U2 でユーザー判断待ち）
- EPUB フォーマット・KDP メタデータ仕様の変更
- Codex CLI 本体の動作変更・設定変更
- CI/CD や自動デプロイの整備

### 保留事項（ユーザー判断待ち）

- U2: 古い `.company/handoff/codex-image-gen/` の扱い（本ドキュメント末尾参照）
- U3: Codex 側スクリプトのファイル名

---

## フォルダ構造（工程 1 で新設）

```
.company/codex/
├── CLAUDE.md                          # Codex キュー運用ルール（本 REQUIREMENTS 参照）
├── _template.md                       # Codex タスク指示書の雛形
├── _spec/                             # スキーマ・参考実装一式（旧 .company/handoff/codex-image-gen/_spec/ を移植・更新）
│   ├── SPEC.md                        # fire-and-forget 版仕様書（本ドキュメント更新版）
│   ├── manifest.schema.json           # バンドル型 manifest の JSON Schema
│   ├── done_progress.schema.json      # done/<job-id>/progress.json の JSON Schema
│   └── gen_manga_bundle.py            # Codex 側参考実装（Step 5 + Step 6 + QC ループ）
│
├── queue/                             # Claude が配置 → Codex がピックアップ
│   └── <job-id>/                      # 例: manga-career-restart_vol1_20260425_143000
│       ├── manifest.json              # バンドル型生成指示（Step 5 全ページ + Step 6 表紙）
│       ├── characters/                # キャラ参照 PNG（Step 3 完了後に manuscript/characters/ からコピー）
│       ├── gen_manga_bundle.py        # Codex 実行スクリプト（_spec/ からコピー）
│       └── TASK.md                    # Codex 向けタスク指示書（_template.md から生成）
│
├── in-progress/                       # Codex が作業開始時に queue/<job-id>/ を移動
│   └── <job-id>/                      # （構造は queue と同じ）
│
├── done/                              # Codex が完了後に成果物を書き出す
│   └── <job-id>/
│       ├── pages/                     # 本文ページ PNG 全件（page_001.png ... page_NNN.png）
│       ├── cover.png                  # 表紙 PNG
│       └── progress.json             # QC 結果・needs_manual_review_pages 含む完了レポート
│
└── archive/                           # Claude が done/ を処理後に移動
    └── <job-id>/
```

---

## 工程一覧

| 工程 | 中間成果物 | 入力 |
|---|---|---|
| 工程 1: フォルダ構造再編 + CLAUDE.md 新設 + skill.md パス更新 | `.company/codex/` ディレクトリ一式 + CLAUDE.md + _template.md + _spec/SPEC.md（更新）+ skill.md（パス参照更新） | 本要件定義書 + 旧 SPEC.md |
| 工程 2: Codex 側スクリプト拡張（QC ループ取り込み） | `gen_manga_bundle.py` + `manifest.schema.json` + `done_progress.schema.json` | 工程 1 の成果物 + 旧 `gen_pages.py` |
| 工程 3: skill.md Step 5/6 codex-handoff 節を fire-and-forget 型へ書き換え | 改修済み skill.md（Step 5-A/5-C/Step 6 節更新）+ 旧要件定義書 superseded バナー追記 | 工程 2 の成果物 + 現行 skill.md |

---

## 工程 1: フォルダ構造再編 + CLAUDE.md 新設 + skill.md パス更新

### 中間成果物

- `.company/codex/` 配下のディレクトリ構造（queue / in-progress / done / archive）
- `.company/codex/CLAUDE.md`（Genspark CLAUDE.md を雛形に Codex キュー運用ルールを記述）
- `.company/codex/_template.md`（Codex タスク指示書の雛形）
- `.company/codex/_spec/SPEC.md`（fire-and-forget 版仕様書: フォルダ遷移・QC 責任 Codex 側・manifest バンドル型・ジョブ命名規則を明記）
- skill.md のディレクトリパス参照（`.company/handoff/codex-image-gen/` → `.company/codex/queue/<job-id>/`）が更新済み

### 完了条件

- [ ] `.company/codex/{queue,in-progress,done,archive}/` が作成されていること
- [ ] `.company/codex/CLAUDE.md` が存在し、Genspark と同じフォルダ遷移ルール（queue→in-progress→done→archive）と、done/ 巡回時に Claude がやることを記述していること
- [ ] `.company/codex/_template.md` が存在し、TASK.md 生成の雛形として利用できること（job_id・manifest パス・実行コマンド・完了条件・報告欄のフィールドを含む）
- [ ] `.company/codex/_spec/SPEC.md` が fire-and-forget 方式（ハンドオフ 1 回きり・QC は Codex 側・フォルダ遷移図）を正確に記述していること
- [ ] skill.md 内の `.company/handoff/codex-image-gen/` パス参照がすべて `.company/codex/` 系に更新されていること
- [ ] Step 1〜4 / Step 7〜8 の節に不要な変更が加わっていないこと（差分最小）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Genspark CLAUDE.md と同じ感覚で運用できるか（フォルダ遷移・ファイル命名・巡回ルールが整合） | Genspark パターン整合 | 25 |
| 2 | _spec/SPEC.md が fire-and-forget 方式（ハンドオフ 1 回・QC は Codex 側）を正確に記述し、旧 SPEC.md との差分が明確か | 設計完全性 | 20 |
| 3 | _template.md が TASK.md 生成に必要なフィールドをすべて含んでいるか（job_id / manifest / 実行コマンド / 完了条件 / 報告欄） | 自己完結性 | 20 |
| 4 | skill.md のパス参照更新が完全で、旧パスの記述が残っていないか | リクエスト一致度 | 20 |
| 5 | Step 1〜4 / Step 7〜8 に不要な変更がないこと（後方互換） | 差分最小 | 15 |
| 合計 | | | 100 |

---

## 工程 2: Codex 側スクリプト拡張（QC ループ取り込み）

### 中間成果物

- `.company/codex/_spec/gen_manga_bundle.py`: Step 5 全ページ + Step 6 表紙の画像生成と QC ループ（OCR + Vision-check + ベストエフォート採用）を完結させるスクリプト
- `.company/codex/_spec/manifest.schema.json`: バンドル型 manifest の JSON Schema（Step 5 items + Step 6 item を統合）
- `.company/codex/_spec/done_progress.schema.json`: `done/<job-id>/progress.json` の JSON Schema（`needs_manual_review_pages` 含む）

### スクリプト仕様（gen_manga_bundle.py）

#### 入力

- `manifest.json`（queue/<job-id>/ 内）の `items[]` を読み込む
- 各 item は `type: "page" | "cover"` で種別を区別
- `characters/` ディレクトリのキャラ参照 PNG を参照（Step 5 / Step 6 共通）
- 環境変数 `OPENAI_API_KEY` のみでキー取得（ハードコード禁止）

#### 処理フロー（Step 5: 本文ページ）

```
for each page_item in manifest.items where type == "page":
  iter = 1
  while iter <= max_iter (default: 3):
    [1] gpt-image-2 で images.edit を呼び出し PNG を生成
    [2] Blind-OCR: gpt-4o Vision API に生成 PNG を渡し、テキスト抽出と読み取り可否を確認
        - manifest の expected_text と照合（完全一致不要、主要語句の出現確認）
    [3] Vision-check: gpt-4o Vision API で指定キャラクターの存在・外見整合性を確認
    [4] 統合判定:
        - OCR PASS かつ Vision-check PASS → done/<job-id>/pages/page_{NNN}.png に保存、break
        - FAIL → iter 内でフィードバック注入したプロンプトで再生成
    [5] iter == max_iter かつ FAIL → ベストエフォート採用（最後の iter の PNG を採用）
                                       needs_manual_review_pages[] に page_num を追加
    iter += 1
```

#### 処理フロー（Step 6: 表紙）

```
cover_item = manifest.items where type == "cover"
[1] gpt-image-2 で images.edit（主人公キャラ参照 PNG を使用）
[2] done/<job-id>/cover.png に保存
    ※ 表紙は QC ループなし（単発生成・ベストエフォート）
```

#### 出力

- `done/<job-id>/pages/page_001.png` ... `page_NNN.png`（is_text_only=true のページはスキップ）
- `done/<job-id>/cover.png`
- `done/<job-id>/progress.json`（下記スキーマ参照）

#### フォルダ遷移（Codex スクリプト責務）

```
queue/<job-id>/  →（作業開始時）→  in-progress/<job-id>/  →（完了時）→  done/<job-id>/
```

Codex スクリプトは処理開始時に `queue/<job-id>/` を `in-progress/<job-id>/` に移動し、
完了時に `done/<job-id>/` に成果物を書き出す。
`in-progress/<job-id>/` のフォルダは `archive/<job-id>/` への移動は Claude 側が担当する。

#### done/<job-id>/progress.json スキーマ

```json
{
  "job_id": "manga-career-restart_vol1_20260425_143000",
  "book_id": "manga-career-restart",
  "vol": 1,
  "completed_at": "2026-04-25T16:45:00+09:00",
  "status": "success",
  "pages": {
    "total": 100,
    "generated": 98,
    "skipped_text_only": 2,
    "needs_manual_review": 3
  },
  "needs_manual_review_pages": [15, 42, 77],
  "cover": {
    "status": "success",
    "path": "done/<job-id>/cover.png"
  },
  "api_cost_estimate": {
    "gpt_image_2_calls": 152,
    "gpt_4o_vision_calls": 304,
    "estimated_usd": 35.50
  },
  "errors": []
}
```

#### manifest.json バンドル型スキーマ（抜粋）

```json
{
  "job_id": "manga-career-restart_vol1_20260425_143000",
  "book_id": "manga-career-restart",
  "vol": 1,
  "model": "gpt-image-2",
  "size_page": "1024x1536",
  "size_cover": "1024x1536",
  "quality": "high",
  "max_iter": 3,
  "characters_dir": "./characters",
  "output_dir": "../../../done/<job-id>",
  "items": [
    {
      "id": "page_001",
      "type": "page",
      "page_num": 1,
      "template": "template_3",
      "prompt": "◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。...",
      "expected_text": ["えっ", "本当に"],
      "char_refs": ["ミサキ_20260425_120000.png"],
      "is_text_only": false
    },
    {
      "id": "cover",
      "type": "cover",
      "prompt": "◆【絶対最優先】...",
      "char_refs": ["ミサキ_20260425_120000.png"],
      "protagonist_ref": "ミサキ_20260425_120000.png"
    }
  ]
}
```

### 完了条件

- [ ] `gen_manga_bundle.py` が manifest.json を読み込み、Step 5 全ページ + Step 6 表紙を 1 スクリプトで処理できること
- [ ] Blind-OCR（gpt-4o Vision API）が各ページ生成後に自動実行されること
- [ ] Vision-check（gpt-4o Vision API）が各ページ生成後に自動実行されること
- [ ] `max_iter`（既定 3）連続 FAIL でベストエフォート採用し `needs_manual_review_pages[]` に記録すること
- [ ] 表紙（type="cover"）は QC ループなし・単発生成であること
- [ ] 完了時に `done/<job-id>/progress.json` が出力され、スキーマ準拠であること
- [ ] `OPENAI_API_KEY` は `os.environ` のみで取得し、スクリプト内ハードコード・manifest への書き込みが一切ないこと
- [ ] `manifest.schema.json` と `done_progress.schema.json` が JSON Schema として valid であること
- [ ] 既存 `gen_pages.py` の構造（API 呼び出し部）を最大限流用していること（新規コード量を最小化）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | queue/<job-id>/ の内容だけで Codex が完走できるか（Claude への問い合わせ不要・自己完結） | 自己完結性 | 25 |
| 2 | QC ループ（OCR + Vision-check + ベストエフォート採用 + needs_manual_review 記録）が Codex 側で完結しているか | 機能要件 | 25 |
| 3 | OPENAI_API_KEY が queue/done フォルダに一切書き込まれていないか | セキュリティ | 20 |
| 4 | progress.json スキーマが needs_manual_review_pages・コスト見積もり・エラー情報を網羅しているか | 完全性 | 15 |
| 5 | 既存 gen_pages.py の構造を流用し、差分が最小限か | 差分最小 | 15 |
| 合計 | | | 100 |

---

## 工程 3: skill.md Step 5/6 codex-handoff 節を fire-and-forget 型へ書き換え

### 中間成果物

- 改修済み skill.md（Step 5-A / Step 5-C / Step 6 節が fire-and-forget 方式で記述）
- 旧要件定義書（`ebook-to-manga-codex-handoff/REQUIREMENTS.md`）冒頭に superseded バナー追記済み

### skill.md 改修方針

#### Step 5-A: queue 投入（Claude が実行）

1. ジョブ ID 生成: `{book_id}_vol{N}_{YYYYMMDD_HHMMSS}`
2. `queue/<job-id>/` を新設
3. manifest.json（バンドル型）を生成・保存（Step 5 全ページ + Step 6 表紙 item を含む）
4. キャラ参照 PNG を `queue/<job-id>/characters/` にコピー（`manuscript/characters/` から）
5. `gen_manga_bundle.py` を `_spec/` からコピー
6. `TASK.md` を `_template.md` から生成（job_id・実行コマンド・完了条件を埋める）
7. ユーザーに以下を提示:
   ```
   queue/<job-id>/ を配置しました。
   別ターミナルで以下を実行してください:
     cd .company/codex/queue/<job-id>
     python gen_manga_bundle.py
   完了したら「Codex 完了しました」と教えてください。
   ```

#### Step 5-B: 削除

旧 Step 5-B（Claude が DONE.json を待機するフェーズ）は削除する。
Claude は「ユーザーから完了通知を受けるまで」何もしない。待機コマンド等の記述は不要。

#### Step 5-C: done/ 受け取り（Claude が実行）

ユーザーから「Codex 完了しました」通知を受けた後:

1. `done/<job-id>/progress.json` を読み込む
2. `progress.json` の `status` を確認（"success" / "partial" / "failed"）
3. `done/<job-id>/pages/` の全 PNG を出力ディレクトリ `panels/pages/` に配置
4. `done/<job-id>/cover.png` を `KDP出版用/cover.png` に配置
5. `needs_manual_review_pages[]` の内容を出力先 `progress.json` の同フィールドに転記
6. `done/<job-id>/` を `archive/<job-id>/` に移動
7. `needs_manual_review_pages` が空でない場合、ユーザーに該当ページのリストを提示して手動確認を促す
8. Step 5 / Step 6 完了を `progress.json` に記録し、Step 7（EPUB 製本）へ進む

#### Step 6 の扱い

Step 6 は Step 5 と同一バンドルに含まれるため、独立した Step 6-A / 6-B / 6-C の記述は削除し、
「Step 6 表紙は Step 5 の manifest バンドルに `type: "cover"` の item として含まれる」と一文で明示する。

#### iter ループ再ハンドオフの削除

旧方式の `step5_regen_iter_<n>/` 再ハンドオフ節（Claude が QC FAIL ページを再度 Codex に投げる仕組み）は削除する。
QC ループは Codex 側で完結するため、Claude 側の再ハンドオフ処理は不要になる。

#### HANDOFF_MODE フラグ

`HANDOFF_MODE=codex-handoff` の分岐は維持する。`HANDOFF_MODE=inline` 時の既存フロー（Claude 内完結）は変更しない。

### 完了条件

- [ ] Step 5-A が「queue/<job-id>/ 投入 + ユーザーへの Codex 起動依頼」として記述されていること
- [ ] 旧 Step 5-B（Claude の能動的な待機フェーズ）が削除されていること
- [ ] Step 5-C が「done/<job-id>/ からの受け取り + pages/ 配置 + needs_manual_review 転記 + archive 移動」として記述されていること
- [ ] Step 6 節が「Step 5 バンドルに cover item を追加」と明示するだけの簡潔な記述になっていること
- [ ] `step5_regen_iter_<n>/` 再ハンドオフ節が削除されていること
- [ ] `HANDOFF_MODE=inline` 時の既存フローが変更されていないこと（後方互換）
- [ ] Step 1〜4 / Step 7〜8 の節に不要な変更が加わっていないこと
- [ ] 旧要件定義書の冒頭に superseded バナーが追記されていること
- [ ] skill.md の日本語・構造スタイルが既存セクションと一貫していること（命名・箇条書き・コードブロック）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Claude と Codex の担当範囲が一意に記述されているか（責務の明快さ・混在ゼロ） | 責務明快性 | 25 |
| 2 | fire-and-forget の流れが Step 5-A → 「ユーザーが Codex を fire」→ Step 5-C（通知受信後）として論理的に完結しているか | 設計完全性 | 20 |
| 3 | HANDOFF_MODE=inline 時の既存フローが変更されていないか（後方互換） | 後方互換 | 20 |
| 4 | Step 1〜4 / Step 7〜8 に不要な変更がないか（差分最小） | 差分最小 | 20 |
| 5 | skill.md の日本語・構造スタイルが既存セクションと一貫しているか | 可読性 | 15 |
| 合計 | | | 100 |

---

## ユーザー確認事項（実装前に判断が必要）

| # | 確認事項 | 選択肢 | 推奨案 |
|---|---|---|---|
| U1 | Step 3 キャラ参照画像の扱い | A) inline 固定（Step 3 は常に Claude 内完結） / B) 別 Codex bundle に分離 / C) 選択式（HANDOFF_MODE で分岐） | **A 案推奨**（今回のスコープ外・複雑化を避ける。Step 3 は枚数が少なく inline でコスト少。後から B/C に移行可能） |
| U2 | 古い `.company/handoff/codex-image-gen/` フォルダの扱い | A) そのまま残す（参照資料として） / B) `.company/codex/archive/legacy-codex-image-gen/` に移動 / C) 物理削除 | **B 案推奨**（参考実装 gen_pages.py・旧 SPEC.md が含まれており削除はリスクあり。archive に退避してリポジトリ汚染を避ける） |
| U3 | Codex 側スクリプトのファイル名 | A) `gen_manga_bundle.py` / B) `gen_pages_v2.py` / C) 既存 `gen_pages.py` を拡張上書き | **A 案推奨**（Step 5 + Step 6 バンドルを明示する名称。C 案は旧方式との混同リスクあり） |
| U4 | テスト運用のスケール（初回ミニテスト） | A) 2 ページ（約 $0.50） / B) 3 ページ（約 $0.75） / C) 5 ページ（約 $1.25） | **B 案推奨**（3 ページなら OCR FAIL パターンを含めやすく QC ループの動作確認に適切。コスト上限も許容範囲） |
| U5 | Codex 実行完了通知方式 | A) ユーザーが「完了しました」と Claude に通知 / B) Claude が何もしない（ユーザーが done/ を確認して Step 5-C を呼び出す） / C) done/ ポーリング（Claude が Monitor ツールで確認） | **A 案推奨**（最もシンプル。fire-and-forget の趣旨に合致。Codex が progress.json を書き出した時点でユーザーが確認できる） |
| U6 | ジョブ並走（同時に複数 job-id を流す） | A) 単一ジョブのみ（vol1 完了後に vol2） / B) 並走あり（vol1 と vol2 を同時投入） | **A 案推奨（初回）**（queue/ はジョブ別ディレクトリで並走対応済みだが、初回は単一ジョブで動作確認を優先。問題なければ並走へ） |

---

## コスト透明性（参考試算）

### Codex 側 API 呼び出し（100 ページ・平均 1.5 iter 前提）

| 呼び出し種別 | 想定コール数 | 想定コスト |
|---|---|---|
| gpt-image-2（Step 5 本文、high quality） | 150 コール | 約 $31.50 |
| gpt-image-2（Step 6 表紙） | 1 コール | 約 $0.21 |
| gpt-4o Vision（Blind-OCR、各 iter 後） | 150 コール | 約 $1.50 |
| gpt-4o Vision（Vision-check、各 iter 後） | 150 コール | 約 $1.50 |
| **合計** | | 約 **$34.71 / 冊** |

ミニテスト（3 ページ、1 iter）: 約 $0.75

---

## 備考

### 旧方式（codex-handoff）との主な差分

| 項目 | 旧方式（codex-handoff） | 新方式（fire-and-forget） |
|---|---|---|
| ハンドオフ回数 | 複数（QC FAIL ごとに再ハンドオフ） | 1 回きり |
| QC ループ担当 | Claude 側 | Codex 側 |
| フォルダ構造 | `.company/handoff/codex-image-gen/<step>/`（固定パス） | `.company/codex/{queue,in-progress,done,archive}/<job-id>/`（ジョブ別パス）|
| Step 6 扱い | 独立した step6/ フォルダ | Step 5 バンドルに統合 |
| Claude の待機フェーズ | Step 5-B で DONE.json をポーリング | なし（ユーザー通知待ち） |
| 再ハンドオフフォルダ | `step5_regen_iter_<n>/` | なし（Codex 内完結） |

### Genspark パターンとの整合

本方式は `.company/genspark/` の運用ルールと以下の点で同じ感覚で扱える:

- フォルダ遷移: queue → in-progress → done → archive（完全一致）
- Claude の done/ 巡回タイミング: ユーザーからの「完了しました」通知時（Genspark と同じ）
- ファイル命名: `YYYY-MM-DD-task-name.md` → Codex は `<job-id>/` ディレクトリ単位（命名規則は別途 CLAUDE.md に記載）
- 報告書フォーマット: progress.json（Genspark の完了報告 md に対応する役割）
