---
title: Google Drive × Git 共存セットアップ手順書（GitHub軸・確定構成）
last_updated: "2026-05-30"
status: 確定（GitHub軸）
applies_to: 全端末（自宅PC / 職場PC / Mac Mini / Surface）
priority: 高（ハンドオフ失敗の根本対策）
---

# 2026-06-15 現行方針への注意

この文書は 2026-05-30 時点の復旧・移行経緯を含む参考資料。現在の実運用は、Drive側を日常作業場、ローカルGit側をGitHub反映用、ZSlimを復元用バックアップとする方針に更新済み。最新ルールは `docs/multi-pc-rules.md` と `docs/setup-multi-pc.md` を優先する。

特に、Drive側 `.git` ポインタを作り直す旧手順は、現在の標準手順として新規適用しない。

# Google Drive × Git 共存セットアップ手順書（GitHub軸・確定構成）

> 本手順書は **確定構成（GitHub軸）** を記載する。旧版で比較していた「方法A/B/C」は
> 2026-05-30 の方針確定により役目を終えた（経緯は末尾に1段落で要約。比較の詳細は設計書を参照）。

## 確定構成（3レイヤーの役割分担）

このプロジェクト（`G:\マイドライブ\YNFactory-cc`）は Google Drive for desktop 上にあり、
複数PCを行き来して作業する。`.git` を Drive 同期下に置くと index 破損・HEAD 消失・
ハンドオフ commit ハングが繰り返し起きるため、以下の **3レイヤーで責務を分離** した。

```
┌─ 作業ツリー: G:\マイドライブ\YNFactory-cc\   ← Drive同期（スキルのパス不変・全PCへ配布）
│   ├─ コード/ドキュメント (.md/.py/.html/.pdf 等 ≈248MB)   → Git + GitHub で履歴同期
│   └─ 大容量成果物 (画像/EPUB/keibaデータ/動画 ≈7GB)        → Git管理外、Driveのみが配布
│
└─ .git: C:\dev\YNFactory-git\.git  ← 各PCローカル（Drive に絶対乗せない）
                                       ↕ push / pull
                              GitHub private リポジトリ（同期の軸）
                              https://github.com/yuichi4107-lab/YNFactory-cc  (branch: main)
```

| レイヤー | 置き場 | 役割 | 同期方法 |
|---|---|---|---|
| **作業ツリー**（オーナーが触る場所） | `G:\マイドライブ\YNFactory-cc\`（現状維持） | 全ファイルの実体 | Drive（全PCに自動配布） |
| **大容量成果物**（画像/EPUB/keiba/動画） | 作業ツリー内（同上） | 生成物 | Git管理外。Drive のみが配布 |
| **`.git`（履歴）** | `C:\dev\YNFactory-git\.git`（各PCローカル） | コード+ドキュメントの履歴 | GitHub private 経由で pull/push |

**作業ディレクトリは `G:\マイドライブ\YNFactory-cc\` のまま変わらない。変わるのは .git の置き場とGitHub同期だけ。**
既存スキルの絶対パス前提（`g:\マイドライブ\…`）はそのまま動く。

### なぜ競合が再発しないか

Drive は「大容量ファイルの配布」、GitHub は「履歴の同期」と **責務が完全に分離** される。
Drive が `.git` の中身（index/HEAD/objects）に触れることが二度と無くなるため、
HEAD 消失・index 破損・ハンドオフハングが原理的に発生しなくなる。
履歴がローカルに分離していても、複数台間の整合は GitHub 経由の pull/push が担保する。

---

## 既存PC（YN_FACTORY / 自宅Windows）の現状

セットアップ完了済み（2026-05-30）。

| 項目 | 値 |
|---|---|
| 作業ツリー | `G:\マイドライブ\YNFactory-cc\`（Drive同期） |
| `.git` 本体 | `C:\dev\YNFactory-git\.git`（ローカル） |
| Drive 側 `.git` | gitdir ポインタファイル（`gitdir: C:/dev/YNFactory-git/.git`） |
| remote | `origin  https://github.com/yuichi4107-lab/YNFactory-cc.git` |
| ブランチ | `main`（既定・作業ブランチ） |
| セットアップ完了日 | 2026-05-30 |

---

## 2台目以降のセットアップ手順

新しい端末を追加するときの手順（bash 表記）。**gitdir ポインタは端末固有のパスを含む** ため、
各端末で個別に実施する。Drive 側の `.git` ポインタが他PCのパスを指したままだと壊れるので、
必ずローカルに clone してから自端末用ポインタを書き直す。

```bash
# 前提: その端末でも作業ツリーは G:\マイドライブ\YNFactory-cc（Drive同期済）
# 1. GitHub から .git をローカルに clone（作業ツリーとは別の場所へ）
mkdir -p /c/dev
git clone https://github.com/yuichi4107-lab/YNFactory-cc.git /c/dev/YNFactory-cc-clone
# 2. clone の .git だけをローカル保管場所へ
mkdir -p /c/dev/YNFactory-git
mv /c/dev/YNFactory-cc-clone/.git /c/dev/YNFactory-git/.git
# 3. Drive 作業ツリーの .git を、この端末固有の gitdir ポインタに
echo "gitdir: C:/dev/YNFactory-git/.git" > "/g/マイドライブ/YNFactory-cc/.git"
# 4. clone 残骸を削除し、作業ツリーで認識確認
rm -rf /c/dev/YNFactory-cc-clone
cd "/g/マイドライブ/YNFactory-cc"
git config core.longpaths true
git status   # 正常に動けばOK（大容量はDrive側に既にある）
```

> 注: 大容量ファイル（画像/EPUB/keibaデータ等）は GitHub には含まれない。
> それらは Drive 同期で各PCに配布される。clone 直後でも、Drive 同期が済んでいれば
> 作業ツリーには実ファイルが揃っている。

### Mac の場合

パスを Mac 用に読み替える（作業ツリーが Drive のどこにマウントされるかは環境依存）。

```bash
mkdir -p ~/dev
git clone https://github.com/yuichi4107-lab/YNFactory-cc.git ~/dev/YNFactory-cc-clone
mkdir -p ~/dev/YNFactory-git
mv ~/dev/YNFactory-cc-clone/.git ~/dev/YNFactory-git/.git
echo "gitdir: $HOME/dev/YNFactory-git/.git" > "<Drive上の作業ツリー>/.git"
rm -rf ~/dev/YNFactory-cc-clone
```

---

## 日常運用ルール

- **作業開始時**: `git pull origin main`（最新履歴を取得してから作業を始める）
- **作業終了時**: `/handoff`（HANDOFF/TODO 更新 → `git commit` → `git push origin main` を一括実行）
- **大容量ファイル**: Git に追加しない。Drive が自動配布する。新種の大容量拡張子が出たら `.gitignore` に追記する

---

## やってはいけないこと

1. **`.git` 本体を Drive に置く** — Drive 同期と git の競合で index/HEAD が破損する。
   `.git` 本体は必ずローカル（`C:\dev\YNFactory-git\.git`）、Drive 側はポインタファイルのみ。
2. **大容量バイナリを `git add` する** — リポジトリが肥大化し、GitHub の 100MB/ファイル制限を超過して
   push できなくなる。画像/EPUB/動画/keibaデータは `.gitignore` で除外し Drive 配布に任せる。
3. **`.env`・トークン・パスワード・APIキーをコードに直書きする** — 必ず環境変数か `.env`（gitignore済）から
   読む。プレースホルダ以外の実在の機密値はリポジトリに絶対に入れない。

---

## 端末別セットアップ状況

| 端末 | 採用構成 | セットアップ日 | 備考 |
|------|---------|----------------|------|
| YN_FACTORY（自宅Windows） | GitHub軸 | 2026-05-30 | 完了。`.git`=`C:\dev\YNFactory-git\.git`、remote=origin、branch=main |
| 職場PC | 未設定 | - | 次回利用時に「2台目以降のセットアップ手順」を実施 |
| Mac Mini | 未設定 | - | 同上（Mac 用にパス読み替え） |
| Surface | 未設定 | - | 同上 |

適用後、この表を各自更新すること。

---

## 経緯（参考）

旧版（2026-04-15）は Drive 同期と git の競合を避ける手段として「方法A（Drive維持・ストリーミングで `.git` 除外）/
方法B（`.git` をローカル `C:\dev` へ分離）/ 方法C（リポジトリ全体を Drive 外へ＋成果物だけ symlink）」を比較・未決のまま並べていた。
しかし複数台運用では **方法B 単独が原理的に破綻** し（`.git` が各PCローカルに分離するため、2台目に履歴が無い／
ポインタが別PCのパスを指して壊れる）、2026-05-30 に実際に HEAD 消失で全 git コマンドが落ちる障害が発生した。
これを機に、**Drive=大容量配布／GitHub=履歴同期** と責務を完全分離する **GitHub軸** へ確定した（方法A/B/C 比較の詳細は設計書に温存）。

---

## 関連リンク

- 設計書: [2026-05-30-workdir-git-architecture-design.md](../../../docs/superpowers/specs/2026-05-30-workdir-git-architecture-design.md)
- 実装計画: [2026-05-30-workdir-git-architecture.md](../../../docs/superpowers/plans/2026-05-30-workdir-git-architecture.md)
- git 復旧手順書（HEAD消失障害）: [2026-05-30-git-head-recovery.md](../debug-log/2026-05-30-git-head-recovery.md)
- シークレットローテーション手順書（GitHub漏洩対応）: [2026-05-31-secret-rotation-after-github-leak.md](../debug-log/2026-05-31-secret-rotation-after-github-leak.md)
