---
name: shorts-factory-ops
description: shorts-factory の生成・Telegram承認・4媒体自動投稿・重複動画/二重投稿の障害対応を行う専用運用スキル。動画被り、Claude CLI未ログイン、Driveロック、Telegram操作パネル不応答、SNS投稿失敗、posting ledger復旧を扱う。
---

# shorts-factory 運用スキル

## 使う場面

このスキルは、`shorts-factory` の日次ショート動画生成と自動投稿で以下が起きた時に使う。

- 同じ動画・同じ台本・同じタイトルが連続して生成された
- 生成が失敗し、Claude CLI / フォールバック台本 / Driveロックが疑われる
- Telegram承認ボタンが反応しない、または承認前に投稿された
- X / Instagram / TikTok / YouTube の投稿失敗、部分失敗、二重投稿リスクがある
- runtime `~/shorts-factory/app` とDrive正本 `shorts-factory/` の反映差分を確認したい

## 最初に見るもの

1. `.company/secretary/HANDOFF.md`
2. `.company/secretary/todos/` の最新日付TODO
3. `~/Library/Logs/shorts-generate.log`
4. `~/Library/Logs/shorts-approval.log`
5. `.company/marketing/shorts-factory/queue/<queue_id>.json`
6. `.company/outputs/shorts-factory/<queue_id>/`
7. runtime側の `~/shorts-factory/work/<queue_id>/` と `~/shorts-factory/posting_ledger/<queue_id>.json`

Drive上のoutputsを広く走査するとGoogle Drive File Providerのロックで生成が止まりやすい。生成時の重複検知や復旧判断は、原則としてruntimeローカルの `~/shorts-factory/work/` と queue item を正にする。

## 2026-07-01 動画被り修正の登録内容

発生した問題:

- Claude CLI が未ログイン状態になり、台本生成が失敗した
- 生成失敗後のフォールバック台本が固定的な内容になり、過去動画と同じ `title` / subtitles / reading cue を再生成した
- その結果、2026-06-29 19:00 と 2026-06-30 09:00 で同一動画が並んだ

以後の必須ルール:

- フォールバック台本も通常台本と同じ重複検証に通す
- 直近タイトルと一致したら生成不合格にする
- 字幕・読み上げキューの正規化シグネチャが直近動画と一致したら生成不合格にする
- Claude CLIの確認は `claude auth status` だけでなく、非対話実行 `claude -p` まで通す
- `Not logged in - Please run /login` が出たら、動画を量産せずログイン復旧を先に行う
- 重複動画を見つけたら、後続の重複queueは `skipped` にし、Telegramボタンは無効化してから別テーマで再生成する

## 実装済みガード

- `shorts-factory/src/script_gen.py`
  - `recent_duplicate_errors()` が直近タイトルと字幕/読み上げキューの同一性を検査する
  - `_recent_output_scripts()` はDriveではなく `CONFIG.work_dir` のruntime履歴を見る
  - フォールバック台本も重複検査で落とす
  - Claude CLI失敗時はstdout JSONを含め、ログイン失効などの理由を通知に出す

- `shorts-factory/scripts/run_generate.sh`
  - nvm配下の最新NodeをPATHへ追加し、launchd実行でも `claude` が動きやすくする

- `shorts-factory/src/platforms/poster.py`
  - `~/shorts-factory/posting_ledger/` に媒体別投稿成功URLを保存する
  - retry時はledgerに投稿済みURLがあれば外部投稿せずqueueへ復元する

- `shorts-factory/src/approval_bot.py`
  - Telegram callback応答が失敗した場合は、承認/却下/保留の状態変更をしない
  - 古い `approved` item は自動再開しない
  - 一部媒体が投稿済みのitemは承認スキャンから再投稿しない

- `shorts-factory/scripts/post_approved_item.py`
  - 承認後30分超過、または一部媒体投稿済みの `approved` item をworker側でもブロックする

## 復旧手順

### 同じ動画ができた時

1. queue itemの `id`、`title`、`topic`、`difficulty`、`review`、`platforms` を確認する
2. `final.mp4` のハッシュ、`script.json` の `title`、`topic`、`cues` を直近動画と比較する
3. 同一なら後続itemを `skipped` にし、`review.reason` に `duplicate_guard` を残す
4. Telegramの該当メッセージはボタンなし状態へ編集する
5. Claude CLIログインを確認し、別topicまたは別切り口で再生成する

### Claude CLIの状態確認

```bash
claude auth status
printf '{"ok": true}' | claude -p 'Return this JSON unchanged.'
```

2つ目が非対話で成功しない場合、launchdの生成では失敗しやすい。ログイン復旧後に再生成する。

### 投稿の二重実行が疑われる時

1. queue itemの `platforms.*.status/url` を確認する
2. `~/shorts-factory/posting_ledger/<queue_id>.json` を確認する
3. ledgerに成功URLがある媒体は外部投稿せず、queueへURLを復元する
4. `approved` のまま古いitemが残っていても、30分超過または一部投稿済みならworkerでブロックする

## 禁止事項

- 投稿済みSNSの削除、公開状態変更、アカウント設定変更は、ユーザーの明示承認なしに実行しない
- 同一動画の疑いがあるitemを、確認なしに再承認・再投稿しない
- Driveロックが出ている時にDrive outputsを広範囲に走査しない
- Telegram callback失敗を「承認済み」と扱わない

## 品質基準

- 同一 `title` の直近再利用が生成段階で止まる
- 同一字幕/読み上げキューの動画が生成段階で止まる
- 生成失敗時のフォールバックでも重複検査を必ず通る
- 投稿済み媒体は自動再投稿・手動retryのどちらでも二重投稿されない
- ユーザーには「生成失敗」「重複検出」「投稿復旧」のどれが起きたかを分けて報告する
