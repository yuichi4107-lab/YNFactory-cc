---
name: post-sns
description: SNS（X / Instagram / Facebook / Threads）へ投稿する。テキスト・画像を指定して各プラットフォームに最適化した内容を投稿。対象SNSの指定も可能。
---

# SNS投稿スキル (post-sns)

## 概要

指定されたテキストや画像をSNSに投稿する。投稿先の指定がなければ全対応SNSに一括投稿する。各SNSの制約に合わせてコンテンツを自動調整する。

## 入力

- **投稿内容**（必須）: 投稿したいテキスト。テーマやキーワードだけでもOK。
- **画像パス**（任意）: 添付する画像ファイルのパス
- **投稿先**（任意）: `x` / `instagram` / `facebook` / `threads` / `all`（デフォルト: 対応済みの全SNS）

## 各SNSの制約

| SNS | テキスト上限 | 画像 | 備考 |
|-----|------------|------|------|
| X | 280文字 | 任意 | URLは23文字換算 |
| Instagram | 2,200文字 | 必須 | テキストのみ投稿不可 |
| Facebook | 63,206文字 | 任意 | |
| Threads | 500文字 | 任意 | |

## ワークフロー

### Step 1: コンテンツ準備

ユーザーの投稿内容を各SNS向けに調整する。

- ユーザーがテーマやキーワードだけ指定した場合は、投稿文を作成する
- 各SNSの文字数制限に合わせてバリエーションを作成する
- ハッシュタグを適切に付与する
- 投稿先が指定されていない場合は、対応済みの全SNSを対象とする

調整後の投稿内容をユーザーに確認してから投稿する。

### Step 2: X に投稿

投稿スクリプトを実行する：

```bash
cd "G:/マイドライブ/YNFactory-cc"
python scripts/post_to_x.py "投稿テキスト"
```

画像付きの場合：

```bash
python scripts/post_to_x.py "投稿テキスト" --image "画像パス"
```

投稿成功したらURLを記録する。

### Step 3: Instagram に投稿（Phase 2で実装予定）

Meta Graph API経由で投稿する。

```bash
python scripts/post_to_meta.py instagram "キャプション" --image "画像パス"
```

### Step 4: Facebook に投稿（Phase 2で実装予定）

```bash
python scripts/post_to_meta.py facebook "投稿テキスト" [--image "画像パス"]
```

### Step 5: Threads に投稿（Phase 2で実装予定）

```bash
python scripts/post_to_meta.py threads "投稿テキスト" [--image "画像パス"]
```

### Step 6: 結果報告

全投稿の結果を一覧で報告する：

```
投稿結果:
- X: https://x.com/i/status/xxxxx
- Instagram: （Phase 2で対応）
- Facebook: （Phase 2で対応）
- Threads: （Phase 2で対応）
```

## 対応状況

- [x] X（対応済み）
- [ ] Instagram（Phase 2）
- [ ] Facebook（Phase 2）
- [ ] Threads（Phase 2）

## ファイル構成

- 認証情報: `G:/マイドライブ/YNFactory-cc/.company/engineering/sns-credentials/.env`
- X投稿スクリプト: `G:/マイドライブ/YNFactory-cc/scripts/post_to_x.py`
- Meta投稿スクリプト: `G:/マイドライブ/YNFactory-cc/scripts/post_to_meta.py`（Phase 2で作成）
