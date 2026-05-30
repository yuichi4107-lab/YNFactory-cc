---
created: "2026-03-25"
project: "ai-trade-autotrade"
assignee: "engineering"
priority: normal
status: done
goal_type: "仕組み"
milestone: "MS4"
depends_on: ["2026-03-25-ai-trade-ms3-notification"]
blocks: []
---

# MS4: 本番移行（Coincheck）

## ゴール
- **種別**: 仕組み
- **概要**: Binanceテストネットで検証済みのシステムをCoincheck本番環境に移行

## 担当部署
- **部署**: 開発
- **振り分け元**: ceo/decisions/2026-03-25-ai-trade-realtime-autotrade.md

## 完了条件
- [x] Coincheck API連携の実装・切り替え
- [x] 少額での実運用テスト
- [x] 24/7 常駐運用の安定稼働確認

## 成果物の保存先
- ai-trade-system/src/trading/

## 承認ポイント
- [x] MS4: 本番運用開始前にオーナー最終承認（実運用で承認済み）

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-03-25 | open | チケット作成（MS3完了待ち） |
| 2026-03-26 | in-progress | MS3完了。Coincheck本番移行の実装着手 |
| 2026-03-26 | in-progress | exchange.pyにシンボル自動変換(USDT↔JPY)・建て通貨対応を実装済み。trader.pyもJPY対応済み。Binanceテストネットでリグレッション確認完了。残作業: CoincheckのAPIキー設定→接続テスト→少額本番テスト |
| 2026-04-09 | done | 全完了条件クリア確認。本番デーモン稼働中（VPS Docker）、BTC/JPY実ポジション保有実績あり、シミュレーション記録機能も追加済み。チケットクローズ |

## メモ
- Coincheck APIキーの取得・設定が必要（オーナー対応） → 完了済み
- CoincheckはSL注文非対応のため自前監視で対応（exchange.py）
- シミュレーション記録機能（simulation_tracker.py）追加済み。週次・月次レポート自動生成
