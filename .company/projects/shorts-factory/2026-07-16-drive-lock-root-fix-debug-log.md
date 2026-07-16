# shorts-factory Driveロック根本改善 デバッグ・検証記録

- 日付: 2026-07-16
- 対象: 生成、Telegram承認、4媒体投稿のruntime制御プレーン
- 結論: Driveを正本にした同期I/Oが根因。`~/shorts-factory/` を正本、Driveを非同期一方向ミラーへ変更した

## 根因の実測

- 2026-07-12以降の生成成功12件中12件で、Drive上の `topics.json` 消費が `Resource deadlock avoided` になった
- Drive側 `topics.json` は2026-07-11 19:03以降更新されていなかった
- 2026-07-11以降、approval botはDrive待ちでwatchdog再起動を130回記録した
- queue 177件を30秒ごとにDriveから最大80件走査し、File Provider待ちがwatchdog 600秒を超えていた
- 二重LaunchAgent、二重approval PID、Telegram 409、直近SNS API投稿失敗は確認されなかった

## 実装

- queue、topics、通知outbox、却下待ち、outputs、work、SNS認証をローカル正本へ移行
- queue/topicsを `flock` とatomic write、file/directory `fsync` で保護
- stale queue snapshotの `message_id`、投稿URL、terminal status消失を防ぐmergeとnested reference維持を実装
- 生成全体をglobal generator lockで直列化し、並行生成のtopic重複選択を防止
- 外部投稿前にposting ledgerへ `attempting` を確定し、成功後だけ `posted` URLへ更新
- `attempting` 残存・送信結果不明・ledger破損はfail closedし、`reconcile_required` で自動再投稿を停止
- posting workerはPIDファイル判定をやめ、worker生存期間中のkernel `flock` を正本に変更
- Telegramプレビューreceiptが不明な場合も自動再送せず、二重ボタンを防止
- generate/approval/post workerからDriveパスと毎回のDriveコード同期を除去
- Drive専用mirror workerを別プロセス化し、90秒timeout、lock、指数backoff、hash検証を実装
- queue mirror payloadの時刻依存hashを除去し、未変更queueを5分ごとに再コピーしないよう修正
- runtime health check、初回migration、認証明示同期、運用手順を追加

## 移行結果

- queue: 177件
- status: posted 126 / skipped 36 / blocked 1 / partial_failed 6 / ready_for_review 8
- topics: backlog 45 / used 70
- deferred topic消費: 16件解消、残り0件
- active itemのローカル動画欠損: 0件
- SNS認証: ローカルへ16 assignmentを同期、mode `0600`
- queue全走査: 0.038秒

## 切替中に検出・修正した回帰

10:15の初回approval起動時、2件のTelegramプレビュー送信後に `message_id` がqueueへ残らない問題を検出した。`queue_lib.save_item()` がnested mapping参照を置換し、送信結果を古い参照へ書いていたことが原因。

- approval botを直ちに停止
- nested mappingをin-place更新するよう修正し、送信後は参照も再取得
- 送信済み2件は `preview_sent_untracked_at` を記録して自動再送を停止
- health checkへpreview receipt不整合検出を追加
- SNS投稿は行っていない

## 検証

- runtime venv: unittest 111件、全件合格
- quality-checker最終採点: 96/100、重大ゲートすべて合格
- Python compile: 合格
- shell `bash -n`: 合格
- launchd plist `plutil -lint`: 5件合格
- runtime health: `ok=true`、queue 177/177読込、Drive hot path 0、ledger破損0、preview receipt不整合0
- Drive mirror: 修正反映1回目177件更新、直後2回目 `copied=0 / skipped=313`
- approval launchd: 最終コードを反映して2026-07-16 10:40:48 JST再開、Drive環境変数なし、起動直後エラーなし
- AIからのSNS試験投稿・再投稿: 未実施

## オーナー承認による実運用確認

10:40:36 JST、オーナーがTelegram上の既存プレビューを承認したため、通常の投稿workerが起動した。これはAIが開始した試験投稿ではない。

- X / Instagram / TikTok / YouTube: 各1回で `posted`
- 各platformのattempts: 1
- posting ledger: 4媒体すべてURL付き `posted`
- worker: 10:42:14 JST完了、exit code 0
- worker実行中にapproval botを再起動しても、`already_partially_posted` とworker lockにより同じitemを再起動しなかった
- 完了後health: `ok=true`、queue走査0.0156秒、posted 127 / ready_for_review 7
- 完了状態のDrive mirror: 2件更新後、直後の再実行は `copied=0 / skipped=314`

## 残る運用上の注意

- 14:00の次回定刻生成が、切替後最初の実生成になる。healthと自動テストは合格済みだが、その実行ログも通常監視対象とする
- 初回mirrorがDriveへ作った空のlegacy lockファイルは処理対象から除外済み。削除は行っていない
- 過去ログに未マスクのTelegram bot tokenを含む古い例外履歴がある。値は再表示していない。token再発行と旧ログ整理は外部認証・削除を伴うため別途オーナー承認で行う

## 最終安定稼働確認

2026-07-16 10:51:12 JST、最終コードでのapproval再起動から10分24秒後に再確認した。

- approval: PID 3254を維持、`runs=1`、`last exit=(never exited)`
- 10:40:48以降のwatchdog再起動・Drive I/Oエラー・Traceback: 0件
- approval PIDが開いているCloudStorage / GoogleDriveファイル: 0件
- health: `ok=true`、queue 177/177、走査0.0189秒、未解消topic 0、active media欠損0、preview receipt不整合0、posting ledger破損0
- mirror: 10:50:22完了、`copied=0 / skipped=314 / consecutive_failures=0`

## ロールバック

問題時はapproval/generateを停止し、ローカルqueueとposting ledgerを保全する。Driveをruntime正本へ戻さず、直前runtime appへ戻してhealth checkを通す。公開済みか不明な媒体はledgerを削除せず `reconcile_required` のままSNS公開状態を照合する。
