"""台本生成。

デフォルトは claude CLI ヘッドレス実行（このMacで認証済み・APIキー不要）。
secrets.yaml に openai_api_key を入れて llm.provider=openai にすれば
OpenAI Structured Outputs へ切替できる。

生成物はバリデータで機械検証し、違反があればエラー内容をフィードバックして
再生成する（最大 llm.retries 回）。字幕正確性の「生成層」防御。
"""
from __future__ import annotations

import json
import re
import subprocess
import unicodedata

from .config import CONFIG
from .jp_text import lcs_coverage, phonetic_hira
from . import topic_store

SCRIPT_SCHEMA_KEYS = {"title", "cues", "caption", "hashtags", "card_keywords"}
_KANA_RE = re.compile(r"^[ァ-ヶー、。・\s０-９0-9？?！!]+$")


def _char_width(s: str) -> int:
    """全角=1, 半角=0.5 で数える（字幕13文字制限は全角換算）。"""
    w = 0.0
    for ch in s:
        w += 1.0 if unicodedata.east_asian_width(ch) in ("F", "W", "A") else 0.5
    return int(w + 0.999)


def validate_script(data: dict, image_count: int) -> list[str]:
    """台本JSONの機械検証。問題点のリストを返す（空なら合格）。"""
    errs: list[str] = []
    if not isinstance(data, dict):
        return ["JSONオブジェクトではない"]
    missing = SCRIPT_SCHEMA_KEYS - set(data)
    if missing:
        errs.append(f"必須キー欠落: {sorted(missing)}")
        return errs

    title = data["title"]
    if not isinstance(title, str) or not (4 <= len(title) <= 32):
        errs.append("title は4〜32文字の文字列にすること")

    cues = data["cues"]
    if not isinstance(cues, list) or not (8 <= len(cues) <= 16):
        errs.append(f"cues は8〜16個にすること（現在 {len(cues) if isinstance(cues, list) else '不正'}）")
        return errs

    total_kana = 0
    max_line = CONFIG.get("subtitle", "max_chars_per_line", default=13)
    for i, cue in enumerate(cues):
        if not isinstance(cue, dict):
            errs.append(f"cue[{i}] がオブジェクトでない")
            continue
        disp = cue.get("display")
        if not isinstance(disp, list) or not (1 <= len(disp) <= 2):
            errs.append(f"cue[{i}].display は1〜2行の配列にすること")
        else:
            for j, line in enumerate(disp):
                if not isinstance(line, str) or not line.strip():
                    errs.append(f"cue[{i}].display[{j}] が空")
                elif _char_width(line) > max_line:
                    errs.append(
                        f"cue[{i}].display[{j}]「{line}」が{_char_width(line)}文字で上限{max_line}文字超過。短く分割すること"
                    )
        tts = cue.get("tts_text", "")
        if not isinstance(tts, str) or len(tts.strip()) < 3:
            errs.append(f"cue[{i}].tts_text が短すぎる")
        kana = cue.get("reading_kana", "")
        if not isinstance(kana, str) or len(kana.strip()) < 3:
            errs.append(f"cue[{i}].reading_kana が空または短すぎる")
        elif not _KANA_RE.match(kana.strip()):
            bad = "".join(sorted({c for c in kana if not _KANA_RE.match(c)}))[:10]
            errs.append(f"cue[{i}].reading_kana に非カタカナ文字あり（{bad}）。全てカタカナにすること")
        total_kana += len(kana)
        # 字幕表示内容が読み上げ文に実際に含まれるか（音韻ベースLCS包含チェック）
        if isinstance(disp, list) and isinstance(tts, str) and tts.strip():
            disp_norm = phonetic_hira("".join(disp))
            if disp_norm and lcs_coverage(disp_norm, phonetic_hira(tts)) < 0.70:
                errs.append(
                    f"cue[{i}] の字幕「{''.join(disp)}」に読み上げ文「{tts}」で話していない内容がある。"
                    "字幕は読み上げ文と同じ内容にすること"
                )

    if not (230 <= total_kana <= 480):
        errs.append(
            f"reading_kana 合計が{total_kana}文字。280〜400文字（許容230〜480）に収めること"
        )

    cap = data["caption"]
    if not isinstance(cap, str) or not (60 <= len(cap) <= 350):
        errs.append("caption は60〜350文字にすること")
    tags = data["hashtags"]
    if not isinstance(tags, list) or not (3 <= len(tags) <= 10) or not all(
        isinstance(t, str) and t.startswith("#") for t in tags
    ):
        errs.append("hashtags は #始まりの文字列3〜10個にすること")
    kws = data["card_keywords"]
    if not isinstance(kws, list) or len(kws) < image_count:
        errs.append(f"card_keywords は{image_count}個以上にすること")
    else:
        for k in kws[:image_count]:
            if not isinstance(k, str) or _char_width(k) > 12:
                errs.append(f"card_keyword「{k}」は12文字以内にすること")
    return errs


def _extract_json(text: str) -> dict:
    """LLM出力からJSONを頑健に抽出する。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return json.loads(text)


DIFFICULTY_GUIDANCE = {
    "beginner": (
        "初心者向け。専門用語を避け、今日すぐ1回試せる単純な使い方に絞る。"
        "前提知識は置かず、手順は3ステップ以内にする。"
    ),
    "intermediate": (
        "中級者向け。単なる便利ワザではなく、実務ワークフロー化・品質チェック・失敗例・"
        "判断基準・テンプレ運用を中心にする。プロンプト文の紹介だけで終わらせず、"
        "入力設計、検証、改善ループ、チーム運用のどれかを必ず入れる。"
    ),
}


def _build_prompt(topic: str, image_count: int, difficulty: str = "beginner") -> str:
    tpl = (CONFIG.prompts_dir / "script_prompt.md").read_text(encoding="utf-8")
    recent = topic_store.recent_titles(30)
    recent_str = "\n".join(f"- {t}" for t in recent) if recent else "（まだ無し）"
    difficulty = topic_store.normalize_difficulty(difficulty) or "beginner"
    return (
        tpl.replace("{topic}", topic)
        .replace("{difficulty}", difficulty)
        .replace("{difficulty_guidance}", DIFFICULTY_GUIDANCE[difficulty])
        .replace("{image_count}", str(image_count))
        .replace("{recent_titles}", recent_str)
    )


def _call_claude_cli(prompt: str) -> str:
    bin_path = CONFIG.get("llm", "claude_bin")
    model = CONFIG.get("llm", "claude_model") or None
    cmd = [bin_path, "-p", "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    # cwd はランタイムディレクトリ（プロジェクトのCLAUDE.md等を読み込ませない）
    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=CONFIG.get("llm", "timeout_sec", default=300),
        cwd=str(CONFIG.runtime_dir),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed rc={proc.returncode}: {proc.stderr[:500]}")
    wrapper = json.loads(proc.stdout)
    result = wrapper.get("result")
    if not result:
        raise RuntimeError(f"claude CLI empty result: {proc.stdout[:300]}")
    return result


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=CONFIG.openai_api_key)
    resp = client.chat.completions.create(
        model=CONFIG.get("llm", "openai_model", default="gpt-5.1"),
        messages=[
            {"role": "system", "content": "JSONのみを出力する日本語放送作家。"},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or ""


def generate_script(topic: str, difficulty: str = "beginner") -> dict:
    """テーマから検証済み台本JSONを生成する。"""
    image_count = int(CONFIG.get("images", "count", default=4))
    provider = CONFIG.get("llm", "provider", default="claude_cli")
    if provider == "openai" and not CONFIG.openai_api_key:
        provider = "claude_cli"

    difficulty = topic_store.normalize_difficulty(difficulty) or "beginner"
    prompt = _build_prompt(topic, image_count, difficulty)
    retries = int(CONFIG.get("llm", "retries", default=3))
    last_errs: list[str] = []
    for attempt in range(1, retries + 1):
        full_prompt = prompt
        if last_errs:
            full_prompt += (
                "\n\n## 前回出力の問題点（必ず修正すること）\n"
                + "\n".join(f"- {e}" for e in last_errs)
            )
        raw = _call_openai(full_prompt) if provider == "openai" else _call_claude_cli(full_prompt)
        try:
            data = _extract_json(raw)
        except (json.JSONDecodeError, ValueError) as e:
            last_errs = [f"JSONとしてパース不能: {e}"]
            continue
        errs = validate_script(data, image_count)
        if not errs:
            data["topic"] = topic
            data["difficulty"] = difficulty
            return data
        last_errs = errs
    raise RuntimeError(
        f"台本生成が{retries}回失敗。最終エラー: " + "; ".join(last_errs[:5])
    )
