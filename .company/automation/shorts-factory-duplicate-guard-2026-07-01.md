---
date: "2026-07-01"
project: shorts-factory
status: registered
type: automation-runbook
related_skill: shorts-factory-ops
---

# shorts-factory 動画被り防止・二重投稿防止 自動化登録

## 登録目的

ショート動画の自動生成/自動投稿で、同じ動画が連続生成されることと、承認・retry・復旧時に同じ媒体へ二重投稿されることを防ぐ。

## 対象自動化

- `com.ynfactory.shorts-generate`: 09:00 / 14:00 / 19:00 の生成
- `com.ynfactory.shorts-approval`: Telegram承認パネルと投稿worker起動
- `shorts-factory/scripts/post_approved_item.py`: 承認済みitemの投稿worker
- `shorts-factory/scripts/retry_failed_posts.py`: 失敗媒体だけの再投稿

## 2026-07-01 登録済みガード

### 生成側

- 直近50本のタイトル再利用を禁止する
- 字幕・読み上げ文・読み仮名の正規化署名が直近動画と一致したら禁止する
- Claude CLI失敗後のフォールバック台本も重複検査対象にする
- 重複履歴はDrive outputsではなくruntime `~/shorts-factory/work/` から読む
- `llm.retries` はruntime configで3回にする
- launchd環境でClaude CLIが見つかるよう `run_generate.sh` でnvm NodeのPATHを補強する

### 承認・投稿側

- Telegram callback応答に失敗した場合、承認/却下/保留の状態を変えない
- `approved` itemの自動再開は、承認から短時間かつ未投稿の場合だけ許可する
- workerは承認から30分超過、または一部媒体投稿済みのitemをブロックする
- 投稿成功は `~/shorts-factory/posting_ledger/<queue_id>.json` に媒体別URLとして保存する
- retry時にledgerへ投稿済みURLがある媒体は外部投稿せず、queueへURLを復元する

## 監視・復旧時の判断

以下のいずれかに該当する場合は、通常投稿ではなく復旧フローに入る。

- Telegram通知のタイトルが直近動画と同じ
- `script.json` の `title` が最近使用済み
- `script.json` の `cues` が直近動画と同一
- 生成失敗通知に `Not logged in - Please run /login` が含まれる
- queue itemが `approved` のまま古く、すでに一部媒体が `posted`
- queueとposting ledgerの投稿済みURLに差分がある

## 復旧フロー

1. 対象queue itemを確認する
2. `final.mp4` のハッシュ、`script.json`、`platforms`、`review` を確認する
3. 重複動画なら後続itemを `skipped` にし、`review.reason=duplicate_guard` を残す
4. Telegramの操作パネルはボタンなしに編集する
5. Claude CLIを `claude auth status` と `claude -p` で確認する
6. 別topicまたは別切り口で再生成する
7. 投稿済み媒体はposting ledgerから復元し、外部へ再投稿しない

## 完了条件

- 同一台本のフォールバック動画がqueue登録されない
- 同じタイトルの連続利用が生成段階で止まる
- 投稿済み媒体がretryや承認bot復旧で二重投稿されない
- 復旧時に「生成重複」「承認失敗」「投稿復旧」を分けて説明できる
