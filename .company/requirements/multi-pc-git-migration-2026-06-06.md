# 要件定義書: マルチPC同時運用への移行（git正典化 + Phase A〜工程5）

> **実行はオーナー承認後**。本書はすべて計画・定義のみ。破壊的操作（git commit / rm、ファイル移動、ジャンクション作成、Task Scheduler変更）は一切含まない。

作成日: 2026-06-06  
作成者: requirements-definer エージェント  
対象リポジトリ: `yuichi4107-lab/YNFactory-cc` branch `main`

---

## ゴール

各PCが独立クローン `C:\YNFactory-cc` で安全に作業・自動化できるマルチPC構成を完成させ、大容量バイナリはDrive専用フォルダ＋ジャンクションで各クローンに合成、自動化スクリプトはクローンパスで稼働している状態を実現する。

---

## スコープ

### やること

- Drive作業ツリーの未コミットchurnをパッチ/bundleで安全退避する（Phase A）
- 今日分の新しいファイル（lifelog/inbox/todos）をクローン経由でoriginに取り込む（Phase A）
- クローンを `origin/main`（cac2631）にFF追従して正典に一本化する（Phase A）
- `.company/outputs` 配下の大容量ディレクトリをgit管理外化し `YNFactory-cc-data` へ移動する（工程2）
- クローンに対象ディレクトリのジャンクションを張る（工程3）
- 4つの自動化スクリプトのハードコードパスをクローン参照に修正する（工程3）
- Task Scheduler「YNFactory-MorningBriefing」をクローンパスに再登録する（工程3）
- マルチPCセットアップ手順書 `docs/setup-multi-pc.md` を作成する（工程4）
- 同時運用ルール `docs/multi-pc-rules.md` を作成する（工程5）

### やらないこと

- `C:\dev\YNFactory-git`（Drive側の旧repo）への新規コミット・修正・削除（当面はそのまま保持、自動化の参照先を工程3でクローンへ切替えるだけ）
- keiba-unified・ai-trade-system・notebooklm-sync など `.company/outputs` 以外のコード系プロジェクトのリポジトリ統廃合
- Macや2台目WindowsのClaudeセットアップ（工程4手順書作成で参照するのみ）
- yntools・VPS上のデプロイや設定変更

---

## 工程一覧

| 工程 | 名称 | 中間成果物 | 入力 |
|---|---|---|---|
| Phase 0 | 前提・オーナー作業 | オーナー確認ゲート合格 | オーナーによる手動確認 |
| Phase A | git正典化 | クローン = origin/main 完全一致、今日分ファイルがoriginに反映 | Phase 0 合格 |
| 工程2 | 大容量バイナリ切り出し | git追跡から大物消去、YNFactory-cc-data 完全構成 | Phase A 合格 |
| 工程3 | ジャンクション＋自動化パス修正＋Task Scheduler再登録 | クローンで自動化が旧来通り動作 | 工程2 合格 |
| 工程4 | セットアップ手順書 | `docs/setup-multi-pc.md` | 工程3 合格 |
| 工程5 | 同時運用ルール策定 | `docs/multi-pc-rules.md` | 工程4 合格 |

---

## Phase 0: 前提・オーナー作業

### 概要

他端末（Mac・2台目Windows）がDriveを同時同期中のまま10GBファイルを移動すると、Drive競合コピー大量発生・他端末の自動化スクリプトパス破損が起きる。これを防ぐために、このPCだけが書き手であることをオーナーが確認してからPhase Aに進む。

### オーナーが確認・実施すること（Claude実行不可）

1. **Mac のDrive同期を一時停止する**（Finderメニューバー → Google Drive → 同期を一時停止）
2. **2台目Windows（ある場合）のDrive同期を一時停止する**（タスクトレイ → Google Drive → 同期を一時停止）
3. **2台目Windowsに自動化タスク（Task Scheduler等）が稼働中でないことを確認する**（稼働している場合は先に停止する）
4. 上記が完了し「このPCだけがDriveの書き手」の状態になったことをオーナーが口頭でClaudeに確認報告する

### 完了条件

- [ ] Mac・2台目WindowsのDrive同期が停止済みであるとオーナーが確認した
- [ ] 2台目Windowsの自動化タスクが停止済みであるとオーナーが確認した（2台目がない場合はN/A）
- [ ] このPCが唯一のDrive書き手であることをオーナーが明示的に報告した

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | Mac の Drive 同期停止を確認した | 前提条件 | 50 |
| 2 | 2台目Windowsの稼働有無と停止を確認した | 前提条件 | 30 |
| 3 | オーナーが口頭確認報告済みである | 前提条件 | 20 |
| 合計 | | | 100 |

### ロールバック手順

- Phase 0 はオーナー確認のみ。ロールバック対象の変更なし。他端末の同期は作業完了後に再開する。

### リスク

| リスク | 影響 | 対策 |
|---|---|---|
| 同期停止忘れで10GB移動した場合 | Drive競合コピー大量生成・他端末のスクリプトパス破損 | 必ずPhase 0合格後にのみ工程2へ進む |
| 2台目Windowsの存在忘れ | 自動化の二重起動・競合 | チェックリストで明示確認 |

---

## Phase A: git正典化

### 概要

Drive作業ツリー（`G:\マイドライブ\YNFactory-cc`）の未コミットchurnを安全に退避し、今日分の新しいファイルをoriginへ取り込んだうえで、クローン（`C:\YNFactory-cc`）を `origin/main`（cac2631）にFF追従して正典に一本化する。Drive側repo（`C:\dev\YNFactory-git`）の重複コミットは当面触らず、参照先を工程3でクローンへ切り替える。

### やること（細分化ステップ）

#### A-1: Drive作業ツリーのchurnを安全退避

対象: Drive作業ツリーの未コミット変更（git status で18 modified + 2 untracked）

実施手順:
```
# Drive作業ツリーで実行（C:\dev\YNFactory-git を gitdir として使用）
git --git-dir="C:\dev\YNFactory-git\.git" --work-tree="G:\マイドライブ\YNFactory-cc" diff HEAD > G:\マイドライブ\YNFactory-cc\.git_drivebackup\drive-churn-2026-06-06.patch
git --git-dir="C:\dev\YNFactory-git\.git" --work-tree="G:\マイドライブ\YNFactory-cc" bundle create G:\マイドライブ\YNFactory-cc\.git_drivebackup\drive-churn-2026-06-06.bundle HEAD
```

保存先 `.git_drivebackup/` は .gitignore 済みのため git 追跡されない（安全）。

#### A-2: 今日分の新しいファイルをoriginへ取り込み

保全対象ファイル（originにない可能性があるもの）:
- `04_インプット/inputs/conversations/2026-06-05-lifelogs.md`
- `04_インプット/inputs/indexes/lifelog-decisions.md`（更新分）
- `04_インプット/inputs/indexes/lifelog-people.md`（更新分）
- `04_インプット/inputs/indexes/lifelog-todo-candidates.md`（更新分）
- `04_インプット/inputs/indexes/lifelog-topics.md`（更新分）
- `.company/secretary/inbox/2026-06-06.md`
- `.company/secretary/todos/2026-06-06 (1).md`（Drive競合コピー。内容確認後にリネームorマージ）
- `.company/requirements/notebooklm-sync-mac-migration-2026-06-06.md`（更新分）
- `.company/secretary/HANDOFF.md`（更新分）

実施手順:
```
# クローンで実行
cd C:\YNFactory-cc
git pull origin main   # cac2631 -> 最新（FFのはず）
# 上記ファイルをクローンにコピー（Drive → C:\YNFactory-cc）
# git add <対象ファイルのみ>
# git commit -m "chore: Drive作業ツリーの今日分ファイルを保全取り込み"
# git push origin main
```

注意事項:
- `M sengoku-game` は gitlink（独立リポ）のため据え置き。触らない。
- `?? .company/secretary/todos/2026-06-06 (1).md` はDrive競合コピー。`2026-06-06.md` と内容比較し、新しい方を正とする。競合コピーは削除してよい。
- scanner.py は origin/main と diff 0 のため skip。
- expand_manga_to_100_pages.py、batch_*.md、comicle_output.csv、verify_downtrend_filter.py、notebooklm.py は内容確認してから判断（originより旧い場合はskip）。

#### A-3: クローンをorigin/mainへFF

```
cd C:\YNFactory-cc
git fetch origin
git merge --ff-only origin/main  # A-2のpush後ならすでに一致のはず
```

#### A-4: Drive側repoの扱い（当面は触らない）

- `C:\dev\YNFactory-git` の HEAD=609bbe0 は「ahead3」だが origin に同内容（別ハッシュ）で反映済み。作業消失なし。
- 工程3で自動化スクリプトのgit参照先をクローンへ切り替えた後、Drive側repoは参照されなくなる。
- Drive側repoの整理（削除・アーカイブ）は工程3完了後に別タスクとして検討する。今フェーズでは読み取りのみ。

#### A-5: 検証

```
cd C:\YNFactory-cc
git log --oneline -5
git status         # 「nothing to commit, working tree clean」であること
git rev-parse HEAD # origin/main と一致すること
```

### 完了条件

- [ ] `C:\YNFactory-cc` の HEAD が origin/main と同一ハッシュであること
- [ ] `git status` が「nothing to commit, working tree clean」であること
- [ ] 今日分のファイル（lifelog/inbox/todos/HANDOFF）がoriginに存在すること
- [ ] Drive作業ツリーのchurnパッチ・bundleが `.git_drivebackup/` に保存されていること
- [ ] sengoku-game gitlink が変更されていないこと

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | クローン HEAD = origin/main ハッシュ一致 | 機能要件 | 35 |
| 2 | working tree clean（余分なファイルなし） | 機能要件 | 25 |
| 3 | 今日分保全ファイルが全てoriginに存在 | 機能要件 | 20 |
| 4 | churnパッチ/bundleがバックアップとして保存済み | 可用性 | 10 |
| 5 | 作業消失ゼロ（origin logsで内容が確認できる） | 品質保証 | 10 |
| 合計 | | | 100 |

### ロールバック手順

- A-3が失敗した場合: `git reset --hard <元のHEAD>` でクローンを戻す
- A-2でpushしたcommitを取り消す場合: `git revert HEAD` でrevertコミットを作成（force pushは禁止）
- Drive作業ツリーのファイルはパッチ/bundleから完全復元可能（`.git_drivebackup/` を保持）

### リスク

| リスク | 影響 | 対策 |
|---|---|---|
| A-2の保全コピーで旧版を誤push | originが古い内容に汚染 | diff確認後に対象ファイルを個別判断してからadd |
| 競合コピー「2026-06-06 (1).md」を間違えて本物として扱う | 本物todosが消える | 両ファイルの内容を確認して新しい方を使用 |
| `git merge --ff-only` が失敗（非FF状態） | HEAD不一致 | `git fetch && git status` で原因確認後、rebaseかresetで解決 |

---

## 工程2: 大容量バイナリ切り出し

### 概要

`.company/outputs` 配下の大容量ディレクトリおよびgitignoreに指定されている大物ディレクトリをgit追跡から完全除外し、Drive専用フォルダ `G:\マイドライブ\YNFactory-cc-data` へ移動する。原稿・生成スクリプト・EPUB内部ファイルも含む「丸ごと」の移動。

### 移動対象インベントリ（確定）

#### A群: .company/outputs 配下（丸ごとDrive専用化）

| ディレクトリ | 現git追跡数 | 概算容量 | 備考 |
|---|---|---|---|
| `03_成果物/outputs/ebooks-manga/` | 1816ファイル | 7.88GB | xhtml/csv/md/py混在。EPUB本体は.gitignore済みだが付随ファイルがgit追跡中 |
| `03_成果物/outputs/ai-stock-investment/` | 233ファイル（_archives=141） | 1.14GB | _archivesは.gitignore済みだが本体部分が追跡中 |
| `03_成果物/outputs/picture-books/` | 0（.gitignore済み） | 不明 | .gitignoreに記載済みだがDriveに存在する場合は移動対象 |

#### B群: .gitignoreで既に除外済みだが移動が必要な大物

| ディレクトリ/パターン | 備考 |
|---|---|
| `AYC/` | ルート直下。.gitignore済み。物理的にはDrive上に存在する可能性あり |
| `.company/codex/` | .gitignore済み。Codex画像キューのキャッシュ等 |
| `keiba-unified/jra/data/` | .gitignore済み。本番VPS用データの旧コピー |
| `03_成果物/outputs/ai-stock-investment/_archives/` | .gitignore済み |
| `03_成果物/outputs/ebooks-manga/**/pages_backup_*/` | .gitignore済み |
| `03_成果物/outputs/ebooks-manga/**/_cache/` | .gitignore済み |
| `03_成果物/outputs/ebooks-manga/**/archive_20260512_pre-redo/` | .gitignore済み（688MB） |
| `.git_drivebackup/` | .gitignore済み（4.7GB）。git復元コピー。そのままDriveに残す（移動不要） |

#### C群: 全バイナリ（*.png/*.jpg/*.jpeg/*.webp/*.gif/*.mp4/*.mov 等）

.gitignore済みのため git 追跡はなし。ただしこれらを含むディレクトリを丸ごと移動する際は当然含まれる。

### 総移動容量見積もり

| 対象 | 容量 |
|---|---|
| ebooks-manga | 7.88GB |
| ai-stock-investment | 1.14GB |
| picture-books | 不明（要実測） |
| AYC/ | 不明（要実測） |
| .company/codex/ | 不明（要実測） |
| keiba-unified/jra/data/ | 不明（要実測） |
| **合計** | **約10GB以上（確定後に更新）** |

**注**: 正確な総容量は工程2実行前にオーナーが確認すること。Drive空き容量が移動元+移動先を賄えるかの確認も必要。

### 実施手順

#### 2-1: git rm --cached でgit追跡からA群を除外（クローンで実施）

```
cd C:\YNFactory-cc
git rm -r --cached 03_成果物/outputs/ebooks-manga/
git rm -r --cached 03_成果物/outputs/ai-stock-investment/
git rm -r --cached 03_成果物/outputs/picture-books/   # 追跡ファイルがあれば
```

#### 2-2: .gitignoreに丸ごと除外エントリを追加

```
# .gitignore に追記
03_成果物/outputs/ebooks-manga/
03_成果物/outputs/ai-stock-investment/
03_成果物/outputs/picture-books/
```

現在の .gitignore はパターン単位（`*.epub` 等）で除外しているが、これをディレクトリ丸ごと除外に格上げする。

#### 2-3: commit & push

```
git add .gitignore
git commit -m "chore(git): 大容量outputs丸ごとgit管理外化（マルチPC移行 工程2）"
git push origin main
```

#### 2-4: YNFactory-cc-data ディレクトリ作成

```
mkdir "G:\マイドライブ\YNFactory-cc-data"
```

元パス構造をミラーして格納:
```
G:\マイドライブ\YNFactory-cc-data\
  03_成果物\outputs\ebooks-manga\
  03_成果物\outputs\ai-stock-investment\
  03_成果物\outputs\picture-books\
  AYC\
  .company\codex\
  keiba-unified\jra\data\
```

#### 2-5: Drive作業ツリーから移動（Phase 0の他端末同期停止下で実施）

```powershell
# PowerShellで実行
$src = "G:\マイドライブ\YNFactory-cc\03_成果物\outputs\ebooks-manga"
$dst = "G:\マイドライブ\YNFactory-cc-data\03_成果物\outputs\ebooks-manga"
Move-Item -Path $src -Destination $dst
# 同様に ai-stock-investment、picture-books、AYC、.company\codex、keiba-unified\jra\data も移動
```

#### 2-6: クローンの対象ディレクトリが空になったことを確認

### 完了条件

- [ ] `git ls-files 03_成果物/outputs/ebooks-manga/` の出力が空であること
- [ ] `git ls-files 03_成果物/outputs/ai-stock-investment/` の出力が空であること
- [ ] `03_成果物/outputs/picture-books/`・`AYC/`・`.company/codex/`・`keiba-unified/jra/data/` の追跡ファイルが0であること
- [ ] `G:\マイドライブ\YNFactory-cc-data` が作成されており、移動対象のディレクトリが元パス構造で格納されていること
- [ ] 総移動容量が事前見積もりと±10%以内であること
- [ ] `git status` がclean（大物ディレクトリが消えた状態でdirtyにならない）であること
- [ ] Drive上のoriginal位置からファイルが消えていること（移動済み）

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | git追跡から全移動対象ディレクトリが消えている | 機能要件 | 35 |
| 2 | YNFactory-cc-data に完全版が元パス構造で格納されている | 機能要件 | 30 |
| 3 | 総移動容量が見積もり範囲内 | データ完全性 | 15 |
| 4 | git status がclean | 機能要件 | 10 |
| 5 | originにpushが完了している | 機能要件 | 10 |
| 合計 | | | 100 |

### ロールバック手順

- 移動中に失敗した場合: `Move-Item` は移動先にデータが残るため、移動先から元パスに `Move-Item -Path $dst -Destination $src` で戻せる
- `git rm --cached` の取り消し: `git reset HEAD 03_成果物/outputs/ebooks-manga/` でunstageに戻せる（ファイルは消えていない）
- コミット取り消し: `git revert HEAD` でrevertコミットを作成

### リスク

| リスク | 影響 | 対策 |
|---|---|---|
| Drive空き容量不足 | 移動途中でエラー・ファイル破損 | 移動前にDrive空き容量を確認（移動対象の2倍以上の空き必要） |
| 他端末が同期再開して競合コピー発生 | ファイルが重複・破損 | Phase 0で他端末同期停止を徹底 |
| picture-books / AYC / codex の実サイズ未確認 | 想定外の大容量 | 実施前に `Get-ChildItem -Recurse | Measure-Object -Sum Length` で実測 |
| スクリプトがhardcodeで `03_成果物/outputs/ebooks-manga/` を参照している場合 | スクリプト実行エラー | 工程3で修正（工程2後すぐに工程3に進む） |

---

## 工程3: ジャンクション＋自動化パス修正＋Task Scheduler再登録

### 概要

工程2で移動した大物ディレクトリへのジャンクションをクローンに張り、4つの自動化スクリプトのハードコードパスをクローン参照に修正し、Task SchedulerをクローンパスのPS1で再登録する。これにより「クローンで全自動化が旧来通り動く」状態を実現する。

### 3-1: ジャンクション作成

クローン `C:\YNFactory-cc` に対して以下のジャンクションを作成する（`mklink /J`）:

```cmd
mklink /J "C:\YNFactory-cc\03_成果物\outputs\ebooks-manga" "G:\マイドライブ\YNFactory-cc-data\03_成果物\outputs\ebooks-manga"
mklink /J "C:\YNFactory-cc\03_成果物\outputs\ai-stock-investment" "G:\マイドライブ\YNFactory-cc-data\03_成果物\outputs\ai-stock-investment"
mklink /J "C:\YNFactory-cc\03_成果物\outputs\picture-books" "G:\マイドライブ\YNFactory-cc-data\03_成果物\outputs\picture-books"
mklink /J "C:\YNFactory-cc\AYC" "G:\マイドライブ\YNFactory-cc-data\AYC"
mklink /J "C:\YNFactory-cc\.company\codex" "G:\マイドライブ\YNFactory-cc-data\.company\codex"
mklink /J "C:\YNFactory-cc\05_プロジェクト\keiba-unified\jra\data" "G:\マイドライブ\YNFactory-cc-data\keiba-unified\jra\data"
```

**注意**: `mklink /J` は管理者権限が必要。実行前に管理者PowerShellを起動すること。

ジャンクションのgit追跡除外（`.gitignore` に追加済み確認が必要）:
- ジャンクション自体はgitが `symlink` として認識する場合がある。必要に応じて `.git/config` に `core.symlinks=false` を設定するか、`.gitignore` で除外する。

### 3-2: 自動化スクリプトのハードコードパス修正

#### morning-briefing.ps1 の修正箇所

**現状の修正が必要な箇所（読み取り結果から抽出）:**

```powershell
# 修正前
$TodosDir = 'G:\マイドライブ\YNFactory-cc\.company\secretary\todos'
$LogDir   = 'G:\マイドライブ\YNFactory-cc\.company\secretary\scripts\logs'

# 修正後
$TodosDir = 'C:\YNFactory-cc\.company\secretary\todos'
$LogDir   = 'C:\YNFactory-cc\.company\secretary\scripts\logs'
```

（Telegram設定は環境変数から取得済みのため修正不要）

**修正ファイル**: `C:\YNFactory-cc\.company\secretary\scripts\morning-briefing.ps1`

#### register-task.ps1 の修正箇所

**現状の修正が必要な箇所:**

```powershell
# 修正前
$scriptPath = 'G:\マイドライブ\YNFactory-cc\.company\secretary\scripts\morning-briefing.ps1'

# 修正後
$scriptPath = 'C:\YNFactory-cc\.company\secretary\scripts\morning-briefing.ps1'
```

**修正ファイル**: `C:\YNFactory-cc\.company\secretary\scripts\register-task.ps1`

#### sync_all.bat の修正箇所

**現状の修正が必要な箇所:**

```bat
# 修正前
cd /d "G:\マイドライブ\YNFactory-cc"
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 "04_インプット\inputs\sync_limitless.py" ...
# (全行がG:\マイドライブ\YNFactory-ccを作業ディレクトリとして使用)

# 修正後
cd /d "C:\YNFactory-cc"
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" -X utf8 "04_インプット\inputs\sync_limitless.py" ...
```

**Pythonパス** `C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe` はユーザー固有パス。他PCへの展開時は変更が必要だが、このPCではそのまま使用可能。

**修正ファイル**: `C:\YNFactory-cc\04_インプット\inputs\sync_all.bat`

#### sync_limitless.bat の修正箇所

**現状の修正が必要な箇所:**

```bat
# 修正前
cd /d "G:\マイドライブ\YNFactory-cc"
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" ...

# 修正後
cd /d "C:\YNFactory-cc"
"C:\Users\fcmdt\AppData\Local\Programs\Python\Python312\python.exe" ...
```

**修正ファイル**: `C:\YNFactory-cc\04_インプット\inputs\sync_limitless.bat`

#### .bat ファイルの文字コード注意事項

Windows .bat はCP932（Shift-JIS）で動作する。`.bat` ファイルにはASCII文字のみ使用すること（日本語コメントは削除またはREADMEへ移動）。現状のsync_all.bat / sync_limitless.bat はすべてASCIIのため問題なし。

### 3-3: Task Scheduler「YNFactory-MorningBriefing」再登録

**現在の登録内容（読み取り結果）:**
- Execute: `powershell.exe`
- Arguments: `-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "G:\マイドライブ\YNFactory-cc\.company\secretary\scripts\morning-briefing.ps1"`
- WorkingDirectory: （空）
- State: Ready

**修正後の引数:**
```
-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\YNFactory-cc\.company\secretary\scripts\morning-briefing.ps1"
```

**再登録方法（register-task.ps1 を修正後に実行）:**
```powershell
# 修正済みregister-task.ps1を実行
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\YNFactory-cc\.company\secretary\scripts\register-task.ps1"
```

`register-task.ps1` は冒頭で `Unregister-ScheduledTask` を実行してから再登録する設計のため、そのまま実行すれば既存タスクを上書き再登録できる。

### 3-4: 修正後コミット

```
cd C:\YNFactory-cc
git add .company\secretary\scripts\morning-briefing.ps1
git add .company\secretary\scripts\register-task.ps1
git add 04_インプット\inputs\sync_all.bat
git add 04_インプット\inputs\sync_limitless.bat
git commit -m "chore(scripts): 自動化スクリプトのパスをクローン参照に修正（マルチPC移行 工程3）"
git push origin main
```

### 完了条件

- [ ] 6本のジャンクションがクローン内に作成されており、`dir /AL C:\YNFactory-cc\03_成果物\outputs\` でJUNCTIONと表示されること
- [ ] ジャンクション経由でYNFactory-cc-data内のファイルが参照できること（テストread）
- [ ] morning-briefing.ps1 の `$TodosDir` と `$LogDir` がクローンパスに修正されていること
- [ ] register-task.ps1 の `$scriptPath` がクローンパスに修正されていること
- [ ] sync_all.bat / sync_limitless.bat の `cd /d` 行がクローンパスに修正されていること
- [ ] Task Scheduler「YNFactory-MorningBriefing」の引数パスがクローンパスに更新されていること
- [ ] Task Schedulerのタスク状態が「Ready」であること
- [ ] 修正済みスクリプトがoriginにpushされていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 全6ジャンクションが正常に作成され参照できる | 機能要件 | 25 |
| 2 | 4スクリプトの全ハードコードパスがクローン参照に修正された | 機能要件 | 30 |
| 3 | Task Schedulerの引数パスが更新されReady状態 | 機能要件 | 25 |
| 4 | 修正スクリプトがoriginにpushされた | 完了条件 | 10 |
| 5 | ジャンクション先のファイルにread/write疎通確認ができた | 可用性 | 10 |
| 合計 | | | 100 |

### ロールバック手順

- ジャンクション削除: `rmdir "C:\YNFactory-cc\03_成果物\outputs\ebooks-manga"` （ジャンクション自体のみ削除、実体は消えない）
- スクリプト修正の取り消し: `git revert HEAD` でrevertコミット
- Task Scheduler戻し: パスを `G:\マイドライブ\YNFactory-cc\...` に戻して `register-task.ps1` を実行

### リスク

| リスク | 影響 | 対策 |
|---|---|---|
| mklink /J に管理者権限が必要 | 実行エラー | 管理者PowerShellで実行 |
| DriveがオフラインのときジャンクションでI/Oエラー | スクリプト失敗 | Drive同期状態を確認してから実行。スクリプトはTry-Catchでエラーハンドリング済み |
| Python scripts が内部で G:\マイドライブ\YNFactory-cc をhardcodeしている場合 | sync_all実行エラー | `04_インプット/inputs/` 配下のPythonファイルでパス検索して確認（工程3実施前に調査） |

---

## 工程4: セットアップ手順書

### 概要

新規PCでこの構成を再現するための手順書 `C:\YNFactory-cc\02_設定\docs\setup-multi-pc.md` を作成する。

### 必須記載項目

以下のセクションをすべて含むこと:

#### 4-1. 前提条件

- Windows 11 + Google Drive Desktop インストール済みであること
- GitHub アカウント `yuichi4107-lab` への read/write アクセスがあること
- `git` がインストール済みであること
- Python 3.12 が `C:\Users\<USER>\AppData\Local\Programs\Python\Python312\` にあること（またはPATHに存在）
- Telegram Bot Token / Chat ID の環境変数 `TG_BOT_TOKEN` / `TG_CHAT_ID` が設定済みであること

#### 4-2. 手順: クローン作成

```
git clone https://github.com/yuichi4107-lab/YNFactory-cc.git C:\YNFactory-cc
```

#### 4-3. 手順: ジャンクション作成

YNFactory-cc-data がDriveに既に存在する前提で、6本のジャンクションを張る手順（管理者コマンドプロンプト必要）。

#### 4-4. 手順: 環境変数設定

```powershell
[Environment]::SetEnvironmentVariable('TG_BOT_TOKEN', '<your_token>', 'User')
[Environment]::SetEnvironmentVariable('TG_CHAT_ID', '<your_chat_id>', 'User')
```

#### 4-5. 手順: Task Scheduler 登録

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\YNFactory-cc\.company\secretary\scripts\register-task.ps1"
```

#### 4-6. 手順: Pythonパスの確認と必要に応じたスクリプト修正

sync_all.bat / sync_limitless.bat 内のPythonパスがこのPCと一致するか確認。異なる場合はパスを修正してcommit。

#### 4-7. マルチPC運用開始前の確認チェックリスト

- [ ] git clone 完了・HEAD が origin/main に一致
- [ ] ジャンクション 6本が正常に作成されている
- [ ] Task Scheduler「YNFactory-MorningBriefing」が Ready 状態
- [ ] テスト実行（morning-briefing.ps1 を手動で1回実行）で Telegram 通知が届く
- [ ] git pull / push が正常に動作する
- [ ] 他のアクティブなPCのDrive同期が有効になっている（このPCのセットアップ完了後に他端末の同期を再開する）

### 完了条件

- [ ] `C:\YNFactory-cc\02_設定\docs\setup-multi-pc.md` が存在すること
- [ ] 4-1〜4-7 の全セクションが記載されていること
- [ ] 手順がMacやWindowsで再現可能な具体的コマンドを含むこと
- [ ] originにpushされていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 全必須セクション（4-1〜4-7）が揃っている | 網羅性 | 40 |
| 2 | 手順書通りに実行すれば環境を再現できるレベルの具体性 | 実現可能性 | 35 |
| 3 | 確認チェックリストが全項目 Yes/No で判定できる | 検証可能性 | 15 |
| 4 | originにpushされている | 完了条件 | 10 |
| 合計 | | | 100 |

### ロールバック手順

- 手順書作成は新規ファイル追加のみ。ロールバックは `git revert` または `git rm --cached docs/setup-multi-pc.md`。

---

## 工程5: 同時運用ルール策定

### 概要

複数PCが同じリポジトリを同時に使用するための書き込みルール `C:\YNFactory-cc\02_設定\docs\multi-pc-rules.md` を作成する。ファイル競合・gitコンフリクト・Drive競合コピーを防ぐ運用指針。

### 必須記載項目

#### 5-1. 書き込み担当の固定（分業原則）

- **大原則**: 同一ファイルの同時編集を避ける。ファイル種類ごとに「どのPCが主担当か」を決める。
- `.company/secretary/todos/` や `.company/secretary/HANDOFF.md` は「1日1PC書き込み」を原則とする。
- 自動化スクリプト修正は作業PCのみ。修正後は即push。

#### 5-2. pull/push 規律

- **作業開始前**: 必ず `git pull origin main` で最新を取得してから作業を始める。
- **push頻度**: 当日分の作業は当日中にpush（翌日以降に溜めない）。
- **コンフリクト発生時**: `git merge` でなく `git rebase origin/main` を優先。コンフリクト解消後にpush。
- **force push禁止**: `git push --force` は絶対に使わない（別PCのHEADが飛ぶ）。

#### 5-3. Drive競合コピー回避

- `YNFactory-cc-data` 配下のファイル（大容量成果物）への書き込みは、Driveの同期が安定している（オンライン＆同期済み）状態で行う。
- 複数PCが同時に同じ成果物ファイルを書き込まない（後から書いたPCがDrive競合コピーを作る）。
- Drive競合コピー（ファイル名に「競合コピー」が付く）を発見した場合: 新しいタイムスタンプの方を正とし、古い方を削除する。

#### 5-4. 日次同期ルーティン

```
[朝] git pull origin main → 最新を取り込み → 作業開始
[夕] git add <変更ファイル> → git commit → git push origin main
```

#### 5-5. 禁止事項一覧

- `git push --force` / `git push --force-with-lease` の実行
- 同一ファイルを複数PCから同時に `git add && git push`（必ずpull先行）
- `YNFactory-cc-data` 移行前に Drive 同期を再開（他端末の保護のため）
- Task Scheduler タスクを複数PCに同名で同時登録（同一Telegramアカウントへの重複通知発生）

#### 5-6. Driveバックアップの意義と役割

- `YNFactory-cc-data` = 全PCが参照するDrive専用の大容量成果物。書き込みPCは基本1台ずつ。
- `git` = コードとテキスト成果物の正典。GitHub が唯一の真実のソース。
- Drive は大容量バイナリの配布基盤であり、バージョン管理はしない（git役割外）。

### 完了条件

- [ ] `C:\YNFactory-cc\02_設定\docs\multi-pc-rules.md` が存在すること
- [ ] 5-1〜5-6 の全セクションが記載されていること
- [ ] 禁止事項一覧が明確に記載されていること
- [ ] originにpushされていること

### 品質チェック項目

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 全必須セクション（5-1〜5-6）が揃っている | 網羅性 | 35 |
| 2 | 禁止事項が具体的なコマンド例付きで記載されている | 表現の品質 | 25 |
| 3 | 複数PCのコンフリクトシナリオへの対処が明記されている | 整合性 | 25 |
| 4 | originにpushされている | 完了条件 | 15 |
| 合計 | | | 100 |

### ロールバック手順

- 手順書作成は新規ファイル追加のみ。ロールバックは `git revert` または `git rm --cached docs/multi-pc-rules.md`。

---

## 全体リスクサマリー

| リスク | 影響フェーズ | 優先度 |
|---|---|---|
| 他端末同期停止忘れで10GB移動中に競合発生 | 工程2 | 最高 |
| git ff-only 失敗（origin との diverge） | Phase A | 高 |
| picture-books / AYC / codex の実容量が想定外 | 工程2 | 高 |
| Drive容量不足で移動失敗・ファイル破損 | 工程2 | 高 |
| mklink /J に管理者権限が必要で実行失敗 | 工程3 | 中 |
| Python内部スクリプトのhardcodeパス修正漏れ | 工程3 | 中 |
| setup-multi-pc.md の手順が特定PCに依存しすぎて他PCで再現不可 | 工程4 | 低 |

---

## 付録: 工程間依存関係

```
Phase 0 合格
    ↓
Phase A 合格（git正典化）
    ↓
工程2 合格（大容量切り出し） ← Phase 0同期停止が前提
    ↓
工程3 合格（ジャンクション＋スクリプト修正）
    ↓
工程4 合格（setup手順書）
    ↓
工程5 合格（同時運用ルール）
    ↓
完了 → 他端末のDrive同期を再開
```

**前工程が合格（85点以上）するまで次工程に進まない。**

---

## 備考

- 本要件定義書の実行タイミングはオーナーが決定する。Claude（executor）は本書の承認後に初めて破壊的操作を実行する。
- `C:\dev\YNFactory-git` （旧Drive側repo）は工程3完了後に「不要になるが削除はしない」の方針とする。削除・アーカイブは別タスクで検討。
- Macでの同等構成は工程4の手順書内に「Mac版」セクションとして追加することを推奨するが、今フェーズのスコープ外とする。
- `sengoku-game` サブモジュール（gitlink）は独立リポジトリのため本工程では一切操作しない。
