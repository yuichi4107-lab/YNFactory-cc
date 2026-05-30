# 品質チェックレポート（第1回）

採点日: 2026-04-25
対象工程: 工程1 — フォルダ構造再編 + CLAUDE.md 新設 + skill.md パス更新

---

## サマリー

- **スコア**: 63 / 100
- **判定**: FAIL
- **完了条件充足**: 4 / 6 項目

---

## 完了条件チェック

| # | 条件 | 判定 | 備考 |
|---|---|---|---|
| 1 | `.company/codex/{queue,in-progress,done,archive}/` が作成されていること | OK | 4フォルダすべて存在確認済み |
| 2 | `.company/codex/CLAUDE.md` が存在し、フォルダ遷移ルール・done/ 巡回ルールを記述していること | OK | queue→in-progress→done→archive の遷移、done/ 巡回手順（9ステップ）、セキュリティ方針、ステータス管理すべて記述あり |
| 3 | `.company/codex/_template.md` が存在し、必要フィールドを含むこと | OK | job_id・manifest パス・実行コマンド・完了条件・報告欄すべて含む |
| 4 | `.company/codex/_spec/SPEC.md` が fire-and-forget 方式を正確に記述していること | OK | 1 task = 1 bundle / QC は Codex 側 / フォルダ遷移図 / ピンポン型への言及なし（SPEC.md 内） |
| 5 | skill.md 内の `.company/handoff/codex-image-gen/` パス参照がすべて `.company/codex/` 系に更新されていること | NG | 旧パス `handoff/codex-image-gen` は 0 件だが、**旧方式の設計記述が大量に残存**（後述） |
| 6 | Step 1〜4 / Step 7〜8 の節に不要な変更が加わっていないこと | OK | Step 1〜4 / Step 7〜8 は変更なし（grep 確認済み） |

---

## 品質スコア詳細

| # | チェック項目 | 配点 | 得点 | 根拠 |
|---|---|---|---|---|
| 1 | Genspark CLAUDE.md と同じ感覚で運用できるか（フォルダ遷移・ファイル命名・巡回ルールが整合） | 25 | 22 | フォルダ遷移（queue→in-progress→done→archive）、done/ 巡回ルール（起動時 + 「完了」通知時の 2 パターン）、ステータス管理テーブル、ファイル命名規則（job-id 形式 + ページ画像命名）、セキュリティ方針がすべて明記されており Genspark と同レベルの運用ドキュメントと判断。OPENAI_API_KEY の取り扱いも CLAUDE.md / SPEC.md / _template.md の 3 ファイルに記述あり。archive 内の `legacy-codex-image-gen/codex-image-gen/` 二段ネストが CLAUDE.md フォルダ構成図に正確に記載されていない点で -3。 |
| 2 | _spec/SPEC.md が fire-and-forget 方式（ハンドオフ 1 回・QC は Codex 側）を正確に記述し、旧 SPEC.md との差分が明確か | 20 | 18 | 旧方式 vs 新方式の差分表、1 task = 1 bundle 宣言、QC ループ仕様（OCR + Vision-check + ベストエフォート + needs_manual_review_reasons）、HANDOFF_MODE フラグ、エラーハンドリング、done/ 巡回仕様がすべて揃っている。ピンポン型（step5_regen_iter_N/）への言及が SPEC.md 自体には一切なく、新方式として完結している。archive の旧 SPEC.md を `superseded` として参照していることも明記。-2 は「並走対応（複数 job-id 同時投入）」についての記述がないため（要件定義書 U6 は A 案推奨だが SPEC.md に並走可否の明示がない）。 |
| 3 | _template.md が TASK.md 生成に必要なフィールドをすべて含んでいるか（job_id / manifest / 実行コマンド / 完了条件 / 報告欄） | 20 | 19 | YAML フロントマター（task_id / task_type / book_id / vol / created_at / status）、入力ファイル表、実行手順（`echo $OPENAI_API_KEY` 確認 + `cd` + `python gen_manga_bundle.py` の 3 ステップ）、期待する出力表、QC ループ説明、環境変数欄、完了条件チェックリスト、完了後の通知手順、Codex 記入欄（ステータス・ページ数・needs_manual_review_pages・コスト・時間・備考）がすべて含まれている。-1 は `task-id` と `job_id` の表記が混在している（フロントマターは `task_id`、本文見出しは `task-id`、CLAUDE.md は `job-id`）ことで若干の一貫性欠如。 |
| 4 | skill.md のパス参照更新が完全で、旧パスの記述が残っていないか | 20 | 4 | **旧パス `handoff/codex-image-gen` は 0 件**。しかしこれは工程1の最重要目標である「旧方式設計の刷新」を達成していない。skill.md には旧方式の設計記述が以下の箇所に残存している: (a) 行 33: `DONE.json を待機してから QC ループを続行` という旧方式の説明が冒頭モード説明に残る (b) 行 279: Step 3 の codex-handoff フロー概要に `DONE.json 受け取り` が残る (c) 行 406: `output/DONE.json` 参照が残る (d) 行 652-655: Step 5 の codex-handoff モード概要に `[A-2]〜[A-5] は Claude 側で実行する` という旧方式説明・`step5_regen_iter_2/` への言及が残る (e) 行 695-697: ループフロー疑似コードのコメントに `step5/` や `step5_regen_iter_{iter}/` への言及が残る (f) 行 783: `DONE.json の status 確認` が残る (g) 行 785: `step5_regen_iter_{iter+1}/` 作成手順が残る (h) 行 789-792: 再生成 iter（5-A）手順として `step5_regen_iter_{iter}/` 節が残る (i) 行 1403: Step 6 の codex-handoff フロー概要に `DONE.json 受け取り` が残る (j) 行 1951-1952: エラーハンドリング表に `再ハンドオフ` への言及が残る。これらは **fire-and-forget 方式と矛盾する旧ピンポン型の記述**であり、skill.md を読んだ場合に動作方式が不明瞭になる。配点 20 点に対して、物理パスの更新（+4 点）と `done/<job-id>/progress.json` パスの正常化（行 1950）は適切。残存旧方式記述の多さから大幅減点。 |
| 5 | Step 1〜4 / Step 7〜8 に不要な変更がないこと（後方互換） | 15 | 0 | N/A — 工程1の品質チェック項目5は「不要な変更がないこと」の確認。Step 1〜4 / Step 7〜8 への変更は確認されなかった（OK）が、**採点対象はチェック項目4の残存問題との重複は避け、本項では差分最小の観点でのみ判断**。Step 1〜4 / Step 7〜8 は変更なし → 満点とする。 |
| 合計 | | 100 | 63 | |

**注記**: 項目5の採点を修正する。

| # | チェック項目 | 配点 | 得点 | 根拠（再計） |
|---|---|---|---|---|
| 5 | Step 1〜4 / Step 7〜8 に不要な変更がないこと（後方互換） | 15 | 15 | Step 1〜4（行 275〜451）および Step 7〜8（行 1512〜末尾付近）に意図しない変更は確認されなかった。満点。 |
| **修正後合計** | | **100** | **78** | |

---

## 改善指示

### 優先度1: skill.md のパス参照更新（得点: 4/20）

**問題**: 物理パス `handoff/codex-image-gen` は 0 件になったが、**旧方式（ピンポン型）の設計記述が skill.md 内に大量残存**している。具体的には以下の箇所が fire-and-forget 方式と矛盾した旧方式を指示している:

1. **行 33 — モード説明**:
   - 現状: `manifest を生成してハンドオフフォルダに配置し、ユーザーが別ターミナルの Codex CLI で gen_pages.py を実行。Claude は DONE.json を待機してから QC ループを続行`
   - 修正案: `manifest を生成して queue/<job-id>/ に配置し、ユーザーが別ターミナルで python gen_manga_bundle.py を実行。Claude は完了通知を受けるまで何もしない（fire-and-forget）`

2. **行 279 — Step 3 フロー概要**:
   - 現状: `codex-handoff モード: 3-1 → 3-2-A-codex → 3-2-B-codex（DONE.json 受け取り）→ 3-3`
   - 修正案: `DONE.json` の言及を `progress.json` に置き換え、または Step 3 は今後も旧 gen_pages.py 使用なら旧方式のままでよいが、その場合は `HANDOFF_MODE=codex-handoff` の Step 3 部分が新方式に対応していないことを注記する

3. **行 406 — Step 3 codex-handoff 節**:
   - `output/DONE.json` → `done/<job-id>/progress.json` に変更する

4. **行 652-655 / 695-697 / 783 / 785 / 789-792 — Step 5 codex-handoff 節（最重要）**:
   - 行 652: `[A-2] Blind-OCR・[A-3] Vision-check・[A-4] 統合判定・[A-5] フィードバック注入・iter 超過判定は常に Claude 側で実行する` → **削除またはコメントアウト**（fire-and-forget では Codex 側が実行する）
   - 行 653: `step5/ に manifest を配置し Codex 起動依頼 → DONE.json 受け取り後に QC ループ実行` → **削除**
   - 行 654: `step5_regen_iter_2/ を新規作成して再ハンドオフ` → **削除**
   - 行 695-697: ループフロー疑似コードのコメント内 `step5/ または step5_regen_iter_{iter}/` → `queue/<job-id>/` に修正
   - 行 783: `DONE.json の status 確認` → `progress.json の status 確認` に修正
   - 行 785-792: `step5_regen_iter_{iter+1}/` 作成・再ハンドオフ節全体 → **削除**（fire-and-forget では Codex 内完結）

5. **行 1403 — Step 6 フロー概要**:
   - `DONE.json 受け取り` → 削除またはコメントアウト

6. **行 1951-1952 — エラーハンドリング表**:
   - `sha256 不一致 → 再ハンドオフ` → `progress.json の errors[] を確認してユーザーに通知` に変更
   - `partial（部分生成） → 不足 items を新 manifest に転記して再ハンドオフ` → `needs_manual_review_pages をユーザーに提示して手動確認を促す` に変更

**改善方法**: skill.md のうち `HANDOFF_MODE=codex-handoff` の説明箇所を一通り精査し、「Claude が QC を行う / 再ハンドオフする」旨の記述をすべて削除・修正する。特に `step5_regen_iter_N/` や `DONE.json` の言及を全件置換することで、fire-and-forget 方式と一致させる。

---

### 優先度2: CLAUDE.md フォルダ構成図の不整合（得点: 22/25 の -3 に相当）

**問題**: CLAUDE.md 内のフォルダ構成図（コードブロック）の `archive/` 配下に `legacy-codex-image-gen/` は示されているが、実際のパス `archive/legacy-codex-image-gen/codex-image-gen/`（二段ネスト）が明示されていない。

**改善方法**: CLAUDE.md のフォルダ構成図に以下を追記する:
```
└── archive/
    ├── <job-id>/
    └── legacy-codex-image-gen/      # 旧 .company/handoff/codex-image-gen/ の退避
        └── codex-image-gen/         # ネストあり（旧フォルダ名を保持）
```

---

### 優先度3: _template.md の表記ゆれ（得点: 19/20 の -1 に相当）

**問題**: `task_id`（フロントマター）と `task-id`（本文見出し）の表記が混在している。CLAUDE.md では `job-id` が基本表記。

**改善方法**: `_template.md` 内の本文見出し・説明文の `task-id` を `job-id` または `task_id` に統一する。

---

## 総評

フォルダ構造の新設、CLAUDE.md・SPEC.md・_template.md の品質は高く、工程1の成果物の大半は要件を満たしている。しかし **skill.md の旧方式設計記述が大量に残存**していることが唯一かつ最大の問題点である。物理パス（`handoff/codex-image-gen`）は正しく更新されているが、旧方式の「Claude が QC を行い再ハンドオフする」フローの説明文・疑似コードコメント・フロー概要が skill.md の複数箇所（行 33, 279, 406, 652-655, 695-697, 783, 785, 789-792, 1403, 1951-1952）に残っており、火和 forget 方式と矛盾した手順書になっている。これは実際の運用時に混乱を招く致命的な問題である。

再採点スコア: **78 / 100（FAIL、85点未満）**
