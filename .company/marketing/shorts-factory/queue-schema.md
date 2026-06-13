# shorts-factory 投稿キュー仕様

場所: `.company/marketing/shorts-factory/queue/{id}.json`（id = `YYYY-MM-DD_slug`）
書き込みは atomic rename・**Macのみが書き込む**（他端末は読み取りのみ）。

## ステータス遷移（social-auto-ops 準拠）

```
draft → ready_for_review → approved → posted
                         → skipped（却下）
        blocked（品質不合格・全媒体失敗等、人間の介入待ち）
        failed（投稿失敗）
```

- 生成パイプラインが品質検証**合格**時に `ready_for_review`（auto_post=true なら直接 `approved`）
- 品質検証**不合格**（修正ループ上限到達）時は `blocked` ＋ Telegram通知
- 承認デーモン（approval_bot）が Telegram ボタンで `approved`/`skipped` へ遷移させ、`approved` を検知して投稿する

## フィールド

| キー | 内容 |
|---|---|
| `id` | `YYYY-MM-DD_slug` |
| `topic` / `title` / `caption` / `hashtags` | 台本由来のメタ |
| `video.path` / `video.duration` / `video.size_mb` | 完成動画（`.company/outputs/shorts-factory/{id}/final.mp4`） |
| `quality.pass` / `quality.avg_cer` / `quality.report_path` | 機械検証の結果 |
| `review.owner_approved` / `decided_at` / `via` | 承認記録（telegram / auto_post） |
| `telegram.message_id` | プレビュー送信済みメッセージ |
| `platforms.{x,youtube,instagram,tiktok}` | `{enabled, status, url, error, posted_at}` |
| `history[]` | `{ts, event}` の監査ログ |

## 関連ファイル

- ネタ帳: `topics.json`（backlog から1日1本消費。残り7本以下でTelegram補充アラート）
- 成果物: `.company/outputs/shorts-factory/{id}/`（final.mp4, script.json, subtitles.ass, quality_report.json, captions.md, images/, preview_*.jpg）
