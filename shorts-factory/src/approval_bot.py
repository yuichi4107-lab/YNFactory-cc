"""Telegram承認デーモン。

- queue の ready_for_review を検知 → 動画プレビュー+承認ボタンを送信
- ボタン押下（callback_query）を getUpdates ロングポーリングで受信
    ✅承認 → approved へ遷移 → 有効媒体へ投稿 → posted/failed
    ❌却下 → skipped
    ⏸保留 → そのまま（ボタンは残る）
- approved（auto_post含む）を検知 → 投稿実行

launchd（com.ynfactory.shorts-approval）で KeepAlive 常駐する。
"""
from __future__ import annotations

import atexit
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests

from .config import CONFIG
from . import notify, queue_lib
from .platforms import poster

LOCK_FILE = CONFIG.runtime_dir / "approval_bot.pid"
QUEUE_SCAN_INTERVAL = 30


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(CONFIG.logs_dir / "approval_bot.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _acquire_lock() -> None:
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            os.kill(pid, 0)
            raise SystemExit(f"approval_bot は既に稼働中です (pid={pid})")
        except (ValueError, ProcessLookupError, PermissionError):
            pass  # 死んだロック
    LOCK_FILE.write_text(str(os.getpid()))
    atexit.register(lambda: LOCK_FILE.unlink(missing_ok=True))


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{CONFIG.telegram_token}/{method}"


def _answer_callback(cb_id: str, text: str) -> None:
    requests.post(
        _api("answerCallbackQuery"),
        data={"callback_query_id": cb_id, "text": text[:190]},
        timeout=15,
    )


def _remove_buttons(message_id: int) -> None:
    requests.post(
        _api("editMessageReplyMarkup"),
        data={
            "chat_id": CONFIG.telegram_chat_id,
            "message_id": message_id,
            "reply_markup": json.dumps({"inline_keyboard": []}),
        },
        timeout=15,
    )


def scan_queue() -> None:
    """未送信プレビューの送付と、approved の投稿実行。"""
    for item in queue_lib.list_items("ready_for_review"):
        if not item.get("telegram", {}).get("message_id"):
            mid = notify.send_video(
                Path(item["video"]["path"]),
                notify.preview_caption(item),
                reply_markup=notify.approval_keyboard(item["id"]),
            )
            if mid:
                item["telegram"]["message_id"] = mid
                queue_lib.save_item(item)
                log(f"プレビュー送信: {item['id']}")

    for item in queue_lib.list_items("approved"):
        log(f"投稿実行: {item['id']}")
        item = poster.post_item(item, queue_lib, notify)
        log(f"投稿完了: {item['id']} → {item['status']}")


def handle_callback(cb: dict) -> None:
    data = cb.get("data", "")
    cb_id = cb["id"]
    msg = cb.get("message", {})
    if ":" not in data:
        _answer_callback(cb_id, "不明な操作")
        return
    action, item_id = data.split(":", 1)
    try:
        item = queue_lib.load_item(item_id)
    except FileNotFoundError:
        _answer_callback(cb_id, "対象が見つかりません")
        return

    if item["status"] not in ("ready_for_review", "blocked"):
        _answer_callback(cb_id, f"既に処理済み（{item['status']}）")
        return

    if action == "approve":
        item["review"].update(
            {"owner_approved": True, "decided_at": datetime.now().isoformat(), "via": "telegram"}
        )
        queue_lib.transition(item, "approved", "Telegramで承認")
        _answer_callback(cb_id, "承認しました。投稿します…")
        if msg.get("message_id"):
            _remove_buttons(msg["message_id"])
        log(f"承認: {item_id}")
        item = poster.post_item(item, queue_lib, notify)
        log(f"投稿完了: {item_id} → {item['status']}")
    elif action == "reject":
        item["review"].update(
            {"owner_approved": False, "decided_at": datetime.now().isoformat(), "via": "telegram"}
        )
        queue_lib.transition(item, "skipped", "Telegramで却下")
        _answer_callback(cb_id, "却下しました")
        if msg.get("message_id"):
            _remove_buttons(msg["message_id"])
        log(f"却下: {item_id}")
    elif action == "hold":
        _answer_callback(cb_id, "保留しました。ボタンはそのまま使えます")
        log(f"保留: {item_id}")
    else:
        _answer_callback(cb_id, "不明な操作")


def main() -> None:
    if not notify.enabled():
        raise SystemExit("Telegram設定がありません（secrets.yaml を確認）")
    _acquire_lock()
    log("approval_bot 起動")
    offset = 0
    last_scan = 0.0
    while True:
        try:
            if time.time() - last_scan > QUEUE_SCAN_INTERVAL:
                scan_queue()
                last_scan = time.time()
            r = requests.get(
                _api("getUpdates"),
                params={"offset": offset, "timeout": 25, "allowed_updates": '["callback_query"]'},
                timeout=35,
            )
            if not r.ok:
                if r.status_code == 409:
                    log("⚠️ getUpdates 409: 別プロセスがこのbotをポーリング中。60秒待機")
                    time.sleep(60)
                continue
            for upd in r.json().get("result", []):
                offset = max(offset, upd["update_id"] + 1)
                if "callback_query" in upd:
                    handle_callback(upd["callback_query"])
        except KeyboardInterrupt:
            log("停止")
            break
        except Exception as e:  # デーモンは死なない
            log(f"エラー: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
