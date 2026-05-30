---
title: AI集中版 SNS自動運用 現状棚卸し
created: 2026-05-26
status: completed
phase: 1
---

# AI集中版 SNS自動運用 現状棚卸し

## 1. 対象方針

今回の初期運用では、note 5アカウント運用はいったん保留し、AI活用・AI導入商材に集中する。

対象媒体:

- note
- X
- Threads
- Instagram
- LP

主導線:

```text
X / Threads / Instagram
  -> note
  -> LP
  -> 相談・資料請求・申し込み
```

補助導線:

```text
X / Threads / Instagram プロフィール
  -> LP
```

## 2. noteアカウント

対象はAIアカウントのみ。

| 項目 | 内容 |
|---|---|
| account_id | you-ai-dx |
| slug | ai |
| note URL | https://note.com/you_ai_dx |
| note ID | you_ai_dx |
| ブラウザプロファイル | note-ai |
| テーマ | ai-utilization |
| 表示名案 | 仕事で使うAI活用メモ |
| 基本トーン | 専門用語を増やしすぎず、具体例と小さな行動に落として伝える |
| 文字数目安 | 3500〜5000字 |
| 標準タグ | AI活用 / 生成AI / DX / 業務効率化 / ChatGPT |

保留対象:

- money
- career
- spiritual
- love

これら4テーマは、今回のAI導入集客導線には含めない。

## 3. note履歴から見た直近テーマ

AIアカウントの直近テーマは以下。

- Claudeに任せて気づいた、人間が残すべき仕事の境界線
- AI導入は、ツール選びより「社内説明の1枚」から始める
- AIに渡す仕事は、先に「決裁ライン」を決めるとうまくいく
- 社内でAIエージェントを導入して失敗した3つ
- プロンプトに前提を書きすぎて精度が落ちた話
- AIに英語メール下書きを任せるときの最低限のチェック
- ChatGPTで提案書骨子を5分で作る手順
- 営業ロープレ相手にClaudeを使った1週間

今後は、既存の「業務で使うAI活用」路線を保ちつつ、LP申込につながる以下の切り口を増やす。

- AI導入で何から始めるか
- 中小企業・個人事業主の業務効率化
- 社内説明、決裁、定着、運用ルール
- 投稿作成、資料作成、営業支援、問い合わせ対応
- AI導入の失敗例と立て直し方

## 4. X

現状:

- `scripts/post_to_x.py` が存在する。
- `.company/engineering/sns-credentials/.env` にX認証情報が設定済み。
- 画像付き投稿にも対応している。

初期運用:

- 1日2〜3投稿。
- note記事への誘導を主目的にする。
- プロフィール欄にはLP URLを掲載する。
- 投稿文は280文字以内で、問題提起・気づき・短い事例を中心にする。

実装上の注意:

- 既存スクリプトを壊さない。
- dry-runを先に共通化する。
- 投稿済みURLをログに残す。

## 5. Threads

現状:

- Meta Step6が未完了。
- Threads投稿用の本番トークンは未設定。
- `tools/x-threads-auto-post/` にGAS経由の設計資産がある。

初期運用:

- 1日1〜2投稿。
- Xより少し長く、体験談・考え方・チェックリストを投稿する。
- noteへの誘導を主目的にする。
- プロフィール欄にはLP URLを掲載する。

実装上の注意:

- Meta権限 `threads_basic` / `threads_content_publish` が必要。
- 初期はテキスト投稿を優先する。
- 画像付き投稿はInstagram側が安定してから広げる。

## 6. Instagram

現状:

- Meta Step6が未完了。
- IG Business Account IDは既存手順書上で `17841477801881765` と記録されている。
- 投稿用トークンは未設定。

初期運用:

- 週3投稿から開始し、慣れたら週5投稿へ増やす。
- 図解・カルーセル・短尺動画の入口として使う。
- noteまたはプロフィールLPへ誘導する。
- プロフィール欄にはLP URLを掲載する。

実装上の注意:

- Instagramは画像必須として扱う。
- Meta Graph API経由では画像URLの扱いが必要になる可能性が高い。
- 初期は画像1枚投稿を優先し、カルーセルやリールは後続にする。

## 7. LP

現状:

- Google Sites公開URL: https://sites.google.com/yn-factory.com/ai-lp
- 独自ドメイン候補: https://ai.yn-factory.com
- `https://ai.yn-factory.com` は2026-05-28 18:53 JST時点では名前解決不可。接続完了まではGoogle Sites公開URLを使用する。
- プロフィール欄に掲載するURLとして全媒体で使う。

初期運用:

- note記事末尾からLPへ誘導する。
- X / Threads / Instagramのプロフィール欄にもLP URLを掲載する。
- 投稿本文では押し売りにせず、詳しい相談先として自然に案内する。

必要情報:

- LP URL
- 申し込み種別
  - 無料相談
  - 資料請求
  - 導入診断
  - 個別見積もり
- 主な対象者
  - 個人事業主
  - 中小企業
  - 社内担当者
  - 経営者

## 8. 外部ブロッカー

現時点で実投稿まで進むために必要な外部作業:

1. Meta Developer Consoleで権限追加
2. Graph API ExplorerでMetaトークン取得
3. `.company/engineering/sns-credentials/.env` にMeta系キーを追加
4. `ai.yn-factory.com` のDNS / Google SitesカスタムURL接続
5. X / Threads / Instagramプロフィール欄へのLP URL掲載

## 9. 工程1 品質チェック

| 項目 | 判定 |
|---|---|
| AI集中方針が明確 | OK |
| 保留対象4テーマが明確 | OK |
| note / X / Meta / GAS の状態を分離 | OK |
| 生トークン非表示 | OK |
| 次工程のブロッカー明確化 | OK |

自己採点: 92 / 100

工程1は合格。
