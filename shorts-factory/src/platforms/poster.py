"""各SNSへの投稿ディスパッチャ。

既存の scripts/post_to_x.py 等を venv の python でサブプロセス実行する
（既存スクリプトの .env 読み込み・認証ロジックをそのまま活かす）。
"""
from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from ..config import CONFIG

SCRIPTS_DIR = CONFIG.repo_root / "scripts"
PYTHON = str(CONFIG.runtime_dir / ".venv" / "bin" / "python")


def _x_text(item: dict, limit: int = 270) -> str:
    """X用の投稿文を280字制限内で組み立てる。"""

    def width(s: str) -> int:  # Xは全角2/半角1の重み（280=全角140）
        return sum(2 if unicodedata.east_asian_width(c) in ("F", "W", "A") else 1 for c in s)

    tags = " ".join(item["hashtags"][:4])
    title = item["title"]
    body = item["caption"].strip()
    text = f"{title}\n\n{body}\n\n{tags}"
    while width(text) > limit and len(body) > 20:
        body = body[: max(20, len(body) - 10)].rstrip() + "…"
        text = f"{title}\n\n{body}\n\n{tags}"
    if width(text) > limit:
        text = f"{title}\n\n{tags}"
    return text


def post_x(item: dict) -> str:
    """Xへ動画投稿し、投稿URLを返す。"""
    text = _x_text(item)
    proc = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / "post_to_x.py"), text, "--video", item["video"]["path"]],
        capture_output=True,
        text=True,
        timeout=600,
    )
    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise RuntimeError(f"X投稿失敗: {out[-400:]}")
    m = re.search(r"Posted:\s*(\S+)", out)
    if not m:
        raise RuntimeError(f"X投稿のURLが取得できません: {out[-300:]}")
    return m.group(1)


def post_instagram(item: dict) -> str:
    """Instagram Reels へ投稿し、permalink を返す。

    --publish-approved は Telegram承認（または auto_post 設定）を経た
    キューからのみ呼ばれるため、オーナー承認済みとして付与する。
    """
    import json

    caption = item["caption"].strip() + "\n\n" + " ".join(item["hashtags"][:8])
    proc = subprocess.run(
        [
            PYTHON, str(SCRIPTS_DIR / "post_to_meta.py"),
            "instagram-reels", caption,
            "--video", item["video"]["path"],
            "--publish-approved",
        ],
        capture_output=True,
        text=True,
        timeout=1800,
    )
    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise RuntimeError(f"IG Reels投稿失敗: {out[-400:]}")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"IG Reels出力のパース失敗: {out[-300:]}")
    if result.get("status") != "posted":
        raise RuntimeError(f"IG Reels投稿失敗: {result.get('error', result)}")
    return result.get("permalink") or f"media_id:{result.get('id')}"


def post_youtube(item: dict) -> str:
    """YouTube Shorts へCDP経由でアップロードし、動画URLを返す。"""
    from . import youtube_cdp

    description = (
        item["caption"].strip()
        + "\n\n"
        + " ".join(item["hashtags"][:6])
        + f"\n\n{CONFIG.get('speaker_credit')}\n音声・映像はAIで自動生成しています"
    )
    return youtube_cdp.upload(
        video_path=Path(item["video"]["path"]),
        title=item["title"][:95],
        description=description,
    )


def post_tiktok(item: dict) -> str:
    from . import tiktok_cdp

    caption = item["title"] + " " + " ".join(item["hashtags"][:5])
    return tiktok_cdp.upload(Path(item["video"]["path"]), caption)


POSTERS = {
    "x": post_x,
    "instagram": post_instagram,
    "youtube": post_youtube,
    "tiktok": post_tiktok,
}


def post_item(item: dict, queue_lib, notify) -> dict:
    """有効な全プラットフォームへ投稿し、結果を item に記録して返す。"""
    results = []
    for platform, info in item["platforms"].items():
        if not info.get("enabled") or info.get("status") == "posted":
            continue
        try:
            url = POSTERS[platform](item)
            item = queue_lib.mark_platform(item, platform, "posted", url=url)
            results.append(f"✅ {platform}: {url}")
        except Exception as e:  # 1媒体の失敗で他媒体を止めない
            item = queue_lib.mark_platform(item, platform, "failed", error=str(e))
            results.append(f"❌ {platform}: {str(e)[:120]}")

    statuses = [v["status"] for v in item["platforms"].values() if v.get("enabled")]
    if statuses and all(s == "posted" for s in statuses):
        item = queue_lib.transition(item, "posted", "全媒体投稿完了")
    elif any(s == "posted" for s in statuses):
        item = queue_lib.transition(item, "posted", "一部媒体のみ投稿成功")
    else:
        item = queue_lib.transition(item, "failed", "全媒体投稿失敗")

    notify.send_message(
        f"📤 <b>{item['title']}</b> 投稿結果\n" + "\n".join(results)
    )
    return item
