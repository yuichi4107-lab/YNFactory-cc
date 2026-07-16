# shorts-factory 制御プレーンのローカル正本化

- 日付: 2026-07-16
- 決定: 採用
- 主担当: 開発

## 決定

shorts-factoryの可変状態は `~/shorts-factory/` を正本とする。Google Driveは共有・監査用の非同期ミラーとし、生成・承認・投稿の成否条件から外す。

## 理由

Drive File Providerのロックはプロセス内の再試行やSIGALRMで確実に中断できず、queueをDrive上に置く限り承認ボット全体が停止する。SNS投稿自体は直近で成功しており、障害点はDrive上の制御状態であるため、排他強化ではなく境界の分離が必要。

## 安全境界

- Driveミラー失敗はローカルoutbox/manifestに残し、投稿を失敗扱いにしない。
- SNS投稿成功はローカルqueueとposting ledgerへ先に永続化する。
- Drive側データは移行時も削除しない。
- 公開投稿を伴う検証は別途オーナー承認まで行わない。

## 影響

Drive上のqueue/topicsは閲覧用ミラーになる。手動操作はruntime用CLIまたはTelegram承認から行い、Drive JSONの直接編集は運用対象外とする。
