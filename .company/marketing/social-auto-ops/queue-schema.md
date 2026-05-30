---
title: AI集中版 共通投稿キュー仕様
created: 2026-05-26
status: draft
---

# AI集中版 共通投稿キュー仕様

## 1. 目的

1つのAI活用・AI導入コンテンツ企画から、note、X、Threads、Instagramへ展開するための共通キューを定義する。

初期版は実投稿前のdry-runと承認確認を重視する。

## 2. 保存場所

```text
.company/marketing/social-auto-ops/queue/
```

1企画につき1つのJSONファイルを保存する。

ファイル名:

```text
YYYY-MM-DD_slug.json
```

## 3. ステータス

| status | 意味 |
|---|---|
| draft | 作成中 |
| ready_for_review | 投稿前確認待ち |
| approved | 投稿承認済み |
| posted | 投稿済み |
| failed | 投稿失敗 |
| skipped | 意図的に投稿しない |
| blocked | ログイン・権限・画像など外部要因で停止 |

## 4. 媒体別フィールド

### note

- title
- body_path
- note_account_id
- note_url
- status
- draft_url
- cta_lp_url

### x

- text
- image_path
- status
- post_url
- target
  - note
  - lp_profile

### threads

- text
- image_path
- status
- post_url
- target
  - note
  - lp_profile

### instagram

- caption
- image_path
- status
- post_url
- target
  - note
  - lp_profile

## 5. 最小JSON例

```json
{
  "id": "2026-05-26-ai-decision-line",
  "created_at": "2026-05-26T09:00:00+09:00",
  "campaign": {
    "theme": "AI導入",
    "product": "AI活用・AI導入支援",
    "lp_url": "",
    "primary_goal": "相談・資料請求・申し込み"
  },
  "source": {
    "title": "AIに渡す仕事は、先に決裁ラインを決めるとうまくいく",
    "angle": "AI導入で現場が止まる原因を、決裁ラインから説明する",
    "note_account_id": "you-ai-dx"
  },
  "platforms": {
    "note": {
      "status": "draft",
      "title": "",
      "body_path": "",
      "draft_url": null,
      "cta_lp_url": ""
    },
    "x": {
      "status": "draft",
      "text": "",
      "image_path": null,
      "post_url": null,
      "target": "note"
    },
    "threads": {
      "status": "draft",
      "text": "",
      "image_path": null,
      "post_url": null,
      "target": "note"
    },
    "instagram": {
      "status": "draft",
      "caption": "",
      "image_path": null,
      "post_url": null,
      "target": "note"
    }
  },
  "review": {
    "owner_approved": false,
    "quality_score": null,
    "notes": []
  }
}
```

## 6. 実装方針

- 初期版では、投稿キュー生成とdry-run確認までをローカルで行う。
- Xは既存 `scripts/post_to_x.py` を後続で呼び出す。
- Threads / InstagramはMeta Step6完了後に `scripts/post_to_meta.py` を実装して接続する。
- noteは既存noteワークフローを使い、AIアカウントの下書き保存までを基本にする。
