---
date: "2026-06-16"
project: shorts-factory
status: implemented_waiting_external_login
owner_request: "YouTube / Instagram / TikTok 実投稿有効化、1日3回投稿、初中中バランス"
external_posting_boundary: "actual publish and auto_post=true require final confirmation"
---

# shorts-factory 3回投稿・複数媒体・中級者メイン化 要件定義

## ゴール

shorts-factory を、X単独・1日1本・初心者向け中心から、YouTube / Instagram / TikTok も投稿対象にできる、1日3本、初級1本＋中級2本の運用へ拡張する。

## スコープ

### やること

1. 投稿スケジュールを 9:00 / 14:00 / 19:00 に変更する。
   - launchd の `StartCalendarInterval` を3枠にする。
   - pipeline が実行時刻から難易度スロットを判定できるようにする。

2. 投稿内容を「初中中」バランスにする。
   - 9:00 は `beginner`。
   - 14:00 / 19:00 は `intermediate`。
   - ネタ帳に `difficulty` を持たせ、指定難易度から優先選択する。
   - 中級者向けプロンプトでは、一般論ではなく実務ワークフロー・失敗例・判断基準・テンプレ運用を中心にする。

3. YouTube / Instagram Reels / TikTok の有効化準備をする。
   - 認証・ログイン状態を確認する preflight を追加する。
   - `~/shorts-factory/config.yaml` は staged 状態で作成し、投稿対象に全媒体を入れるが `auto_post: false` とする。
   - Telegram承認後に全媒体へ投稿できる状態を目指す。

### やらないこと

- この工程では `auto_post: true` にしない。
- この工程では実テスト投稿・公開を実行しない。
- YouTube / Instagram / TikTok のログイン画面での手入力・2FA突破は、必要になった時点でオーナー操作にする。
- Meta / YouTube / TikTok アカウント上の削除や設定変更は行わない。

## 完了条件

- launchd が 9:00 / 14:00 / 19:00 の3回実行に変わっている。
- pipeline が `--difficulty beginner|intermediate` と時刻自動判定の両方に対応している。
- topics.json に中級者向けネタが十分追加され、既存初心者向けネタも維持されている。
- 台本生成プロンプトが難易度別に出力傾向を変える。
- platform preflight で YouTube / Instagram / TikTok の状態を確認できる。
- runtime に同期済みで、テストが通る。
- 実投稿を始めるために残っている承認事項が明確。

## 工程

### 工程1: スケジュール・難易度ルーティング

対象:
- `shorts-factory/src/config.py`
- `shorts-factory/src/topic_store.py`
- `shorts-factory/src/script_gen.py`
- `shorts-factory/src/pipeline.py`
- `shorts-factory/scripts/run_generate.sh`
- `shorts-factory/launchd/com.ynfactory.shorts-generate.plist`

品質基準:
- 9時台は beginner、14時台/19時台は intermediate になる。
- CLI引数で明示難易度指定できる。
- 指定難易度のネタがない場合は安全にフォールバックし、通知で分かる。

### 工程2: 中級ネタ帳と生成プロンプト

対象:
- `.company/marketing/shorts-factory/topics.json`
- `shorts-factory/prompts/script_prompt.md`

品質基準:
- 中級ネタが少なくとも20本以上ある。
- 初心者向けの既存ネタを破壊しない。
- 中級者向けが「プロンプト基礎」だけでなく、実務の分解・検証・改善に寄る。

### 工程3: 複数媒体preflightとstaged config

対象:
- `shorts-factory/scripts/check_platforms.py`
- `shorts-factory/src/platforms/tiktok_cdp.py`
- `shorts-factory/config.yaml.example`
- `~/shorts-factory/config.yaml`

品質基準:
- dry-runで外部投稿なしに状態確認できる。
- staged config は `auto_post: false`。
- platforms は `x/youtube/instagram/tiktok` を含む。

### 工程4: 検証・runtime反映

品質基準:
- `python3 -m unittest discover -s shorts-factory/tests` PASS。
- `py_compile` PASS。
- `bash -n` PASS。
- runtime `~/shorts-factory/app` へ同期済み。
- launchd plist再読込済み。

## 最終承認が必要な操作

以下は別途、実行直前に明示承認を取る。

- `queue.auto_post: true` への変更。
- 実テスト投稿。
- YouTube / Instagram / TikTok で公開状態を作る操作。
- テスト投稿の削除。

## 実装結果

- launchd `com.ynfactory.shorts-generate` を 09:00 / 14:00 / 19:00 の3枠に変更。
- `content.scheduled_slots` を追加し、09:00=beginner、14:00/19:00=intermediate に設定。
- pipeline に `--difficulty beginner|intermediate` を追加。
- topic selection が難易度を優先するように変更。該当難易度が空なら通知してフォールバック。
- 台本プロンプトに難易度別方針を追加。
- queue item とTelegram preview に `difficulty` を保持・表示。
- 中級ネタを24本追加。現在 backlog は beginner 26本、intermediate 24本。
- `~/shorts-factory/config.yaml` を staged config として作成。
  - `queue.platforms: [x, youtube, instagram, tiktok]`
  - `queue.auto_post: false`
- `scripts/check_platforms.py` を追加し、実投稿なしでplatform readinessを確認可能にした。
- `scripts/login_tiktok.sh` を追加。`login_youtube.sh` / `start_chrome_shorts.sh` も目的URLを開けるように修正。

## 品質チェック

score: 90/100

合格:
- `python3 -m json.tool .company/marketing/shorts-factory/topics.json` PASS。
- `bash -n` PASS。
- `py_compile` PASS。
- `python -m unittest discover -s shorts-factory/tests` PASS（4 tests）。
- launchd plist `plutil -lint` PASS。
- runtime `~/shorts-factory/app` へ同期済み。
- launchd generate / approval 再読込済み。
- runtime config は `auto_post=false` かつ platforms 全媒体。
- schedule確認: 09:00 beginner / 14:00 intermediate / 19:00 intermediate。

現時点のpreflight:
- X: ready
- Instagram Reels: ready（必要envあり）
- YouTube: not ready（専用Chromeプロファイル未ログイン）
- TikTok: not ready（専用Chromeプロファイル未ログイン）

残作業:
- オーナーが `~/shorts-factory/app/scripts/login_youtube.sh` と `login_tiktok.sh` でログイン。
- `~/shorts-factory/.venv/bin/python ~/shorts-factory/app/scripts/check_platforms.py` で全ready確認。
- 初回テスト投稿の実行可否を明示承認。
- 問題なければ `queue.auto_post: true` へ切替するか判断。

## 2026-07-01 追補: 動画被り防止

2026-06-29 19:00 と 2026-06-30 09:00 で同一動画が連続生成されたため、1日3回運用の必須品質基準に「直近動画との重複禁止」を追加した。

追加完了条件:

- 直近50本と同じ `title` は生成不合格にする。
- 字幕・読み上げ文・読み仮名を正規化したキュー署名が直近動画と一致する場合は生成不合格にする。
- Claude CLI失敗後のフォールバック台本も同じ重複検査を通し、被る場合はqueue登録しない。
- 重複履歴はDrive outputsではなくruntime `~/shorts-factory/work/` を参照し、Driveロックで生成を止めない。
- Claude CLI復旧確認は `claude auth status` だけでなく、非対話実行 `claude -p` まで確認する。
- 重複queueを見つけた場合は `skipped` + `review.reason=duplicate_guard` で残し、別topic/別切り口で再生成する。

## 2026-07-02 追補: 英語ツール名テロップ

AIツール全般へテーマを広げたことで、`NotebookLM` などの英語ツール名が読み上げ用カタカナに寄ってテロップへ焼き込まれる問題が発生した。

追加完了条件:

- 英語ツール名・サービス名・一般的な英字略語（PDFなど）は `display` で英字表記を維持する。
- `tts_text` / `reading_kana` は音声安定のためカタカナ読みでよい。
- 表示正規化辞書と音韻比較辞書を同時に更新し、英字表示とカタカナ読みを同一語として検証できる。
- 表示ルールを修正した既存候補は、旧queueを `skipped` にしてTelegramボタンを外し、再レンダリング後に `subtitles.ass` と動画フレームで確認する。
