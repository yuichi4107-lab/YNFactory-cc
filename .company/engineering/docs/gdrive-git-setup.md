---
title: Google Drive × Git 共存セットアップ手順書
last_updated: "2026-04-15"
applies_to: 全端末（自宅PC / 職場PC / Mac Mini / Surface）
priority: 高（ハンドオフ失敗の根本対策）
---

# Google Drive × Git 共存セットアップ手順書

## なぜ必要か

このプロジェクト（`g:\マイドライブ\YNFactory-cc`）は Google Drive for desktop 上にあり、
複数端末で同期しながら作業している。しかし `.git/` フォルダまで Drive が同期すると以下の問題が発生する:

- `.git/index.lock` が Drive によってコピー中に残留 → 次回 `git add/commit` が失敗
- Drive が `.git/objects/` を部分アップロード中に git が読み書き → index 破損
- 複数端末で同時に commit した場合、`.git/refs/` で競合 → 履歴不整合
- ファイルロック競合で `Permission denied` エラー

**ハンドオフ時の git commit 失敗の大半はこれが原因。**

## 解決策（3択）

### 【推奨】方法A: Google Drive の選択的同期で `.git/` を除外

**メリット**: 設定1回で済む／ワークフロー変更なし
**デメリット**: Drive for desktop のバージョンによっては個別フォルダ除外UIが制限される

#### Windows手順

1. タスクバー右下のGoogle Drive アイコンをクリック
2. 右上の歯車 → **「設定」**
3. 左メニュー **「Google Drive」** → **「マイドライブのフォルダを同期」**
4. **「ファイルをストリーミング」** モードを使っている場合は、そもそも `.git/` はローカルにダウンロードされないので安全（ただし `git` コマンド実行時はダウンロードされる）
5. **「ファイルをミラーリング」** モードを使っている場合、個別フォルダの除外UIが出ないことがある → 方法B/Cへ

**確認コマンド**（PowerShell）:
```powershell
# .git/ フォルダの Drive 状態を確認
Get-Item "g:\マイドライブ\YNFactory-cc\.git" | Select-Object Attributes, Mode
```

`Offline` 属性が付いていれば同期対象、付いていなければストリーミング／除外済み。

#### Mac手順

1. メニューバーのGoogle Drive アイコン → 歯車 → **「設定」**
2. **「Google Drive」** → **「マイドライブのフォルダを同期」**
3. Windows同様、ストリーミングモード推奨

---

### 【確実】方法B: `.git/` を Drive 外に分離（推奨の第2候補）

`.git/` 本体を Drive 外（例: `C:\dev\YNFactory-git\`）に置き、作業ディレクトリだけ Drive 上に残す。

#### セットアップ手順（Windows）

```bash
# 1. Drive 同期を一時停止（タスクバー → 歯車 → 同期を一時停止）

# 2. .git/ フォルダをローカルディスクに移動
mkdir -p /c/dev/YNFactory-git
mv "/g/マイドライブ/YNFactory-cc/.git" /c/dev/YNFactory-git/

# 3. Drive 側に .git ファイル（ファイル1個）を作成し、gitdir を指す
echo "gitdir: C:/dev/YNFactory-git/.git" > "/g/マイドライブ/YNFactory-cc/.git"

# 4. 動作確認
cd "/g/マイドライブ/YNFactory-cc"
git status  # 正常に動けばOK

# 5. Drive 同期を再開
```

#### Mac手順

```bash
mkdir -p ~/dev/YNFactory-git
mv "/Volumes/GoogleDrive/マイドライブ/YNFactory-cc/.git" ~/dev/YNFactory-git/
echo "gitdir: $HOME/dev/YNFactory-git/.git" > "/Volumes/GoogleDrive/マイドライブ/YNFactory-cc/.git"
```

#### 注意
- **各端末ごとに個別セットアップが必要**（`.git` ファイルはgitdirパスを含むため端末依存）
- `.git` ファイルが Drive 同期で上書きされないよう、セットアップ後に `.gitignore` に追加：
  ```
  # gitdir ポインタは端末固有なので同期しない
  /.git
  ```
  ※ただしこれは効かない（`.git` はそもそもgitが特別扱い）ので、運用で気をつける

---

### 【最終手段】方法C: リポジトリ全体を Drive 外にクローンし、成果物だけシンボリックリンク

Drive 同期のメリット（複数端末での共有）を残しつつ、git は完全にローカルで運用する。

#### 概念

```
C:\dev\YNFactory-cc\          ← git 管理の本体（ローカル）
└── .company/outputs/         ← ここだけ symlink で Drive 上を指す
                               ↓
g:\マイドライブ\YNFactory-outputs\   ← Drive 同期（成果物のみ）
```

#### メリット・デメリット
- **メリット**: git 操作は完全ローカル、Drive競合ゼロ
- **デメリット**: リポジトリ構造の大改修が必要、既存スキル・パスの修正多数

**現実的には方法A or B を先に試す。方法Cは最終手段。**

---

## 端末別セットアップ状況

| 端末 | 採用方法 | セットアップ日 | 備考 |
|------|---------|----------------|------|
| 自宅PC (Windows) | 方法A（ストリーミング） | 2026-04-15 | 既にストリーミングモードで運用中。追加設定不要 |
| 職場PC | 未確認 | - | 次回作業時にモード確認 |
| Mac Mini | 未確認 | - | 3デバイス運用移管工程0と併せて確認 |
| Surface | 未確認 | - | Genspark専用だが念のため確認 |

適用後、この表を各自更新すること。

---

## 動作確認チェックリスト

セットアップ後、以下が成功すれば完了:

- [ ] `git status` がエラーなく動く
- [ ] `git add -A && git commit -m "test"` が3回連続で成功
- [ ] Drive 同期中に git 操作してもエラーが出ない
- [ ] `.git/index.lock` が残留しない（もし残ったら一度削除して再実行）
- [ ] 別端末で最新 commit が `git pull` 後に反映される

---

## トラブルシューティング

### `.git/index.lock` が頻繁に残る

→ 方法A/Bが効いていない。Drive for desktop のモードを「ストリーミング」に変更するか、方法Bで `.git/` 自体を Drive 外に出す。

### 別端末で pull したら conflict だらけ

→ 両端末で同時 commit した可能性。片方を `git reset --hard origin/main` で巻き戻すか、手動マージ。
→ 予防策: 作業開始時に必ず `git pull`、終了時に必ず `/handoff`（push まで実行）。

### `fatal: bad index file sha1 signature`

→ Drive 同期中に index が破損した。以下で復旧:
```bash
rm .git/index
git reset
```

---

## 参考

- git 公式: [worktree / gitdir の仕様](https://git-scm.com/docs/gitrepository-layout)
- Google Drive for desktop: [選択的同期の設定](https://support.google.com/drive/answer/10838124)
