---
created: "2026-04-09"
project: "fx-auto-trading"
assignee: "engineering"
priority: high
status: open
goal_type: "成果物"
milestone: "MS2"
depends_on: ["2026-04-09-fx-ms1-oanda-setup"]
blocks: ["2026-04-09-fx-ms3-forward-test"]
---

# [FX] MS2: Phase1戦略バックテスト

## ゴール
- **種別**: 成果物
- **概要**: USD/JPYでPhase1戦略（MA+RSI、ダブルボトム等）のバックテストを実行し、最適パラメータを確定する

## 担当部署
- **部署**: 開発部
- **振り分け元**: ceo/decisions/2026-04-09-fx-auto-trading.md

## 完了条件
- [ ] USD/JPY 1年分のOHLCVデータ取得
- [ ] ダブルボトム + RSIバウンス戦略のバックテスト実行
- [ ] パラメータ最適化（SL/TP/Hold期間のグリッドサーチ）
- [ ] PF、勝率、最大DD、Calmar比の評価レポート
- [ ] 最適パラメータをstrategy_config.jsonに反映

## 成果物の保存先
- `ai-trade-system/results/fx_backtest_*/`

## 承認ポイント
- [ ] バックテスト結果をオーナーに提示、パラメータ確定の承認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-04-09 | open | チケット作成 |

## メモ
- FXはボラが暗号資産より低いため、SL/TPは0.2-0.6%程度の小さい値が適切
- スプレッドコスト（USD/JPY: 0.3pips）をバックテストに織り込むこと
- DD目標: 20%以下
