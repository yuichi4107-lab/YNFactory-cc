# 引き継ぎとTODOの運用

複数のPC（自宅・職場）で作業するため、Claude Code のローカルメモリ（`~/.claude/`）は共有されない。
**引き継ぎ情報は必ず `.company/` 配下に保存する**（Drive経由でPC間共有される）。

## ファイルの役割

| パス | 中身 | いつ使うか |
|---|---|---|
| `.company/secretary/HANDOFF.md` | セッション引き継ぎ本体（**今の状態だけ**・400行/60KB以内） | **作業開始時に最初に読む** |
| `.company/secretary/todos/YYYY-MM-DD.md` | 日次TODO | HANDOFF の次に読む |
| `.company/secretary/handoff-log/YYYY-MM.md` | セッション要約の履歴（月次） | 過去の経緯を追うとき |
| `.company/secretary/tech-notes.md` | 技術・環境メモ（VPS・API・既知の落とし穴） | 環境情報が必要なとき |
| `.company/secretary/archive/` | 完了案件・旧HANDOFF全文 | 詳細を掘るとき |
| `.company/secretary/notes/` | トピック別メモ | 必要に応じて |
| `.company/secretary/inbox/` | 未整理の放り込み先 | 分類に迷ったら |
| `.company/DASHBOARD.md` | 全体進捗 | 俯瞰したいとき |
| `.company/DASHBOARD_SALES.md` | 営業KPI | 営業レビュー時 |

## セッション開始時

**0. まず GitHub 最新を取り込む（必須）**

```bash
cd C:\YNFactory-cc   # Mac は ~/YNFactory-cc
python 01_コード/scripts/company/sync_drive_git.py pull-sync
```

他PCが前回のセッション終了時にpushした内容がDriveへ反映される。
GitHubに新着が無ければ `No GitHub updates to sync to Drive.` と出て何も起きない。

1. `HANDOFF.md` を読む
2. `todos/` の直近ファイルを読む
3. 未完了項目があれば、進捗サマリーを報告して再開するか確認する

## セッション終了時

`/handoff` スキルを実行する。次を一括で行う。

1. `HANDOFF.md` を更新（frontmatter4キーを上書き、本文の状態を書き換え、完了案件は削除）
2. セッション要約を `handoff-log/YYYY-MM.md` へ追記
3. `todos/YYYY-MM-DD.md` を更新（完了分にチェック、残タスクを記録）
4. Drive ↔ ローカルGit を同期して `git commit` / `push`

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

### 例外: 状態ファイルは上書きする（2026-08-08 追加）

次は「今の状態」を表すファイルなので、**追記ではなく上書き更新**する。

| ファイル | 扱い |
|---|---|
| `HANDOFF.md` | frontmatterは `last_updated` / `last_device` / `last_session_summary` / `next_action` の**4キー固定**で毎回上書き。**キー名に日付・トピックのサフィックスを付けて追記しない**。本文は書き換え、完了案件は削除 |
| `todos/YYYY-MM-DD.md` | その日の状態を上書き更新 |
| `DASHBOARD.md` / `DASHBOARD_SALES.md` | 現況を上書き更新 |

履歴を残したいときは `handoff-log/YYYY-MM.md`（月次）へ追記し、状態ファイル自体には積まない。

> このルールを追記のみで運用した結果、HANDOFF.md が frontmatter 131キー・1448行・387KB まで肥大化し、
> 一度に読み込めなくなった。2026-08-08に9KBへ再構成し、旧全文は
> `.company/secretary/archive/HANDOFF-2026-08-08-full.md` に退避した。

## 過去の運営記録

2026-08-06 まで「秘書 → CEO → 各部署」という組織の比喩で運用していた。
その記録（案件・要件・提案・調査など）は `99_その他/company-records/` にある。
現在は要件定義 → 実行 → 品質チェックの3エージェントに一本化している（`02_設定/docs/quality-loop.md`）。
