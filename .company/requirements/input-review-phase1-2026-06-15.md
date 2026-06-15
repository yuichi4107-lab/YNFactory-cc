---
date: 2026-06-15
type: requirements
project: input-review-phase1
status: approved-by-user-request
---

# Input Review Phase 1 Requirements

## Goal

`.company/inputs/` に蓄積される raw / organized / indexes を、毎日レビューできる形に集約する。

Phase 1 では日別TODOやプロジェクトファイルへの自動反映は行わず、判断用レビューMarkdownの生成までを実装する。

## Scope

Do:

- `.company/inputs/process_daily_inputs.py` を追加する
- `.company/inputs/reviews/YYYY-MM-DD-input-review.md` を生成する
- 既存の `organized/` と `indexes/` を入力として使う
- 未整理バックログ、TODO候補、決定事項候補、機密・個人情報候補を可視化する
- デフォルトでは外部APIを叩かない
- 既存の日次パイプラインからレビュー生成を呼べるようにする
- 運用ドキュメントを更新する

Do not:

- 日別TODOへ自動追記しない
- HANDOFFやプロジェクト状態ファイルを自動更新しない
- 外部サービスへの投稿・送信・削除を行わない
- 既存 raw / organized / indexes の内容を破壊的に変更しない

## Completion Criteria

- `process_daily_inputs.py --help` が正常に表示される
- `process_daily_inputs.py --date 2026-06-15 --skip-refresh --force` でレビューが生成される
- 生成レビューに以下が含まれる
  - input inventory summary
  - TODO candidates
  - decision candidates
  - sensitive-data candidates
  - unorganized backlog
  - explicit note that TODO auto-apply is disabled
- `.company/inputs/run_daily.sh` からレビュー生成が呼ばれる
- `.company/inputs/CLAUDE.md` と README 類に Phase 1 の使い方が残る

## Quality Criteria

- 既存スクリプトへの干渉が最小である
- 出力は200行を超える大量ログを前提にしない
- 失敗時に raw データを失わない
- 機密候補をレビュー内で過度に展開しない
- TODO候補は「未判定」として扱い、自動実行キューに入れない

## Phase Split

### Phase 1: Review Generation

Daily review file generation only. This session implements this phase.

### Phase 2: Approved Routing

Add an explicit `--apply-todo` or equivalent approval-gated route after the review format has proven useful.
