#!/usr/bin/env python3
"""Create and preview AI-focused social posting queue items."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
QUEUE_DIR = ROOT / ".company" / "marketing" / "social-auto-ops" / "queue"


@dataclass
class CampaignInput:
    title: str
    angle: str
    lp_url: str
    note_url: str


def slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u3040-\u30ff\u3400-\u9fff]+", "-", text)
    normalized = normalized.strip("-").lower()
    return normalized[:60] or "ai-campaign"


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def build_texts(data: CampaignInput) -> dict:
    note_target = data.note_url or "note"
    lp_target = data.lp_url or "プロフィールのリンク"

    x_text = (
        f"AI導入で大事なのは、ツール選びの前に「どの仕事をAIに任せるか」を決めることです。\n\n"
        f"{data.angle}\n\n"
        f"詳しくは{note_target}で整理します。"
    )

    threads_text = (
        f"{data.title}\n\n"
        "AI活用は、便利なツールを入れれば自然に広がるわけではありません。\n\n"
        "・どの業務で使うか\n"
        "・誰が最終判断するか\n"
        "・失敗したとき誰が直すか\n"
        "・社内でどう説明するか\n\n"
        f"このあたりを決めてから始めると、現場に定着しやすくなります。詳しくは{note_target}へ。"
    )

    instagram_caption = (
        f"{data.title}\n\n"
        "AI導入で最初に見るべきなのは、最新ツールの比較ではなく、現場で止まりやすいポイントです。\n\n"
        "1. 任せる業務を決める\n"
        "2. 人が判断する境界を決める\n"
        "3. 社内で説明できる形にする\n\n"
        f"詳しい考え方はnoteにまとめます。無料AI導入診断は{lp_target}からどうぞ。\n\n"
        "#AI活用 #生成AI #ChatGPT #業務効率化 #DX"
    )

    note_cta = (
        "AIを使ってみたいけれど、自社のどの業務から始めればいいか分からない。\n"
        "ツールは触っているけれど、社内での使い方やルールづくりで止まっている。\n\n"
        "そんな場合は、まず「最初にAI化する1業務」を決めるところから始めるのがおすすめです。"
        f"無料AI導入診断では、現在の業務を整理し、AI化しやすい業務と人が判断すべき業務を一緒に切り分けます。詳細は {lp_target} から確認できます。"
    )

    return {
        "x": truncate(x_text, 280),
        "threads": truncate(threads_text, 500),
        "instagram": truncate(instagram_caption, 2200),
        "note_cta": note_cta,
    }


def create_queue_item(data: CampaignInput) -> Path:
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    item_id = f"{now:%Y-%m-%d}-{slugify(data.title)}"
    texts = build_texts(data)

    item = {
        "id": item_id,
        "created_at": now.isoformat(),
        "campaign": {
            "theme": "AI活用・AI導入",
            "product": "AI活用・AI導入支援",
            "lp_url": data.lp_url,
            "primary_goal": "無料AI導入診断の申し込み",
        },
        "source": {
            "title": data.title,
            "angle": data.angle,
            "note_account_id": "you-ai-dx",
            "note_url": data.note_url,
        },
        "platforms": {
            "note": {
                "status": "draft",
                "title": data.title,
                "body_path": "",
                "draft_url": None,
                "cta_lp_url": data.lp_url,
                "cta_text": texts["note_cta"],
            },
            "x": {
                "status": "draft",
                "text": texts["x"],
                "image_path": None,
                "post_url": None,
                "target": "note",
            },
            "threads": {
                "status": "draft",
                "text": texts["threads"],
                "image_path": None,
                "post_url": None,
                "target": "note",
            },
            "instagram": {
                "status": "draft",
                "caption": texts["instagram"],
                "image_path": None,
                "post_url": None,
                "target": "note",
            },
        },
        "review": {
            "owner_approved": False,
            "quality_score": None,
            "notes": ["Initial AI-focused funnel queue item. Review before posting."],
        },
    }

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    out = QUEUE_DIR / f"{item_id}.json"
    out.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n")
    return out


def preview_queue_item(path: Path) -> str:
    item = json.loads(path.read_text())
    platforms = item["platforms"]
    sections = [
        f"ID: {item['id']}",
        f"Title: {item['source']['title']}",
        "",
        "[X]",
        platforms["x"]["text"],
        "",
        "[Threads]",
        platforms["threads"]["text"],
        "",
        "[Instagram]",
        platforms["instagram"]["caption"],
        "",
        "[note CTA]",
        platforms["note"]["cta_text"],
    ]
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and preview AI social posting queue items.")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a new queue item.")
    create.add_argument("--title", required=True)
    create.add_argument("--angle", required=True)
    create.add_argument("--lp-url", default="")
    create.add_argument("--note-url", default="")

    preview = sub.add_parser("preview", help="Preview an existing queue item.")
    preview.add_argument("path")

    args = parser.parse_args()
    if args.command == "create":
        path = create_queue_item(
            CampaignInput(
                title=args.title,
                angle=args.angle,
                lp_url=args.lp_url,
                note_url=args.note_url,
            )
        )
        print(path)
    elif args.command == "preview":
        print(preview_queue_item(Path(args.path)))


if __name__ == "__main__":
    main()
