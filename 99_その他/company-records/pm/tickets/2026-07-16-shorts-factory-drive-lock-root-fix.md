---
title: shorts-factory Driveロック根本改善
status: done
department: engineering
priority: high
created: 2026-07-16
---

# shorts-factory Driveロック根本改善

## 完了条件

- ローカル制御プレーンと非同期Driveミラーを実装・移行する
- Drive障害注入を含む自動テストに合格する
- launchd切替後にwatchdog再起動が再発しないことを確認する
- README・運用スキル・デバッグログへ再発防止を反映する

## 作業ログ

- 2026-07-16: 実ログ、launchd、queue、プロセスを調査。二重起動ではなくDrive上のqueue/topics同期I/Oが根因と確定。
- 2026-07-16: ローカル制御プレーン、原子的状態保存、投稿台帳、kernel lock、Drive非同期ミラー、migration/health/deployを実装し、queue 177件を移行。
- 2026-07-16: runtime unittest 111件PASS、quality-checker 96/100、オーナー承認の実投稿4媒体成功、10分超のapproval安定稼働を確認して完了。
