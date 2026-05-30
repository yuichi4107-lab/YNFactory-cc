---
created: "2026-03-25"
project: "ai-trade-autotrade"
assignee: "engineering"
priority: high
status: done
goal_type: "仕組み"
milestone: "MS2"
depends_on: ["2026-03-25-ai-trade-ms1-signal-engine"]
blocks: ["2026-03-25-ai-trade-ms3-notification"]
---

# MS2: 自動発注・ポジション管理

## ゴール
- **種別**: 仕組み
- **概要**: シグナル検出時に自動でエントリー注文を発行し、SL/TP/保有期間で自動決済

## 担当部署
- **部署**: 開発
- **振り分け元**: ceo/decisions/2026-03-25-ai-trade-realtime-autotrade.md

## 完了条件
- [ ] シグナル検出 → 成行注文で自動エントリー
- [ ] SL: 逆指値注文を取引所に設置
- [ ] TP: 自前監視で利確判定・決済
- [ ] 保有期間(hold_bars)経過 → 自動決済
- [ ] ポジション状態管理（建玉・決済の追跡）
- [ ] Binanceテストネットで売買サイクル一連の動作確認

## 成果物の保存先
- ai-trade-system/src/trading/

## 承認ポイント
- [ ] MS2: テストネットでの売買サイクル結果をオーナーに提示し承認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-03-25 | open | チケット作成（MS1完了待ち） |
| 2026-03-25 | in-progress | MS1完了。自動発注・ポジション管理の実装着手 |
| 2026-03-26 | done | 全機能実装完了。Binanceテストネットで売買サイクル検証済み（買い/SL設置/決済/ポジション管理/残高反映）。統合テスト（trader.py --exchange binance_testnet）も正常動作確認 |

## メモ
- MS1のシグナルエンジンに依存
