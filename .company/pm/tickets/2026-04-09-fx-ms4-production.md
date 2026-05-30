---
created: "2026-04-09"
project: "fx-auto-trading"
assignee: "engineering"
priority: normal
status: open
goal_type: "仕組み"
milestone: "MS4"
depends_on: ["2026-04-09-fx-ms3-forward-test"]
blocks: []
---

# [FX] MS4: 本番口座運用開始

## ゴール
- **種別**: 仕組み
- **概要**: OANDA本番口座に10万円入金し、FX自動売買を本番稼働させる

## 担当部署
- **部署**: 開発部
- **振り分け元**: ceo/decisions/2026-04-09-fx-auto-trading.md

## 完了条件
- [ ] OANDA本番口座開設・10万円入金（オーナー手動）
- [ ] 本番用APIトークン取得・.env設定
- [ ] trader.py --exchange oanda で本番接続確認
- [ ] 小ロット（1,000通貨以下）で自動売買開始
- [ ] VPS Docker環境にFXデーモン追加デプロイ
- [ ] 安定稼働の確認

## 成果物の保存先
- VPS: `/opt/ai-trader/`

## 承認ポイント
- [ ] 本番稼働開始前にオーナー最終承認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-04-09 | open | チケット作成 |

## メモ
- レバレッジ実効5-10倍（25倍は使い切らない）
- 最大DD 20%（2万円）をハードリミットとして設定
- 暗号資産とは別のDockerコンテナ/プロセスで管理することを推奨
