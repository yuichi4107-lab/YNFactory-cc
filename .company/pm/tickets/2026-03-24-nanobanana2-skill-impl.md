---
created: "2026-03-24"
project: "nanobanana2-image-gen-skill"
assignee: "engineering"
priority: high
status: done
goal_type: "仕組み"
milestone: "完了"
depends_on: ["2026-03-24-nanobanana2-research"]
blocks: []
---

# NanoBanana2 画像生成スキル実装

## ゴール
- **種別**: 仕組み（スキル）
- **概要**: 調査結果をもとに、プロンプト→API呼出→画像保存のスキルを実装する

## 担当部署
- **部署**: 開発
- **振り分け元**: ceo/decisions/2026-03-24-nanobanana2-image-gen-skill.md

## 完了条件
- [x] `.claude/skills/nanobanana2-image-gen/SKILL.md` 作成
- [x] プロンプトを受け取りAPI呼び出し→画像保存のフロー実装
- [x] 保存先: `.company/outputs/{指定フォルダ}/`
- [x] APIキーは環境変数 GOOGLE_AI_STUDIO_API_KEY から取得
- [x] 動作確認

## 成果物の保存先
- .claude/skills/nanobanana2-image-gen/SKILL.md

## 承認ポイント
- [ ] 完了: スキル動作確認でオーナー承認

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-03-24 | open | チケット作成（リサーチ完了待ち） |
| 2026-03-24 | done | SKILL.md作成完了。google-genai SDK使用、プロンプト→API呼出→PNG保存のフロー実装。エラーハンドリング・将来拡張考慮済み。 |

## メモ
- 将来拡張: 複数枚生成、サイズ指定
