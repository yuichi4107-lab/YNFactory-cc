---
title: Google Drive で Git を壊さないルール
status: active
last_updated: "2026-08-06"
applies_to: "YNFactory-cc の全PC・全Git操作"
---

# Google Drive で Git を壊さないルール

## 0. 結論

**`.git` を Google Drive の同期対象に置かない。** これだけで過去に出た git エラーのほぼ全部が消える。

| 場所 | 置くもの | Git操作 |
|---|---|---|
| Drive側 `YNFactory-cc` | 日常作業、制作物、入力 | **禁止** |
| ローカルGit側 `~/YNFactory-cc` / `C:\YNFactory-cc` | Git履歴（`.git` 本体） | ここだけで実行する |

加えて、各PCで1回だけ次を実行しておく。以後は壊れた状態でのコミット・プッシュが自動で止まる。

```bash
cd ~/YNFactory-cc
python3 01_コード/scripts/company/git_drive_guard.py install-hooks
```

## 1. なぜ Drive 上で Git が壊れるのか

Git は `.git` の中で、次の3つを前提に動く。

1. ロックファイル（`index.lock` など）を作った瞬間から、消すまで自分だけが触る
2. オブジェクトファイルは書き込みが完了した時点で全バイト揃っている
3. ファイル名が一意である

Google Drive はこの3つを全部壊す。

- 同期はファイル単位・非同期なので、**ロックファイルだけが先に他PCへ配られる**（→ `index.lock` が消えない）
- 大きいオブジェクトの同期が途中で切れると、**0バイトのファイル**が残る（→ `object file is empty`）
- 2台で同時に触ると、**`HEAD (1)` や `config の競合コピー` を `.git` の中に作る**（→ `bad object` / `broken link`）
- ストリーミング（オンラインのみ）設定だと、**実体のないプレースホルダ**を Git が読む

つまり Drive は「Git が壊れることがある」のではなく、**Drive 上に `.git` を置いた時点で壊れるのが正常動作**。だから設定で回避するのではなく、置き場所で回避する。

## 2. エラー別の原因と対処

| 出たエラー | 原因 | 対処 |
|---|---|---|
| `fatal: Unable to create '.../index.lock': File exists` | 同期で残留したロック、または他PCのgitが動作中 | 他PCでgitが動いていないことを確認 → `git_drive_guard.py fix` |
| `error: object file .git/objects/xx/... is empty` | Drive がオブジェクトを0バイトで同期 | §4 の復旧手順（自動修復しない） |
| `fatal: loose object ... is corrupt` | 同上 | §4 の復旧手順 |
| `error: bad signature 0x00000000` / `index file corrupt` | `.git/index` が同期で破損 | `rm .git/index && git reset` で index を作り直す |
| `error: bad object HEAD` / `broken link from ...` | `.git` 内に競合コピーが混入 | `git_drive_guard.py fix` → 直らなければ §4 |
| `warning: unable to unlink ...: Permission denied` | Drive がファイルをロック中 | 同期完了を待つ。Drive のアイコンが「完了」になってから再実行 |
| `fatal: not a git repository` | Drive側で git を叩いた | ローカルGit側へ `cd` する |
| 何も変えていないのに全ファイルが差分になる | PC間の改行コード差 | `git config core.autocrlf` を全PCで揃える（Mac/Linux `input`、Windows `true`） |
| `desktop.ini` / `.DS_Store` が毎回差分に出る | Drive のメタデータが追跡されている | `git rm --cached <path>`（大規模なら実行前に承認を取る） |

## 3. 予防の3段構え

### (1) 置き場所

- Drive側に `.git` を作らない・置かない（マルチPCルール §9）
- Drive側でのGit操作は `sync_drive_git.py` 経由に限る。直接 `git` を叩かない
- Drive for desktop は「ストリーミング」ではなく **「ミラーリング」** で使う

### (2) 自動ガード（pre-commit / pre-push フック）

`install-hooks` を実行すると、コミット時とプッシュ時に次を自動判定して、危険なら操作を中止する。

- 作業ツリーまたは `.git` がクラウド同期フォルダ内にある
- 残留ロックファイルがある
- `.git` に競合コピー・同期ゴミがある
- `.git` に0バイトのファイルがある

フックは `.git/hooks` 配下でGit管理外のため、**PCごとに1回インストールが必要**。緊急時のみ `--no-verify` で回避できる。

### (3) 定期点検

```bash
cd ~/YNFactory-cc
python3 01_コード/scripts/company/git_drive_guard.py check          # 通常点検
python3 01_コード/scripts/company/git_drive_guard.py check --deep   # git fsck --full まで
```

`check` は上記に加えて、Drive側の `.git` 残存、作業ツリーの競合コピー、追跡済みDriveゴミ、`.gitignore` の不足、フック未導入も見る。

**危険** が1件でも出たら終了コード1を返す。ZSlimバックアップ前に流しておくと、壊れた状態をバックアップに焼き付けずに済む。

### 修復

```bash
python3 01_コード/scripts/company/git_drive_guard.py fix --dry-run   # 何が動くか確認
python3 01_コード/scripts/company/git_drive_guard.py fix
```

`fix` は**削除をしない**。対象を `_archive/git-drive-quarantine/<日時>/` へ移動するだけなので、判断を誤っても戻せる。実行前に、他PC・他ターミナル・エディタで git が動いていないことを必ず確認する。隔離ファイルの削除は、問題解決を確認したうえで承認を取ってから行う。

自動修復するのは次の2つだけ。

- 残留ロックファイル（既定で10分以上放置されたもの）
- `.git` 内の競合コピー・同期ゴミ

作業ツリー側の競合コピーは、本体と中身が違う可能性があるため**報告のみ**。内容を本体へ統合してから手で消す（マルチPCルール §6）。

## 4. 壊れてしまったときの復旧

上から順に試す。オブジェクト破損は直せないので、履歴を作り直すのが最短。

1. **点検**: `git_drive_guard.py check --deep` で破損範囲を把握する
2. **ロック・競合コピーだけなら**: `git_drive_guard.py fix` → `git status` が通れば完了
3. **index だけ壊れているなら**: `rm .git/index && git reset`（作業ツリーの中身は消えない）
4. **オブジェクトが壊れているなら**: 未プッシュの変更を退避してから、`.git` を作り直す

```bash
# 4の手順。未コミットの変更を先に別フォルダへコピーしておく
cd ~
mv YNFactory-cc YNFactory-cc.broken
git clone git@github.com:yuichi4107-lab/YNFactory-cc.git YNFactory-cc
cd YNFactory-cc
python3 01_コード/scripts/company/git_drive_guard.py install-hooks
```

5. **GitHub にも無い変更が失われたら**: ZSlim の世代バックアップから戻す → `02_設定/docs/backup-zslim.md`

`.git_drivebackup/` は過去の `.git` 復元コピー（約4.7GB）。復旧の材料にはなるが、**作業ツリーへ戻してコミットしない**。履歴が再肥大化する。

## 5. やってはいけないこと

- Drive側で `git init` / `git clone` / `git commit` / `git pull` / `git push`
- 同期中（Drive アイコンが回転中）のGit操作
- 破損した `.git` に対する `git gc` / `git prune`（壊れたまま確定する）
- `.git` 内のファイルを手で削除する（`fix` の隔離を使う）
- `git push --force`

## 6. 関連ドキュメント

- `02_設定/docs/multi-pc-rules.md` — マルチPC共有ルール全体
- `02_設定/docs/backup-zslim.md` — ZSlim 世代バックアップ
- `02_設定/docs/setup-multi-pc.md` — 新しいPCのセットアップ
