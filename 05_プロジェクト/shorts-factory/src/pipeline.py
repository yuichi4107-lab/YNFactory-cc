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
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import unicodedata
from datetime import date, datetime
from pathlib import Path

from .config import CONFIG
from . import (
    image_gen,
    notify,
    queue_lib,
    renderer,
    script_gen,
    topic_store,
    tts_voicevox,
    topview_inventory,
    verifier,
    video_bg_gen,
)
from .fs_retry import is_transient_io_error, retry_io
from .logging_utils import redact_secrets
from .state_io import file_lock
from . import drive_guard


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {redact_secrets(msg)}"
    print(line, flush=True)
    with open(CONFIG.logs_dir / "pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


class HybridGenerationBlocked(RuntimeError):
    """混在形式を完走できず、カード版への代替を禁止して停止した状態。"""


TopviewInventoryError = topview_inventory.TopviewInventoryError

# 混在1本あたりに使う長尺実写クリップ数。前後の2区間へ切り出すが、
# 素材自体は最終ショート間で再利用しない。
TOPVIEW_CLIPS_PER_VIDEO = 1


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
    credit: str | None = None,
) -> Path:
    """Commit generated artifacts atomically to the local runtime archive."""

    def _save_once() -> Path:
        CONFIG.outputs_dir.mkdir(parents=True, exist_ok=True)
        out_dir = CONFIG.outputs_dir / item_id
        stage = Path(tempfile.mkdtemp(dir=str(CONFIG.outputs_dir), prefix=f".{item_id}."))
        try:
            shutil.copy2(final, stage / "final.mp4")
            shutil.copy2(work / "script.json", stage / "script.json")
            shutil.copy2(ass, stage / "subtitles.ass")
            shutil.copy2(work / "quality_report.json", stage / "quality_report.json")
            (stage / "images").mkdir(exist_ok=True)
            for p in images:
                shutil.copy2(p, stage / "images" / p.name)
            for p in previews:
                shutil.copy2(p, stage / p.name)
            captions = (
                f"# {title}\n\n## キャプション\n{script['caption']}\n\n"
                f"## ハッシュタグ\n{' '.join(script['hashtags'])}\n\n"
                f"## クレジット（概要欄に含めること）\n"
                f"{credit or (str(CONFIG.get('speaker_credit')) + '／音声・映像はAIで自動生成しています')}\n"
            )
            (stage / "captions.md").write_text(captions, encoding="utf-8")
            (stage / ".complete.json").write_text(
                json.dumps(
                    {
                        "item_id": item_id,
                        "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            if out_dir.exists():
                shutil.rmtree(out_dir)
            os.replace(stage, out_dir)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            raise
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


def _topic_text(topic_entry: str | dict) -> str:
    if isinstance(topic_entry, dict):
        return str(topic_entry.get("topic") or "").strip()
    return str(topic_entry or "").strip()


def _build_candidate(
    topic_entry: str | dict,
    selected_difficulty: str,
    attempt: int = 1,
    target_platform: str = "common",
    item_suffix: str | None = None,
) -> dict:
    """Generate one full video candidate and persist its artifacts."""
    # --- 1. 台本生成（生成層バリデーション込み） ---
    topic = _topic_text(topic_entry)
    script = script_gen.generate_script(
        topic_entry,
        selected_difficulty,
        target_platform=target_platform,
    )
    title = script["title"]
    suffix_parts = []
    if item_suffix:
        suffix_parts.append(item_suffix)
    if attempt > 1:
        suffix_parts.append(f"try{attempt}")
    item_id = make_item_id(title, suffix="-".join(suffix_parts) if suffix_parts else None)
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

    # --- 6. 成果物をローカルへ保存（Drive反映は別プロセス） ---
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
        "target_platform": target_platform,
    }


# ===================== Seedance統合（AI動画背景版） =====================
#
# 適用枠は config seedance.slots（例: ["mon-09", "wed-14", ...]）と実行時刻の
# 曜日・時で判定する。該当枠のみSeedance版、他は従来の静止画カード版。
# API失敗・タイムアウト・キー未設定・コスト上限超過・CER不合格継続の
# 通常のSeedance枠は静止画カード版へ自動フォールバックする。一方で混在枠は
# 実写+日本語カードの構成を完走できなければ停止し、従来カード版を出さない。

_WEEKDAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _slot_code(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"{_WEEKDAY_CODES[now.weekday()]}-{now.hour:02d}"


def is_seedance_slot(now: datetime | None = None) -> bool:
    """現在時刻がSeedance適用枠（曜日-時）に該当するかを判定する。"""
    if not CONFIG.get("seedance", "enabled", default=True):
        return False
    slots = CONFIG.get("seedance", "slots", default=[]) or []
    return _slot_code(now) in {str(s).strip().lower() for s in slots}


def is_hybrid_seedance_slot(now: datetime | None = None) -> bool:
    """実写→日本語カードを交互にする混在版の適用枠かを判定する。"""
    if not is_seedance_slot(now):
        return False
    slots = CONFIG.get("seedance", "hybrid_slots", default=[]) or []
    return _slot_code(now) in {str(s).strip().lower() for s in slots}


def is_topview_slot(now: datetime | None = None) -> bool:
    """Topview書き出し素材による混在形式を使う定刻枠か。"""
    if not CONFIG.get("topview", "enabled", default=False):
        return False
    slots = CONFIG.get("topview", "slots", default=[]) or []
    return _slot_code(now) in {str(s).strip().lower() for s in slots}


def _seedance_cost_settings() -> tuple[float, float]:
    max_per_video = float(CONFIG.get("seedance", "max_cost_per_video_usd", default=10.0))
    monthly_budget = float(CONFIG.get("seedance", "monthly_budget_usd", default=130.0))
    return max_per_video, monthly_budget


def _build_seedance_video(
    script: dict,
    work: Path,
    *,
    cue_indices: list[int] | None = None,
) -> tuple[Path, list[dict], list]:
    """台本のcuesからSeedanceでカットごとの動画を連鎖生成し、1本に連結する。

    Returns:
        (連結済みmp4パス, タイミング確定済みcues, CutResultリスト)

    Raises:
        video_bg_gen.SeedanceError系: API失敗・タイムアウト・予算超過等。
        呼び出し元でフォールバック判断すること。
    """
    cues = script["cues"]
    selected_indices = cue_indices if cue_indices is not None else list(range(len(cues)))
    if not selected_indices or any(index < 0 or index >= len(cues) for index in selected_indices):
        raise video_bg_gen.SeedanceError("Seedance生成対象のキュー番号が不正です")
    selected_cues = [cues[index] for index in selected_indices]
    cut_duration = int(CONFIG.get("seedance", "cut_duration_sec", default=10))
    model = CONFIG.get("seedance", "model", default="fast")
    estimated_total_sec = cut_duration * len(selected_cues)
    estimated_cost = video_bg_gen.estimate_cost(estimated_total_sec, model)

    max_per_video, _ = _seedance_cost_settings()
    if not video_bg_gen.is_budget_available(estimated_cost):
        raise video_bg_gen.SeedanceError(
            f"予算上限超過見込み（推定${estimated_cost}, 1本上限${max_per_video}, "
            f"今月残${video_bg_gen.budget_remaining()}）"
        )

    character = script.get("character_description", "")
    room = script.get("room_description", "")
    camera = script.get("camera_description", "")
    chain_cuts = []
    for i, cue in enumerate(selected_cues):
        prompt = cue["video_prompt"]
        # キャラクター統一の固定句をカット1にも明示しておく（カット2以降は
        # video_bg_gen.CONTINUITY_SUFFIX が自動付与するため、ここでは
        # カット1向けに設定文をまとめて先頭に足すだけでよい）
        if i == 0 and character:
            prompt = f"{character}, in {room}, {camera}. {prompt}"
        chain_cuts.append({"name": f"cut{i + 1}", "prompt": prompt, "duration": cut_duration})

    chain_config = video_bg_gen.ChainConfig(
        cuts=chain_cuts,
        resolution=CONFIG.get("seedance", "resolution", default="720p"),
        ratio=CONFIG.get("seedance", "ratio", default="9:16"),
        generate_audio=bool(CONFIG.get("seedance", "generate_audio", default=True)),
        watermark=bool(CONFIG.get("seedance", "watermark", default=False)),
        seed=CONFIG.get("seedance", "seed", default=42),
        model=model,
    )
    seedance_dir = work / "seedance"
    cut_results = video_bg_gen.generate_chained_cuts(chain_config, seedance_dir)
    timed_cues = (
        video_bg_gen.assign_cue_timings_from_cuts(cues, cut_results)
        if len(selected_cues) == len(cues)
        else []
    )
    # compose_finalはwork直下のファイル名(cwd相対)でffmpegを呼ぶため、連結結果はwork直下に置く
    bg = video_bg_gen.concat_cuts(cut_results, work / "bg_seedance.mp4", seedance_dir)
    return bg, timed_cues, cut_results


#  字幕タイミング: 各カットの実尺（video_bg_gen.assign_cue_timings_from_cuts）
#  で start/end を機械的に確定し、字幕正確性そのものは
#  verifier.verify_video → verifier.transcribe（whisper.cpp）が
#  最終mp4の音声を文字起こしして台本の tts_text と音韻CER突合する。
#  つまり「Seedance音声をwhisperで文字起こしして台本と突合」は
#  verifier側の既存ロジックをそのまま再利用し、しきい値だけ
#  seedance.cer_line_max / cer_avg_max に緩めている。


def _seedance_audio_mode() -> str:
    mode = str(CONFIG.get("seedance", "audio_mode", default="voicevox") or "voicevox").lower()
    return mode if mode in {"voicevox", "native"} else "voicevox"


def _seedance_voicevox_cues(script: dict) -> list[dict]:
    cues: list[dict] = []
    for cue in script.get("cues", []):
        out = dict(cue)
        out["reading_kana"] = cue.get("tts_kana") or cue.get("reading_kana") or cue.get("tts_text", "")
        cues.append(out)
    return cues


def _hybrid_segment_durations(cues: list[dict], total_dur: float) -> list[float]:
    """TTSキューごとの開始時刻から、4場面の背景尺を確定する。"""
    if len(cues) != 4:
        raise video_bg_gen.SeedanceError("混在版は4つのセリフキューが必要です")
    starts = [float(cue["start"]) for cue in cues]
    boundaries = starts[1:] + [float(total_dur)]
    durations = [round(end - start, 3) for start, end in zip(starts, boundaries)]
    if any(duration <= 0 for duration in durations):
        raise video_bg_gen.SeedanceError("混在版のセリフ尺を確定できませんでした")
    # 冒頭の無音は混在版では0秒にするため、先頭キューは必ず0秒開始となる。
    if starts[0] > 0.05:
        raise video_bg_gen.SeedanceError("混在版の冒頭発話に無音が残っています")
    return durations


def _topview_split_clip_offsets(clip: dict, segment_durations: list[float]) -> list[float]:
    """1本の12秒素材から、第1・第4区間の実写を安全に切り出す。"""
    if len(segment_durations) != 6:
        raise TopviewInventoryError("Topview長尺素材の区間数が不正です")
    clip_duration = float(clip["duration_sec"])
    first_duration = float(segment_durations[0])
    second_duration = float(segment_durations[3])
    max_live_duration = float(CONFIG.get("topview", "max_live_segment_sec", default=5.0))
    if first_duration > max_live_duration or second_duration > max_live_duration:
        raise TopviewInventoryError(
            "Topview 12秒素材へ収まらない実写セリフ尺です。台本を短くして再生成してください。"
        )
    desired = float(CONFIG.get("topview", "second_segment_start_sec", default=6.0))
    min_gap = float(CONFIG.get("topview", "min_segment_gap_sec", default=1.0))
    latest_start = clip_duration - second_duration
    earliest_late_start = first_duration + min_gap
    if latest_start < earliest_late_start:
        raise TopviewInventoryError(
            "Topview 12秒素材から前後2区間を切り出せません。素材尺または台本尺を確認してください。"
        )
    return [0.0, min(desired, latest_start)]


def _topview_segment_durations(cues: list[dict], total_dur: float) -> list[float]:
    """6つのTTSキューを、実写・カード4枚の6区間へ対応付ける。"""
    if len(cues) != 6:
        raise video_bg_gen.SeedanceError("Topview混在版は6つのセリフキューが必要です")
    starts = [float(cue["start"]) for cue in cues]
    boundaries = starts[1:] + [float(total_dur)]
    durations = [round(end - start, 3) for start, end in zip(starts, boundaries)]
    if any(duration <= 0 for duration in durations):
        raise video_bg_gen.SeedanceError("Topview混在版のセリフ尺を確定できませんでした")
    if starts[0] > 0.05:
        raise video_bg_gen.SeedanceError("Topview混在版の冒頭発話に無音が残っています")
    return durations


def _build_topview_candidate(
    topic_entry: str | dict, selected_difficulty: str, attempt: int = 1,
) -> dict:
    """Topviewの既存書き出し実写 + 日本語カードの混在候補を作る。

    Topview以外の外部生成サービスへのAPIアクセスや新規生成は行わない。在庫異常なら例外で
    停止し、呼び出し元は旧カード版へフォールバックしない。
    """
    topic = _topic_text(topic_entry)
    script = script_gen.generate_seedance_script(topic_entry, selected_difficulty, 6)
    title = script["title"]
    suffix = "topview" if attempt == 1 else f"topview-try{attempt}"
    item_id = make_item_id(title, suffix=suffix)
    work = CONFIG.work_dir / item_id
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    selected_clips, _ = topview_inventory.select_live_clips(CONFIG, count=TOPVIEW_CLIPS_PER_VIDEO)
    speaker_credit = CONFIG.get("topview", "voicevox_speaker_credit", default="VOICEVOX:青山龍星")
    speaker_id = int(CONFIG.get("topview", "voicevox_speaker_id", default=13))
    tts = tts_voicevox.synthesize_cues(
        _seedance_voicevox_cues(script), work, speaker_id=speaker_id, lead_in_sec=0.0,
    )
    master_wav = Path(tts["master_wav"])
    final_cues = tts["cues"]
    total_dur = tts["total_dur"]
    card_indices = (1, 2, 4, 5)
    card_script = dict(script)
    keywords = list(script.get("card_keywords", []))
    card_script["card_keywords"] = [
        keywords[index] if index < len(keywords) else script["title"]
        for index in card_indices
    ]
    images, image_provider = image_gen.generate_images(card_script, work / "images")
    if len(images) < 4:
        raise TopviewInventoryError("混在版用の日本語カードを4枚用意できませんでした")
    segment_durations = _topview_segment_durations(final_cues, total_dur)
    clip = selected_clips[0]
    live_offsets = _topview_split_clip_offsets(clip, segment_durations)
    bg = renderer.render_hybrid_background(
        [Path(clip["path"]), Path(clip["path"])], images[:4], segment_durations, work,
        live_start_offsets=live_offsets,
    )
    script.update({
        "presentation_mode": "hybrid_topview_card_6",
        "video_provider": "topview_manual_export",
        "topview_assets": [clip["id"] for clip in selected_clips],
        "topview_segments": [
            {"asset_id": clip["id"], "start_sec": live_offsets[0], "duration_sec": segment_durations[0]},
            {"asset_id": clip["id"], "start_sec": live_offsets[1], "duration_sec": segment_durations[3]},
        ],
        "image_provider": image_provider,
        "speaker_credit": speaker_credit,
        "audio_mode": "voicevox",
    })
    (work / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    overlay = work / "overlay.png"
    renderer.make_overlay(title, f"{speaker_credit}／実写映像はTopview書き出し素材", overlay)
    ass = work / "subs.ass"
    renderer.make_ass(final_cues, total_dur, ass)
    measured = renderer.measure_loudnorm(master_wav, work)
    final = renderer.compose_final(bg, overlay, ass, master_wav, total_dur, work, measured=measured)
    report = verifier.verify_video(final, final_cues, total_dur, work)
    report["fix_loops"] = 0
    (work / "quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    previews = renderer.extract_previews(final, final_cues, work)
    out_dir = save_outputs(
        item_id, final, ass, work, images, previews, title, script,
        credit=f"{speaker_credit}／実写映像はTopview書き出し素材",
    )
    if report["pass"]:
        topview_inventory.record_usage(CONFIG, [clip["id"] for clip in selected_clips])
        log(f"Topview混在成果物保存: {out_dir}; assets={[clip['id'] for clip in selected_clips]}")
        warn_topview_stock_running_out()
    else:
        log(
            "Topview混在候補は品質不合格のため素材を消費せず再生成対象にする: "
            f"{out_dir}"
        )
    return {
        "item_id": item_id, "output_dir": str(out_dir), "out_dir": out_dir,
        "report": report, "title": title, "topic": topic, "script": script,
        "final": final, "ass": ass, "work": work, "images": images, "previews": previews,
        "attempt": attempt, "target_platform": "common", "provider": "hybrid_topview",
    }


def _generate_passable_topview_candidate(topic_entry: str | dict, selected_difficulty: str) -> tuple[dict, int]:
    """品質不合格なら、未消費の同一素材を使って安全に再生成する。

    素材不足・台本尺超過など候補を組み立てられない失敗は隠さず上位へ渡す。
    一方、完成後のCERなど品質だけの不合格は、外部投稿も新規素材消費もせず、
    verify設定の上限まで別台本で作り直す。
    """
    remake_enabled, remake_max_attempts = _quality_remake_settings()
    candidate = None
    discarded_count = 0
    for attempt in range(1, remake_max_attempts + 1):
        candidate = _build_topview_candidate(topic_entry, selected_difficulty, attempt)
        report = candidate["report"]
        if report["pass"]:
            break
        if not remake_enabled or attempt >= remake_max_attempts:
            break
        discarded_count += 1
        _mark_discarded_candidate(candidate, attempt + 1)
        failed_checks = ", ".join(
            check["name"] for check in report.get("checks", []) if not check.get("pass")
        )
        log(
            "Topview混在品質検証不合格のため自動再生成: "
            f"{candidate['item_id']} → attempt {attempt + 1}/{remake_max_attempts}"
            + (f" failed={failed_checks}" if failed_checks else "")
        )
    assert candidate is not None
    return candidate, discarded_count


def _build_seedance_candidate(
    topic_entry: str | dict,
    selected_difficulty: str,
    attempt: int = 1,
    *,
    hybrid: bool = False,
) -> dict:
    """Seedance版（AI動画背景）の候補を1本生成する。

    静止画カード版の _build_candidate と対になるが、TTS(VOICEVOX)を使わず、
    Seedance生成音声をそのまま使うnativeモードと、映像だけSeedanceで作り
    音声はVOICEVOXで差し替えるvoicevoxモードを持つ。
    失敗時は video_bg_gen.SeedanceError系 を送出し、呼び出し元でフォールバックする。
    """
    topic = _topic_text(topic_entry)
    cut_count = 4
    script = script_gen.generate_seedance_script(topic_entry, selected_difficulty, cut_count)
    title = script["title"]
    suffix_parts = ["hybrid" if hybrid else "seedance"]
    if attempt > 1:
        suffix_parts.append(f"try{attempt}")
    item_id = make_item_id(title, suffix="-".join(suffix_parts))
    work = CONFIG.work_dir / item_id
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "script.json").write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"Seedance台本OK: 「{title}」 cuts={len(script['cues'])} candidate={attempt}")

    video_id = item_id
    cut_results: list = []
    images: list[Path] = []
    try:
        if hybrid and _seedance_audio_mode() != "voicevox":
            raise video_bg_gen.SeedanceError("混在版はVOICEVOX音声モードでのみ実行できます")
        bg, timed_cues, cut_results = _build_seedance_video(
            script, work, cue_indices=[0, 2] if hybrid else None
        )
        log(
            f"Seedance生成OK: {len(cut_results)}カット "
            f"({sum(c.duration_sec for c in cut_results):.0f}秒)"
        )
        video_bg_gen.record_cost(video_bg_gen.make_cost_record(video_id, cut_results, success=True))

        audio_mode = _seedance_audio_mode()
        if audio_mode == "voicevox":
            speaker_id = int(CONFIG.get("seedance", "voicevox_speaker_id", default=13))
            tts = tts_voicevox.synthesize_cues(
                _seedance_voicevox_cues(script),
                work,
                speaker_id=speaker_id,
                lead_in_sec=(
                    float(CONFIG.get("seedance", "hybrid_lead_in_sec", default=0.0))
                    if hybrid
                    else None
                ),
            )
            master_wav = Path(tts["master_wav"])
            final_cues = tts["cues"]
            total_dur = tts["total_dur"]
            credit = (
                f"{CONFIG.get('seedance', 'voicevox_speaker_credit', default='VOICEVOX:青山龍星')}"
                "／映像はAIで自動生成"
            )
            script["speaker_credit"] = CONFIG.get(
                "seedance", "voicevox_speaker_credit", default="VOICEVOX:青山龍星"
            )
            script["audio_mode"] = "voicevox"
            log(
                f"Seedance音声差し替えOK: VOICEVOX speaker={speaker_id} "
                f"duration={total_dur}s"
            )
        else:
            total_dur = timed_cues[-1]["end"] if timed_cues else 0.0
            # Seedance音声をそのままmaster_wavとして抽出（loudnorm測定・最終合成用）
            master_wav = work / "master_voice.wav"
            ffmpeg_bin = CONFIG.get("ffmpeg", default="ffmpeg")
            proc = subprocess.run(
                [str(ffmpeg_bin), "-y", "-i", str(bg), "-vn", "-ar", "48000", "-ac", "1", str(master_wav)],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise video_bg_gen.SeedanceError(
                    f"音声抽出失敗: {proc.stderr.decode('utf-8', errors='replace')[:300]}"
                )
            final_cues = timed_cues
            credit = "音声・映像はAIで自動生成"
            script["speaker_credit"] = "音声・映像はAIで自動生成"
            script["audio_mode"] = "native"
        if hybrid:
            images, image_provider = image_gen.generate_images(script, work / "images")
            if len(images) < 2:
                raise video_bg_gen.SeedanceError("混在版用の日本語カードを2枚用意できませんでした")
            bg = renderer.render_hybrid_background(
                [Path(cut_results[0].path), Path(cut_results[1].path)],
                images[:2],
                _hybrid_segment_durations(final_cues, total_dur),
                work,
            )
            script["presentation_mode"] = "hybrid_live_card"
            script["image_provider"] = image_provider
            log("混在背景OK: 実写→日本語カード→実写→日本語カード")
        (work / "script.json").write_text(
            json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        overlay = work / "overlay.png"
        renderer.make_overlay(title, credit, overlay)
        ass = work / "subs.ass"
        renderer.make_ass(final_cues, total_dur, ass)
        measured = renderer.measure_loudnorm(master_wav, work)
        final = renderer.compose_final(
            bg, overlay, ass, master_wav, total_dur, work, measured=measured,
        )
        log("SeedanceレンダリングOK")

        if audio_mode == "voicevox":
            report = verifier.verify_video(final, final_cues, total_dur, work)
        else:
            cer_line_max = float(CONFIG.get("seedance", "cer_line_max", default=0.30))
            cer_avg_max = float(CONFIG.get("seedance", "cer_avg_max", default=0.18))
            report = verifier.verify_video(
                final, final_cues, total_dur, work,
                cer_line_max=cer_line_max, cer_avg_max=cer_avg_max,
            )
        report["fix_loops"] = 0
        (work / "quality_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log(
            f"Seedance検証{'合格✅' if report['pass'] else '不合格⚠️'} "
            f"avg_cer={report['accuracy']['avg_cer']}"
        )
        previews = renderer.extract_previews(final, final_cues, work)
    except video_bg_gen.SeedanceError as e:
        # 課金ゼロの失敗(カット0件)も監査用に必ず記録する
        video_bg_gen.record_cost(
            video_bg_gen.make_cost_record(
                video_id, cut_results, success=False, detail=str(e)[:200]
            )
        )
        raise

    out_dir = save_outputs(
        item_id, final, ass, work, images, previews, title, script,
        credit=f"{credit}しています",
    )
    log(f"Seedance成果物保存: {out_dir}")
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
        "target_platform": "common",
        "provider": "hybrid_seedance" if hybrid else "seedance",
    }


def _generate_passable_seedance_candidate(
    topic_entry: str | dict,
    selected_difficulty: str,
    *,
    hybrid: bool = False,
) -> tuple[dict, int]:
    """Seedance候補を生成し、CER不合格なら1回だけ再生成する（config seedance.remake_max_attempts）。

    それでも不合格、または例外が発生した場合は呼び出し元でフォールバックする。
    """
    remake_max_attempts = max(1, int(CONFIG.get("seedance", "remake_max_attempts", default=1)) + 1)
    candidate = None
    discarded_count = 0
    for attempt in range(1, remake_max_attempts + 1):
        candidate = _build_seedance_candidate(
            topic_entry, selected_difficulty, attempt, hybrid=hybrid
        )
        report = candidate["report"]
        if report["pass"]:
            break
        if attempt >= remake_max_attempts:
            break
        discarded_count += 1
        _mark_discarded_candidate(candidate, attempt + 1)
        log(
            f"Seedance品質検証不合格のため再生成: "
            f"{candidate['item_id']} → attempt {attempt + 1}/{remake_max_attempts}"
        )
    assert candidate is not None
    return candidate, discarded_count


def _enabled_platforms() -> list[str]:
    configured = CONFIG.get("queue", "platforms", default=["x"]) or ["x"]
    valid = ("x", "instagram", "tiktok", "youtube")
    platforms = []
    for platform in configured:
        platform = script_gen.normalize_target_platform(str(platform))
        if platform in valid and platform not in platforms:
            platforms.append(platform)
    return platforms or ["x"]


def _select_topic_entry(topic: str | None, selected_difficulty: str) -> dict:
    if topic:
        return {"topic": topic, "difficulty": selected_difficulty}

    try:
        replenished = topic_store.replenish_topics(selected_difficulty)
        if replenished.get("added"):
            detail = replenished.get("details", {}).get(selected_difficulty, {})
            log(
                "ネタ帳を自動補充: "
                f"difficulty={selected_difficulty} added={replenished['added']} "
                f"before={detail.get('before')} after={detail.get('after')}"
            )
            notify.send_message(
                "📋 shorts-factory: "
                f"{selected_difficulty} のネタを{replenished['added']}本自動補充しました。"
            )
    except OSError as exc:
        if not topic_store.is_transient_io_error(exc):
            raise
        log(f"ネタ帳自動補充を一時スキップ: {exc}")

    # 未消費deferred itemを含むqueue内topicも予約済みとして扱い、再利用しない。
    topic_entry, remaining = topic_store.next_topic_entry(
        selected_difficulty, include_queue=True
    )
    if not topic_entry:
        fallback_entry, fallback_remaining = topic_store.next_topic_entry(include_queue=True)
        if fallback_entry:
            notify.send_message(
                f"⚠️ shorts-factory: {selected_difficulty} のネタが空です。"
                "別難易度のネタで代替します。"
            )
            return fallback_entry
        notify.send_message("⚠️ shorts-factory: ネタ帳が空です。topics.json に補充してください。")
        raise SystemExit("ネタ帳が空")
    return topic_entry


def _queue_candidate(
    candidate: dict,
    *,
    enabled_platforms: list[str] | tuple[str, ...] | None = None,
    variant_group_id: str | None = None,
) -> dict:
    report = candidate["report"]
    queue_kwargs = {}
    if enabled_platforms is not None:
        queue_kwargs["enabled_platforms"] = enabled_platforms
    if variant_group_id is not None:
        queue_kwargs["variant_group_id"] = variant_group_id
    item = queue_lib.new_item(
        candidate["item_id"],
        candidate["topic"],
        candidate["script"],
        candidate["out_dir"] / "final.mp4",
        report["duration"],
        report["size_mb"],
        candidate["out_dir"] / "quality_report.json",
        report["pass"],
        report["accuracy"]["avg_cer"],
        candidate["out_dir"],
        **queue_kwargs,
    )
    return item


def _generate_passable_candidate(
    topic_entry: str | dict,
    selected_difficulty: str,
    target_platform: str,
    item_suffix: str | None = None,
) -> tuple[dict, int]:
    remake_enabled, remake_max_attempts = _quality_remake_settings()
    candidate = None
    discarded_count = 0
    for attempt in range(1, remake_max_attempts + 1):
        candidate = _build_candidate(
            topic_entry,
            selected_difficulty,
            attempt,
            target_platform,
            item_suffix=item_suffix,
        )
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
    return candidate, discarded_count


def _platform_generation_retry_attempts() -> int:
    try:
        configured = int(CONFIG.get("content", "platform_generation_retry_attempts", default=2))
    except (TypeError, ValueError):
        configured = 2
    return max(1, configured)


def _generate_platform_candidate_with_retries(
    topic_entry: str | dict,
    selected_difficulty: str,
    target_platform: str,
    item_suffix: str | None = None,
) -> tuple[dict, int]:
    attempts = _platform_generation_retry_attempts()
    last_exc: Exception | None = None
    for platform_attempt in range(1, attempts + 1):
        try:
            return _generate_passable_candidate(
                topic_entry,
                selected_difficulty,
                target_platform,
                item_suffix=item_suffix,
            )
        except Exception as exc:
            last_exc = exc
            if platform_attempt >= attempts:
                break
            log(
                f"{target_platform}向け生成が失敗したため再試行: "
                f"attempt {platform_attempt + 1}/{attempts}: {exc}"
            )
    raise RuntimeError(f"{target_platform}向け生成が{attempts}回失敗: {last_exc}") from last_exc


def _record_topic_consume_deferred(item: dict, exc: OSError) -> None:
    item.setdefault("topic_store", {})["consume_deferred_error"] = str(exc)
    item.setdefault("history", []).append(
        {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "event": "topic_consume_deferred",
        }
    )
    queue_lib.save_item(item)


def produce(
    topic: str | None = None,
    send_queue: bool = True,
    difficulty: str | None = None,
    target_platform: str = "common",
) -> dict:
    """1本の動画を生成して結果情報を返す。"""
    selected_difficulty = topic_store.normalize_difficulty(difficulty) or scheduled_difficulty()
    target_platform = script_gen.normalize_target_platform(target_platform)
    use_topview = target_platform == "common" and is_topview_slot()
    # ネタ補充・消費やキュー遷移より先に実写在庫を検査する。不足時は外部通知も
    # 旧カード版の生成も起こさず、この定刻枠を安全停止する。
    if use_topview:
        topview_inventory.validate_inventory(CONFIG)
    if not topic and send_queue:
        scheduled_item = queue_lib.find_due_scheduled_draft(
            datetime.now().astimezone(), selected_difficulty
        )
        if scheduled_item:
            if use_topview and scheduled_item.get("provider") != "hybrid_topview":
                log(f"従来形式の予約済み動画はTopview枠に投入せず保留: {scheduled_item['id']}")
            else:
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
    topic_entry = _select_topic_entry(topic, selected_difficulty)
    selected_difficulty = topic_store.normalize_difficulty(
        topic_entry.get("difficulty") if isinstance(topic_entry, dict) else None
    ) or selected_difficulty
    topic = _topic_text(topic_entry)
    log(f"テーマ: {topic} (difficulty={selected_difficulty}, target_platform={target_platform})")

    # Topview枠ではSeedanceの判定・クライアント経路にすら入らない。
    use_seedance = False if use_topview else (target_platform == "common" and is_seedance_slot())
    use_hybrid_seedance = False if use_topview else (target_platform == "common" and is_hybrid_seedance_slot())
    candidate = None
    discarded_count = 0
    if use_topview:
        try:
            candidate, discarded_count = _generate_passable_topview_candidate(
                topic_entry, selected_difficulty
            )
            if not candidate["report"]["pass"]:
                raise HybridGenerationBlocked(
                    "Topview混在形式の品質検証が不合格のため停止しました。"
                    "従来カード版への代替は行いません。"
                )
        except HybridGenerationBlocked:
            raise
        except Exception as exc:  # Topview在庫/レンダリングの全失敗を安全停止する
            log(f"Topview混在形式を完走できないため停止: {exc}")
            raise HybridGenerationBlocked(
                "Topview混在形式を生成できなかったため停止しました。"
                "従来カード版への代替は行いません。"
            ) from exc
    elif use_seedance:
        try:
            candidate, discarded_count = _generate_passable_seedance_candidate(
                topic_entry, selected_difficulty, hybrid=use_hybrid_seedance
            )
            if not candidate["report"]["pass"]:
                if use_hybrid_seedance:
                    raise HybridGenerationBlocked(
                        "混在形式の品質検証が不合格のため停止しました。"
                        "従来カード版への代替は行いません。"
                    )
                log(
                    "Seedance版が品質検証不合格のまま上限到達 → "
                    "静止画カード版へフォールバック"
                )
                candidate = None
        except HybridGenerationBlocked:
            # 混在形式を作れない場合は公開候補・キューを作らず、その場で停止する。
            raise
        except video_bg_gen.SeedanceError as exc:
            if use_hybrid_seedance:
                log(f"混在形式の生成に失敗 → 従来カード版へ代替せず停止: {exc}")
                raise HybridGenerationBlocked(
                    "混在形式を生成できなかったため停止しました。"
                    "従来カード版への代替は行いません。"
                ) from exc
            log(f"Seedance版の生成に失敗 → 静止画カード版へフォールバック: {exc}")
            notify.send_message(
                f"⚠️ shorts-factory: Seedance生成に失敗したため静止画版で代替しました。\n"
                f"理由: {redact_secrets(str(exc))[:200]}"
            )
            candidate = None
        except Exception as exc:  # noqa: BLE001 - 予期しない失敗でも投稿を止めない
            if use_hybrid_seedance:
                log(f"混在形式で予期しない例外 → 従来カード版へ代替せず停止: {exc}")
                raise HybridGenerationBlocked(
                    "混在形式を生成できなかったため停止しました。"
                    "従来カード版への代替は行いません。"
                ) from exc
            log(f"Seedance版で予期しない例外 → 静止画カード版へフォールバック: {exc}")
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            log("Seedance失敗詳細:\n" + tb[-2000:])
            candidate = None

    if candidate is None:
        candidate, discarded_count = _generate_passable_candidate(
            topic_entry,
            selected_difficulty,
            target_platform,
            item_suffix=None if target_platform == "common" else target_platform,
        )
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
    item = _queue_candidate(candidate)

    try:
        remaining = topic_store.consume_topic(topic, item_id, title, selected_difficulty)
        if remaining <= topic_store.LOW_STOCK_THRESHOLD:
            notify.send_message(f"📋 shorts-factory: ネタ帳の残りが{remaining}本です。補充してください。")
    except OSError as exc:
        if not is_transient_io_error(exc):
            raise
        log(f"ネタ帳消費を後回し: {exc}")
        _record_topic_consume_deferred(item, exc)
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


def produce_platform_variants(
    topic: str | None = None,
    send_queue: bool = True,
    difficulty: str | None = None,
) -> dict:
    """有効SNSごとに別台本・別動画を生成し、1媒体1キューで登録する。"""
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

    topic_entry = _select_topic_entry(topic, selected_difficulty)
    selected_difficulty = topic_store.normalize_difficulty(
        topic_entry.get("difficulty") if isinstance(topic_entry, dict) else None
    ) or selected_difficulty
    topic_text = _topic_text(topic_entry)
    platforms = _enabled_platforms()
    group_id = f"{datetime.now().date().isoformat()}_{datetime.now().strftime('%H%M%S')}_platforms"
    log(
        f"テーマ: {topic_text} (difficulty={selected_difficulty}, "
        f"platform_variants={','.join(platforms)})"
    )

    candidates: list[tuple[str, dict, int]] = []
    for platform in platforms:
        candidate, discarded_count = _generate_platform_candidate_with_retries(
            topic_entry,
            selected_difficulty,
            platform,
            item_suffix=platform,
        )
        candidates.append((platform, candidate, discarded_count))

    results = []
    queued_items = []
    for platform, candidate, discarded_count in candidates:
        item = _queue_candidate(
            candidate,
            enabled_platforms=[platform],
            variant_group_id=group_id,
        )
        queued_items.append(item)
        report = candidate["report"]
        results.append(
            {
                "id": candidate["item_id"],
                "platform": platform,
                "output_dir": str(candidate["out_dir"]),
                "report": report,
                "title": candidate["title"],
                "quality_attempt": candidate.get("attempt", 1),
                "discarded_quality_failures": discarded_count,
            }
        )

    consume_title = f"SNS別動画: {topic_text}"
    for item in queued_items:
        item.setdefault("topic_store", {})["consume_group_slug"] = group_id
        item["topic_store"]["consume_title"] = consume_title

    try:
        remaining = topic_store.consume_topic(
            topic_text,
            group_id,
            consume_title,
            selected_difficulty,
        )
        for item in queued_items:
            item["topic_store"]["remaining"] = remaining
            queue_lib.save_item(item)
        if remaining <= topic_store.LOW_STOCK_THRESHOLD:
            notify.send_message(f"📋 shorts-factory: ネタ帳の残りが{remaining}本です。補充してください。")
    except OSError as exc:
        if not is_transient_io_error(exc):
            raise
        log(f"ネタ帳消費を後回し: {exc}")
        if queued_items:
            _record_topic_consume_deferred(queued_items[0], exc)
        notify.send_message(
            "⚠️ shorts-factory: Driveロックでネタ帳更新だけ後回しになりました。"
            f"SNS別キュー登録は完了しています: <code>{group_id}</code>"
        )

    for item, result in zip(queued_items, results):
        report = result["report"]
        out_dir = Path(result["output_dir"])
        if not report.get("pass"):
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
        elif CONFIG.get("queue", "auto_post", default=False):
            item["review"].update(
                {"owner_approved": True, "decided_at": datetime.now().isoformat(), "via": "auto_post"}
            )
            queue_lib.transition(item, "approved", "auto_post=true により自動承認")
            notify.send_video(
                out_dir / "final.mp4",
                "🤖 自動投稿モード: まもなく投稿します\n" + notify.preview_caption(item),
            )
        else:
            queue_lib.transition(item, "ready_for_review", "Telegram承認待ち")

    return {
        "id": group_id,
        "topic": topic_text,
        "difficulty": selected_difficulty,
        "platform_variants": True,
        "items": results,
    }


def result_summary(result: dict) -> dict:
    """Build stable CLI output for both newly generated and scheduled items."""
    if result.get("items"):
        items = result["items"]
        return {
            "id": result.get("id"),
            "platform_variants": True,
            "items": [
                {
                    "id": item.get("id"),
                    "platform": item.get("platform"),
                    "pass": (item.get("report") or {}).get("pass"),
                    "avg_cer": ((item.get("report") or {}).get("accuracy") or {}).get("avg_cer"),
                    "output": item.get("output_dir"),
                    "quality_attempt": item.get("quality_attempt"),
                    "discarded_quality_failures": item.get("discarded_quality_failures", 0),
                }
                for item in items
            ],
        }
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


def _topview_stock_counts() -> tuple[int, int, int] | None:
    """マニフェストから (有効, 未使用, 必要) を数える。読めない場合はNone。

    在庫不足の判定そのものは topview_inventory 側が行う。ここは通知に載せる
    残量表示だけを担い、ffprobeの再検査はしない。
    """
    try:
        manifest_path = Path(
            CONFIG.get("topview", "manifest", default="~/shorts-factory/topview_assets/manifest.json")
        ).expanduser()
        clips = json.loads(manifest_path.read_text(encoding="utf-8")).get("clips") or []
        enabled_clips = [c for c in clips if isinstance(c, dict) and c.get("enabled", True)]
    except Exception:  # noqa: BLE001 - 在庫が読めない事実自体は本文の詳細で伝わる
        return None
    unused = sum(1 for c in enabled_clips if int(c.get("use_count", 0) or 0) == 0)
    required = max(2, int(CONFIG.get("topview", "min_enabled_clips", default=6)))
    return len(enabled_clips), unused, required


def _topview_inventory_summary() -> str:
    """安全停止通知へ載せる実写在庫の残量。読めない場合は空文字を返す。"""
    counts = _topview_stock_counts()
    if counts is None:
        return ""
    total, unused, required = counts
    return f"在庫: 有効 {total} 本 / 未使用 {unused} 本 / 必要 {required} 本"


def warn_topview_stock_running_out() -> None:
    """未使用の実写在庫が次の定刻枠で尽きる前にオーナーへ補充を促す。

    1本の生成で未使用の12秒素材を1本消費し、使用済みは再利用しない。枯渇してから
    安全停止で気づくと、その枠の投稿がそのまま失われる。
    """
    counts = _topview_stock_counts()
    if counts is None:
        return
    _, unused, _ = counts
    threshold = int(CONFIG.get("topview", "low_stock_warn_clips", default=6))
    if unused > threshold:
        return
    remaining_videos = unused // TOPVIEW_CLIPS_PER_VIDEO
    try:
        notify.send_message(
            "⚠️ shorts-factory: Topview実写素材の残りが少なくなっています。\n"
            f"未使用 {unused} 本（残り約 {remaining_videos} 本ぶん）\n"
            "1本の生成で未使用の12秒素材1本を消費し、使用済みは再利用しません。\n"
            "補充: Topviewで9:16・無字幕の素材を書き出し、"
            "scripts/register_topview_assets.py で登録する"
        )
    except Exception as exc:  # noqa: BLE001 - 通知失敗で生成結果を捨てない
        log(f"Topview在庫警告の送信に失敗: {exc}")


def notify_safe_stop(exc: Exception) -> None:
    """定刻枠を安全停止した事実をオーナーへ通知する。

    安全停止は動画もキューも投稿も作らないため、通知がないと「投稿がなかった」
    ことに気づけない。通知の失敗で終了処理を壊さない。
    """
    if isinstance(exc, TopviewInventoryError):
        cause = "Topview実写素材の在庫不足または在庫不正"
        recovery = (
            "Topviewで9:16・無字幕の素材を書き出し、"
            "scripts/register_topview_assets.py で登録する"
        )
        detail = _topview_inventory_summary()
    else:
        # Telegramには例外本文や旧経路名を載せない。外部サービス由来のURL・
        # 応答本文などが、利用者向けの障害通知に混ざることを防ぐ。
        cause = "Topview混在動画の生成処理で停止"
        recovery = "Topview素材の在庫と実行ログを確認する"
        detail = _topview_inventory_summary()
    lines = [
        "⏹ shorts-factory: 定刻枠を安全停止しました（動画・キュー・投稿なし）",
        f"枠: {_slot_code()}",
        f"原因: {cause}",
    ]
    if detail:
        lines.append(detail)
    lines.append(f"復旧: {recovery}")
    lines.append("従来カード版への自動代替は行いません。")
    try:
        notify.send_message("\n".join(lines))
    except Exception as notify_exc:  # noqa: BLE001 - 通知失敗で停止処理を止めない
        log(f"安全停止通知の送信に失敗: {notify_exc}")


def main() -> None:
    drive_guard.install()
    CONFIG.assert_runtime_ready()
    ap = argparse.ArgumentParser(description="ショート動画全自動生成")
    ap.add_argument("--topic", help="テーマ（省略時はネタ帳から）")
    ap.add_argument("--no-queue", action="store_true", help="キュー登録・Telegram送信をしない")
    ap.add_argument(
        "--difficulty",
        choices=["beginner", "intermediate"],
        help="ネタ選択と台本の難易度。省略時は実行時刻のスロットから自動判定",
    )
    ap.add_argument(
        "--target-platform",
        choices=sorted(script_gen.VALID_TARGET_PLATFORMS),
        default="common",
        help="台本の寄せ先。通常運用はcommon、SNS別台本テスト時に x/instagram/tiktok/youtube を指定",
    )
    ap.add_argument(
        "--single-video",
        action="store_true",
        help="SNS別動画モードを使わず、従来どおり1本の動画を有効媒体へ投稿する",
    )
    args = ap.parse_args()
    try:
        # replacement生成と定刻生成が重なっても、topic選択から消費までを直列化する。
        with file_lock(CONFIG.state_dir / "locks" / "generator.lock"):
            use_platform_variants = (
                not args.no_queue
                and not args.single_video
                and args.target_platform == "common"
                and bool(CONFIG.get("content", "platform_variant_videos", default=True))
            )
            if use_platform_variants:
                result = produce_platform_variants(
                    topic=args.topic,
                    send_queue=not args.no_queue,
                    difficulty=args.difficulty,
                )
            else:
                result = produce(
                    topic=args.topic,
                    send_queue=not args.no_queue,
                    difficulty=args.difficulty,
                    target_platform=args.target_platform,
                )
        print(json.dumps(result_summary(result), ensure_ascii=False))
    except (HybridGenerationBlocked, TopviewInventoryError) as e:
        # 想定済みの混在形式停止は、投稿候補・承認ボタン付きプレビューを作らない。
        # ただし「今回は投稿がない」事実だけはオーナーへ通知する。
        log(f"⏹ 混在形式を安全停止: {e}")
        notify_safe_stop(e)
        sys.exit(1)
    except Exception as e:
        log(f"❌ パイプライン失敗: {e}")
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        log("失敗詳細:\n" + tb[-4000:])
        # 例外本文はログにだけ残す。Telegramへ生の外部応答・URL・旧経路名を
        # 転送しない。
        notify.send_message(
            "❌ shorts-factory: 動画生成処理で予期しない障害が発生しました。\n"
            "動画・キュー・投稿は作成していません。\n"
            "実行ログを確認してください。"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
