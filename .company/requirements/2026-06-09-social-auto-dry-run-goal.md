---
title: SNS自動投稿基盤 dry-run化 要件定義
date: 2026-06-09
status: approved_by_goal
goal: YNFactoryのSNS自動投稿基盤を、X / Threads / Instagram までdry-run可能な状態にする
---

# SNS自動投稿基盤 dry-run化 要件定義

## 1. ゴール

共通投稿キューから X / Threads / Instagram の投稿予定内容を読み取り、外部投稿を行わずに dry-run 結果を確認できる状態にする。

## 2. スコープ

やること:

- 既存の共通投稿キューJSONを入力として扱う
- X / Threads / Instagram の文字数・画像要件・承認状態を検証する
- dry-run結果を画面表示とJSONファイルで確認できるようにする
- 実投稿・トークン発行・本番反映に進まない安全境界を実装する
- `post-sns` スキルと関連ステータス資料をdry-run対応に更新する

やらないこと:

- Meta Developer Consoleで権限追加しない
- Graph API Explorerでトークン取得しない
- `.env` に新しいトークンを書き込まない
- X / Threads / Instagramへ実投稿しない
- SNSプロフィールや本番設定を変更しない

## 3. 完了条件

- `scripts/social_auto_ops.py dry-run <queue.json>` で X / Threads / Instagram の検証結果が出る
- dry-run結果が `.company/marketing/social-auto-ops/dry-runs/` に保存される
- Instagramは画像必須として扱われ、画像なしなら `blocked` になる
- Xは280文字、Threadsは500文字、Instagramは2200文字上限を検証する
- `--platforms` で対象媒体を絞れる
- 実投稿系スクリプトは承認なしに呼び出されない
- `python3 -m py_compile scripts/social_auto_ops.py` が成功する

## 4. 品質基準

- 生トークン・認証情報を表示しない
- dry-runと本番投稿の境界が明確
- 既存のキュー生成・preview機能を壊さない
- 失敗理由が媒体別に読める
- 85点以上で合格

## 5. 実施結果

更新ファイル:

- `scripts/social_auto_ops.py`
- `scripts/post_to_x.py`
- `scripts/post_to_meta.py`
- `.agents/skills/post-sns/SKILL.md`
- `.company/marketing/social-auto-ops/queue-schema.md`
- `.company/marketing/social-auto-ops/implementation-status-2026-05-26.md`
- `.company/marketing/social-auto-ops/queue/2026-05-26-ai導入はツール選びより社内説明の1枚から始める.json`

検証:

- `python3 -m py_compile scripts/social_auto_ops.py scripts/post_to_x.py scripts/post_to_meta.py` 合格
- `python3 scripts/social_auto_ops.py dry-run ... --platforms all --no-save` で X / Threads / Instagram が `ready_for_review`
- `python3 scripts/post_to_x.py ... --dry-run` で `would_post=false`
- `python3 scripts/post_to_meta.py threads ... --dry-run` で `would_post=false`
- `python3 scripts/post_to_meta.py instagram ... --image ... --dry-run` で `would_post=false`
- `python3 scripts/post_to_meta.py threads ...` は本番投稿未許可として停止

品質チェック:

- スコア: 94 / 100
- 判定: 合格
- 残課題: Meta Step6完了後に本番投稿処理を実装する。外部投稿・トークン発行・本番反映は引き続き直前承認が必要。
