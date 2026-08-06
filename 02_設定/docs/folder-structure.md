# フォルダ構成

ルート直下は用途別の6バケットに固定する。Drive側とローカルGit側は**同じ構成**を保つ。

| バケット | 中身 | 例 |
|---|---|---|
| `01_コード/` | 単体で動く汎用スクリプト | `scripts/post_to_x.py`, `scripts/company/sync_drive_git.py` |
| `02_設定/` | ルール・手順書・要件定義 | `docs/backup-zslim.md`, `requirements/` |
| `03_成果物/` | 完成した納品物・出版物 | `ebooks/`, `outputs/{project}/` |
| `04_インプット/` | 制作の素材・取り込みデータ | `inputs/`, `context/` |
| `05_プロジェクト/` | 実行可能なアプリの作業ディレクトリ | `shorts-factory/`, `keiba-unified/` |
| `99_その他/` | 上記5つに当てはまらないもの・退避品 | `company-records/`, `ebook-vol4/` |

## 新しいものを置くとき

まずこの6バケットのどれかに割り当てる。判断がつかないものだけ `99_その他/` に入れる。

- 実行可能なアプリ一式 → `05_プロジェクト/`
- 単体で完結するスクリプト → `01_コード/scripts/`
- 完成して外部に出せるもの → `03_成果物/outputs/{project}/`
- 制作の材料として取り込んだもの → `04_インプット/`
- 手順書・ルール・要件定義 → `02_設定/`

## バケットに入れないもの

| パス | 理由 |
|---|---|
| `CLAUDE.md` `AGENTS.md` `.gitignore` | ツールがルート直下で固定的に読む |
| `.claude/` `.agents/` `.codex/` | スキル・エージェント定義の探索先が固定 |
| `.vscode/` | エディタがワークスペース直下で読む |
| `.company/` | HANDOFF・TODO・DASHBOARD。パスがスキルと通知に直接埋まっている |

`.company/` は**セッション引き継ぎ専用**に縮小してある。中身は `secretary/`（HANDOFF・TODO・notes・inbox）と DASHBOARD 2種のみ。
かつてここにあった成果物・インプット・コード・運営記録は、すべて上のバケットへ移動済み。

## 過去の運営記録

`99_その他/company-records/` に、旧「会社組織」運用の記録が入っている（案件記録・要件・提案・調査など）。
参照はするが日常的には触らない。

## Drive側の整理

`01_コード/scripts/company/organize_drive_root.py` で行う。手順は `02_設定/docs/organize-drive.md`。
