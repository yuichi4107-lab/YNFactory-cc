# 競馬予想AI

JRA（keiba-unified/jra）・ばんえい（keiba-ai-system）の予想AI運用プロジェクト。

## 概要

- 本番: ConoHa VPS 163.44.101.31
  - JRA: `/opt/keiba-unified/jra/`（cron: 朝7:00 C5b / 9:30ライブFULL / 17:30結果集計）
  - ばんえい: `/opt/keiba-unified/keiba-ai-system/`（毎日、開催種別ごとcron）
- コード正本: リポジトリルート `keiba-unified/`（Drive）。VPSへはscp反映
- 分析スクリプト: `C:\dev\jra_*.py`（Windows端末ローカル）

## フォルダマップ

- `2026-07-05-モデル検証とバージョンアップ.md` — フォワード検証・払戻文字化け障害の修復・モデル新旧OOS比較・全券種19.4万構成スイープ（ROI130%探索）の総合レポート

## 関連外部資産

- 旧調査レポート: `.company/research/topics/2026-06-06-jra-keiba-no-odds-investigation.md`（凍結フォルダ内・参照のみ）
- 障害デバッグログ: `.company/engineering/debug-log/2026-06-07-jra-thisweek-403.md`（同上）
- メモリ: jra-payout-mojibake-fix / jra-odds-scraper-fix / jra-no-odds-ab / banei-deploy
