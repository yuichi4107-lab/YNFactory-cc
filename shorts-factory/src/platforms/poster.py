"""各SNSへの投稿ディスパッチャ。

既存の scripts/post_to_x.py 等を venv の python でサブプロセス実行する
（既存スクリプトの .env 読み込み・認証ロジックをそのまま活かす）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from ..config import CONFIG
from ..logging_utils import redact_secrets
from ..platform_copy import copy_for_platform

SCRIPTS_DIR = CONFIG.repo_root / "scripts"
PYTHON = str(CONFIG.runtime_dir / ".venv" / "bin" / "python")
INSTAGRAM_EXISTING_LOOKBACK = timedelta(minutes=30)


def _tail(text: str | None, limit: int = 500) -> str:
    return (text or "")[-limit:]


def _read_json_result(stdout: str, stderr: str, result_path: Path | None = None) -> dict:
    raw = stdout.strip()
    if not raw and result_path and result_path.exists():
        raw = result_path.read_text(encoding="utf-8").strip()
    if not raw:
        detail = _tail(stderr) or "(stderrなし)"
        raise RuntimeError(f"JSONを返しませんでした: stderr={detail}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if result_path and result_path.exists():
            try:
                return json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        raise RuntimeError(f"JSON出力のパース失敗: stdout={_tail(stdout)} stderr={_tail(stderr)}")


def _write_instagram_helper_diagnostic(item: dict, proc: subprocess.CompletedProcess, result_path: Path) -> Path:
    path = CONFIG.logs_dir / f"ig_helper_{item['id']}_{datetime.now().strftime('%m%d_%H%M%S')}.json"
    payload = {
        "item_id": item["id"],
        "returncode": proc.returncode,
        "stdout_len": len(proc.stdout or ""),
        "stderr_len": len(proc.stderr or ""),
        "stdout_tail": _tail(proc.stdout, 1200),
        "stderr_tail": _tail(proc.stderr, 1200),
        "result_json": str(result_path),
        "result_json_exists": result_path.exists(),
        "result_json_size": result_path.stat().st_size if result_path.exists() else 0,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _normalized_caption(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _parse_meta_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def _meta_module():
    repo_root = str(CONFIG.repo_root)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from scripts import post_to_meta

    return post_to_meta


def _find_recent_instagram_post(caption: str, since: datetime) -> str | None:
    """Return an existing permalink for the same caption to avoid duplicate retries."""
    post_to_meta = _meta_module()
    env = post_to_meta.load_env(CONFIG.sns_env_path)
    ig_user_id = env.get("META_IG_USER_ID")
    token = env.get("META_ACCESS_TOKEN")
    if not ig_user_id or not token:
        return None

    target = _normalized_caption(caption)
    if not target:
        return None
    response = post_to_meta.graph_get(
        f"{ig_user_id}/media",
        token,
        {"fields": "id,permalink,caption,timestamp,media_type", "limit": 25},
    )
    for media in response.get("data", []):
        timestamp = _parse_meta_timestamp(media.get("timestamp"))
        if timestamp and timestamp < since:
            continue
        media_caption = _normalized_caption(media.get("caption"))
        if media_caption == target:
            return media.get("permalink") or f"media_id:{media.get('id')}"
    return None


def post_x(item: dict) -> str:
    """Xへ動画投稿し、投稿URLを返す。"""
    text = copy_for_platform(item, "x")["text"]
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
    caption = copy_for_platform(item, "instagram")["caption"]
    now = datetime.now().astimezone()
    existing = _find_recent_instagram_post(caption, now - INSTAGRAM_EXISTING_LOOKBACK)
    if existing:
        return existing

    post_to_meta = _meta_module()
    result = post_to_meta.post_instagram_reels(
        caption,
        item["video"]["path"],
        post_to_meta.load_env(CONFIG.sns_env_path),
    )
    if result.get("status") != "posted":
        raise RuntimeError(f"IG Reels投稿失敗: {result.get('error', result)}")
    return result.get("permalink") or f"media_id:{result.get('id')}"


def post_youtube(item: dict) -> str:
    """YouTube Shorts へCDP経由でアップロードし、動画URLを返す。"""
    from . import youtube_cdp

    copy = copy_for_platform(item, "youtube")
    return youtube_cdp.upload(
        video_path=Path(item["video"]["path"]),
        title=copy["title"],
        description=copy["description"],
    )


def post_tiktok(item: dict) -> str:
    from . import tiktok_cdp

    caption = copy_for_platform(item, "tiktok")["caption"]
    return tiktok_cdp.upload(Path(item["video"]["path"]), caption)


POSTERS = {
    "x": post_x,
    "instagram": post_instagram,
    "youtube": post_youtube,
    "tiktok": post_tiktok,
}
POST_ORDER = ("x", "instagram", "tiktok", "youtube")


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


def _retry_settings() -> tuple[int, float]:
    enabled = _as_bool(CONFIG.get("queue", "retry_failed_posts", default=True))
    if not enabled:
        return 0, 0.0
    attempts = _as_int(CONFIG.get("queue", "retry_max_attempts", default=2), 2)
    delay_sec = _as_float(CONFIG.get("queue", "retry_delay_sec", default=60), 60.0)
    return max(0, attempts), max(0.0, delay_sec)


def _pending_platforms(platforms: dict, ordered_platforms: list[str]) -> list[str]:
    return [
        platform
        for platform in ordered_platforms
        if platforms[platform].get("enabled")
        and platforms[platform].get("status") != "posted"
        and not platforms[platform].get("non_retryable")
    ]


def _non_retryable_error(platform: str, error: str) -> bool:
    if platform == "tiktok":
        return "セッション失効" in error or "ログイン" in error
    return False


def _record_attempt(item: dict, queue_lib, platform: str, retry_round: int) -> None:
    info = item["platforms"][platform]
    now = _now()
    info["attempts"] = int(info.get("attempts") or 0) + 1
    info["last_attempt_at"] = now
    if retry_round:
        info["last_retry_at"] = now
        info["last_retry_round"] = retry_round
    if hasattr(queue_lib, "save_item"):
        queue_lib.save_item(item)


def post_item(
    item: dict,
    queue_lib,
    notify,
    retry_attempts: int | None = None,
    retry_delay_sec: float | None = None,
) -> dict:
    """有効な全プラットフォームへ投稿し、結果を item に記録して返す。"""
    results = []
    platforms = item.get("platforms", {})
    ordered_platforms = [p for p in POST_ORDER if p in platforms]
    ordered_platforms.extend(p for p in platforms if p not in ordered_platforms)

    configured_retry_attempts, configured_retry_delay_sec = _retry_settings()
    if retry_attempts is None:
        retry_attempts = configured_retry_attempts
    if retry_delay_sec is None:
        retry_delay_sec = configured_retry_delay_sec
    for retry_round in range(retry_attempts + 1):
        pending = _pending_platforms(platforms, ordered_platforms)
        if not pending:
            break
        if retry_round:
            results.append(f"🔁 自動再投稿 {retry_round}/{retry_attempts}: {', '.join(pending)}")
            if retry_delay_sec:
                time.sleep(retry_delay_sec)
        for platform in pending:
            try:
                _record_attempt(item, queue_lib, platform, retry_round)
                url = POSTERS[platform](item)
                item = queue_lib.mark_platform(item, platform, "posted", url=url)
                results.append(f"✅ {platform}: {url}")
            except Exception as e:  # 1媒体の失敗で他媒体を止めない
                err = redact_secrets(e)
                item = queue_lib.mark_platform(item, platform, "failed", error=err)
                if _non_retryable_error(platform, err):
                    item["platforms"][platform]["non_retryable"] = True
                    if hasattr(queue_lib, "save_item"):
                        queue_lib.save_item(item)
                results.append(f"❌ {platform}: {err[:120]}")

    statuses = [v["status"] for v in item["platforms"].values() if v.get("enabled")]
    if statuses and all(s == "posted" for s in statuses):
        item = queue_lib.transition(item, "posted", "全媒体投稿完了")
    elif any(s == "posted" for s in statuses):
        item = queue_lib.transition(item, "partial_failed", "一部媒体のみ投稿成功。失敗媒体は再試行待ち")
    else:
        item = queue_lib.transition(item, "failed", "全媒体投稿失敗")

    extra = ""
    if item["status"] in {"failed", "partial_failed"}:
        retry_note = ""
        if retry_attempts:
            retry_note = f"\n\n自動再投稿: 最大{retry_attempts}回まで実行済み"
        extra = (
            retry_note
            + "\n\n手動再試行: "
            + f"<code>python3 shorts-factory/scripts/retry_failed_posts.py {item['id']} --execute</code>"
        )
    notify.send_message(
        f"📤 <b>{item['title']}</b> 投稿結果\n" + "\n".join(results) + extra
    )
    return item
