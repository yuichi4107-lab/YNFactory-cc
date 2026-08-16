---
title: YNFactory-cc 複数PCセットアップ手順
date: "2026-08-16"
status: active
---

# YNFactory-cc 複数PCセットアップ手順

## 基本方針

**リポジトリ本体はローカル（`C:\YNFactory-cc` / `~/YNFactory-cc`）。**
重い領域と Git 管理外の領域だけを、リンクで Google Drive へ逃がす。

| 場所 | 役割 |
|---|---|
| ローカル | 作業場所・Gitリポジトリ本体。ここで作業し、ここでgitを実行する |
| Google Drive | 成果物・素材・Git管理外プロジェクトの実体（リンク先） |

Drive側では `git commit` / `git pull` / `git push` を実行しない。

## Windows のセットアップ

### 1. リポジトリを clone

```powershell
cd C:\
git clone https://github.com/yuichi4107-lab/YNFactory-cc.git C:\YNFactory-cc
cd C:\YNFactory-cc
git pull --ff-only origin main
```

### 2. Google Drive for desktop を有効にする

`G:\マイドライブ\YNFactory-cc` が見えることを確認する。

### 3. リンクを張る

`mklink` は cmd の内部コマンド。PowerShell からは必ず `cmd /c` を付ける。

```powershell
cmd /c mklink /J "C:\YNFactory-cc\03_成果物\outputs" "G:\マイドライブ\YNFactory-cc\03_成果物\outputs"
cmd /c mklink /J "C:\YNFactory-cc\04_インプット"     "G:\マイドライブ\YNFactory-cc\04_インプット"
```

`05_プロジェクト` 配下は、Git追跡ゼロのプロジェクトだけをリンクにする。
判定と一括作成は `docs/link-architecture.md` の手順に従う。

C: 側に同名フォルダが既にある場合、**中身を確認せずに消さない**。ファイルが1件でもあれば中断する形にする。

### 4. Cowork の接続フォルダ

デスクトップアプリの「フォルダを追加」で `C:\YNFactory-cc` を接続する。

### 5. 確認

```powershell
cd C:\YNFactory-cc
git status --short          # リンクした領域が出てこないこと
dir "03_成果物\outputs"      # Drive側の中身が見えること
```

## Mac のセットアップ

**Mac 側のリンク方式は未検証（2026-08-16 時点）。**
Windows のジャンクションと Mac のシンボリックリンクは別物で、
Git がシンボリックリンクをリンクとして記録するため、`.gitignore` での除外が Windows 以上に重要になる。

検証が済むまで、Mac では従来どおり Drive 側で作業する。

```text
/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc
```

Git操作用のローカル作業ディレクトリは `~/YNFactory-cc`。

```bash
git clone https://github.com/yuichi4107-lab/YNFactory-cc.git ~/YNFactory-cc
```

## 日常作業

### Drive側で作業するもの

- 電子書籍、マンガ、絵本、SNS素材などの成果物
- `03_成果物/outputs/`
- `.company/codex/`
- `04_インプット/inputs/`
- 生活ログ、音声入力、画像、動画、EPUB、PDF、ZIP

### GitHubへ送るもの

- `AGENTS.md`
- `CLAUDE.md`
- `.agents/`
- `.codex/`
- `01_コード/scripts/company/`
- `02_設定/requirements/`
- `docs/`
- 主要コード、設定テンプレート、運用ルール

### Drive側からGitHubへ送る

ローカルGit側で実行する。

```bash
cd ~/YNFactory-cc
python3 01_コード/scripts/company/sync_drive_git.py commit-push -m "変更内容" docs AGENTS.md CLAUDE.md
```

Windowsでは `cd C:\YNFactory-cc` に読み替える。

### GitHubからDrive側へ反映する

ローカルGit側で実行する。

```bash
cd ~/YNFactory-cc
python3 01_コード/scripts/company/sync_drive_git.py pull-sync
```

## 禁止事項

- Drive側でGit操作しない。
- Drive側に `.git` 本体を置かない。
- 大容量成果物をGitに入れない。
- `.env`、APIキー、トークン、パスワードをGitに入れない。
- 同じファイルを複数PCから同時編集しない。
- 同じ自動化を複数PCで同時起動しない。

## 新しいPCを追加したら最初に読むもの

```text
AGENTS.md
CLAUDE.md
docs/multi-pc-rules.md
docs/backup-zslim.md
.company/secretary/HANDOFF.md
.company/secretary/todos/
```

## 完了チェック

- [ ] Drive側 `YNFactory-cc` が見える
- [ ] ローカルGit側 `YNFactory-cc` が見える
- [ ] ローカルGit側で `git pull --ff-only origin main` が成功する
- [ ] ClaudeCode / Codex でDrive側を開ける
- [ ] GitHubへ送る変更は `sync_drive_git.py` で反映できる
- [ ] ZSlimバックアップ方針を確認した
