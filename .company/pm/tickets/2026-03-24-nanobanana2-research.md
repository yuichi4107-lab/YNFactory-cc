---
created: "2026-03-24"
project: "nanobanana2-image-gen-skill"
assignee: "research"
priority: high
status: done
goal_type: "仕組み"
milestone: "MS1"
depends_on: []
blocks: ["2026-03-24-nanobanana2-skill-impl"]
---

# NanoBanana2 API仕様調査

## ゴール
- **種別**: 仕組み（スキルの前提調査）
- **概要**: Google AI Studio APIでNanoBanana2（Gemini画像生成）を呼び出すための仕様を調査する

## 担当部署
- **部署**: リサーチ
- **振り分け元**: ceo/decisions/2026-03-24-nanobanana2-image-gen-skill.md

## 完了条件
- [x] エンドポイントURL特定
- [x] 認証方法（APIキーの渡し方）
- [x] リクエスト形式（JSON構造、モデル名）
- [x] レスポンス形式（画像データの取得方法、base64等）
- [x] 画像保存に必要な処理

## 成果物の保存先
- research/topics/nanobanana2-api.md

## 承認ポイント
- [ ] MS1: 調査結果をオーナーに共有し、実装方針を承認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-03-24 | open | チケット作成 |
| 2026-03-24 | done | API仕様調査完了。エンドポイント、認証、リクエスト/レスポンス形式、画像保存処理、サンプルコード（Python/curl）を調査し research/topics/nanobanana2-api.md に保存 |

## メモ
- APIキー: 環境変数 GOOGLE_AI_STUDIO_API_KEY に設定済み
