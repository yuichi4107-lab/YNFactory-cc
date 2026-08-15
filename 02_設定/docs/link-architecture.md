---
title: リンク方式のフォルダ構成
date: "2026-08-16"
status: active
applies_to: "YNFactory-cc の置き場所・リンク・Git管理範囲の判断すべて"
---

# リンク方式のフォルダ構成

## 0. 結論

`YNFactory-cc` は **`C:\YNFactory-cc`（Mac は `~/YNFactory-cc`）が本体**。
重い領域と Git 管理外の領域だけを、ジャンクション（Mac はシンボリックリンク）で
Google Drive 側へ逃がしている。

```
C:\YNFactory-cc\                    ← Gitリポジトリ本体・ここで作業する
├── CLAUDE.md / AGENTS.md            実体
├── .agents\ .codex\ .claude\        実体
├── .company\                        実体
├── 01_コード\                       実体
├── 02_設定\                         実体
├── 99_その他\                       実体
├── 03_成果物\                       実体
│   ├── ebooks\ ebook-produce\       実体（原稿はGit管理）
│   └── outputs\      ──リンク──▶   Drive（55.6GB）
├── 04_インプット\    ──リンク──▶   Drive（502MB）
└── 05_プロジェクト\                 実体
    ├── keiba-unified\               実体（Git管理）
    ├── shorts-factory\              実体（Git管理）
    └── その他31プロジェクト ──リンク──▶ Drive（1.2GB）
```

Drive 側へ逃がした合計は約 **56.8 GB**。

## 1. なぜこの形か

以前は Drive 側と C: 側に同名フォルダが2つあり、`sync_drive_git.py` で
パスを明示してコピーし合う二重管理だった。「どっちが最新か」を人間が覚える必要があり、
2026-08-09 には Windows と Mac が同じ `HANDOFF.md` を同時に触る事故も起きた。

リンク方式にすると次が同時に解決する。

1. 二重管理が消える。同じファイルの実体は世界に1つだけになる
2. `ROOT / "03_成果物" / "outputs"` のような相対パスがそのまま動く（コード改修ゼロ）
3. Drive 側に `__pycache__` `node_modules` `.venv` が新規に増えなくなる
4. Git が Drive を一切見ないので `.git` 破損リスクが構造的に消える

## 2. リンクにするかどうかの判断基準

**「Git 追跡ファイルを1件も含まない」かつ「重い、またはDrive側にしか存在しない」領域だけをリンクにする。**

Git 追跡ファイルが混ざっている場所でリンクを切ると `git rm -r --cached` が必要になり、
GitHub からファイルが消える。判断は目視ではなく測定する。

```powershell
python 01_コード\scripts\company\link_points.py 05_プロジェクト
```

このスクリプトが「容量」と「Git追跡件数」を並べ、条件を満たす場所だけを候補として出す。

## 3. リンクの張り方

`mklink` は cmd の内部コマンド。PowerShell から呼ぶときは必ず `cmd /c` を付ける。

```powershell
cmd /c mklink /J "C:\YNFactory-cc\03_成果物\outputs" "G:\マイドライブ\YNFactory-cc\03_成果物\outputs"
```

C: 側に同名フォルダが既にある場合、**中身を確認せずに消さない**。
ファイルが1件でもあれば中断する形にする。

```powershell
$p = "C:\YNFactory-cc\<パス>"
$n = @(Get-ChildItem $p -Recurse -Force -File -EA SilentlyContinue).Count
if ($n -eq 0) {
  Get-ChildItem $p -Recurse -Force -Directory | Sort-Object FullName -Descending | ForEach-Object { [IO.Directory]::Delete($_.FullName,$false) }
  [IO.Directory]::Delete($p,$false)
  cmd /c mklink /J $p "G:\マイドライブ\YNFactory-cc\<パス>"
}
```

`[IO.Directory]::Delete($path, $false)` は空でないと失敗するので、ファイルは絶対に消えない。

## 4. リンクを外すとき

```powershell
rmdir "C:\YNFactory-cc\03_成果物\outputs"
```

**`/s /q` を付けてはいけない。** 付けるとリンク先（Drive 上の成果物）まで消える。
PowerShell なら `[IO.Directory]::Delete($path, $false)` が安全。

## 5. 実測でわかったジャンクションの性質（2026-08-15 検証）

`01_コード/scripts/company/junction_probe.py` による実測結果。

| 項目 | 結果 |
|---|---|
| `mklink /J` は管理者権限なしで通るか | 通る |
| リンク経由の読み書きが Drive の実体に届くか | 届く |
| `shutil.rmtree` がリンクを貫通するか | **貫通しない**（Python 3.12.10） |
| `os.rmdir` でリンクだけ外せるか | 外せる |
| `git` がリンク先を追跡できるか | できる（`git add -f` も有効） |
| `.gitignore` でリンクを除外できるか | できる |

**最重要の落とし穴**: Python から見るとジャンクションは「普通のフォルダ」に見える。

```
Path.is_symlink()  = False
os.path.islink()   = False
リパースポイント属性 = True   ← これだけが True
```

したがって `is_symlink()` で判定するコードはすべてすり抜ける。
`sync_drive_git.py` の `is_link()` はファイル属性のリパースポイントビット
（`FILE_ATTRIBUTE_REPARSE_POINT = 0x400`）を見て判定している。
**リンクを扱うコードを書くときは必ずこの方式を使うこと。**

## 6. Git 管理の範囲

`04_インプット` は、中身が2種類に分かれていた。

- **コード44件**（`sync_notion.py` `setup_auto_import_windows.bat` など取込自動化）→ `git add -f` で追跡継続
- **データ376件**（`conversations/` `organized/lifelogs/` など）→ Git から除外、Drive にのみ存在

`.gitignore` で除外したうえで、残したいファイルだけ `git add -f` で戻す、という形になっている。
`04_インプット` 配下のスクリプトを増やしたときは、`git add -f` を明示的に実行しないと追跡されない。

## 7. Windows 特有の注意

### 実行権限が落ちる

Windows は実行ビットを持たないため、Mac 用の `.sh` を Windows 側でコミットすると
`100755 => 100644` に落ちて Mac で実行できなくなる。復元はこれ。

```powershell
git update-index --chmod=+x -- "04_インプット/inputs/setup_auto_import_mac.sh"
```

### .gitignore の表示が化ける

Windows PowerShell 5.1 の `Get-Content` は UTF-8 を cp932 として読むため、日本語が化ける。
**ファイルは壊れていない。** 追記するときは .NET で UTF-8（BOMなし）を明示する。

```powershell
[IO.File]::AppendAllText("C:\YNFactory-cc\.gitignore", "`r`n/パス/`r`n", [Text.UTF8Encoding]::new($false))
```

判定に使うときは文字列比較ではなく git 自身に聞く。

```powershell
git check-ignore -q "04_インプット/inputs/conversations"
```

## 8. 未処理の課題

### 8-1. Drive 上の入れ子リポジトリ

`05_プロジェクト/20260511_yn-tools/.git` が Drive 上に存在する（1,402ファイル）。
`docs/git-drive-safety.md` が禁じている状態。ルート直下の `.git` は無効化済みだが、
入れ子が見落とされていた。**未対応。**

### 8-2. Drive 上の開発ゴミ

| パス | ファイル数 | 容量 |
|---|---:|---:|
| `20260325_biz_idea_generator/.venv` | 6,949 | 221.0 MB |
| `20260625_multi-ai-sparring/.venv` | 4,466 | 32.7 MB |
| `20260627_blockcraft-lite/node_modules` | 1,522 | 38.9 MB |

約13,000ファイル / 290MB。再生成できるので削除してよいはずだが、**未対応。**

### 8-3. C: 直下の旧フォルダ

6バケット構成になる前の残骸が8件、Git管理外で残っている。

```
.company/outputs/  ai-trade-system/  gourmet-share/  jp-daytrade/
keiba-unified/     sales-ops/        sengoku-game/   yn-tools/
```

`git status` が毎回8行汚れる。中身を突き合わせてから処理する。**未対応。**

### 8-4. Mac 側

Windows のジャンクションと Mac のシンボリックリンクは別物。
Mac では `ln -s` になるが、Git がシンボリックリンクをリンクとして記録するため、
`.gitignore` での除外が Windows 以上に重要になる。**未検証。**

### 8-5. 退避フォルダ

`%USERPROFILE%\_pre_link_04_インプット` に移行前の実体が残してある。
動作確認が済むまで削除しないこと。
