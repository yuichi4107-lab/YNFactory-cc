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
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from .config import CONFIG
from . import notify, queue_lib
from .logging_utils import redact_secrets
from .platforms import poster

LOCK_FILE = CONFIG.runtime_dir / "approval_bot.pid"
QUEUE_SCAN_INTERVAL = 30
PENDING_REJECTIONS_DIR = CONFIG.marketing_dir / "pending_rejections"
PREVIEW_RETRY_DELAY = timedelta(minutes=10)


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%m-%d %H:%M:%S')}] {redact_secrets(msg, [CONFIG.telegram_token])}"
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
    try:
        requests.post(
            _api("answerCallbackQuery"),
            data={"callback_query_id": cb_id, "text": text[:190]},
            timeout=15,
        ).raise_for_status()
    except requests.RequestException as exc:
        log(f"Telegram callback応答失敗: {exc}")


def _remove_buttons(message_id: int) -> None:
    try:
        requests.post(
            _api("editMessageReplyMarkup"),
            data={
                "chat_id": CONFIG.telegram_chat_id,
                "message_id": message_id,
                "reply_markup": json.dumps({"inline_keyboard": []}),
            },
            timeout=15,
        ).raise_for_status()
    except requests.RequestException as exc:
        log(f"Telegramボタン削除失敗: {exc}")


def _pending_rejection_path(chat_id: str | int) -> Path:
    PENDING_REJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    return PENDING_REJECTIONS_DIR / f"{chat_id}.json"


def _set_pending_rejection(chat_id: str | int, item_id: str) -> None:
    _pending_rejection_path(chat_id).write_text(
        json.dumps(
            {"item_id": item_id, "created_at": datetime.now().isoformat()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _spawn_replacement(item: dict) -> None:
    """Rejected slots should get another candidate without requiring manual recovery."""
    difficulty = item.get("difficulty") or "intermediate"
    script = CONFIG.runtime_dir / "app" / "scripts" / "run_generate.sh"
    log_path = CONFIG.logs_dir / "replacement_generate.log"
    env = os.environ.copy()
    env["SHORTS_REPO_ROOT"] = str(CONFIG.repo_root)
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(
            f"\n[{datetime.now().isoformat()}] replacement_for={item['id']} difficulty={difficulty}\n"
        )
        try:
            subprocess.Popen(
                [str(script), "--difficulty", difficulty],
                cwd=str(CONFIG.runtime_dir / "app"),
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as exc:
            log(f"代替候補生成の起動失敗: {exc}")


def _preview_video_path(item: dict) -> Path:
    """Prefer the runtime copy for Telegram previews to avoid Drive read locks."""
    video_path = Path(item["video"]["path"])
    output_dir = item.get("output_dir")
    if output_dir:
        runtime_path = CONFIG.work_dir / Path(output_dir).name / video_path.name
        if runtime_path.exists():
            return runtime_path
    return video_path


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _preview_retry_allowed(item: dict) -> bool:
    telegram = item.setdefault("telegram", {})
    started_at = _parse_iso(telegram.get("preview_send_started_at"))
    if not started_at:
        return True
    return datetime.now().astimezone() - started_at >= PREVIEW_RETRY_DELAY


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _deferred_retry_settings() -> tuple[bool, int, float, timedelta]:
    enabled = _as_bool(CONFIG.get("queue", "deferred_retry_failed_posts", default=True))
    attempts = _as_int(CONFIG.get("queue", "deferred_retry_max_attempts", default=3), 3)
    delay_sec = _as_float(CONFIG.get("queue", "deferred_retry_delay_sec", default=900), 900.0)
    window_hours = _as_float(CONFIG.get("queue", "deferred_retry_window_hours", default=6), 6.0)
    return enabled, max(0, attempts), max(0.0, delay_sec), timedelta(hours=max(0.0, window_hours))


def _failed_retry_platforms(item: dict) -> list[str]:
    return [
        name
        for name, info in (item.get("platforms") or {}).items()
        if info.get("enabled")
        and info.get("status") == "failed"
        and not info.get("non_retryable")
    ]


def _latest_platform_attempt_at(item: dict, platforms: list[str]) -> datetime | None:
    values = []
    for platform in platforms:
        value = (item.get("platforms") or {}).get(platform, {}).get("last_attempt_at")
        parsed = _parse_iso(value)
        if parsed:
            values.append(parsed)
    return max(values) if values else None


def _retry_window_reference_at(item: dict) -> datetime | None:
    for value in (
        item.get("review", {}).get("decided_at"),
        item.get("scheduled_for"),
        item.get("created_at"),
    ):
        parsed = _parse_iso(value)
        if parsed:
            return parsed
    return None


def _deferred_retry_allowed(item: dict, now: datetime | None = None) -> tuple[bool, str, list[str]]:
    now = now or datetime.now().astimezone()
    enabled, max_attempts, delay_sec, window = _deferred_retry_settings()
    if not enabled:
        return False, "disabled", []
    if item.get("status") not in {"partial_failed", "failed"}:
        return False, "status", []
    if not item.get("review", {}).get("owner_approved"):
        return False, "not_approved", []
    platforms = _failed_retry_platforms(item)
    if not platforms:
        return False, "no_failed_platforms", []

    reference_at = _retry_window_reference_at(item)
    if reference_at:
        if reference_at.tzinfo is None and now.tzinfo is not None:
            reference_at = reference_at.replace(tzinfo=now.tzinfo)
        if now - reference_at > window:
            return False, "expired", platforms

    retry_state = item.setdefault("deferred_retry", {})
    attempts = _as_int(retry_state.get("attempts"), 0)
    if attempts >= max_attempts:
        return False, "max_attempts", platforms

    last_attempt = _parse_iso(retry_state.get("last_attempt_at")) or _latest_platform_attempt_at(item, platforms)
    if not last_attempt:
        return False, "missing_attempt_at", platforms
    if last_attempt.tzinfo is None and now.tzinfo is not None:
        last_attempt = last_attempt.replace(tzinfo=now.tzinfo)
    elapsed = now - last_attempt
    if elapsed > window:
        return False, "expired", platforms
    if elapsed < timedelta(seconds=delay_sec):
        return False, "cooldown", platforms
    return True, "due", platforms


def _scan_deferred_retries() -> None:
    for status in ("partial_failed", "failed"):
        for item in queue_lib.list_items(status):
            allowed, reason, platforms = _deferred_retry_allowed(item)
            if not allowed:
                continue
            retry_state = item.setdefault("deferred_retry", {})
            retry_state["attempts"] = _as_int(retry_state.get("attempts"), 0) + 1
            retry_state["last_attempt_at"] = _now_iso()
            retry_state["platforms"] = platforms
            item.setdefault("history", []).append(
                {
                    "ts": _now_iso(),
                    "event": f"遅延自動再投稿 {retry_state['attempts']}: {', '.join(platforms)} ({reason})",
                }
            )
            queue_lib.save_item(item)
            log(f"遅延自動再投稿: {item['id']} platforms={','.join(platforms)}")
            updated = poster.post_item(item, queue_lib, notify, retry_attempts=0, retry_delay_sec=0)
            log(f"遅延自動再投稿完了: {item['id']} → {updated['status']}")


def scan_queue() -> None:
    """未送信プレビューの送付と、approved の投稿実行。"""
    flushed = notify.flush_pending_messages()
    if flushed:
        log(f"保留通知を再送: {flushed}件")

    _scan_deferred_retries()

    for item in queue_lib.list_items("ready_for_review"):
        telegram = item.setdefault("telegram", {})
        if not telegram.get("message_id") and _preview_retry_allowed(item):
            telegram["preview_send_started_at"] = _now_iso()
            telegram["preview_send_attempts"] = int(telegram.get("preview_send_attempts") or 0) + 1
            queue_lib.save_item(item)
            mid = notify.send_video(
                _preview_video_path(item),
                notify.preview_caption(item),
                reply_markup=notify.approval_keyboard(item["id"]),
            )
            if mid:
                telegram["message_id"] = mid
                telegram["preview_sent_at"] = _now_iso()
                telegram.pop("preview_send_failed_at", None)
                queue_lib.save_item(item)
                log(f"プレビュー送信: {item['id']}")
            else:
                telegram["preview_send_failed_at"] = _now_iso()
                queue_lib.save_item(item)
                log(f"プレビュー送信未確認（短時間の自動再送を抑止）: {item['id']}")

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
        chat_id = msg.get("chat", {}).get("id") or CONFIG.telegram_chat_id
        item["review"].update(
            {
                "owner_approved": False,
                "decided_at": datetime.now().isoformat(),
                "via": "telegram",
                "rejection_reason_pending": True,
                "replacement_requested_at": datetime.now().isoformat(),
            }
        )
        queue_lib.transition(item, "skipped", "Telegramで却下")
        _set_pending_rejection(chat_id, item_id)
        _spawn_replacement(item)
        _answer_callback(cb_id, "却下しました。代替候補を作成します…")
        if msg.get("message_id"):
            _remove_buttons(msg["message_id"])
        notify.send_message(
            "📝 却下理由をこのチャットに普通のメッセージで送ると、"
            f"<code>{item_id}</code> の理由として保存します。\n"
            "代替候補は自動で作成中です。"
        )
        log(f"却下: {item_id}")
    elif action == "hold":
        _answer_callback(cb_id, "保留しました。ボタンはそのまま使えます")
        log(f"保留: {item_id}")
    else:
        _answer_callback(cb_id, "不明な操作")


def _record_rejection_reason(item_id: str, reason: str) -> bool:
    try:
        item = queue_lib.load_item(item_id)
    except FileNotFoundError:
        return False
    item.setdefault("review", {}).update(
        {
            "rejection_reason": reason,
            "rejection_reason_at": datetime.now().isoformat(),
            "rejection_reason_pending": False,
        }
    )
    item.setdefault("history", []).append(
        {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "event": "却下理由を保存",
        }
    )
    queue_lib.save_item(item)
    return True


def handle_message(msg: dict) -> None:
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id or not text:
        return
    if str(chat_id) != str(CONFIG.telegram_chat_id):
        return

    item_id = None
    reason = text
    if text.startswith("/reason "):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            notify.send_message("形式: <code>/reason item_id 理由</code>")
            return
        _, item_id, reason = parts
    else:
        pending_path = _pending_rejection_path(chat_id)
        if not pending_path.exists():
            return
        try:
            pending = json.loads(pending_path.read_text(encoding="utf-8"))
            item_id = pending.get("item_id")
        except json.JSONDecodeError:
            pending_path.unlink(missing_ok=True)
            return

    if item_id and _record_rejection_reason(item_id, reason):
        _pending_rejection_path(chat_id).unlink(missing_ok=True)
        notify.send_message(f"📝 却下理由を保存しました: <code>{item_id}</code>")
        log(f"却下理由保存: {item_id}")


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
                params={
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": '["callback_query","message"]',
                },
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
                elif "message" in upd:
                    handle_message(upd["message"])
        except KeyboardInterrupt:
            log("停止")
            break
        except Exception as e:  # デーモンは死なない
            log(f"エラー: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
