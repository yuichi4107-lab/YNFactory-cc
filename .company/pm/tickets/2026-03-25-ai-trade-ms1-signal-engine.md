---
created: "2026-03-25"
project: "ai-trade-autotrade"
assignee: "engineering"
priority: high
status: done
goal_type: "仕組み"
milestone: "MS1"
depends_on: []
blocks: ["2026-03-25-ai-trade-ms2-auto-order"]
---

# MS1: リアルタイムシグナル生成エンジン

## ゴール
- **種別**: 仕組み（自動売買パイプラインの基盤）
- **概要**: 最新OHLCVデータを取得し、AI判定でシグナルを生成するエンジンを実装

## 担当部署
- **部署**: 開発
- **振り分け元**: ceo/decisions/2026-03-25-ai-trade-realtime-autotrade.md

## 完了条件
- [ ] 最新OHLCVデータのリアルタイム取得機能（ccxt経由）
- [ ] 直近50本のチャート画像を動的生成
- [ ] Gemini AI判定でシグナル検出（strategy_config.json準拠）
- [ ] 4通貨（BTC, ETH, SOL, XRP）一括スキャン
- [ ] コマンド1つで「今シグナルが出ているか」を確認可能
- [ ] Binanceテストネットでの動作確認

## 成果物の保存先
- ai-trade-system/src/signal/scanner.py（メインスキャナー）
- ai-trade-system/src/signal/（関連モジュール）

## 承認ポイント
- [ ] MS1: 4通貨スキャン結果をオーナーに提示し承認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-03-25 | in-progress | チケット作成、実装着手 |
| 2026-03-25 | done | scanner.py実装完了。4通貨フルスキャン動作確認済み。オーナー承認 |

## メモ
- 既存パイプライン: fetch_ohlcv.py → generate_chart_images.py → gemini_client.py → runner.py
- これをリアルタイム用に再構成する
- strategy_config.json の通貨別設定（プロンプトバージョン、window_size等）を参照
