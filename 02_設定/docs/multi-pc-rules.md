---
title: マルチPC共有ルール
status: active
last_updated: "2026-08-16"
applies_to: "YNFactory-cc を複数PCと ClaudeCode / Codex で共有する全作業"
---

# マルチPC共有ルール

## 0. 結論

**リポジトリ本体は `C:\YNFactory-cc`（Mac は `~/YNFactory-cc`）。**
重い領域と Git 管理外の領域だけを、ジャンクション（Mac はシンボリックリンク）で Drive 側へ逃がす。

| レイヤー | 役割 | 置き場 |
|---|---|---|
| ローカル（C: / ~） | Gitリポジトリ本体。ここで作業し、ここでgitを実行する | `C:\YNFactory-cc` |
| Google Drive | 重い成果物・素材・Git管理外プロジェクトの実体。リンク先 | `G:\マイドライブ\YNFactory-cc` |
| GitHub | コード、ルール、スキル、手順書の履歴 | `yuichi4107-lab/YNFactory-cc` |
| ZSlim | Drive削除・上書き・破損から戻す世代バックアップ | `/Volumes/ZSlim/YNFactory-backups/restic` |

**リンクは「近道」であって「コピー」ではない。実体は世界に1つだけ。**
どちらのパスで書いても同じ場所に保存されるので、「どっちが最新か」を考える必要はない。
どこが実体でどこがリンクかは `docs/folder-structure.md`、仕組みと落とし穴は `docs/link-architecture.md`。

Drive側で `git` を実行しない。Drive上に `.git` を置くと、残留ロック・0バイトオブジェクト・競合コピーによりGitは必ず壊れる。
原因と復旧手順は `docs/git-drive-safety.md`。各PCで初回に1回、ガードフックを入れる。

```bash
cd ~/YNFactory-cc            # Windows は cd C:\YNFactory-cc
python3 01_コード/scripts/company/git_drive_guard.py install-hooks
```

## 1. 作業場所

**作業もgit操作も、すべてローカル側で行う。**

Windows:

```text
C:\YNFactory-cc
```

Mac:

```text
/Users/yuichi/YNFactory-cc
```

Drive側のパス（`G:\マイドライブ\YNFactory-cc` / `~/Library/CloudStorage/...`）を直接開く必要はない。
リンク経由で C: 側から見えるため、日常の作業では意識しなくてよい。

> **移行中の注意（2026-08-16 時点）**
> Cowork の接続フォルダはまだ Drive 側を指している場合がある。
> デスクトップアプリの「フォルダを追加」で `C:\YNFactory-cc` に切り替えること。
> Mac 側のリンクは未対応。Mac では従来どおり Drive 側で作業する。

## 2. Gitに入れるもの

原則として、履歴を残したいコード・ルール・手順だけをGitHubへ送る。

- `AGENTS.md`
- `CLAUDE.md`
- `.agents/`
- `.codex/`
- `01_コード/scripts/company/`
- `02_設定/requirements/`
- `docs/`
- 主要コード
- 設定テンプレート

## 3. Gitに入れないもの

以下はDrive側に残し、GitHubへ送らない。

- `03_成果物/outputs/`
- `.company/codex/`
- `04_インプット/inputs/` の生成・取込状態
- 画像、動画、音声、EPUB、PDF、ZIP
- `.company/.venvs/`
- `node_modules`
- `.env`、APIキー、トークン、認証情報
- ブラウザプロファイル、Playwrightスナップショット、キャッシュ

必要な小さなテキスト成果物だけをGitへ送る場合は、対象パスを明示して個別に扱う。

## 4. Drive側からGitHubへ送る

ローカルGit側で実行する。

```bash
cd /Users/yuichi/YNFactory-cc
python3 01_コード/scripts/company/sync_drive_git.py commit-push -m "変更内容" <相対パス...>
```

Windowsでは `cd C:\YNFactory-cc` に読み替える。

重要:

- パスはリポジトリルートからの相対パスで指定する。
- `git add -A` のような広いステージングは避ける。
- 秘密情報・大容量ファイル・生成物が混ざっていないか確認する。

## 5. GitHubからDrive側へ反映する

**セッション開始時に必ず実行する。** ローカルGit側で実行する。

```bash
cd /Users/yuichi/YNFactory-cc
python3 01_コード/scripts/company/sync_drive_git.py pull-sync
```

これにより、GitHubから取得したコード・ルール・手順書がDrive側へ戻る。

### 基本サイクル（2026-08-09 確立）

```
セッション開始 → pull-sync（GitHub → Drive）
       ↓
   Drive側で作業
       ↓
セッション終了 → /handoff → commit-push（Drive → GitHub、パス明示）
```

`pull-sync` は **pullで新たに取得したパスだけ** をDriveへ書き戻す。
ローカルGitが `origin/main` と同一なら何もしない（`No GitHub updates to sync to Drive.`）。
既存の乖離をまとめて埋めたいときは `local-to-drive` にパスを明示する。

**注意**: `pull-sync` は対象パスのDrive側ファイルを**上書きする**。
Driveは全PCで即時共有されるため、別PCがDrive上で同じファイルを編集中だと、
GitHub側の古い内容で上書きされうる。開始時pullの前に、GitHubへ未pushの変更が
Drive側に無いか確認する。心配なら先に `commit-push` してから `pull-sync` する
（毎日03:00の `daily_git_sync.py` も commit → push → pull の順）。

**実例（2026-08-09）**: Windows側で整理作業中にMac側セッションが同じDriveの
`HANDOFF.md` と `shorts-factory/src/pipeline.py` を更新した。§6の「その日の主担当PCだけが書く」
を守れないと、この種の同時編集が起きる。

## 6. 同時編集ルール

- 同じファイルを複数PCから同時に編集しない。
- `.company/secretary/HANDOFF.md` と当日TODOは、その日の主担当PCだけが書く。
- 自動化は1つのPCまたはVPSだけで動かす。同じタスクを複数PCに登録しない。
- Drive競合コピーを見つけたら、片方を即削除せず、本体へ内容を統合してから削除する。

## 7. Git破損の点検

Git操作でエラーが出たとき、およびバックアップ前に点検する。

```bash
cd /Users/yuichi/YNFactory-cc
python3 01_コード/scripts/company/git_drive_guard.py check
python3 01_コード/scripts/company/git_drive_guard.py fix   # 安全に直せるものだけ隔離
```

`fix` は削除せず `_archive/git-drive-quarantine/` へ移動する。実行前に、他PC・他ターミナルでgitが動いていないことを確認する。

詳細は `docs/git-drive-safety.md` を読む。

## 8. バックアップ

Google Drive同期はバックアップではない。削除や破損も同期される。

このPCでは、ZSlimへ世代バックアップする。

```bash
cd /Users/yuichi/YNFactory-cc
python3 01_コード/scripts/company/backup_zslim_restic.py run
```

保持期間:

- 日次7世代
- 週次8世代
- 月次12世代

詳細は `docs/backup-zslim.md` を読む。

## 9. 実行直前に承認が必要な操作

以下は、方針が決まっていても直前承認を取る。

- `.git_drivebackup` の削除
- Drive競合ファイルの削除
- 大規模な `git rm --cached`
- 外部サービスへの投稿、送信、公開
- 本番環境への不可逆反映

## 10. 禁止事項

- Drive側で `git commit` / `git pull` / `git push` しない。
- Drive側に `.git` 本体を置かない。
- Drive同期中（Driveアイコンが回転中）にGit操作しない。
- `.env` や実トークンをGitに入れない。
- 大容量成果物をGitに入れない。
- `git push --force` を使わない。
- 手作業でDrive側とローカルGit側を丸ごと上書き同期しない。

## 11. 迷ったとき

- 制作物か、履歴管理したいコードかを先に分ける。
- 制作物ならDrive側に置く。
- コード・ルール・手順ならGitHubへ送る。
- 復元性が必要ならZSlimバックアップを見る。
