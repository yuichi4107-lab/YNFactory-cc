---
title: マルチPC共有移行後の整理候補
date: "2026-06-15"
status: review
---

# マルチPC共有移行後の整理候補

## 現状

ZSlim への初回フルバックアップは完了済み。

| 項目 | 内容 |
|---|---|
| restic snapshot | `9322a1e5` |
| 処理量 | 28,544 files / 17.765 GiB |
| ZSlim保存量 | 12.542 GiB |
| 実行時間 | 25分15秒 |
| 整合性チェック | no errors |

2026-06-15 23:17 JST 追記: Drive側の壊れた `.git` ポインタは、削除ではなく `.git.disabled-20260615` へ退避済み。Drive側で `git status` を実行すると `not a git repository` で止まることを確認した。

## 削除候補（実行前に承認必須）

| 候補 | サイズ | 理由 | 推奨 |
|---|---:|---|---|
| `.git_drivebackup/` | 4.7GB | 旧Git復旧用コピー。現在はGitHub・ローカルGit・ZSlimバックアップがある | 削除候補。ただし直前承認後 |
| Drive側 `.git` | 4KB | `gitdir: C:/dev/YNFactory-git/.git` の古いWindowsパスポインタ。このMacではGit操作を壊す | `.git.disabled-20260615` へ退避済み |
| TODO競合コピー `YYYY-MM-DD (1).md` | 11件 | Google Drive競合コピー。内容比較・本体統合後に削除 | 全件確認・統合・削除済み |

検出済みTODO競合コピー:

```text
.company/secretary/todos/2026-05-22 (1).md
.company/secretary/todos/2026-05-25 (1).md
.company/secretary/todos/2026-05-29 (1).md
.company/secretary/todos/2026-06-01 (1).md
.company/secretary/todos/2026-06-03 (1).md
.company/secretary/todos/2026-06-04 (1).md
.company/secretary/todos/2026-06-05 (1).md
.company/secretary/todos/2026-06-07 (1).md
.company/secretary/todos/2026-06-08 (1).md
.company/secretary/todos/2026-06-10 (1).md
.company/secretary/todos/2026-06-12 (1).md
```

2026-06-15 23:21 JST 追記:

- `2026-05-22.md` / `2026-05-25.md` / `2026-05-29.md` はDrive側で本体が欠けていたため、ローカルGit側から本体をDrive側へ復元済み。
- 復元後、以下3件は本体と `(1)` が完全一致。削除承認後に `(1)` 側を削除してよい候補。
  - `2026-05-22 (1).md`
  - `2026-05-25 (1).md`
  - `2026-05-29 (1).md`
- 2026-06-16 00:32 JST 追記: 上記3件はオーナー承認後に削除済み。削除直前に本体とのSHA-256一致を再確認した。
- 以下8件は `(1)` 側に本体へ未統合の可能性がある行が残っているため、削除前に内容判断が必要。
  - `2026-06-01 (1).md`
  - `2026-06-03 (1).md`
  - `2026-06-04 (1).md`
  - `2026-06-05 (1).md`
  - `2026-06-07 (1).md`
  - `2026-06-08 (1).md`
  - `2026-06-10 (1).md`
  - `2026-06-12 (1).md`

2026-06-16 00:35 JST 追記:

- `2026-06-05 (1).md` はJRA競馬予想見直し・Telegram常駐bot復旧改善の記録が本体より詳細だったため、本体 `2026-06-05.md` へ内容統合済み。統合後、両ファイルのSHA-256一致を確認した。
- 残る6月分の判定:
  - `2026-06-01 (1).md`: 古い一般タスクのみ。Git×Drive Phase2は現行方針で解消済み、Claude Code支援は後続TODOに存在。
  - `2026-06-03 (1).md`: 意味のある差分なし。
  - `2026-06-04 (1).md`: NotebookLM構築・認証課題はHANDOFFと後続TODOに記録済み。
  - `2026-06-05 (1).md`: 本体へ統合済み。
  - `2026-06-07 (1).md`: NotebookLM通知・再認証タスクは後続TODOに存在。
  - `2026-06-08 (1).md`: 6/7初稼働確認タスクは日付経過済みで、後続TODOに現状確認タスクとして残存。
- `2026-06-10 (1).md`: Meta SNS Step6とJRAタスクは後続TODOに存在。
- `2026-06-12 (1).md`: Meta SNS Step6は後続TODOに存在。
- 2026-06-16 00:36 JST 追記: 上記8件はオーナー承認後に削除済み。`2026-06-05 (1).md` は本体統合後、それ以外は後続TODO/HANDOFFで保持済みまたは意味差分なしとして処理した。

## Git追跡解除候補（実ファイルは消さない）

`.gitignore` に該当しているのに、まだGitで追跡されているファイルが 4,731件ある。

| 分類 | 件数 | ローカルGit側サイズ | 推奨 |
|---|---:|---:|---|
| `.company/outputs/` | 3,783 | 174.4 MiB | `git rm --cached` 候補 |
| `.company/.venvs/` | 779 | 18.5 MiB | `git rm --cached` 候補 |
| `keiba-unified/win5/data/cache/` | 97 | 8.0 MiB | `git rm --cached` 候補 |
| `.playwright-mcp/` | 72 | 0.4 MiB | `git rm --cached` 候補 |

実行する場合は、ローカルGit側で対象パスだけ `git rm --cached` し、Drive側の実ファイルは残す。

## バックアップ性能メモ

初回フルバックアップで時間がかかった箇所:

- `ai-trade-system/results/**/charts/*.png`
- `keiba-unified/win5/data/cache/*.html`

どちらも再生成可能な結果・キャッシュのため、今後の定期バックアップでは除外候補。ただし初回スナップショット `9322a1e5` には保存済み。

## 次工程案

1. Drive側 `.git` を `.git.disabled-20260615` へ退避する。
2. TODO競合コピーを1件ずつ比較し、本体にない内容があれば統合してから削除する。
3. `.git_drivebackup/` を削除する。
4. `git rm --cached` で生成物・仮想環境・キャッシュをGit追跡対象から外す。
5. バックアップスクリプトに再生成可能キャッシュの除外を追加する。

## 承認境界

上記 1〜4 は、実行直前にオーナー確認を取る。
