"""ショート動画 全自動生成パイプライン。

テーマ → 台本(LLM) → TTS(VOICEVOX) → 背景画像 → FFmpeg合成 → 機械検証
→ 不合格箇所の自動修正ループ → 成果物保存 → 投稿キュー登録 → Telegramプレビュー

使い方:
  python -m src.pipeline --topic "ChatGPTで議事録を3分で作る方法"
  python -m src.pipeline                  # ネタ帳から自動選択
  python -m src.pipeline --no-queue      # キュー登録もTelegram送信もしない（テスト用）
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import traceback
import unicodedata
from datetime import date, datetime
from pathlib import Path

from .config import CONFIG
from . import image_gen, notify, queue_lib, renderer, script_gen, topic_store, tts_voicevox, verifier
from .fs_retry import is_transient_io_error, retry_io
from .logging_utils import redact_secrets


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {redact_secrets(msg)}"
    print(line, flush=True)
    with open(CONFIG.logs_dir / "pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def make_slug(title: str) -> str:
    s = unicodedata.normalize("NFKC", title).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) < 4:  # 日本語タイトルはローマ字が残らないので時刻ベースに
        s = datetime.now().strftime("%H%M%S")
    return s[:40]


def make_item_id(title: str, now: datetime | None = None, suffix: str | None = None) -> str:
    """Create a queue/output id that will not collide across same-day posts."""
    now = now or datetime.now()
    item_id = f"{now.date().isoformat()}_{now.strftime('%H%M%S')}_{make_slug(title)}"
    if suffix:
        item_id = f"{item_id}-{suffix}"
    return item_id


def save_outputs(
    item_id: str,
    final: Path,
    ass: Path,
    work: Path,
    images: list[Path],
    previews: list[Path],
    title: str,
    script: dict,
) -> Path:
    """Copy generated artifacts to Drive, retrying transient Drive I/O errors."""

    def _save_once() -> Path:
        out_dir = CONFIG.outputs_dir / item_id
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final, out_dir / "final.mp4")
        shutil.copy2(work / "script.json", out_dir / "script.json")
        shutil.copy2(ass, out_dir / "subtitles.ass")
        shutil.copy2(work / "quality_report.json", out_dir / "quality_report.json")
        (out_dir / "images").mkdir(exist_ok=True)
        for p in images:
            shutil.copy2(p, out_dir / "images" / p.name)
        for p in previews:
            shutil.copy2(p, out_dir / p.name)
        captions = (
            f"# {title}\n\n## キャプション\n{script['caption']}\n\n"
            f"## ハッシュタグ\n{' '.join(script['hashtags'])}\n\n"
            f"## クレジット（概要欄に含めること）\n{CONFIG.get('speaker_credit')}／音声・映像はAIで自動生成しています\n"
        )
        (out_dir / "captions.md").write_text(captions, encoding="utf-8")
        return out_dir

    return retry_io(_save_once, attempts=5, delay_sec=5.0)


def scheduled_difficulty(now: datetime | None = None) -> str:
    """現在時刻から投稿スロットの難易度を返す。"""
    now = now or datetime.now()
    slots = CONFIG.get("content", "scheduled_slots", default=[]) or []
    for slot in slots:
        if int(slot.get("hour", -1)) == now.hour:
            return topic_store.normalize_difficulty(slot.get("difficulty")) or "beginner"
    return topic_store.normalize_difficulty(
        CONFIG.get("content", "default_difficulty", default="beginner")
    ) or "beginner"


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _quality_remake_settings() -> tuple[bool, int]:
    enabled = _as_bool(CONFIG.get("verify", "auto_remake_on_fail", default=True))
    attempts = _as_int(CONFIG.get("verify", "remake_max_attempts", default=2), 2)
    return enabled, max(1, attempts)


def _mark_discarded_candidate(candidate: dict, next_attempt: int) -> None:
    """Record that a low-quality candidate was intentionally not queued."""
    report = candidate["report"]
    failed_checks = [c["name"] for c in report.get("checks", []) if not c.get("pass")]
    marker = {
        "status": "discarded_quality_fail",
        "next_attempt": next_attempt,
        "item_id": candidate["item_id"],
        "failed_checks": failed_checks,
        "avg_cer": (report.get("accuracy") or {}).get("avg_cer"),
        "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path = Path(candidate["out_dir"]) / "remake_status.json"
    path.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_candidate(topic: str, selected_difficulty: str, attempt: int = 1) -> dict:
    """Generate one full video candidate and persist its artifacts."""
    # --- 1. 台本生成（生成層バリデーション込み） ---
    script = script_gen.generate_script(topic, selected_difficulty)
    title = script["title"]
    item_id = make_item_id(title, suffix=f"try{attempt}" if attempt > 1 else None)
    work = CONFIG.work_dir / item_id
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "script.json").write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"台本OK: 「{title}」 cues={len(script['cues'])} candidate={attempt}")

    # --- 2. TTS（合成層: 読み突合） ---
    try:
        tts = tts_voicevox.synthesize_cues(script["cues"], work)
        max_sec = float(CONFIG.get("video", "max_sec", default=60))
        if tts["total_dur"] > max_sec:
            # 尺超過 → 話速を上げて全再合成（1回だけ）
            new_speed = min(
                round(
                    float(CONFIG.get("speed_scale", default=1.0))
                    * tts["total_dur"]
                    / (max_sec * 0.96),
                    2,
                ),
                1.35,
            )
            log(f"尺超過 {tts['total_dur']}s → speed_scale={new_speed} で再合成")
            CONFIG.cfg["speed_scale"] = new_speed
            tts = tts_voicevox.synthesize_cues(script["cues"], work)
        fallbacks = [c["index"] for c in tts["cues"] if c["used_kana_fallback"]]
        log(f"TTS OK: {tts['total_dur']}s, 読み仮名フォールバック行={fallbacks or 'なし'}")

        # --- 3. 背景画像 ---
        images, provider = image_gen.generate_images(script, work / "images")
        log(f"画像OK: {len(images)}枚 (provider={provider})")

        # --- 4. レンダリング ---
        bg = renderer.render_background(images, tts["total_dur"], work)
        credit = f"{CONFIG.get('speaker_credit')}／音声・映像はAIで自動生成"
        overlay = work / "overlay.png"
        renderer.make_overlay(title, credit, overlay)
        ass = work / "subs.ass"
        renderer.make_ass(tts["cues"], tts["total_dur"], ass)
        measured = renderer.measure_loudnorm(Path(tts["master_wav"]), work)
        final = renderer.compose_final(
            bg,
            overlay,
            ass,
            Path(tts["master_wav"]),
            tts["total_dur"],
            work,
            measured=measured,
        )
        log("レンダリングOK")

        # --- 5. 検証 → 自動修正ループ ---
        report = verifier.verify_video(final, tts["cues"], tts["total_dur"], work)
        loops = 0
        max_loops = int(CONFIG.get("verify", "max_fix_loops", default=5))
        crf = int(CONFIG.get("video", "crf", default=23))
        while not report["pass"] and loops < max_loops:
            loops += 1
            log(
                f"検証不合格 → 修正ループ {loops}/{max_loops}: "
                + ", ".join(c["name"] for c in report["checks"] if not c["pass"])
            )
            failed_idx = report["accuracy"]["failed_indices"]
            # かな直読み済みのキューは再合成しても変わらない → 打つ手が無ければ打ち切り
            actionable = [i for i in failed_idx if not tts["cues"][i].get("used_kana_fallback")]
            other_fails = [
                c["name"]
                for c in report["checks"]
                if not c["pass"] and not c["name"].startswith("subtitle_accuracy")
            ]
            if failed_idx and not actionable and not other_fails:
                log("修正手段なし（全不合格行がかな直読み済み）→ 候補作り直し判定へ")
                break
            rerender_needed = False
            if actionable:
                old_total = tts["total_dur"]
                tts = tts_voicevox.resynth_cues(tts, actionable, work)
                renderer.make_ass(tts["cues"], tts["total_dur"], ass)
                if abs(tts["total_dur"] - old_total) > 0.2:
                    bg = renderer.render_background(images, tts["total_dur"], work)
                rerender_needed = True
            for c in report["checks"]:
                if c["pass"]:
                    continue
                if c["name"] == "filesize":
                    crf += 3
                    rerender_needed = True
                if c["name"] in (
                    "loudness",
                    "no_black_frames",
                    "duration",
                    "subtitle_within_audio",
                    "resolution",
                    "codecs",
                ):
                    rerender_needed = True
            if rerender_needed:
                measured = renderer.measure_loudnorm(Path(tts["master_wav"]), work)
                final = renderer.compose_final(
                    bg,
                    overlay,
                    ass,
                    Path(tts["master_wav"]),
                    tts["total_dur"],
                    work,
                    crf=crf,
                    measured=measured,
                )
            report = verifier.verify_video(final, tts["cues"], tts["total_dur"], work)

        report["fix_loops"] = loops
        (work / "quality_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log(
            f"検証{'合格✅' if report['pass'] else '不合格⚠️（上限到達）'} "
            f"avg_cer={report['accuracy']['avg_cer']} loops={loops}"
        )

        previews = renderer.extract_previews(final, tts["cues"], work)
    finally:
        tts_voicevox.shutdown_engine()

    # --- 6. 成果物をDriveへ保存 ---
    out_dir = save_outputs(item_id, final, ass, work, images, previews, title, script)
    log(f"成果物保存: {out_dir}")
    return {
        "item_id": item_id,
        "output_dir": str(out_dir),
        "out_dir": out_dir,
        "report": report,
        "title": title,
        "topic": topic,
        "script": script,
        "final": final,
        "ass": ass,
        "work": work,
        "images": images,
        "previews": previews,
        "attempt": attempt,
    }


def produce(
    topic: str | None = None,
    send_queue: bool = True,
    difficulty: str | None = None,
) -> dict:
    """1本の動画を生成して結果情報を返す。"""
    selected_difficulty = topic_store.normalize_difficulty(difficulty) or scheduled_difficulty()
    if not topic and send_queue:
        scheduled_item = queue_lib.find_due_scheduled_draft(
            datetime.now().astimezone(), selected_difficulty
        )
        if scheduled_item:
            queue_lib.transition(
                scheduled_item,
                "ready_for_review",
                f"予約済み動画を{scheduled_item.get('scheduled_for')}枠へ投入",
            )
            log(f"予約済み動画を投入: {scheduled_item['id']}")
            return {
                "id": scheduled_item["id"],
                "output_dir": scheduled_item.get("output_dir"),
                "report": scheduled_item.get("quality", {}),
                "title": scheduled_item.get("title"),
                "scheduled": True,
            }

    # --- 0. トピック決定 ---
    if not topic:
        topic, remaining = topic_store.next_topic(selected_difficulty)
        if not topic:
            fallback_topic, fallback_remaining = topic_store.next_topic()
            if fallback_topic:
                notify.send_message(
                    f"⚠️ shorts-factory: {selected_difficulty} のネタが空です。"
                    "別難易度のネタで代替します。"
                )
                topic, remaining = fallback_topic, fallback_remaining
                selected_difficulty = "beginner"
            else:
                notify.send_message("⚠️ shorts-factory: ネタ帳が空です。topics.json に補充してください。")
                raise SystemExit("ネタ帳が空")
    log(f"テーマ: {topic} (difficulty={selected_difficulty})")

    remake_enabled, remake_max_attempts = _quality_remake_settings()
    candidate = None
    discarded_count = 0
    for attempt in range(1, remake_max_attempts + 1):
        candidate = _build_candidate(topic, selected_difficulty, attempt)
        report = candidate["report"]
        if report["pass"]:
            break
        if not remake_enabled or attempt >= remake_max_attempts:
            break
        discarded_count += 1
        _mark_discarded_candidate(candidate, attempt + 1)
        failed_checks = ", ".join(c["name"] for c in report.get("checks", []) if not c.get("pass"))
        log(
            f"品質検証不合格のため候補を作り直し: "
            f"{candidate['item_id']} → attempt {attempt + 1}/{remake_max_attempts}"
            + (f" failed={failed_checks}" if failed_checks else "")
        )

    assert candidate is not None
    item_id = candidate["item_id"]
    out_dir = candidate["out_dir"]
    report = candidate["report"]
    title = candidate["title"]
    script = candidate["script"]
    result = {
        "id": item_id,
        "output_dir": str(out_dir),
        "report": report,
        "title": title,
        "quality_attempt": candidate.get("attempt", 1),
        "discarded_quality_failures": discarded_count,
    }
    if not send_queue:
        return result

    # --- 7. キュー登録 + ネタ帳消費 + Telegramプレビュー ---
    item = queue_lib.new_item(
        item_id, topic, script, out_dir / "final.mp4",
        report["duration"], report["size_mb"],
        out_dir / "quality_report.json", report["pass"],
        report["accuracy"]["avg_cer"], out_dir,
    )

    try:
        remaining = topic_store.consume_topic(topic, item_id, title, selected_difficulty)
        if remaining <= topic_store.LOW_STOCK_THRESHOLD:
            notify.send_message(f"📋 shorts-factory: ネタ帳の残りが{remaining}本です。補充してください。")
    except OSError as exc:
        if not is_transient_io_error(exc):
            raise
        log(f"ネタ帳消費を後回し: {exc}")
        item.setdefault("topic_store", {})["consume_deferred_error"] = str(exc)
        item.setdefault("history", []).append(
            {
                "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                "event": "topic_consume_deferred",
            }
        )
        queue_lib.save_item(item)
        notify.send_message(
            "⚠️ shorts-factory: Driveロックでネタ帳更新だけ後回しになりました。"
            f"キュー登録は完了しています: <code>{item_id}</code>"
        )

    if not report["pass"]:
        item = queue_lib.transition(item, "blocked", "品質検証が上限到達でも不合格のため要人間確認")
        mid = notify.send_video(
            out_dir / "final.mp4",
            "⚠️ 品質検証不合格のため投稿保留\n"
            "次の対応をボタンで選んでください。\n\n"
            + notify.preview_caption(item),
            reply_markup=notify.quality_blocked_keyboard(item["id"]),
        )
        if mid:
            item.setdefault("telegram", {})["message_id"] = mid
            queue_lib.save_item(item)
        return result

    if CONFIG.get("queue", "auto_post", default=False):
        item["review"].update({"owner_approved": True, "decided_at": datetime.now().isoformat(), "via": "auto_post"})
        queue_lib.transition(item, "approved", "auto_post=true により自動承認")
        mid = notify.send_video(out_dir / "final.mp4", "🤖 自動投稿モード: まもなく投稿します\n" + notify.preview_caption(item))
    else:
        queue_lib.transition(item, "ready_for_review", "Telegram承認待ち")
        # The approval daemon is the single sender for approval previews.
        # Sending here as well races with the daemon and can duplicate buttons.
    return result


def result_summary(result: dict) -> dict:
    """Build stable CLI output for both newly generated and scheduled items."""
    report = result.get("report") or {}
    accuracy = report.get("accuracy") or {}
    return {
        "id": result.get("id"),
        "pass": report.get("pass"),
        "avg_cer": accuracy.get("avg_cer", report.get("avg_cer")),
        "output": result.get("output_dir"),
        "scheduled": bool(result.get("scheduled")),
        "quality_attempt": result.get("quality_attempt"),
        "discarded_quality_failures": result.get("discarded_quality_failures", 0),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="ショート動画全自動生成")
    ap.add_argument("--topic", help="テーマ（省略時はネタ帳から）")
    ap.add_argument("--no-queue", action="store_true", help="キュー登録・Telegram送信をしない")
    ap.add_argument(
        "--difficulty",
        choices=["beginner", "intermediate"],
        help="ネタ選択と台本の難易度。省略時は実行時刻のスロットから自動判定",
    )
    args = ap.parse_args()
    try:
        result = produce(topic=args.topic, send_queue=not args.no_queue, difficulty=args.difficulty)
        print(json.dumps(result_summary(result), ensure_ascii=False))
    except Exception as e:
        log(f"❌ パイプライン失敗: {e}")
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        log("失敗詳細:\n" + tb[-4000:])
        notify.send_message(f"❌ shorts-factory 生成失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
