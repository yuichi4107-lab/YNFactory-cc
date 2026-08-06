# git HEAD消失からの復旧手順書（runbook）

- 日付: 2026-05-30 (土)
- 対象機: **YN_FACTORY**（自宅Windows・作業本機）
- 起票: 秘書（Claude Code / systematic-debugging）
- 状態: **復旧完了（2026-05-30 Claude Code が実施）** — 末尾「実施結果」を参照

## 症状
`git` の全コマンドが `fatal: not a git repository: C:/dev/YNFactory-git/.git` で失敗。コミット不能。

## 根本原因（特定済み・2つの故障が重複）
1. **アクティブ `.git` 実体の不在**: Drive側 `G:\マイドライブ\YNFactory-cc\.git` は
   `gitdir: C:/dev/YNFactory-git/.git` を指すポインタファイルだが、`C:\dev\YNFactory-git\` が本機に存在しない。
   → Phase2（.gitのローカル移設）が**未完了**だった（移設先フォルダが作られていない）。
2. **唯一の実体 `.git_drivebackup`（Drive上, 4.69GB）の `HEAD` 欠落**:
   `HEAD.lock`（中身 `ref: refs/heads/codex/sagyo`）が残存していた。
   = HEAD書き込みの最中に中断（電源断 / Drive同期競合）し、HEADファイルを喪失。HEADが無いと git はリポジトリと認識しない。

## 確定事実（`.git_drivebackup` 内）
| 項目 | 値 |
|---|---|
| バックアップ場所 | `G:\マイドライブ\YNFactory-cc\.git_drivebackup`（4.69GB / objects 25ファイル） |
| 最新コミット | **`d0a777cfac838f451203ccdbba9eb663d716e202`**（"chore(repo): 大型バイナリの履歴除去後の.gitignore更新"） |
| HEADが指すべき先 | **`refs/heads/codex/sagyo`**（loose ref = d0a777c で確認） |
| 他ブランチ | `master`=7a6d830 / `codex/ebookgpt5.5`=7a6d830（packed-refsのみ・古い） |
| reflog | `logs/HEAD` は1行（filter-repo後にリセット済） |

> 補足: 実ブランチは `main` ではなく作業ブランチ **`codex/sagyo`**。最新作業はここに乗っている。

---

## 復旧手順（PowerShell・本機 YN_FACTORY で実行）

> 前提: git GUI/エディタ等の git プロセスを全終了してから実施。
> `.git_drivebackup` は **検証完了まで絶対に消さない**（現状これが唯一の実体）。

### 1. バックアップ → ローカルへ復元（4.69GB / 数分）
```powershell
robocopy "G:\マイドライブ\YNFactory-cc\.git_drivebackup" "C:\dev\YNFactory-git\.git" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /MT:8 /NFL /NDL /NP
# robocopy の終了コードは 8未満なら成功（0〜7は正常系）
```

### 2. ロック・Drive痕跡の除去（ローカル側）
```powershell
$g = 'C:\dev\YNFactory-git\.git'
Get-ChildItem -LiteralPath $g -Recurse -Force -Filter 'desktop.ini' -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -LiteralPath $g -Recurse -Force -Filter '*.lock'      -ErrorAction SilentlyContinue | Remove-Item -Force
```

### 3. HEAD 再作成（codex/sagyo を指す・LF / BOMなし）
```powershell
[System.IO.File]::WriteAllText('C:\dev\YNFactory-git\.git\HEAD', "ref: refs/heads/codex/sagyo`n")
```

### 4. git が認識するか確認（作業ツリーから）
```powershell
Set-Location 'G:\マイドライブ\YNFactory-cc'
git rev-parse --git-dir          # → C:/dev/YNFactory-git/.git
git symbolic-ref HEAD            # → refs/heads/codex/sagyo
git rev-parse --short HEAD       # → d0a777c
git log --oneline -3
```

### 5. 整合性検証（最重要）
```powershell
git fsck --full
```
- `missing` / `broken` が出たら **STOP**。バックアップが不完全（Drive同期漏れ）の可能性。
  `.git_drivebackup` は消さず、Drive 側で当該フォルダを「オフラインで使用可能（ローカルにダウンロード）」にしてから再度 robocopy、それでも駄目なら相談。

### 6. 壊れた index の幽霊削除をクリア（作業ファイルは無変更）
```powershell
git reset            # mixed: index を HEAD から再構築。作業ツリーは触らない
git status -s | Measure-Object -Line   # 実際の差分件数を把握
```

### 7. packed-refs 整備（任意）
```powershell
git pack-refs --all
```

---

## 復旧後：在庫コミット
```powershell
git status -s | Select-Object -First 60    # 内容確認（巨大バイナリ/EPUBが混じっていないか）
git add -A
git commit -m "feat: 在庫一括コミット（vol4マンガ完結巻55P / ChatGPTを部下にする働き方 / 5.5マンガ脚本v2 / TODO整理 ほか）"
```
- 前提: `.gitignore` に `AYC/` `.company/codex/` `.claude/worktrees/` が入っている（d0a777c で対応済）こと。
- EPUB は `.gitignore` 対象（Drive保全）。`git status` で再混入が無いか必ず確認。

## 後片付け（数日 問題なければ・容量 ~17.5GB 解放）
- `.git_drivebackup`（4.69GB）削除
- Google Drive ゴミ箱を空に（旧 worktree 12.69GB）

## 再発防止
- `.git` は必ずローカル（`C:\dev\YNFactory-git\.git`）に置き、**Drive に同期させない**。
  Drive 側は `gitdir:` ポインタファイルのみ（この方式は正しい。今回は「移設先の作成」が抜けていただけ）。
- `config` に `[extensions] worktreeConfig = true` が残存。worktree を使わないなら
  `git config extensions.worktreeConfig false` にしてよい（任意）。

---

## 実施結果（2026-05-30 復旧完了 / Claude Code 実施）

### 復旧前の追加検証（手順書の前提を実機で確認）
- `.git_drivebackup`：4.69GB / Offline(未DL)ファイル **0件** → robocopyで完全コピー可能
- loose ref `refs/heads/codex/sagyo`：**41バイト・クリーン**（先頭hex `64 30 61 37 37 37 63…0a` = `d0a777c…\n`）→ HEAD再作成で最新コミットに正しく着地。packed-refsの古い値(`6ba70f0`)はloose refが上書き
- `HEAD` 実在せず／`HEAD.lock` のみ（中身 `ref: refs/heads/codex/sagyo`）→ 故障②確定
- `config` に remote 無し → clone復旧不可、robocopy復元が唯一の道
- C: 空き 197.6GB

### 実行ログ
1. robocopy 成功（exit=1）：38ファイル / 4.69GB を `C:\dev\YNFactory-git\.git` へ復元。`desktop.ini`/`*.lock` は `/XF` で除外（混入0件）
2. HEAD 再作成（28バイト・LF/BOMなし）：`ref: refs/heads/codex/sagyo`
3. git 認識確認：`git-dir=C:/dev/YNFactory-git/.git` / `symbolic-ref=refs/heads/codex/sagyo` / `HEAD=d0a777c` / `branch=codex/sagyo`
4. `git fsck --full`：**missing/broken/corrupt なし**（dangling 0）→ 整合性クリア
5. `git reset`（mixed）：indexをHEADから再構築。**幽霊削除7307件 → 削除(D)=0** に解消（作業ツリー無変更）
6. 実差分：総1287（M73 / 新規?? 1180 / 改名R 34 / D 0）。EPUB/巨大バイナリの混入なし＝`.gitignore` 健全

### 残作業
- 在庫コミット（1287変更）：**オーナー判断待ち**（コミットすれば「commit がハングしない」最終確認も兼ねる）
- 数日問題なければ `.git_drivebackup`(4.69GB) と Drive ゴミ箱の旧worktree(12.69GB) 削除 → 約17.5GB解放
- 任意：`git pack-refs --all`（packed-refsの古い `codex/sagyo=6ba70f0` を loose `d0a777c` に整理）
