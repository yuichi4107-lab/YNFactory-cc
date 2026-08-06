---
title: マルチPC共有・Git整理・ZSlimバックアップ要件定義
date: "2026-06-15"
status: approved
owner_decisions: "2026-06-15 22:11 JST"
---

# マルチPC共有・Git整理・ZSlimバックアップ要件定義

## ゴール

`YNFactory-cc` を複数PCから ClaudeCode / Codex で安全に使えるようにし、Google Drive 競合、Git混乱、削除・上書き事故から復元できる運用へ移行する。

## オーナー承認済みの前提

1. Google Drive を日常作業場・成果物置き場にする。
2. GitHub はコード・ルール・スキル・手順書の履歴に限定する。
3. バックアップ先はこのPCに接続している `ZSlim` とする。
4. 保持期間は日次7世代、週次8世代、月次12世代とする。
5. 共有権限は推奨どおり、作業者だけ編集、その他は閲覧を基本にする。
6. `.git_drivebackup` 削除、Drive競合ファイル削除、大規模な Git 追跡解除は実行直前に確認する。

## スコープ

### やること

- 既存ドキュメントの矛盾を Drive-first 方針に統一する。
- 新規PC向けセットアップ手順を作成する。
- ZSlim への世代バックアップ手順と実行スクリプトを追加する。
- Git 管理に入れるもの、入れないものの境界を明文化する。
- 今後の Git 整理で使う安全な手順を用意する。

### 今回やらないこと

- `.git_drivebackup` の削除。
- Drive競合ファイルの削除。
- `git rm --cached` による大規模な Git 追跡解除。
- KDP、SNS投稿、外部サービス上の不可逆操作。

## 完了条件

- `docs/multi-pc-rules.md` が最新方針と一致している。
- `docs/setup-multi-pc.md` が存在し、Mac / Windows のセットアップ手順を説明している。
- `docs/backup-zslim.md` が存在し、バックアップ先・保持期間・復元方法を説明している。
- `01_コード/scripts/company/backup_zslim_restic.py` が存在し、`restic` が未導入なら安全に停止して導入案内を出す。
- `AGENTS.md` / `CLAUDE.md` に ZSlim バックアップ方針が登録されている。
- 削除や大規模追跡解除を実行していない。

## 品質基準

- AI が Drive側とローカルGit側を混同しないこと。
- PC固有の絶対パスは、セットアップ手順・環境変数・起動ラッパー以外に広げないこと。
- バックアップは Google Drive と別系統であること。
- 秘密情報をリポジトリに保存しないこと。
- 実ファイル削除を伴う操作は直前承認なしに実行しないこと。

## 工程

### 工程1: 文書統一

中間成果物:
- `docs/multi-pc-rules.md`
- `docs/setup-multi-pc.md`
- `docs/backup-zslim.md`

品質基準:
- 既存の `C:\dev\YNFactory-cc` 旧方針を現行方針として扱わない。
- Drive-first / local Git bridge / ZSlim backup が一貫している。

### 工程2: バックアップスクリプト追加

中間成果物:
- `01_コード/scripts/company/backup_zslim_restic.py`

品質基準:
- `restic` がなければ失敗理由と導入コマンドを短く出す。
- パスワードファイルはリポジトリ外に置く。
- 初期化、バックアップ、保持期間整理、スナップショット確認が分かれている。

### 工程3: 品質チェック

中間成果物:
- 作成ファイル一覧
- 実行可能性チェック結果
- 残作業一覧

品質基準:
- 85点以上で合格。
- 削除・大規模追跡解除・外部送信をしていないこと。
