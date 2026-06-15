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

## 削除候補（実行前に承認必須）

| 候補 | サイズ | 理由 | 推奨 |
|---|---:|---|---|
| `.git_drivebackup/` | 4.7GB | 旧Git復旧用コピー。現在はGitHub・ローカルGit・ZSlimバックアップがある | 削除候補。ただし直前承認後 |
| Drive側 `.git` | 4KB | `gitdir: C:/dev/YNFactory-git/.git` の古いWindowsパスポインタ。このMacではGit操作を壊す | 削除または `.git.disabled-YYYYMMDD` へ退避 |
| TODO競合コピー `YYYY-MM-DD (1).md` | 11件 | Google Drive競合コピー。内容比較・本体統合後に削除 | 1件ずつ確認して削除 |

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
