# 引き継ぎとTODOの運用

複数のPC（自宅・職場）で作業するため、Claude Code のローカルメモリ（`~/.claude/`）は共有されない。
**引き継ぎ情報は必ず `.company/` 配下に保存する**（Drive経由でPC間共有される）。

## ファイルの役割

| パス | 中身 | いつ使うか |
|---|---|---|
| `.company/secretary/HANDOFF.md` | セッション引き継ぎ本体 | **作業開始時に最初に読む** |
| `.company/secretary/todos/YYYY-MM-DD.md` | 日次TODO | HANDOFF の次に読む |
| `.company/secretary/notes/` | トピック別メモ | 必要に応じて |
| `.company/secretary/inbox/` | 未整理の放り込み先 | 分類に迷ったら |
| `.company/DASHBOARD.md` | 全体進捗 | 俯瞰したいとき |
| `.company/DASHBOARD_SALES.md` | 営業KPI | 営業レビュー時 |

## セッション開始時

1. `HANDOFF.md` を読む
2. `todos/` の直近ファイルを読む
3. 未完了項目があれば、進捗サマリーを報告して再開するか確認する

## セッション終了時

`/handoff` スキルを実行する。次を一括で行う。

1. `HANDOFF.md` を更新（last_updated、作業サマリー、各プロジェクトの状態）
2. `todos/YYYY-MM-DD.md` を更新（完了分にチェック、残タスクを記録）
3. Drive ↔ ローカルGit を同期して `git commit` / `push`

次の兆候を検知したら、報告と同じレスポンス内で自動的に実行する。別のレスポンスに分けない。

- 「ありがとう」「おわり」「また明日」等の終了の挨拶
- 依頼されたタスクがすべて完了し、次の指示待ちになった

## TODO の書式

```markdown
- [ ] タスク内容 | 優先度: 高/通常/低 | 期限: YYYY-MM-DD
- [x] 完了タスク | 優先度: 通常 | 完了: YYYY-MM-DD
```

## ファイル命名

- 日次ファイル: `YYYY-MM-DD.md`
- トピックファイル: `kebab-case-title.md`
- テンプレート: `_template.md`（各フォルダに1つ。変更しない）

## 書き方の原則

- 既存ファイルは上書きせず追記する。追記時はタイムスタンプを付ける
- 1トピック1ファイルを守る
- 新規ファイルは `_template.md` をコピーして作る

## 過去の運営記録

2026-08-06 まで「秘書 → CEO → 各部署」という組織の比喩で運用していた。
その記録（案件・要件・提案・調査など）は `99_その他/company-records/` にある。
現在は要件定義 → 実行 → 品質チェックの3エージェントに一本化している（`02_設定/docs/quality-loop.md`）。
