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
from pathlib import Path

from .config import CONFIG
from .fs_retry import is_transient_io_error, retry_io
from .jp_text import lcs_coverage, phonetic_hira
from . import topic_store

SCRIPT_SCHEMA_KEYS = {"title", "cues", "caption", "hashtags", "card_keywords"}
_KANA_RE = re.compile(r"^[ァ-ヶー、。・\s０-９0-9？?！!]+$")
_UNSTABLE_SPEECH_RE = re.compile(r"[A-Za-z%％]")


def _speech_unstable_text(s: str) -> bool:
    return bool(_UNSTABLE_SPEECH_RE.search(s.replace("ChatGPT", "")))


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
                elif _speech_unstable_text(line):
                    errs.append(
                        f"cue[{i}].display[{j}]「{line}」に英字または%記号あり。"
                        "ChatGPT以外はカタカナ・日本語表記にすること"
                    )
        tts = cue.get("tts_text", "")
        if not isinstance(tts, str) or len(tts.strip()) < 3:
            errs.append(f"cue[{i}].tts_text が短すぎる")
        elif _speech_unstable_text(tts):
            errs.append(
                f"cue[{i}].tts_text に英字または%記号あり。ChatGPT以外はカタカナ・日本語表記にすること"
            )
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
    prompt_path = CONFIG.prompts_dir / "script_prompt.md"
    try:
        tpl = retry_io(
            lambda: prompt_path.read_text(encoding="utf-8"),
            attempts=8,
            delay_sec=3.0,
        )
    except OSError as exc:
        if not is_transient_io_error(exc):
            raise
        local_prompt = Path(__file__).resolve().parents[1] / "prompts" / "script_prompt.md"
        tpl = retry_io(
            lambda: local_prompt.read_text(encoding="utf-8"),
            attempts=3,
            delay_sec=1.0,
        )
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


def _fallback_cues_for_topic(topic: str) -> tuple[str, list[dict]]:
    if "営業メール" in topic:
        return "営業メール改善の型", [
            {
                "display": ["返信ゼロの原因", "そこじゃないかも"],
                "tts_text": "返信ゼロの原因、そこじゃないかもしれません。",
                "reading_kana": "ヘンシンゼロノゲンイン、ソコジャナイカモシレマセン。",
                "emphasis": True,
            },
            {
                "display": ["中級者はまず", "数字で見ます"],
                "tts_text": "中級者は、まず反応を数字で見ます。",
                "reading_kana": "チュウキュウシャハ、マズハンノウヲスウジデミマス。",
                "emphasis": True,
            },
            {
                "display": ["件名だけを", "一つ変えます"],
                "tts_text": "最初は、件名だけを一つ変えます。",
                "reading_kana": "サイショハ、ケンメイダケヲヒトツカエマス。",
                "emphasis": False,
            },
            {
                "display": ["本文冒頭は", "別で試します"],
                "tts_text": "本文の冒頭は、別の回で試します。",
                "reading_kana": "ホンブンノボウトウハ、ベツノカイデタメシマス。",
                "emphasis": False,
            },
            {
                "display": ["相手の役職を", "必ず入れる"],
                "tts_text": "相手の役職や悩みを、必ず入れます。",
                "reading_kana": "アイテノヤクショクヤナヤミヲ、カナラズイレマス。",
                "emphasis": False,
            },
            {
                "display": ["誰に何を頼むか", "明確にします"],
                "tts_text": "誰に何を頼むメールなのか、明確にします。",
                "reading_kana": "ダレニナニヲタノムメールナノカ、メイカクニシマス。",
                "emphasis": False,
            },
            {
                "display": ["送った数と返信を", "表に残します"],
                "tts_text": "送った数と返信数を、表に残します。",
                "reading_kana": "オクッタカズトヘンシンスウヲ、ヒョウニノコシマス。",
                "emphasis": True,
            },
            {
                "display": ["勝った文だけ", "残します"],
                "tts_text": "反応がよかった文だけを残します。",
                "reading_kana": "ハンノウガヨカッタブンダケヲノコシマス。",
                "emphasis": False,
            },
            {
                "display": ["次は違う要素を", "一つ試します"],
                "tts_text": "次は違う要素を、一つだけ試します。",
                "reading_kana": "ツギハチガウヨウソヲ、ヒトツダケタメシマス。",
                "emphasis": False,
            },
            {
                "display": ["全部変えると", "理由が消えます"],
                "tts_text": "全部を一気に変えると、理由が分からなくなります。",
                "reading_kana": "ゼンブヲイッキニカエルト、リユウガワカラナクナリマス。",
                "emphasis": True,
            },
            {
                "display": ["うまくいく型を", "共有します"],
                "tts_text": "うまくいく型は、チームで共有します。",
                "reading_kana": "ウマクイクカタハ、チームデキョウユウシマス。",
                "emphasis": False,
            },
            {
                "display": ["毎週見直して", "文面を育てます"],
                "tts_text": "毎週見直して、文面を育てます。",
                "reading_kana": "マイシュウミナオシテ、ブンメンヲソダテマス。",
                "emphasis": False,
            },
            {
                "display": ["保存して次の", "メールで試して"],
                "tts_text": "保存して、次の営業メールで試してください。",
                "reading_kana": "ホゾンシテ、ツギノエイギョウメールデタメシテクダサイ。",
                "emphasis": False,
            },
        ]
    return "仕事で使える改善の型", [
        {
            "display": ["その依頼", "時間をムダに"],
            "tts_text": "その依頼、時間をムダにしているかもしれません。",
            "reading_kana": "ソノイライ、ジカンヲムダニシテイルカモシレマセン。",
            "emphasis": True,
        },
        {
            "display": ["原因は", "型がないこと"],
            "tts_text": "原因は、最初の型がないことです。",
            "reading_kana": "ゲンインハ、サイショノカタガナイコトデス。",
            "emphasis": True,
        },
        {
            "display": ["目的と相手と", "制約を書きます"],
            "tts_text": "目的と相手と制約を、先に書きます。",
            "reading_kana": "モクテキトアイテトセイヤクヲ、サキニカキマス。",
            "emphasis": False,
        },
        {
            "display": ["出力形式も", "先に指定します"],
            "tts_text": "出力形式も、先に指定します。",
            "reading_kana": "シュツリョクケイシキモ、サキニシテイシマス。",
            "emphasis": False,
        },
        {
            "display": ["一回で決めず", "二案出させます"],
            "tts_text": "一回で決めず、二案出させます。",
            "reading_kana": "イッカイデキメズ、ニアンデサセマス。",
            "emphasis": False,
        },
        {
            "display": ["良い案だけを", "残して比べます"],
            "tts_text": "良い案だけを残して、比べます。",
            "reading_kana": "ヨイアンダケヲノコシテ、クラベマス。",
            "emphasis": False,
        },
        {
            "display": ["数字や事例で", "根拠を足します"],
            "tts_text": "数字や事例で、根拠を足します。",
            "reading_kana": "スウジヤジレイデ、コンキョヲタシマス。",
            "emphasis": True,
        },
        {
            "display": ["最後に弱点を", "自分で聞きます"],
            "tts_text": "最後に弱点を、自分で聞きます。",
            "reading_kana": "サイゴニジャクテンヲ、ジブンデキキマス。",
            "emphasis": False,
        },
        {
            "display": ["その反論まで", "直して完成"],
            "tts_text": "その反論まで直して、完成です。",
            "reading_kana": "ソノハンロンマデナオシテ、カンセイデス。",
            "emphasis": False,
        },
        {
            "display": ["毎回同じ型を", "保存します"],
            "tts_text": "毎回同じ型を、保存します。",
            "reading_kana": "マイカイオナジカタヲ、ホゾンシマス。",
            "emphasis": False,
        },
        {
            "display": ["チームなら", "共有します"],
            "tts_text": "チームで使うなら、共有します。",
            "reading_kana": "チームデツカウナラ、キョウユウシマス。",
            "emphasis": False,
        },
        {
            "display": ["迷ったら型に", "戻せば安定"],
            "tts_text": "迷ったら型に戻せば、品質が安定します。",
            "reading_kana": "マヨッタラカタニモドセバ、ヒンシツガアンテイシマス。",
            "emphasis": True,
        },
        {
            "display": ["保存して次の", "仕事で試して"],
            "tts_text": "保存して、次の仕事で試してください。",
            "reading_kana": "ホゾンシテ、ツギノシゴトデタメシテクダサイ。",
            "emphasis": False,
        },
    ]


def _fallback_script(topic: str, difficulty: str, last_errs: list[str]) -> dict:
    title, cues = _fallback_cues_for_topic(topic)
    return {
        "title": title,
        "cues": cues,
        "caption": (
            f"{topic}の実務向けショートです。"
            "一回で当てにいくより、型を作って記録しながら改善する方が安定します。"
            "保存して、次の仕事でそのまま試してみてください。"
        ),
        "hashtags": ["#ChatGPT", "#AI活用術", "#仕事術", "#業務効率化", "#営業"],
        "card_keywords": ["型化", "記録", "改善", "共有"],
        "topic": topic,
        "difficulty": difficulty,
        "fallback_reason": "; ".join(last_errs[:3]),
    }


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
        try:
            raw = _call_openai(full_prompt) if provider == "openai" else _call_claude_cli(full_prompt)
        except subprocess.TimeoutExpired:
            last_errs = [
                f"{provider} が {CONFIG.get('llm', 'timeout_sec', default=300)} 秒でタイムアウト。"
                "同じ条件で再試行すること"
            ]
            continue
        except RuntimeError as e:
            last_errs = [str(e)]
            continue
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
    data = _fallback_script(topic, difficulty, last_errs)
    errs = validate_script(data, image_count)
    if not errs:
        return data
    raise RuntimeError(
        f"台本生成が{retries}回失敗し、フォールバック台本も不合格。最終エラー: "
        + "; ".join((last_errs + errs)[:5])
    )
