# shorts-factory Driveロック根本改善 要件定義

- 日付: 2026-07-16
- 状態: completed
- 承認根拠: オーナー依頼「Driveロックのエラーが多発。根本的な改善をしてください」
- 主担当: 開発
- 品質確認: quality-checker

## ゴール

Google Drive File Providerが停止・EDEADLK・Operation not permittedになっても、ショート動画の生成、Telegram承認、SNS投稿、投稿結果記録が止まらない構造へ移行する。

## 根因（現行証拠）

- 可変状態 `queue/` と `topics.json` がDrive上にあり、承認ボットが30秒ごとに最大80件を読み直している。
- 2026-07-11以降、承認ボットはDrive待ちでwatchdog再起動を130回起こした。
- 2026-07-12以降の生成成功12件すべてで、ネタ帳消費が `Resource deadlock avoided` になった。
- 二重LaunchAgent、二重approval bot、Telegram 409、直近SNS投稿workerの失敗は確認されていない。

## スコープ

### 実施する

1. `queue/topics/outbox/pending_rejections/outputs` の正本を `~/shorts-factory/` のローカル状態へ移す。
2. 動画生成・承認・投稿のホットパスからDriveの読み書きと毎回のDriveコード同期を除去する。
3. SNS認証ファイルはローカルの権限600コピーのみを投稿時に読む。
4. Driveは別プロセスの非同期・失敗許容ミラーにし、停止しても本処理へ影響させない。
5. 既存queue/topicsをローカルへ移行し、未解消のネタ消費を整合させる。
6. ヘルスチェック、移行手順、運用スキル、README、再発防止記録を更新する。

### 実施しない

- 承認のないSNSテスト投稿、投稿済みコンテンツの削除・公開変更
- Google Drive内の既存queue/outputの削除
- 投稿プラットフォームや投稿頻度の変更

## 完了条件

- [x] 実行時の `factory_dir/queue_dir/topics_path/outputs_dir/sns_env_path` がすべてローカルに解決される。
- [x] Driveパスをアクセス不能にしたテストでもqueueの作成・一覧・遷移、topicの選択・消費が成功する。
- [x] 177件規模のqueueスキャンがローカルで短時間に完了し、watchdog時間へ近づかない。
- [x] Driveミラーworkerが別プロセスで動き、タイムアウト・失敗時にも本処理が継続する。
- [x] ミラーはqueue/topics/outputsをDriveへ原子的に反映し、失敗分を次回再試行する。
- [x] 既存queue/topicsとSNS認証がローカルへ安全に移行され、件数・JSON妥当性・権限を確認できる。
- [x] 既存unittest、追加のDrive障害テスト、shell/plist構文検査がすべて合格する。
- [x] approval bot再起動後、queueスキャンが完了し、watchdog再起動が再発しないことをライブ状態で確認する。
- [x] 二重投稿防止ledger・worker lock・承認期限ガードが維持される。

## 品質基準（100点）

- Drive非依存性 30点
- 状態整合性・クラッシュ復旧 25点
- 二重投稿防止・承認境界 20点
- テストとライブ検証 15点
- 運用性・ドキュメント 10点

85点以上を合格とし、重大項目（Driveホットパス残存、queue消失、二重投稿リスク）が1件でもあれば不合格とする。

## 工程

1. ローカル制御プレーン実装 — パス分離、ローカル原子的保存、コード同期分離。
2. 非同期Driveミラー実装 — supervisor/worker分離、タイムアウト、再試行、manifest。
3. 状態移行 — queue/topics/認証の検証付きコピー、未消費topicの復旧。
4. 検証・切替 — 自動テスト、Drive障害注入、launchd切替、ライブ監視。
5. 運用反映 — README、skill、デバッグログ、完了監査。

## 完了監査

- runtime venv unittest: 111件、全件合格
- quality-checker: 96/100、重大ゲートすべて合格
- queue: 177/177件、最終走査0.0189秒
- approval bot: 2026-07-16 10:40:48再起動後、10:51:12時点でもPID 3254 / runs 1 / watchdog再発0 / Drive open file 0
- Drive mirror: 10:50:22時点 `copied=0 / skipped=314 / consecutive_failures=0`
- オーナーTelegram承認の既存1件: X / Instagram / TikTok / YouTubeへ各1回で成功、二重投稿なし
