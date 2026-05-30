# 無料AI導入診断 LP 公開メモ

更新日: 2026-05-28

## 公開状態

- Cloudflare Pages project: `ynfactory-ai-lp`
- 公開URL: https://ynfactory-ai-lp.pages.dev/
- 独自ドメイン: https://ai.yn-factory.com/
- Custom domain登録: Cloudflare Pages側に追加済み
- DNS設定: Squarespace Domains側にCNAME追加済み
- 独自ドメイン状態: Cloudflare Pages側で `active`

## DNSに追加するレコード

現在の `yn-factory.com` は Cloudflare DNS ではなく、Squarespace Domains / Google系ネームサーバーで管理されています。

| Type | Host / Name | Value / Target | TTL |
|---|---|---|---|
| CNAME | `ai` | `ynfactory-ai-lp.pages.dev` | 4時間 |

2026-05-28 20:57 JST時点で、外部DNSは `ai.yn-factory.com -> ynfactory-ai-lp.pages.dev` を返し、Cloudflare Pages側の `status` / `validation` / `verification` はすべて `active`。HTTPSでLP表示確認済み。

## LP内容

- CTAはGoogleフォームに接続済み
- 横幅いっぱいの区切り画像帯を3か所配置
- canonical / OGP は `https://ai.yn-factory.com/` 前提
- 離脱防止ポップアップを追加済み
  - PC: 画面上部から離脱しようとした時に表示
  - スマホ: ページを一定量読んだ後に表示
  - 同じ閲覧中に閉じた場合は再表示しない
  - CTAはGoogleフォームへ遷移

## デプロイ履歴

- 2026-05-28: Cloudflare Pagesへ初回公開
- 2026-05-28: 離脱防止ポップアップを追加して再デプロイ
  - Deployment URL: https://c3ddd1c3.ynfactory-ai-lp.pages.dev
