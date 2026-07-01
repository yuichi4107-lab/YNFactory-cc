"""台本生成。

デフォルトは claude CLI ヘッドレス実行（このMacで認証済み・APIキー不要）。
secrets.yaml に openai_api_key を入れて llm.provider=openai にすれば
OpenAI Structured Outputs へ切替できる。

生成物はバリデータで機械検証し、違反があればエラー内容をフィードバックして
再生成する（最大 llm.retries 回）。字幕正確性の「生成層」防御。
"""
from __future__ import annotations

import json
import os
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
_SPEECH_TERM_REPLACEMENTS = {
    "chatgpt": "チャットジーピーティー",
    "claude": "クロード",
    "gemini": "ジェミニ",
    "perplexity": "パープレキシティ",
    "notebooklm": "ノートブックエルエム",
    "notebook lm": "ノートブックエルエム",
    "canva": "キャンバ",
    "gamma": "ガンマ",
    "figma": "フィグマ",
    "zapier": "ザピアー",
    "make": "メイク",
    "n8n": "エヌエイトエヌ",
    "openai": "オープンエーアイ",
    "youtube": "ユーチューブ",
    "instagram": "インスタグラム",
    "tiktok": "ティックトック",
    "excel": "エクセル",
    "google": "グーグル",
    "notion": "ノーション",
    "slack": "スラック",
    "zoom": "ズーム",
    "teams": "チームズ",
    "powerpoint": "パワーポイント",
    "pdf": "ピーディーエフ",
    "api": "エーピーアイ",
    "sns": "エスエヌエス",
    "kpi": "ケーピーアイ",
    "crm": "シーアールエム",
    "csv": "シーエスブイ",
    "url": "ユーアールエル",
    "llm": "エルエルエム",
    "dx": "ディーエックス",
    "it": "アイティー",
    "ec": "イーシー",
    "ai": "エーアイ",
    "%": "パーセント",
    "％": "パーセント",
}
_SPEECH_TERM_RE = re.compile(
    "|".join(re.escape(k) for k in sorted(_SPEECH_TERM_REPLACEMENTS, key=len, reverse=True)),
    re.IGNORECASE,
)
_DISPLAY_CANONICAL_TERMS = {
    "チャットジーピーティー": "ChatGPT",
    "チャットジィーピィーティィー": "ChatGPT",
    "チャットGPT": "ChatGPT",
    "chatgpt": "ChatGPT",
    "Claude": "Claude",
    "claude": "Claude",
    "クロード": "Claude",
    "Gemini": "Gemini",
    "gemini": "Gemini",
    "ジェミニ": "Gemini",
    "AI": "AI",
    "ai": "AI",
    "エーアイ": "AI",
}
_DISPLAY_CANONICAL_TERM_RE = re.compile(
    "|".join(re.escape(k) for k in sorted(_DISPLAY_CANONICAL_TERMS, key=len, reverse=True)),
    re.IGNORECASE,
)
_ALLOWED_DISPLAY_LATIN_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:ChatGPT|Claude|Gemini|AI)(?![A-Za-z0-9])",
    re.IGNORECASE,
)


def _speech_unstable_text(s: str) -> bool:
    return bool(_UNSTABLE_SPEECH_RE.search(s.replace("ChatGPT", "")))


def _replace_unstable_terms(text: str) -> str:
    return _SPEECH_TERM_RE.sub(
        lambda m: _SPEECH_TERM_REPLACEMENTS[m.group(0).lower()],
        text,
    )


def _normalize_display_terms(text: str) -> str:
    text = unicodedata.normalize("NFKC", _replace_unstable_terms(text))
    return _DISPLAY_CANONICAL_TERM_RE.sub(
        lambda m: _DISPLAY_CANONICAL_TERMS.get(m.group(0), _DISPLAY_CANONICAL_TERMS[m.group(0).lower()]),
        text,
    )


def _display_unstable_text(s: str) -> bool:
    stripped = _ALLOWED_DISPLAY_LATIN_RE.sub("", s)
    return bool(_UNSTABLE_SPEECH_RE.search(stripped))


def normalize_generated_script(data: dict) -> dict:
    """Normalize common English abbreviations before validation/TTS."""
    if not isinstance(data, dict):
        return data
    cues = data.get("cues")
    if not isinstance(cues, list):
        return data
    for cue in cues:
        if not isinstance(cue, dict):
            continue
        display = cue.get("display")
        if isinstance(display, list):
            cue["display"] = [
                _normalize_display_terms(line) if isinstance(line, str) else line
                for line in display
            ]
        for key in ("tts_text", "reading_kana"):
            if isinstance(cue.get(key), str):
                cue[key] = _replace_unstable_terms(cue[key])
    return data


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
                elif _display_unstable_text(line):
                    errs.append(
                        f"cue[{i}].display[{j}]「{line}」に英字または%記号あり。"
                        "AI、Claude、Gemini、ChatGPT以外はカタカナ・日本語表記にすること"
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


def _cue_signature(data: dict) -> str:
    parts: list[str] = []
    for cue in data.get("cues") or []:
        if not isinstance(cue, dict):
            continue
        display = cue.get("display")
        if isinstance(display, list):
            parts.extend(str(line) for line in display)
        parts.append(str(cue.get("tts_text") or ""))
        parts.append(str(cue.get("reading_kana") or ""))
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", "\n".join(parts))).lower()


def _recent_output_scripts(limit: int = 50) -> list[dict]:
    # Drive上のoutputsを直接走査するとFile Providerのロックで生成が止まりやすい。
    # 生成時の重複検知はruntimeローカルのwork履歴を正とする。
    try:
        paths = sorted(
            (p for p in CONFIG.work_dir.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return []
    scripts: list[dict] = []
    for out_dir in paths[:limit]:
        script_path = out_dir / "script.json"
        try:
            scripts.append(json.loads(script_path.read_text(encoding="utf-8")))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            continue
    return scripts


def recent_duplicate_errors(data: dict) -> list[str]:
    """Reject scripts that would recreate a recent video."""
    errs: list[str] = []
    title = str(data.get("title") or "").strip()
    if title:
        recent_titles = {
            unicodedata.normalize("NFKC", t).strip()
            for t in topic_store.recent_titles(50)
        }
        if unicodedata.normalize("NFKC", title).strip() in recent_titles:
            errs.append(f"title「{title}」は最近使用済み。別タイトル・別切り口にすること")

    signature = _cue_signature(data)
    if not signature:
        return errs
    for old in _recent_output_scripts(50):
        if signature == _cue_signature(old):
            old_title = old.get("title") or "無題"
            old_topic = old.get("topic") or ""
            errs.append(
                f"字幕/読み上げキューが過去動画「{old_title}」と同一。"
                f"別構成にすること（過去topic: {old_topic}）"
            )
            break
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

VALID_TARGET_PLATFORMS = {"common", "x", "instagram", "tiktok", "youtube"}

PLATFORM_GUIDANCE = {
    "common": (
        "共通動画向け。4媒体すべてで違和感が出ないよう、業務課題・判断基準・"
        "次に試す1アクションを中心にする。"
    ),
    "x": (
        "X向け。逆張り・問題提起・短い判断軸を強める。"
        "経営者やAI感度の高い実務家が返信・引用したくなる見解を入れる。"
    ),
    "instagram": (
        "Instagram向け。保存版・チェックリスト・3ステップを強める。"
        "後で見返せる実務テンプレとして成立させる。"
    ),
    "tiktok": (
        "TikTok向け。驚き・実演・あるあるを強める。"
        "難しいAI導入論を短く見せ、テンポを落とさない。"
    ),
    "youtube": (
        "YouTube Shorts向け。検索意図に合うHow-to・ツール比較・使い分けを強める。"
        "タイトルと内容を一致させ、長期で見られる解説にする。"
    ),
}


def normalize_target_platform(value: str | None) -> str:
    if not value:
        return "common"
    value = value.strip().lower()
    return value if value in VALID_TARGET_PLATFORMS else "common"


def _topic_text(topic: str | dict) -> str:
    if isinstance(topic, dict):
        return str(topic.get("topic") or "").strip()
    return str(topic or "").strip()


def _topic_meta(topic: str | dict) -> dict:
    if isinstance(topic, dict):
        return {k: v for k, v in topic.items() if v not in (None, "", [])}
    return {"topic": _topic_text(topic)}


def _list_text(value) -> str:
    if isinstance(value, list):
        return "、".join(str(v) for v in value if str(v).strip())
    return str(value or "").strip()


def _topic_context(meta: dict) -> str:
    lines: list[str] = []
    fields = [
        ("domain", "カテゴリ"),
        ("business_function", "業務領域"),
        ("primary_tools", "主なAIツール"),
        ("expertise_angle", "専門家視点"),
        ("target_persona", "想定視聴者"),
        ("avoid_angles", "避ける切り口"),
    ]
    for key, label in fields:
        value = _list_text(meta.get(key))
        if value:
            lines.append(f"- {label}: {value}")
    platform_angles = meta.get("platform_angles")
    if isinstance(platform_angles, dict) and platform_angles:
        lines.append("- SNS別の切り口:")
        for platform in ("x", "instagram", "tiktok", "youtube"):
            angle = str(platform_angles.get(platform) or "").strip()
            if angle:
                lines.append(f"  - {platform}: {angle}")
    return "\n".join(lines) if lines else "（追加メタ情報なし）"


def _build_prompt(
    topic: str | dict,
    image_count: int,
    difficulty: str = "beginner",
    target_platform: str = "common",
) -> str:
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
    target_platform = normalize_target_platform(target_platform)
    meta = _topic_meta(topic)
    topic_text = _topic_text(topic)
    return (
        tpl.replace("{topic}", topic_text)
        .replace("{difficulty}", difficulty)
        .replace("{difficulty_guidance}", DIFFICULTY_GUIDANCE[difficulty])
        .replace("{target_platform}", target_platform)
        .replace("{platform_guidance}", PLATFORM_GUIDANCE[target_platform])
        .replace("{topic_context}", _topic_context(meta))
        .replace("{image_count}", str(image_count))
        .replace("{recent_titles}", recent_str)
    )


def _call_claude_cli(prompt: str) -> str:
    bin_path = CONFIG.get("llm", "claude_bin")
    model = CONFIG.get("llm", "claude_model") or None
    cmd = [bin_path, "-p", "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    env = os.environ.copy()
    path_parts = []
    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if nvm_root.exists():
        path_parts.extend(str(p / "bin") for p in sorted(nvm_root.glob("v*"), reverse=True))
    path_parts.extend(["/opt/homebrew/bin", "/usr/local/bin", str(Path.home() / ".local" / "bin")])
    path_parts.append(env.get("PATH", ""))
    env["PATH"] = ":".join(p for p in path_parts if p)
    # cwd はランタイムディレクトリ（プロジェクトのCLAUDE.md等を読み込ませない）
    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=CONFIG.get("llm", "timeout_sec", default=300),
        cwd=str(CONFIG.runtime_dir),
        env=env,
    )
    if proc.returncode != 0:
        detail = proc.stderr[:500]
        if not detail.strip() and proc.stdout:
            try:
                detail = str(json.loads(proc.stdout).get("result") or proc.stdout[:500])
            except json.JSONDecodeError:
                detail = proc.stdout[:500]
        raise RuntimeError(f"claude CLI failed rc={proc.returncode}: {detail}")
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
        return "営業メール改善の手順", [
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
                "display": ["良い文面を", "共有します"],
                "tts_text": "反応がよかった文面は、チームで共有します。",
                "reading_kana": "ハンノウガヨカッタブンメンハ、チームデキョウユウシマス。",
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
    if "業務フロー" in topic or "自動化候補" in topic:
        return "自動化候補を見抜く3軸", [
            {
                "display": ["自動化する仕事", "勘で選んでない？"],
                "tts_text": "自動化する仕事、勘で選んでいませんか。",
                "reading_kana": "ジドウカスルシゴト、カンデエランデイマセンカ。",
                "emphasis": True,
            },
            {
                "display": ["見るのは", "三つだけです"],
                "tts_text": "見るのは、頻度、時間、ルール化の三つです。",
                "reading_kana": "ミルノハ、ヒンド、ジカン、ルールカノミッツデス。",
                "emphasis": True,
            },
            {
                "display": ["毎日ある作業を", "先に出します"],
                "tts_text": "まず毎日発生する作業を、先に書き出します。",
                "reading_kana": "マズマイニチハッセイスルサギョウヲ、サキニカキダシマス。",
                "emphasis": False,
            },
            {
                "display": ["一回の時間を", "横に書きます"],
                "tts_text": "次に、一回あたりの時間を横に書きます。",
                "reading_kana": "ツギニ、イッカイアタリノジカンヲヨコニカキマス。",
                "emphasis": False,
            },
            {
                "display": ["判断が単純なら", "候補です"],
                "tts_text": "判断が単純な作業ほど、最初の候補になります。",
                "reading_kana": "ハンダンガタンジュンナサギョウホド、サイショノコウホニナリマス。",
                "emphasis": True,
            },
            {
                "display": ["人の確認が多い", "仕事は後回し"],
                "tts_text": "人の確認が多い仕事は、後回しにします。",
                "reading_kana": "ヒトノカクニンガオオイシゴトハ、アトマワシニシマス。",
                "emphasis": False,
            },
            {
                "display": ["一週間だけ", "試します"],
                "tts_text": "候補を一つ選んだら、一週間だけ試します。",
                "reading_kana": "コウホヲヒトツエランダラ、イッシュウカンダケタメシマス。",
                "emphasis": False,
            },
            {
                "display": ["減った時間を", "数字で見ます"],
                "tts_text": "最後に、減った時間を数字で確認します。",
                "reading_kana": "サイゴニ、ヘッタジカンヲスウジデカクニンシマス。",
                "emphasis": False,
            },
            {
                "display": ["保存して次の", "棚卸しに使って"],
                "tts_text": "保存して、次の業務棚卸しで試してください。",
                "reading_kana": "ホゾンシテ、ツギノギョウムタナオロシデタメシテクダサイ。",
                "emphasis": False,
            },
        ]
    if "採用面接" in topic or "評価基準" in topic:
        return "面接評価をそろえる3基準", [
            {
                "display": ["面接評価", "人でズレてない？"],
                "tts_text": "面接評価、人によってズレていませんか。",
                "reading_kana": "メンセツヒョウカ、ヒトニヨッテズレテイマセンカ。",
                "emphasis": True,
            },
            {
                "display": ["質問を増やす前に", "基準をそろえる"],
                "tts_text": "質問を増やす前に、評価基準をそろえます。",
                "reading_kana": "シツモンヲフヤスマエニ、ヒョウカキジュンヲソロエマス。",
                "emphasis": True,
            },
            {
                "display": ["任せる仕事を", "三つ書きます"],
                "tts_text": "まず任せたい仕事を、三つだけ書きます。",
                "reading_kana": "マズマカセタイシゴトヲ、ミッツダケカキマス。",
                "emphasis": False,
            },
            {
                "display": ["必要な行動を", "言葉にします"],
                "tts_text": "次に、その仕事で必要な行動を言葉にします。",
                "reading_kana": "ツギニ、ソノシゴトデヒツヨウナコウドウヲコトバニシマス。",
                "emphasis": False,
            },
            {
                "display": ["五段階ではなく", "具体例で見る"],
                "tts_text": "五段階だけでなく、具体例で評価します。",
                "reading_kana": "ゴダンカイダケデナク、グタイレイデヒョウカシマス。",
                "emphasis": True,
            },
            {
                "display": ["発言の引用を", "一つ残します"],
                "tts_text": "候補者の発言は、引用として一つ残します。",
                "reading_kana": "コウホシャノハツゲンハ、インヨウトシテヒトツノコシマス。",
                "emphasis": False,
            },
            {
                "display": ["面接後すぐ", "根拠を書く"],
                "tts_text": "面接後すぐ、判断の根拠を書き残します。",
                "reading_kana": "メンセツゴスグ、ハンダンノコンキョヲカキノコシマス。",
                "emphasis": False,
            },
            {
                "display": ["評価者同士で", "ズレを見ます"],
                "tts_text": "評価者同士で、点数がズレた理由を見ます。",
                "reading_kana": "ヒョウカシャドウシデ、テンスウガズレタリユウヲミマス。",
                "emphasis": False,
            },
            {
                "display": ["迷った項目は", "保留にします"],
                "tts_text": "迷った項目は、その場で決めず保留にします。",
                "reading_kana": "マヨッタコウモクハ、ソノバデキメズホリュウニシマス。",
                "emphasis": False,
            },
            {
                "display": ["保存して次の", "面接で試して"],
                "tts_text": "保存して、次の面接準備で試してください。",
                "reading_kana": "ホゾンシテ、ツギノメンセツジュンビデタメシテクダサイ。",
                "emphasis": False,
            },
        ]
    if "競合比較" in topic or "差別化" in topic:
        return "競合比較で差が出る3視点", [
            {
                "display": ["競合比較", "表で終わってない？"],
                "tts_text": "競合比較、表で終わっていませんか。",
                "reading_kana": "キョウゴウヒカク、ヒョウデオワッテイマセンカ。",
                "emphasis": True,
            },
            {
                "display": ["見るべきは", "差の理由です"],
                "tts_text": "見るべきは、違いそのものではなく差の理由です。",
                "reading_kana": "ミルベキハ、チガイソノモノデハナクサノリユウデス。",
                "emphasis": True,
            },
            {
                "display": ["価格と機能を", "まず並べます"],
                "tts_text": "まず価格と機能を、横並びにします。",
                "reading_kana": "マズカカクトキノウヲ、ヨコナラビニシマス。",
                "emphasis": False,
            },
            {
                "display": ["次に顧客の", "不満を足します"],
                "tts_text": "次に、顧客が不満に思う点を足します。",
                "reading_kana": "ツギニ、コキャクガフマンニオモウテンヲタシマス。",
                "emphasis": False,
            },
            {
                "display": ["勝ち負けより", "選ばれる条件"],
                "tts_text": "勝ち負けより、選ばれる条件を見ます。",
                "reading_kana": "カチマケヨリ、エラバレルジョウケンヲミマス。",
                "emphasis": False,
            },
            {
                "display": ["自社が勝てる", "場面を探す"],
                "tts_text": "最後に、自社が勝てる場面を探します。",
                "reading_kana": "サイゴニ、ジシャガカテルバメンヲサガシマス。",
                "emphasis": True,
            },
            {
                "display": ["弱い項目は", "補う策を考える"],
                "tts_text": "弱い項目は、補う策を考えます。",
                "reading_kana": "ヨワイコウモクハ、オギナウサクヲカンガエマス。",
                "emphasis": False,
            },
            {
                "display": ["選ばれにくい", "理由も書く"],
                "tts_text": "選ばれにくい理由も、一行で書きます。",
                "reading_kana": "エラバレニクイリユウモ、イチギョウデカキマス。",
                "emphasis": False,
            },
            {
                "display": ["顧客別に", "結論を分ける"],
                "tts_text": "顧客の状況別に、結論を分けます。",
                "reading_kana": "コキャクノジョウキョウベツニ、ケツロンヲワケマス。",
                "emphasis": False,
            },
            {
                "display": ["保存して次の", "提案に使って"],
                "tts_text": "保存して、次の提案準備で試してください。",
                "reading_kana": "ホゾンシテ、ツギノテイアンジュンビデタメシテクダサイ。",
                "emphasis": False,
            },
        ]
    return "仕事で使える改善手順", [
        {
            "display": ["その依頼", "時間をムダに"],
            "tts_text": "その依頼、時間をムダにしているかもしれません。",
            "reading_kana": "ソノイライ、ジカンヲムダニシテイルカモシレマセン。",
            "emphasis": True,
        },
        {
            "display": ["原因は", "前提が足りない"],
            "tts_text": "原因は、最初の前提が足りないことです。",
            "reading_kana": "ゲンインハ、サイショノゼンテイガタリナイコトデス。",
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
            "display": ["一回で決めず", "二案を並べます"],
            "tts_text": "一回で決めず、二案を並べます。",
            "reading_kana": "イッカイデキメズ、ニアンヲナラベマス。",
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
            "display": ["使えた指示を", "保存します"],
            "tts_text": "使えた指示だけを、次回用に保存します。",
            "reading_kana": "ツカエタシジダケヲ、ジカイヨウニホゾンシマス。",
            "emphasis": False,
        },
        {
            "display": ["チームなら", "共有します"],
            "tts_text": "チームで使うなら、共有します。",
            "reading_kana": "チームデツカウナラ、キョウユウシマス。",
            "emphasis": False,
        },
        {
            "display": ["迷ったら", "前提を見直す"],
            "tts_text": "迷ったら、目的と制約を見直すと安定します。",
            "reading_kana": "マヨッタラ、モクテキトセイヤクヲミナオストアンテイシマス。",
            "emphasis": True,
        },
        {
            "display": ["保存して次の", "仕事で試して"],
            "tts_text": "保存して、次の仕事で試してください。",
            "reading_kana": "ホゾンシテ、ツギノシゴトデタメシテクダサイ。",
            "emphasis": False,
        },
    ]


def _fallback_script(
    topic: str | dict,
    difficulty: str,
    last_errs: list[str],
    target_platform: str = "common",
) -> dict:
    meta = _topic_meta(topic)
    topic_text = _topic_text(topic)
    title, cues = _fallback_cues_for_topic(topic_text)
    return {
        "title": title,
        "cues": cues,
        "caption": (
            f"{topic_text}の実務向けショートです。"
            "一回で当てにいくより、前提をそろえて記録しながら改善する方が安定します。"
            "保存して、次の仕事でそのまま試してみてください。"
        ),
        "hashtags": ["#生成AI", "#AI活用", "#AI導入", "#仕事術", "#業務効率化"],
        "card_keywords": ["前提整理", "記録", "改善", "共有"],
        "topic": topic_text,
        "difficulty": difficulty,
        "target_platform": normalize_target_platform(target_platform),
        "content_strategy": {
            key: meta[key]
            for key in ("domain", "business_function", "primary_tools", "expertise_angle", "target_persona")
            if key in meta
        },
        "platform_angles": meta.get("platform_angles", {}),
        "fallback_reason": "; ".join(last_errs[:3]),
    }


def generate_script(topic: str | dict, difficulty: str = "beginner", target_platform: str = "common") -> dict:
    """テーマから検証済み台本JSONを生成する。"""
    image_count = int(CONFIG.get("images", "count", default=4))
    provider = CONFIG.get("llm", "provider", default="claude_cli")
    if provider == "openai" and not CONFIG.openai_api_key:
        provider = "claude_cli"

    difficulty = topic_store.normalize_difficulty(difficulty) or "beginner"
    target_platform = normalize_target_platform(target_platform)
    topic_text = _topic_text(topic)
    meta = _topic_meta(topic)
    prompt = _build_prompt(topic, image_count, difficulty, target_platform)
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
            data = normalize_generated_script(_extract_json(raw))
        except (json.JSONDecodeError, ValueError) as e:
            last_errs = [f"JSONとしてパース不能: {e}"]
            continue
        errs = validate_script(data, image_count)
        if not errs:
            errs = recent_duplicate_errors(data)
        if not errs:
            data["topic"] = topic_text
            data["difficulty"] = difficulty
            data["target_platform"] = target_platform
            data["content_strategy"] = {
                key: meta[key]
                for key in ("domain", "business_function", "primary_tools", "expertise_angle", "target_persona")
                if key in meta
            }
            data["platform_angles"] = meta.get("platform_angles", {})
            return data
        last_errs = errs
    data = _fallback_script(topic, difficulty, last_errs, target_platform)
    errs = validate_script(data, image_count)
    if not errs:
        errs = recent_duplicate_errors(data)
    if not errs:
        return data
    raise RuntimeError(
        f"台本生成が{retries}回失敗し、フォールバック台本も不合格。最終エラー: "
        + "; ".join((last_errs + errs)[:5])
    )
