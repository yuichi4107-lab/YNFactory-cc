---
title: ZSlim バックアップ運用
date: "2026-06-15"
status: active
---

# ZSlim バックアップ運用

## 方針

Google Drive は同期サービスであり、バックアップではない。削除、上書き、破損、競合コピーも同期されるため、`YNFactory-cc` はこのPCに接続している外部ドライブ `ZSlim` に別系統で世代バックアップする。

## 決定事項

| 項目 | 内容 |
|---|---|
| バックアップ先 | `/Volumes/ZSlim/YNFactory-backups/restic` |
| 対象 | Drive側 `YNFactory-cc` |
| 方式 | `restic` による重複排除つき世代バックアップ |
| 保持 | 日次7世代、週次8世代、月次12世代 |
| パスワード | リポジトリ外の `~/.ynfactory/restic-zslim-password` |

`ZSlim` は ExFAT のため、rsyncのハードリンク世代管理には向かない。重複排除と世代管理は `restic` に任せる。

## 導入

`restic` が未導入なら、このPCで導入する。

```bash
brew install restic
```

バックアップリポジトリを初期化する。

```bash
cd /Users/yuichi/YNFactory-cc
python3 .company/scripts/backup_zslim_restic.py init
```

## 手動実行

```bash
cd /Users/yuichi/YNFactory-cc
python3 .company/scripts/backup_zslim_restic.py backup
python3 .company/scripts/backup_zslim_restic.py forget
python3 .company/scripts/backup_zslim_restic.py check
```

まとめて実行する場合:

```bash
python3 .company/scripts/backup_zslim_restic.py run
```

## 確認

```bash
python3 .company/scripts/backup_zslim_restic.py snapshots
```

初回フルバックアップの前に、小さいファイルだけで保存・復元の疎通確認をする。

```bash
python3 .company/scripts/backup_zslim_restic.py smoke-test
```

## 復元テスト

月1回、実ファイルを壊さない場所へ復元テストする。

```bash
mkdir -p /tmp/ynfactory-restore-test
python3 .company/scripts/backup_zslim_restic.py restore-latest --target /tmp/ynfactory-restore-test
```

復元後、最低限これを確認する。

```text
AGENTS.md
.company/secretary/HANDOFF.md
.company/outputs/
```

## バックアップから除外するもの

- Drive側の壊れた `.git` ポインタ
- `.git_drivebackup`
- 仮想環境 `.company/.venvs`
- キャッシュ
- `node_modules`
- Playwrightなどの一時スナップショット
- 一時ファイル、ログ、OSメタデータ
- 再生成可能な重い結果・キャッシュ
  - `ai-trade-system/results/**/charts/*.png`
  - `keiba-unified/win5/data/cache/*.html`

## 注意

- `.git_drivebackup` の削除は、GitHubとローカルGitの復旧性を確認してから直前承認を取って実行する。
- バックアップパスワードを失うと復元できない。`~/.ynfactory/restic-zslim-password` はこのPC外にも安全に控える。
- 初回バックアップは時間がかかる。2回目以降は差分と重複排除により軽くなる。

## 初回実績

2026-06-15 に初回フルバックアップを実行した。

| 項目 | 結果 |
|---|---|
| snapshot | `9322a1e5` |
| 処理量 | 28,544 files / 17.765 GiB |
| ZSlim保存量 | 12.542 GiB |
| 実行時間 | 25分15秒 |
| 整合性チェック | no errors |

時間がかかった主因は、`ai-trade-system/results/**/charts/*.png` と `keiba-unified/win5/data/cache/*.html` の大量小ファイル。どちらも再生成可能な結果・キャッシュのため、初回スナップショット `9322a1e5` には保存したうえで、2026-06-16 以降の定期バックアップからは除外する。
