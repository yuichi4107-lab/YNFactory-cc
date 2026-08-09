---
date: "2026-04-09"
decision: "FX自動売買プロジェクト開始"
departments: [engineering, research, pm]
status: decided
---

# 意思決定: FX自動売買プロジェクト開始

## 背景
オーナーが次の投資戦略としてFX自動売買を検討。既存のAI投資システム（ai-trade-system）の暗号資産自動売買が本番稼働中（Coincheck BTC/JPY）で、この基盤を拡張してFXに対応する方針。初期資金10万円。

## 判断内容
- **ブローカー**: OANDA Japan（REST API v20、1通貨単位取引可、デモ口座あり）
- **通貨ペア**: USD/JPY（メイン）、EUR/JPY（サブ）
- **戦略**: 3段階導入（Phase1: MA+RSI → Phase2: AI転用 → Phase3: ハイブリッド）
- **リスク管理**: 最大DD 20%（2万円）ハードストップ、1トレード1,000通貨
- **実装方針**: 既存ai-trade-systemにOandaClientを追加（ccxt非対応のためhttpx直接呼出し）
- **税制**: 国内FX = 申告分離課税20.315%（暗号資産の雑所得より有利）

## 振り分け先
| 部署 | 指示内容 |
|------|---------|
| リサーチ | FXブローカー・戦略調査 → **完了** |
| 開発 | OANDAアダプター実装、AutoTrader統合、バックテスト |
| PM | MS1-4のチケット管理 |

## マイルストーン
- MS1: OANDA接続 + OANDAアダプター実装
- MS2: Phase1戦略バックテスト（USD/JPY）
- MS3: デモ口座フォワードテスト（1-2週間）
- MS4: 本番口座運用開始（10万円）

## 理由
- 既存のai-trade-systemのコードベース（シグナル検出、AI判定、通知、シミュレーション）を最大限再利用できる
- OANDAは1通貨単位で10万円の少額運用に最適
- FXの税制（申告分離20.315%、3年繰越控除）は暗号資産より有利
- 暗号資産とFXの分散投資になる

## フォローアップ
- [x] リサーチ完了
- [x] OANDAアダプター実装（oanda_client.py）
- [x] trader.py / scanner.py のOANDA対応
- [x] strategy_config.json にFXペア追加
- [ ] OANDA デモ口座開設（オーナー手動）
- [ ] デモ口座でAPI接続テスト
- [ ] MS2: バックテスト実行
