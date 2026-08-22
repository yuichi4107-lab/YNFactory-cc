---
name: start
description: >
  セッション開始時の同期と現況把握。GitHub最新をDriveへ安全に取り込み、
  HANDOFF.md → 当日TODO を読んで、期限・放置・停滞を巡回して報告する。
  PCを起動して最初に作業を始めるとき、「続きから」「今日は何から」「現状は？」と聞かれたとき、
  別PCの作業を引き継ぐとき、またはユーザーが `/start` と入力したときに使う。
  セッション終了時の `/handoff` と対になる。
---

# セッション開始スキル (/start)

`/handoff`（終了時）の対。**開始時 pull → 作業 → 終了時 push** のサイクルの入口。

## なぜ必要か

Driveは全PCで即時共有されるが、**GitHubの履歴は共有されない**。
別PCが `/handoff` でpushした内容は、こちらで pull するまでDriveに来ない。
また `pull-sync` は対象パスのDriveファイルを**上書きする**ため、
別PCがDrive上で編集して未pushのままだと、その作業がGitHubの古い内容で消える。
このスキルは上書き前に衝突を検出してから同期する。

## 実行手順

### Step 1: 日付を確認する

推測しない。ツールで確認する。

```bash
python -c "from datetime import datetime; d=datetime.now(); print(d.strftime('%Y-%m-%d %H:%M'), ['月','火','水','木','金','土','日'][d.weekday()])"
```

以降「今日」「明日」は、ここで得た絶対日付に変換して扱う。

### Step 2: GitHub最新をDriveへ取り込む

ローカルGit作業ディレクトリ（Windows `C:\YNFactory-cc` / Mac `~/YNFactory-cc`）で実行する。
**Drive側で git コマンドを実行しない。**

```bash
cd C:\YNFactory-cc
python 01_コード/scripts/company/session_start.py
```

終了コードで分岐する。

| exit | 意味 | 対応 |
|---|---|---|
| 0 | 最新、または安全にpull完了 | Step 3 へ進む |
| 2 | **衝突あり。pullしていない** | 下記の衝突対応へ |
| 1 | エラー | メッセージを読み、ref破損なら下記へ |

**衝突（exit 2）の対応**: 一覧に出たパスは、別PCがDrive上で編集して未pushの可能性が高い。

1. 一覧をユーザーに提示する
2. Drive側の内容を残すなら、先にそのパスを `commit-push` してから再実行する
   ```bash
   python 01_コード/scripts/company/sync_drive_git.py commit-push -m "sync: 未push分を取り込む" <該当パス...>
   ```
3. Drive側を捨ててよいと**ユーザーが明示した場合のみ** `--force` を付けて再実行する

**ローカルGit作業ディレクトリが無い場合**: Step 2 をスキップし、
「Drive側の内容のみで作業します。GitHubの最新は未取得です」と明記してStep 3へ進む。

**gitエラーが出た場合**: `python 01_コード/scripts/company/git_drive_guard.py check` を実行する。
`cannot lock ref` や `reference broken` が出たら、`.git/logs/HEAD`（reflog）末尾のSHAを確認し、
破損refを `_archive/git-drive-quarantine/` へ退避してから `git update-ref` で復旧する
（過去に2回発生。詳細は `.company/secretary/tech-notes.md`）。

### Step 3: 現況を読む

1. `.company/secretary/HANDOFF.md` — frontmatterの `next_action` と本文の「進行中」「ブロック中」
2. `.company/secretary/todos/YYYY-MM-DD.md`（Step 1の日付）
   - 無ければ**前日のTODOから未完了を引き継いで新規作成**する

### Step 3.5: 完成した要件定義を拾う

AI共同開発プランナーが作り終えた要件定義のうち、**まだ実装に着手していないもの**を検出する。

```bash
python 01_コード/scripts/company/planner_inbox.py --status ready_for_nagame --json
```

`items` が空なら何もしない。1件以上あれば、当日TODOへ次のとおり追記する。

| 検出内容 | 追記先の節 | 書式 |
|---|---|---|
| `items` の各要素 | `## 最優先` | `- [ ] **<project_name>**: 要件定義が完成済み・実装未着手。`/nagame-dev <project_name> 参照:<plan_dir>` で着手する \| 優先度: 高` |
| `decisions_pending` が空でない要素 | `## オーナー操作` | `- [ ] **<project_name>: 要判断 <件数>件** — <decisions_pending[0]>。`01_計画/REQUIREMENTS.md` の14章を確認する \| 優先度: 高` |

**重複防止**: 当日TODOの本文に `<project_name>` を含む行が既にあれば追記しない。

**要判断を `## 最優先` に入れない理由**: どちらのトレードオフを取るかは価値判断であり、
AIが代わりに決める性質のものではない。オーナーが決めるまで実装は進められない。

### Step 4: 定期巡回

読んだ内容から、対処が必要なものだけ拾う。該当が無ければ触れない。

- **期限アラート**: 期限が7日以内、または超過しているもの
- **放置検知**: 5日以上状態が変わっていないもの → ブロッカーの有無を確認して代替案を出す
- **定期リマインド**: 月初の経理チェック、週次の営業レビュー、投稿待ちコンテンツ
- **外部連携の停滞**: トークン待ち等 → 「待ち」で放置せず代替案を提案する

### Step 5: 報告

長くしない。次の形で簡潔に。

```
同期: <取り込んだコミット数 / 最新でした>
現況: <HANDOFFのnext_action を1行>
今日: <最優先TODO を1〜3件>
要件定義待ち: <ready_for_nagame の件数と、うち要判断がある件数。0件なら省略>
注意: <期限・ブロッカーがあれば。無ければ省略>
```

そのうえで「どれから進めますか？」と聞く。ユーザーが指示済みならそのまま着手する。

## 注意事項

- `session_start.py` は取り込むコミットが無ければ**何もしない**。毎回実行して構わない
- 衝突検出は「pullで書き換わるパスだけ」を照合する。全ファイル照合はしないので速い
- `multi-pc-rules.md` §6 のとおり、**HANDOFF.mdと当日TODOはその日の主担当PCだけが書く**。
  複数PCで同時に書くと、このスキルが検出する衝突が日常的に発生する
- 毎日03:00（Asia/Tokyo）の `daily_git_sync.py` が commit→push→pull を自動実行している。
  PCが起動していれば直前に同期済みのことがある

## 関連

| 目的 | 参照先 |
|---|---|
| 同期の全体ルール | `02_設定/docs/multi-pc-rules.md` |
| 引き継ぎとTODOの運用 | `02_設定/docs/company-ops.md` |
| セッション終了時 | `handoff` スキル (`/handoff`) |
| 承認が必要な操作 | `02_設定/docs/approval-rules.md` |
| 要件定義から実装への引き継ぎ | `ai-planner` スキル → `nagame-dev` スキル |
