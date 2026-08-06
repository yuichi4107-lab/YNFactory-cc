# Drive側フォルダ整理の手順

Drive側の `YNFactory-cc` を、ローカルGit側と同じ6バケット構成へ組み替える手順。
`.company/scripts/organize_drive_root.py` を使う。

## 前提

- 2026-08-05 に**ローカルGit側の構成を先に変更済み**（`CLAUDE.md` 「フォルダ構成」参照）
- `sync_drive_git.py` / `daily_git_sync.py` は Drive と Git が**同じ相対パス**で一致していることを前提に動く。
  Git側だけ変わっている状態なので、**Drive側を組み替えるまで自動同期は正しく動かない**
- 実行はローカルGit作業ディレクトリから。Drive側でGit操作はしない

## 目標構成

```
YNFactory-cc/
├── 01_コード/          scripts/
├── 02_設定/            docs/
├── 03_成果物/          ebooks/  ebook-produce/  outputs/
├── 04_インプット/      inputs/  context/
├── 05_プロジェクト/    shorts-factory/ keiba-unified/ ... （22個）
├── 99_その他/          <日付>-cleanup/（ゴミ・キャッシュの退避先）
├── .company/           会社運営のみ（secretary / ceo / pm / sales / finance …）
└── CLAUDE.md  AGENTS.md  .gitignore  .claude/  .agents/  .codex/  .vscode/
```

最後の行はツールが場所固定で読み込むため、**バケットに入れずルート直下に残す**。
これらを動かすと Claude Code / Codex がスキルを見つけられなくなる。

## 実行前チェック

1. Drive の同期が完了していること（同期中のファイルがあると移動が失敗する）
2. ZSlim バックアップが直近で成功していること → `02_設定/docs/backup-zslim.md`
3. shorts-factory の watchdog など、Drive上のファイルを掴むプロセスを止めておく

## 手順

```bash
# 1. 何が起きるかを確認（既定はdry-run、ファイルは一切動かない）
python3 .company/scripts/organize_drive_root.py

# 2. 内容に納得したら実行
python3 .company/scripts/organize_drive_root.py --apply
```

キャッシュ（`.playwright-mcp/` `.pytest_cache/` `.wrangler/` `test-results/` `__pycache__/`）を
退避ではなく削除してDrive容量を空けたい場合:

```bash
python3 .company/scripts/organize_drive_root.py --apply --purge-cache
```

その他のオプション:

- `--drive-root <path>` … Drive ルートを明示指定（既定は `$YNFACTORY_DRIVE_ROOT` → OS別の既定パス）
- `--date YYYY-MM-DD` … `99_その他/<日付>-cleanup/` の日付を上書き

## 実行後の確認

1. `99_その他/<日付>-cleanup/MANIFEST.md` に全移動履歴が残る。まずこれを見る
2. Drive UI でルート直下が6バケット＋ルート固定ファイルだけになっていることを確認
3. Drive の同期完了を待ってから、同期スクリプトの疎通を確認:
   ```bash
   python3 .company/scripts/sync_drive_git.py local-to-drive --dry-run CLAUDE.md
   ```
4. 各PCの LaunchAgent / Task Scheduler が旧パスを指していないか確認する。
   特に `05_プロジェクト/keiba-unified/scripts/task_*.xml` は登録し直しが必要

## 安全性

- **移動のみ。削除は `--purge-cache` を明示したときだけ**
- 移動先に同名がある場合は `-2`, `-3` … を付けて退避する。上書きしない
- `.git` `.git_drivebackup` `.claude` `.agents` `.codex` `CLAUDE.md` `AGENTS.md` `.gitignore` `.vscode`
  は保護対象。ルールに書いても弾かれる
- 冪等。移動済みの項目はスキップされるので、途中で失敗しても再実行できる

`.git` で始まる名前のものは、たとえゴミでも自動では動かさない方針にしている。
そのためDriveルートの `.git.disabled-20260615`（34バイト、`.git` 無効化の名残）は残る。
不要なら実行後に手で削除する:

```bash
rm "$YNFACTORY_DRIVE_ROOT/.git.disabled-20260615"
```

## 次回以降の整理

新しく散らかったものは、スクリプト冒頭のルールテーブルに追記する:

| テーブル | 用途 |
|---|---|
| `MOVES` | `(移動元, 移動先バケット)` |
| `MERGES` | 中身を1件ずつ移して空になった元を削除する |
| `PROJECTS` | `05_プロジェクト/` 行きのディレクトリ名 |
| `JUNK_FILES` / `JUNK_GLOBS` / `JUNK_DIRS` | `99_その他/` 行き |
| `CACHE_DIRS` | 再生成可能。`--purge-cache` で削除対象になる |

テストは `.company/scripts/tests/test_organize_drive_root.py`:

```bash
python3 .company/scripts/tests/test_organize_drive_root.py
```
