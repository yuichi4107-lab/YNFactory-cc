---
date: "2026-06-16"
project: shorts-factory
status: implemented
owner_approval: approved
---

# shorts-factory 自動投稿 改良 要件定義

## ゴール

shorts-factory の自動投稿を、X単独運用から複数媒体運用へ広げても破綻しにくい状態にする。
第一弾では、投稿そのものの外部設定変更は行わず、投稿基盤の安全性・反映性・再試行性を改善する。

## 現状

- 2026-06-16 08:01 JST 時点で、6/13・6/15・6/16 の3本は X 投稿済み。
- `~/shorts-factory/config.yaml` は未作成のため、現在はデフォルト設定の「承認制・Xのみ」運用。
- `shorts-generate.log` に `rsync失敗。既存コードで続行` が出ており、Drive側の修正が runtime `~/shorts-factory/app` へ反映されない可能性がある。
- Telegram 通信エラーの例外文字列に bot token を含む URL が入るため、ログ上の秘密情報マスクが必要。
- 現行 `poster.post_item()` は一部媒体だけ成功した場合もキュー全体を `posted` にするため、失敗媒体だけを後から自動再試行しづらい。

## スコープ

### やること

1. Drive正本からruntimeへの同期を安定化する。
   - `SHORTS_REPO_ROOT` / `YNFACTORY_ROOT` / スクリプト位置からDriveルートを解決できるようにする。
   - パス表記ゆれで同期できない場合も、候補パスを試して分かるログを出す。

2. Telegramログの秘密情報をマスクする。
   - bot token を含むURLや例外文字列をログへ出す前に `[REDACTED]` へ置換する。
   - 投稿失敗通知にも秘密情報が混ざらないようにする。

3. 自動投稿の再試行性を上げる。
   - 一部媒体失敗時は全体ステータスを `posted` ではなく再処理可能な状態に残す。
   - 成功済み媒体は二重投稿しない。
   - 失敗媒体だけを再試行できる CLI または承認bot側の処理を追加する。

4. READMEと運用メモを更新する。
   - 現在の「Xのみ・承認制」状態を明記。
   - `auto_post: true` と複数媒体有効化時の挙動、失敗時の再試行手順を書く。

### やらないこと

- YouTube / Instagram / TikTok への実投稿有効化。
- 外部アカウント操作、ログイン、投稿、公開、削除。
- Telegram bot token のローテーション実行。
- Meta権限追加やGraph API token取得。

## 完了条件

- `run_generate.sh` / `deploy.sh` がDriveルートを安定して解決し、runtime同期できる。
- Telegram関連ログに bot token が平文で出ない。
- 複数媒体のうち一部失敗しても、成功済み媒体を重複投稿せず失敗媒体だけ再試行できる。
- 既存のX投稿済みキュー3件を壊さない。
- READMEに新しい運用手順が反映されている。
- 可能な範囲のローカル検証が通る。

## 工程分割

### 工程1: 同期と秘密情報マスク

成果物:
- `shorts-factory/scripts/run_generate.sh`
- `shorts-factory/scripts/deploy.sh`
- `shorts-factory/src/approval_bot.py`
- 必要なら共通ユーティリティ

品質基準:
- Driveルート解決が現在のMacパスで成功する。
- 通信例外文字列をサンプル入力でマスクできる。
- 既存launchdの呼び出し方法を壊さない。

### 工程2: 投稿ステータスと再試行

成果物:
- `shorts-factory/src/queue_lib.py`
- `shorts-factory/src/platforms/poster.py`
- 必要なら `shorts-factory/scripts/retry_failed_posts.py`

品質基準:
- 全成功は `posted`。
- 全失敗は `failed`。
- 一部成功・一部失敗は再試行可能ステータス。
- 再試行時に `posted` 済み媒体はスキップされる。

### 工程3: ドキュメントと品質チェック

成果物:
- `shorts-factory/README.md`
- この要件定義書の status 更新

品質基準:
- 実運用者が「今どの媒体が有効か」「失敗したら何を打つか」を迷わない。
- 外部投稿・削除・認証変更を実行していないことが明確。

## 承認が必要な点

2026-06-16 にオーナー承認済み。
実装後、工程1〜3はローカル検証まで完了。
実投稿や外部アカウント操作が必要になった場合は、その直前に別途明示承認を取る。

## 実装結果

- Drive同期: `scripts/shorts_env.sh` を追加し、`SHORTS_REPO_ROOT` / `YNFACTORY_ROOT` / 候補パスからrepo rootを解決。
- 秘密情報マスク: `src/logging_utils.py` を追加し、Telegram token をログ・通知前にマスク。
- 再試行性: キューstatusに `partial_failed` を追加し、一部媒体失敗時は再試行可能な状態で保持。
- 再試行CLI: `scripts/retry_failed_posts.py` を追加。既定はdry-run、`--execute` 指定時のみ投稿を実行。
- テスト: `tests/test_posting_core.py` を追加し、マスク・partial_failed・二重投稿回避を検証。

## 品質チェック

score: 92/100

合格理由:
- `python3 -m unittest discover -s shorts-factory/tests` がDrive側・ローカルGit側ともPASS。
- `bash -n` と `py_compile` がPASS。
- `shorts-factory/scripts/deploy.sh` で runtime `~/shorts-factory/app` へ同期済み。
- launchd の `shorts-approval` は再起動済み、`shorts-generate` はplist再読込済み。
- `retry_failed_posts.py --all` はDrive側・runtime側ともdry-runで対象0件を返す。
- 既存ログのTelegram token pattern残存は0件。

残リスク:
- YouTube / Instagram / TikTok の実投稿は未有効化のため、各媒体API/UI変更への実地検証は未実施。
- Telegram bot token は既存ログからマスク済みだが、一度ローカルログに出た履歴があるため、専用bot化またはtokenローテーションは別途推奨。
