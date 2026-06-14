---
title: マルチPC同時運用ルール
status: 確定
last_updated: "2026-06-06"
applies_to: "YNFactory-cc を複数端末（Windows×2 / Mac）で同時運用する全作業者・全自動化"
---

# マルチPC同時運用ルール（YNFactory-cc）

複数のPC（自宅Windows・24h稼働Windows・Mac）で **同じリポジトリを同時に**使うための運用規律。
ファイル競合・git コンフリクト・Google Drive 競合コピーを防ぎ、「どの端末で作業しても履歴が1本にまとまる」状態を保つ。

> このルールは飾りではない。**2026-06-06 に実際の事故が起きたために作られた**（末尾「なぜこのルールがあるか」参照）。

---

## 0. 前提アーキテクチャ（これを破ると全部壊れる）

```
            ┌─────────────────────────────────────────┐
            │  GitHub private（唯一の真実のソース）     │
            │  yuichi4107-lab/YNFactory-cc  branch main │
            └───────────────┬─────────────────────────┘
                 pull/push   │   pull/push
        ┌───────────────────┼───────────────────┐
        │                   │                   │
  ┌───────────┐       ┌───────────┐       ┌───────────┐
  │ Win PC-A  │       │ Win PC-B  │       │   Mac     │
  │ C:\       │       │ C:\       │       │ /Users/   │
  │ YNFactory-│       │ YNFactory-│       │ yuichi/   │
  │ cc (clone)│       │ cc (clone)│       │ YNFactory-│
  │           │       │           │       │ cc (clone)│
  │ .git=local│       │ .git=local│       │ .git=local│
  └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
        │ junction          │ junction          │ symlink
        └───────────────────┴───────────────────┘
                            │
            ┌───────────────▼─────────────────────────┐
            │  Google Drive: YNFactory-cc-data         │
            │  （大容量バイナリ＝画像/動画/EPUB/データ）│
            │  各端末へ Drive が配布・git管理外          │
            └──────────────────────────────────────────┘
```

- **コード・テキスト成果物の正典 = git（GitHub main）**。バージョン管理されるのはこれだけ。
- **各PCは GitHub から自分のローカルディスクへ独立クローン**（`.git` はクローン内＝各PCローカル。Drive上には絶対に置かない）。
- **大容量バイナリ = `YNFactory-cc-data`（Drive）**。git管理外。各クローンへ **ジャンクション（Win）／シンボリックリンク（Mac）** で合成。
- 作業・自動化は **クローンの中**で行う。Drive の作業ツリーを直接 git で触らない。

---

## 5-1. 書き込み担当の固定（分業原則）

同一ファイルを2台が同時に書き換えると、必ず git コンフリクトか Drive 競合コピーになる。これを構造的に避ける。

### 大原則
**「同じファイルを、同じ時間帯に、2台から書かない」**。これだけ守れば事故の8割は消える。

### 主担当の固定
| ファイル種別 | 主担当 | 補足 |
|---|---|---|
| `.company/secretary/HANDOFF.md` | **その日に最後に作業した1台** | 1日のうちで書くのは原則1台。複数台で触ったら必ず pull→マージ（§5-2） |
| `.company/secretary/todos/YYYY-MM-DD.md` | **当日作業した1台** | 同上。`/handoff` を2台で別々に走らせない |
| `.company/secretary/inbox/` `.company/inputs/`（lifelog・voice-journal） | **生成元の1台のみ** | 自動化（voice-journal等）が走る端末でのみ更新。他端末は読むだけ |
| keiba / ai-trade 等の本番自動化 | **VPS or 指定の1台** | cron は1箇所のみ。複数台に同名 cron / Task を置かない |
| 各プロジェクトのコード | 触る人が pull 先行で随時（§5-2） | 別ファイルなら並行編集OK。同一ファイルは避ける |

### 自動化（cron / Task Scheduler）の重複起動禁止
- **同じ自動化タスクを2台に同時登録しない**。例: `YNFactory-MorningBriefing` を Win PC-A と PC-B の両方に登録すると、同一 Telegram アカウントへ二重通知が飛び、todos も二重編集される。
- 自動化を動かす「当番PC」を1台に決める。当番を移すときは旧PCのタスクを `Unregister-ScheduledTask` してから新PCで登録する。

---

## 5-2. pull / push 規律（最重要）

### 作業開始前（必須）
```bash
cd C:\YNFactory-cc      # 自分のクローン（各PCのローカルパス）
git pull --rebase origin main
```
- **必ず最新を取り込んでから書き始める**。これを飛ばすのが事故の最大原因。
- `--rebase` を使う（履歴を1本に保つ。`--no-rebase` のマージコミット乱発を避ける）。

### 作業終了時（当日中に push）
```bash
git add <変更ファイル>
git commit -m "..."
git push origin main
```
- **当日分の作業は当日中に push する**。翌日以降に溜めると、その間に他端末が進んで必ず分岐する。
- push が `rejected (non-fast-forward)` になったら、他端末が先に進んでいる合図 → 下記コンフリクト手順へ。

### コンフリクト発生時の手順
```bash
git pull --rebase origin main     # リモートを取り込み、自分の変更を上に積み直す
# コンフリクトが出たら：該当ファイルを開き、両方の内容を「残す」方向で手で統合
#   → 片方で上書きしない。相手の作業を消さない（§末尾の事故がこれ）
git add <解決したファイル>
git rebase --continue
git push origin main
```
- **コンフリクト解決＝マージであって上書きではない**。HANDOFF / todos で衝突したら、両端末の記述を **両方残す**。
- 手に負えない衝突は、解決前に `git rebase --abort` で安全に元へ戻せる。慌てて force しない。

### 絶対にやらないこと
- ❌ `git push --force` / `git push --force-with-lease` — 他PCの未取得コミットを消し飛ばす。**禁止**（§5-5）。
- ❌ pull せずにいきなり commit→push を繰り返す。
- ❌ コンフリクトを「自分の版で上書き」で握りつぶす。

---

## 5-3. Google Drive 競合コピーの回避

大容量成果物（`YNFactory-cc-data` 配下＝画像・EPUB・データ）は git ではなく Drive で配布される。Drive は「2台が同じファイルを同時に書く」と **競合コピー**（`ファイル名 (1).md` 等）を勝手に作る。

### ルール
- `YNFactory-cc-data` 配下の成果物を**書き込む（生成・上書きする）のは1台ずつ**。生成バッチを2台で同時に走らせない。
- 大容量を書き込む端末は **Drive同期がオンライン＆「最新の状態」になってから**着手する（同期中・一時停止中に書くと取りこぼし／競合の元）。
- **他端末で大量ファイル移動・大量生成をする間は、自分のDrive同期を一時停止する**（例: `YNFactory-cc-data` への切り出しや一括再生成。10GB級の移動は必ず他端末同期停止下で行う）。

### 競合コピーを見つけたら
1. 競合コピー（`… (1).md` 等）と本体ファイルの **両方の中身を比較**する（`Compare-Object` 等）。
2. **新しい／情報量の多い方を正**とし、片方にしか無い記述は本体へ統合する（消さない）。
3. 統合し終えてから競合コピーを削除する。
4. その内容が git 管理対象（`.company/secretary/` 等）なら、統合後に commit→push して git にも反映する。

---

## 5-4. 日次同期ルーティン（これをルーチン化する）

```
[作業開始] cd <自分のクローン> && git pull --rebase origin main   ← 最新を取り込む
   ↓
[作業]     別ファイル同士なら並行OK。同一ファイルは時間をずらす
   ↓
[作業終了] git add → git commit → git push origin main           ← 当日中にpush
   ↓
[当番PCのみ] /handoff（HANDOFF.md・todos 更新 → commit → push）
```

- セッション終了時は `/handoff` スキルで HANDOFF・TODO・commit・push を一括。**ただし当番1台のみ**。
- 別端末で続きをやるときは、その端末で必ず `git pull --rebase` してから。

---

## 5-5. 禁止事項一覧（やったら事故る）

| # | 禁止 | 理由・代替 |
|---|---|---|
| 1 | `git push --force` / `--force-with-lease` | 他PCのコミットを消す。代替＝`pull --rebase` してから通常 push |
| 2 | `.git` を Drive 上に置く（クローンを `G:\マイドライブ\…` に作る） | Drive同期で `.git` が破損・HEAD消失。クローンは必ずローカルディスク（Windows: `C:\YNFactory-cc` / Mac: `/Users/yuichi/YNFactory-cc`） |
| 3 | 大容量バイナリを `git add` する | リポジトリが再肥大化。画像/動画/EPUB/データは `YNFactory-cc-data`（Drive）へ |
| 4 | pull せずに commit→push を続ける | 分岐の温床。開始前 `git pull --rebase` を必須に |
| 5 | 同一ファイルを2台から同時編集（特に HANDOFF / 日次 todos） | 競合コピー・上書き消失。§5-1 の主担当固定を守る |
| 6 | 同じ自動化タスク（cron / Task Scheduler）を2台に登録 | 二重通知・二重編集。当番1台のみ |
| 7 | 他端末が同期中のまま `YNFactory-cc-data` で10GB級の移動/一括生成 | Drive競合コピー大量発生。他端末同期を停止してから |
| 8 | コンフリクトを自分の版で上書きして握りつぶす | 相手の作業消失。両方を残す方向でマージ |

---

## 5-6. 各レイヤーの役割（迷ったらここに戻る）

| レイヤー | 実体 | 役割 | バージョン管理 |
|---|---|---|---|
| **git（GitHub main）** | `yuichi4107-lab/YNFactory-cc` | コード・テキスト成果物の**唯一の正典** | あり（履歴・分岐・マージ） |
| **クローン** | 各PC `C:\YNFactory-cc`（`.git`内蔵・ローカル） | 作業・自動化を行う場所 | git経由 |
| **YNFactory-cc-data** | Drive `G:\マイドライブ\YNFactory-cc-data` | 大容量バイナリの**配布基盤** | **なし**（git役割外。Driveが各PCへ配る） |
| **ジャンクション/シンボリックリンク** | クローン内の各大物ディレクトリ | クローンに data を「合成」して見せる | — |

- **「これは履歴を残したい？」→ git（クローン内で編集・commit）**。
- **「これは大容量の成果物？」→ YNFactory-cc-data（Drive）**。
- 両者を混ぜない。混ぜるとリポジトリ肥大 or Drive競合のどちらかで詰む。

---

## なぜこのルールがあるか（2026-06-06 の実例）

このルールは抽象論ではない。**実際に起きた分岐事故**から作られた:

- 同じ「JRA競馬の本番化作業」が、**別々の端末・別々の .git から二重にコミット**され、origin と手元で履歴が分岐した（ahead 3 / behind 4）。
- `HANDOFF.md` と日次 todos が **片方の端末で上書き**され、もう片方（Mac の telegram-bot 復旧・notebooklm-sync 完了）の記述が消えかけた。
- Google Drive が **競合コピー `2026-06-06 (1).md`** を自動生成していた。

→ 復旧には「churn退避 → 両端末の作業を手でマージ → クローンを origin に一本化」という余計な工程が必要になった（git正典化 Phase A）。
**§5-2（pull先行・上書き禁止）と §5-1（主担当固定）を守っていれば、この事故は丸ごと起きなかった。**

---

## 関連ドキュメント
- 新規PCのセットアップ手順: [setup-multi-pc.md](setup-multi-pc.md)（工程4で作成予定）
- 移行の要件定義: [.company/requirements/multi-pc-git-migration-2026-06-06.md](../.company/requirements/multi-pc-git-migration-2026-06-06.md)
- 旧構成からの移行経緯: [.company/engineering/docs/gdrive-git-setup.md](../.company/engineering/docs/gdrive-git-setup.md)
