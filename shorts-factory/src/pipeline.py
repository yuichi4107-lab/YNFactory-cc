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
import unicodedata
from datetime import date, datetime
from pathlib import Path

from .config import CONFIG
from . import image_gen, notify, queue_lib, renderer, script_gen, topic_store, tts_voicevox, verifier


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(CONFIG.logs_dir / "pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def make_slug(title: str) -> str:
    s = unicodedata.normalize("NFKC", title).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) < 4:  # 日本語タイトルはローマ字が残らないので時刻ベースに
        s = datetime.now().strftime("%H%M%S")
    return s[:40]


def produce(topic: str | None = None, send_queue: bool = True) -> dict:
    """1本の動画を生成して結果情報を返す。"""
    # --- 0. トピック決定 ---
    if not topic:
        topic, remaining = topic_store.next_topic()
        if not topic:
            notify.send_message("⚠️ shorts-factory: ネタ帳が空です。topics.json に補充してください。")
            raise SystemExit("ネタ帳が空")
    log(f"テーマ: {topic}")

    # --- 1. 台本生成（生成層バリデーション込み） ---
    script = script_gen.generate_script(topic)
    title = script["title"]
    item_id = f"{date.today().isoformat()}_{make_slug(title)}"
    work = CONFIG.work_dir / item_id
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    (work / "script.json").write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"台本OK: 「{title}」 cues={len(script['cues'])}")

    # --- 2. TTS（合成層: 読み突合） ---
    try:
        tts = tts_voicevox.synthesize_cues(script["cues"], work)
        max_sec = float(CONFIG.get("video", "max_sec", default=60))
        if tts["total_dur"] > max_sec:
            # 尺超過 → 話速を上げて全再合成（1回だけ）
            new_speed = min(round(float(CONFIG.get("speed_scale", default=1.0)) * tts["total_dur"] / (max_sec * 0.96), 2), 1.35)
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
            bg, overlay, ass, Path(tts["master_wav"]), tts["total_dur"], work, measured=measured
        )
        log("レンダリングOK")

        # --- 5. 検証 → 自動修正ループ ---
        report = verifier.verify_video(final, tts["cues"], tts["total_dur"], work)
        loops = 0
        max_loops = int(CONFIG.get("verify", "max_fix_loops", default=5))
        crf = int(CONFIG.get("video", "crf", default=23))
        while not report["pass"] and loops < max_loops:
            loops += 1
            log(f"検証不合格 → 修正ループ {loops}/{max_loops}: "
                + ", ".join(c["name"] for c in report["checks"] if not c["pass"]))
            failed_idx = report["accuracy"]["failed_indices"]
            # かな直読み済みのキューは再合成しても変わらない → 打つ手が無ければ打ち切り
            actionable = [i for i in failed_idx if not tts["cues"][i].get("used_kana_fallback")]
            other_fails = [c["name"] for c in report["checks"]
                           if not c["pass"] and not c["name"].startswith("subtitle_accuracy")]
            if failed_idx and not actionable and not other_fails:
                log("修正手段なし（全不合格行がかな直読み済み）→ ループ打ち切り、人間確認へ")
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
                if c["name"] in ("loudness", "no_black_frames", "duration",
                                 "subtitle_within_audio", "resolution", "codecs"):
                    rerender_needed = True
            if rerender_needed:
                measured = renderer.measure_loudnorm(Path(tts["master_wav"]), work)
                final = renderer.compose_final(
                    bg, overlay, ass, Path(tts["master_wav"]), tts["total_dur"], work,
                    crf=crf, measured=measured,
                )
            report = verifier.verify_video(final, tts["cues"], tts["total_dur"], work)

        report["fix_loops"] = loops
        (work / "quality_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log(f"検証{'合格✅' if report['pass'] else '不合格⚠️（上限到達）'} "
            f"avg_cer={report['accuracy']['avg_cer']} loops={loops}")

        previews = renderer.extract_previews(final, tts["cues"], work)
    finally:
        tts_voicevox.shutdown_engine()

    # --- 6. 成果物をDriveへ保存 ---
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
    log(f"成果物保存: {out_dir}")

    # --- 7. ネタ帳消費 + キュー登録 + Telegramプレビュー ---
    remaining = topic_store.consume_topic(topic, item_id, title)
    if remaining <= topic_store.LOW_STOCK_THRESHOLD:
        notify.send_message(f"📋 shorts-factory: ネタ帳の残りが{remaining}本です。補充してください。")

    result = {"id": item_id, "output_dir": str(out_dir), "report": report, "title": title}
    if not send_queue:
        return result

    item = queue_lib.new_item(
        item_id, topic, script, out_dir / "final.mp4",
        report["duration"], report["size_mb"],
        out_dir / "quality_report.json", report["pass"],
        report["accuracy"]["avg_cer"], out_dir,
    )
    if not report["pass"]:
        queue_lib.transition(item, "blocked", "品質検証が上限到達でも不合格のため要人間確認")
        notify.send_video(out_dir / "final.mp4",
                          "⚠️ 品質検証不合格のため投稿保留\n" + notify.preview_caption(item))
        return result

    if CONFIG.get("queue", "auto_post", default=False):
        item["review"].update({"owner_approved": True, "decided_at": datetime.now().isoformat(), "via": "auto_post"})
        queue_lib.transition(item, "approved", "auto_post=true により自動承認")
        mid = notify.send_video(out_dir / "final.mp4", "🤖 自動投稿モード: まもなく投稿します\n" + notify.preview_caption(item))
    else:
        queue_lib.transition(item, "ready_for_review", "Telegram承認待ち")
        mid = notify.send_video(
            out_dir / "final.mp4",
            notify.preview_caption(item),
            reply_markup=notify.approval_keyboard(item_id),
        )
    if mid:
        item["telegram"]["message_id"] = mid
        queue_lib.save_item(item)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="ショート動画全自動生成")
    ap.add_argument("--topic", help="テーマ（省略時はネタ帳から）")
    ap.add_argument("--no-queue", action="store_true", help="キュー登録・Telegram送信をしない")
    args = ap.parse_args()
    try:
        result = produce(topic=args.topic, send_queue=not args.no_queue)
        print(json.dumps(
            {"id": result["id"], "pass": result["report"]["pass"],
             "avg_cer": result["report"]["accuracy"]["avg_cer"],
             "output": result["output_dir"]},
            ensure_ascii=False))
    except Exception as e:
        log(f"❌ パイプライン失敗: {e}")
        notify.send_message(f"❌ shorts-factory 生成失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
