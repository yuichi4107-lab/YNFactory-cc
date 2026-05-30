---
created: "2026-04-09"
project: "fx-auto-trading"
assignee: "engineering"
priority: high
status: in-progress
goal_type: "仕組み"
milestone: "MS1"
depends_on: []
blocks: ["2026-04-09-fx-ms2-backtest"]
---

# [FX] MS1: OANDA接続 + OANDAアダプター実装

## ゴール
- **種別**: 仕組み
- **概要**: OANDA REST API v20に接続し、既存ai-trade-systemから透過的にFX取引できるようにする

## 担当部署
- **部署**: 開発部
- **振り分け元**: ceo/decisions/2026-04-09-fx-auto-trading.md

## 完了条件
- [x] OandaClient実装（ExchangeClient互換インターフェース）
- [x] trader.py にOANDA分岐追加（--exchange oanda_demo / oanda）
- [x] scanner.py でFX通貨ペアのOHLCV取得対応
- [x] strategy_config.json にUSD-JPY, EUR-JPYの戦略定義追加
- [ ] OANDA デモ口座開設（オーナー手動）
- [ ] デモ口座でAPI接続テスト（残高取得、ローソク足取得成功）

## 成果物の保存先
- `ai-trade-system/src/trading/oanda_client.py`
- `ai-trade-system/docs/oanda-adapter-design.md`

## 承認ポイント
- [ ] デモ口座でのAPI接続テスト成功時にオーナー確認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-04-09 | open | チケット作成 |
| 2026-04-09 | in-progress | OandaClient実装、trader.py/scanner.py統合、strategy_config.json更新 |

## メモ
- ccxtはOANDA非対応のため、httpxで直接REST API呼出し
- oandapyV20は2021年以降メンテ停止・Python 3.12非対応のため不採用
- デモ口座のAPIトークンは .env の OANDA_DEMO_TOKEN / OANDA_DEMO_ACCOUNT_ID に設定
