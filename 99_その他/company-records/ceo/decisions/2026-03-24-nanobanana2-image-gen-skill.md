---
date: "2026-03-24"
type: decision
---

# NanoBanana2 画像生成スキル作成

## ゴール
- 種別: 仕組み（スキル）
- Google AI Studio API経由でNanoBanana2を呼び出す画像生成スキル
- 完了条件: `/スキル名` でプロンプト → 画像生成 → outputs/に保存

## 振り分け計画
| # | 部署 | 担当内容 | 依存 | 成果物 |
|---|------|---------|------|--------|
| 1 | リサーチ | API仕様調査 | なし | research/topics/nanobanana2-api.md |
| 2 | 開発 | スキル実装 | #1完了後 | .claude/skills/nanobanana2-image-gen/SKILL.md |

## マイルストーン
- MS1: リサーチ完了 → API仕様共有・実装方針承認
- 完了: スキル動作確認

## 承認
- ゴール確認: 2026-03-24 承認済み
- 振り分け計画: 2026-03-24 承認済み
