---
created: "2026-04-09"
project: "fx-auto-trading"
assignee: "engineering"
priority: normal
status: open
goal_type: "仕組み"
milestone: "MS3"
depends_on: ["2026-04-09-fx-ms2-backtest"]
blocks: ["2026-04-09-fx-ms4-production"]
---

# [FX] MS3: デモ口座フォワードテスト

## ゴール
- **種別**: 仕組み
- **概要**: OANDAデモ口座でAutoTraderを1-2週間稼働させ、実環境での動作を検証する

## 担当部署
- **部署**: 開発部
- **振り分け元**: ceo/decisions/2026-04-09-fx-auto-trading.md

## 完了条件
- [ ] デモ口座でAutoTrader（oanda_demo）を常駐デーモン起動
- [ ] 実際の注文約定・ポジション管理の正常動作を確認
- [ ] SL/TP自動決済の動作を確認
- [ ] LINE通知の正常動作を確認
- [ ] 1-2週間の安定稼働を確認

## 成果物の保存先
- VPS: `/opt/ai-trader/` (FX用コンテナまたは既存コンテナに追加)

## 承認ポイント
- [ ] 1-2週間の安定稼働確認後、本番移行の承認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-04-09 | open | チケット作成 |

## メモ
- 土日はFX市場クローズのためデーモンに週末スキップロジックが必要
- デモ口座は仮想資金（デフォルト10万円相当に設定）
