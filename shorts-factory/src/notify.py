"""Telegram通知（プレビュー送付・承認ボタン・運用アラート）。"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from .config import CONFIG


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{CONFIG.telegram_token}/{method}"


def enabled() -> bool:
    return bool(
        CONFIG.get("telegram", "enabled", default=True)
        and CONFIG.telegram_token
        and CONFIG.telegram_chat_id
    )


def send_message(text: str, reply_markup: dict | None = None) -> int | None:
    if not enabled():
        return None
    payload: dict = {
        "chat_id": CONFIG.telegram_chat_id,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    r = requests.post(_api("sendMessage"), data=payload, timeout=30)
    if r.ok:
        return r.json().get("result", {}).get("message_id")
    return None


def send_video(
    video_path: Path, caption: str, reply_markup: dict | None = None
) -> int | None:
    if not enabled():
        return None
    payload: dict = {
        "chat_id": CONFIG.telegram_chat_id,
        "caption": caption[:1000],
        "parse_mode": "HTML",
        "supports_streaming": True,
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    with open(video_path, "rb") as f:
        r = requests.post(
            _api("sendVideo"), data=payload, files={"video": f}, timeout=300
        )
    if r.ok:
        return r.json().get("result", {}).get("message_id")
    # 動画が大きい等で失敗したらテキストにフォールバック
    return send_message(caption + "\n（動画の送信に失敗。Driveで確認してください）", reply_markup)


def approval_keyboard(item_id: str) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ 承認して投稿", "callback_data": f"approve:{item_id}"},
                {"text": "❌ 却下", "callback_data": f"reject:{item_id}"},
            ],
            [{"text": "⏸ 保留（また後で）", "callback_data": f"hold:{item_id}"}],
        ]
    }


def preview_caption(item: dict) -> str:
    q = item.get("quality", {})
    plats = [p for p, v in item.get("platforms", {}).items() if v.get("enabled")]
    return (
        f"🎬 <b>{item['title']}</b>\n"
        f"id: {item['id']}\n"
        f"尺: {item['video']['duration']}s / {item['video']['size_mb']}MB\n"
        f"字幕検証: {'✅PASS' if q.get('pass') else '⚠️FAIL'} (平均CER {q.get('avg_cer')})\n"
        f"投稿先: {', '.join(plats) or 'なし'}\n\n"
        f"{item['caption'][:300]}\n"
        f"{' '.join(item['hashtags'][:6])}"
    )
