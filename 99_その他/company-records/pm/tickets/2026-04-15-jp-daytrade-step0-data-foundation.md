---
created: "2026-04-15"
project: "jp-stock-daytrade"
assignee: "engineering"
priority: high
status: done
goal_type: "仕組み"
milestone: "MS1-データ基盤"
depends_on: []
blocks: ["2026-04-XX-jp-daytrade-step1-backtest"]
---

# JP-DAYTRADE-v1 工程0: データ基盤構築

## ゴール
- **種別**: 仕組み
- **概要**: バックテストおよびリアルタイム運用に必要なデータパイプライン（J-Quants日足DB + kabu APIモック + 気配保存スクリプト）を整備する

## 担当部署
- **部署**: engineering
- **振り分け元**: `.company/engineering/docs/jp-daytrade-v1-requirements.md`（AP1承認済み 2026-04-15）

## 完了条件
- [ ] J-Quants接続モジュール実装（`jp-daytrade/data/jquants_client.py`）
- [ ] 気配データ保存スクリプト実装（`jp-daytrade/data/kabu_push_recorder.py`）
- [ ] kabu APIモック実装（`jp-daytrade/data/kabu_mock.py`）
- [ ] 銘柄マスターDB構築（`jp-daytrade/data/stocks_master.db` — グロース市場、値嵩除外）
- [ ] 日足価格DB構築（`jp-daytrade/data/daily_prices.db` — 過去2年分）
- [ ] データ整備スクリプト（`jp-daytrade/data/setup_db.sh`）
- [ ] J-Quants日足2年分が欠損率 < 0.1%で取得できる
- [ ] kabu APIモックが実際のレスポンス形式（AskSign/BidSign/Sell1-10/Buy1-10等）を返す
- [ ] 気配データ保存スクリプトがモックで1分足単位でSQLiteへ書き込める
- [ ] 値嵩株除外フィルター（株価 > 3,000円 or 単元代金 > 30万円）が境界値テストで動作
- [ ] setup_db.sh が5分以内に初回セットアップを完了できる

## 成果物の保存先
- コード: `/jp-daytrade/data/` （プロジェクトルート直下の新規ディレクトリ）
- DB: `/jp-daytrade/data/*.db` （SQLite）
- 設定: `/jp-daytrade/config/kabu_config.env`（.gitignore対象）

## 品質基準
要件定義書 工程0セクション参照（100点満点、合格85点以上）:
- データ完全性（J-Quants欠損率）: 20点
- 機能要件（kabu APIモック形式）: 20点
- 機能要件（気配データ保存1分足）: 15点
- エラーハンドリング（値嵩除外境界値）: 15点
- 可読性（SQLiteスキーマ・型定義）: 10点
- 運用品質（setup_db.sh 5分以内）: 10点
- 既存一貫性（ai-trade-systemスタイル準拠）: 10点

## 承認ポイント
- [ ] 完了時、quality-checkerで85点以上 → 工程1へ自動進行（AP2準拠）

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-04-15 | open | チケット作成（要件定義承認後） |
| 2026-04-15 | in-progress | executor起動 |
| 2026-04-15 | done | executor完了（74テスト全通過）→ quality-checker 91点 PASS |

## メモ
- 信用口座審査中（2026-04-18〜24予想）のため、実機接続不要の範囲で先行開発
- J-Quants認証情報はオーナー確認必要（Lightプラン無料）
- 既存コードベース（`ai-trade-system/`）のコーディングスタイル・型ヒントを参考に統一
- SQLiteスキーマは拡張性を考慮（カラム追加しやすい設計）
