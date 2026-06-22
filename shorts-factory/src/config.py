"""shorts-factory 設定ローダー。

優先順位: 環境変数 > ~/shorts-factory/config.yaml > DEFAULTS
秘密情報は ~/shorts-factory/secrets.yaml（Drive外）に置く。
SNS認証は既存の .company/engineering/sns-credentials/.env を参照する。
"""
from __future__ import annotations

import copy
import os
from pathlib import Path

import yaml

RUNTIME_DIR = Path(os.environ.get("SHORTS_RUNTIME_DIR", str(Path.home() / "shorts-factory")))


def _candidate_repo_roots() -> list[Path]:
    candidates: list[Path] = []
    for key in ("SHORTS_REPO_ROOT", "YNFACTORY_ROOT"):
        if os.environ.get(key):
            candidates.append(Path(os.environ[key]))

    here = Path(__file__).resolve()
    candidates.extend(
        [
            here.parents[2] if len(here.parents) > 2 else here.parent,
            Path.cwd(),
            Path.home()
            / "Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc",
            Path.home()
            / "Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc",
            Path.home() / "YNFactory-cc",
        ]
    )
    return candidates


def _resolve_repo_root() -> Path:
    for candidate in _candidate_repo_roots():
        if (candidate / "shorts-factory" / "src").exists():
            return candidate
    return _candidate_repo_roots()[0]


# Drive上のリポジトリルート（デプロイ先から実行されても Drive を指す）
DEFAULT_REPO_ROOT = _resolve_repo_root()

DEFAULTS: dict = {
    "speaker_id": 3,  # ずんだもん（ノーマル）
    "speaker_credit": "VOICEVOX:ずんだもん",
    "speed_scale": 1.0,
    "llm": {
        "provider": "claude_cli",  # claude_cli | openai
        "claude_bin": "/Users/yuichi/.local/bin/claude",
        "claude_model": "",  # 空 = CLIデフォルト
        "openai_model": "gpt-5.1",
        "timeout_sec": 300,
        "retries": 3,
    },
    "images": {
        "provider": "card",  # card | openai | gemini （キー投入でAI画像へ切替）
        "count": 4,
        "openai_model": "gpt-image-2",
        "openai_quality": "medium",
        "gemini_model": "gemini-3.1-flash-image-preview",
    },
    "video": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "crf": 23,
        "min_sec": 30,
        "max_sec": 60,
        "max_mb": 50,
        "xfade_sec": 0.5,
        "lead_in_sec": 0.4,
        "tail_sec": 0.8,
        "cue_gap_sec": 0.18,
    },
    "subtitle": {
        "font": "Noto Sans JP",
        "fontsize": 76,
        "max_chars_per_line": 13,
        "margin_v": 600,
    },
    "tts": {
        "engine_dir": str(RUNTIME_DIR / "voicevox"),
        "host": "127.0.0.1",
        "port": 50021,
        "output_sampling_rate": 48000,
        "kana_mismatch_cer": 0.15,  # これを超えたら読み仮名直読みに切替
    },
    "verify": {
        "whisper_provider": "local",  # local | openai
        "whisper_bin": "/opt/homebrew/bin/whisper-cli",
        "whisper_model": str(RUNTIME_DIR / "models" / "ggml-large-v3-turbo.bin"),
        "cer_line_max": 0.20,
        "cer_avg_max": 0.10,
        "lufs_target": -14.0,
        "lufs_tol": 2.0,
        "max_fix_loops": 5,
    },
    "queue": {
        "auto_post": False,  # True で承認スキップ → 即投稿
        "platforms": ["x"],  # x | youtube | instagram | tiktok（工程進行で追加）
        "retry_failed_posts": True,  # 投稿失敗時、失敗媒体だけ自動再投稿
        "retry_max_attempts": 2,  # 初回失敗後の自動再投稿回数
        "retry_delay_sec": 60,  # 再投稿前の待機秒数
    },
    "cta": {
        "lp_url": "https://ai.yn-factory.com/",
        "campaign": "shorts_ai_consult",
    },
    "youtube": {
        "cdp_port": 9223,
    },
    "tiktok": {
        "cdp_port": 9224,
        "profile_dir": str(RUNTIME_DIR / ".auth" / "tiktok-chrome"),
    },
    "content": {
        "default_difficulty": "beginner",
        "scheduled_slots": [
            {"hour": 9, "minute": 0, "difficulty": "beginner"},
            {"hour": 14, "minute": 0, "difficulty": "intermediate"},
            {"hour": 19, "minute": 0, "difficulty": "intermediate"},
        ],
    },
    "telegram": {"enabled": True},
    "ffmpeg": "/Users/yuichi/bin/ffmpeg",
    "ffprobe": "/opt/homebrew/bin/ffprobe",
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_yaml(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


class Config:
    def __init__(self) -> None:
        self.runtime_dir = RUNTIME_DIR
        self.repo_root = DEFAULT_REPO_ROOT
        self.cfg = _deep_merge(DEFAULTS, _load_yaml(RUNTIME_DIR / "config.yaml"))
        self.secrets = _load_yaml(RUNTIME_DIR / "secrets.yaml")

        # ディレクトリ群
        self.factory_dir = self.repo_root / "shorts-factory"
        self.assets_dir = self.factory_dir / "assets"
        self.fonts_dir = self.assets_dir / "fonts"
        self.prompts_dir = self.factory_dir / "prompts"
        self.marketing_dir = self.repo_root / ".company" / "marketing" / "shorts-factory"
        self.queue_dir = self.marketing_dir / "queue"
        self.topics_path = self.marketing_dir / "topics.json"
        self.outputs_dir = self.repo_root / ".company" / "outputs" / "shorts-factory"
        self.work_dir = self.runtime_dir / "work"
        self.logs_dir = self.runtime_dir / "logs"
        self.sns_env_path = (
            self.repo_root / ".company" / "engineering" / "sns-credentials" / ".env"
        )
        for d in (self.work_dir, self.logs_dir):
            d.mkdir(parents=True, exist_ok=True)

    # --- 取得ヘルパ ---
    def get(self, *keys, default=None):
        cur = self.cfg
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def secret(self, *keys, default=None):
        cur = self.secrets
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    @property
    def openai_api_key(self) -> str | None:
        return os.environ.get("OPENAI_API_KEY") or self.secret("openai_api_key") or None

    @property
    def gemini_api_key(self) -> str | None:
        return os.environ.get("GEMINI_API_KEY") or self.secret("gemini_api_key") or None

    @property
    def telegram_token(self) -> str | None:
        return os.environ.get("SHORTS_TG_TOKEN") or self.secret("telegram", "bot_token")

    @property
    def telegram_chat_id(self) -> str | None:
        v = os.environ.get("SHORTS_TG_CHAT_ID") or self.secret("telegram", "chat_id")
        return str(v) if v is not None else None


CONFIG = Config()
