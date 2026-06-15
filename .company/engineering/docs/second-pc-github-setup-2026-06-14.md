---
title: Mac用 2台目PC GitHubセットアップ指示書
date: "2026-06-14"
status: active
scope: GitHubを正本として、MacにYNFactory-cc作業環境を作る
---

# 2026-06-15 現行方針への注意

この文書は「ローカルGit作業ディレクトリを作る」ための参考資料。現在の日常作業はDrive側 `YNFactory-cc` を開き、GitHubへ送るものだけローカルGit側へ反映する。最新の全体手順は `docs/setup-multi-pc.md` を優先する。

# Mac用 2台目PC GitHubセットアップ指示書

この手順は、今GitHubにpushした内容をMacへ持っていき、Codex/Claude系の作業ディレクトリとして使える状態にするためのものです。

## 方針

- 正本は GitHub: `https://github.com/yuichi4107-lab/YNFactory-cc.git`
- Macでは、まず `~/YNFactory-cc` にクローンして使う
- Google Drive は大容量成果物や同期済みファイルの置き場として扱い、Git履歴の正本にはしない
- `.git` はGoogle Drive配下に置かない
- 作業開始時はpull、作業終了時はcommit/pushする

## 事前確認

Macで以下を確認する。

1. Git が入っている
2. GitHubへアクセスできる
3. GitHubの認証が通る
4. `~/YNFactory-cc` が既に存在する場合、中身を勝手に消さない
5. Google Drive for desktop を使う場合、マイドライブがどこにマウントされているか確認する

確認コマンド:

```bash
git --version
git config --global user.name
git config --global user.email
```

未設定なら設定する:

```bash
git config --global user.name "YOUR_NAME"
git config --global user.email "YOUR_EMAIL"
git config --global core.longpaths true
```

Google Driveの場所を確認する:

```bash
ls "$HOME/Library/CloudStorage"
```

よくある候補:

```text
~/Library/CloudStorage/GoogleDrive-メールアドレス/My Drive/YNFactory-cc
~/Library/CloudStorage/GoogleDrive-メールアドレス/マイドライブ/YNFactory-cc
```

## 新規セットアップ手順

ターミナルを開いて実行する。

```bash
cd ~
git clone https://github.com/yuichi4107-lab/YNFactory-cc.git ~/YNFactory-cc
cd ~/YNFactory-cc
git branch --show-current
git rev-parse --short HEAD
git status
```

期待する状態:

- ブランチが `main`
- `git status` が正常に表示される
- `fatal` や認証エラーが出ない

## 既に `~/YNFactory-cc` がある場合

削除せず、まず状態を確認する。

```bash
cd ~/YNFactory-cc
git remote -v
git branch --show-current
git rev-parse --short HEAD
git status --short
```

`origin` が以下ならOK:

```text
https://github.com/yuichi4107-lab/YNFactory-cc.git
```

未保存の変更がない場合だけ、最新化する:

```bash
git pull --ff-only origin main
```

未保存の変更がある場合は、消さずに作業を止めて、変更内容を確認してから判断する。

```bash
git status --short
```

## Codexで開く場所

MacのCodexでは、作業ディレクトリとして次を開く。

```text
~/YNFactory-cc
```

Codexが信頼確認を出したら、このフォルダを信頼する。

作業開始後、最初に確認するファイル:

```text
~/YNFactory-cc/AGENTS.md
~/YNFactory-cc/.company/secretary/HANDOFF.md
~/YNFactory-cc/.company/secretary/todos/
```

## Google Driveを併用する場合

MacにGoogle Drive for desktopがあり、Drive側にも `YNFactory-cc` が存在する場合でも、Git操作は原則 `~/YNFactory-cc` で行う。

やってよいこと:

- Google Drive上の大容量成果物を見る
- 必要な画像、EPUB、動画、データを参照する
- Git管理外の成果物をDriveで受け渡す

避けること:

- Google Drive側で `git commit` / `git pull` / `git push` する
- Google Drive側の `.git` を作り直す
- `~/YNFactory-cc` とGoogle Drive側の同名ファイルを手作業で上書き同期する

## 日常運用

作業開始:

```bash
cd ~/YNFactory-cc
git pull --ff-only origin main
```

作業後の確認:

```bash
git status --short
```

コミット:

```bash
git add <変更したファイル>
git commit -m "変更内容を短く書く"
git push origin main
```

作業中に別PCでも作業した可能性がある場合:

```bash
git pull --rebase origin main
git push origin main
```

## トラブル時

### 認証エラーが出る

GitHubへのログインまたは認証情報の再設定が必要。

```bash
gh auth status
```

GitHub CLIが入っていない場合は、ブラウザ認証またはPersonal Access Tokenで認証する。

GitHub CLIを使う場合:

```bash
gh auth login
```

### `~/YNFactory-cc` が既にあり、cloneできない

削除せず、まず中身を確認する。

```bash
ls -la ~/YNFactory-cc | head -30
git -C ~/YNFactory-cc status --short
git -C ~/YNFactory-cc remote -v
```

既存フォルダをどう扱うか判断が必要な場合は、この出力だけ共有する。

### Google Drive側と `~/YNFactory-cc` で内容が違う

GitHubで管理するコード・指示書・スキルは `~/YNFactory-cc` を優先する。

Google Drive側の成果物が必要な場合は、どのファイルが必要かを明確にしてから個別に扱う。フォルダ丸ごとの上書き同期はしない。

## 完了チェック

- [ ] `~/YNFactory-cc` が存在する
- [ ] `git remote -v` が `yuichi4107-lab/YNFactory-cc.git` を向いている
- [ ] ブランチが `main`
- [ ] `git pull --ff-only origin main` が成功する
- [ ] `AGENTS.md` が読める
- [ ] `.company/secretary/HANDOFF.md` が読める
- [ ] Codexで `~/YNFactory-cc` を開ける
