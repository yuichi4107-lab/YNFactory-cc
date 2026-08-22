from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .domain import ModelTeam, Role


@dataclass(frozen=True)
class VoiceSettings:
    backend: str
    whisper_model: str
    device: str
    compute_type: str
    max_recording_seconds: int
    start_timeout_seconds: int
    silence_seconds: float
    silence_threshold: float
    initial_prompt: str
    corrections: dict[str, str]
    input_device: str


@dataclass(frozen=True)
class AppSettings:
    codex_command: str
    claude_command: str
    timeout_seconds: int
    projects_directory: str
    default_workspace: str
    voice: VoiceSettings
    teams: dict[str, ModelTeam]
    critical_keywords: tuple[str, ...]
    complex_keywords: tuple[str, ...]
    light_keywords: tuple[str, ...]


def load_settings(path: Path) -> AppSettings:
    with path.open("rb") as file:
        data = tomllib.load(file)

    app = data["application"]
    commands = data["commands"]
    routing = data["routing"]
    voice = data.get("voice", {})
    teams: dict[str, ModelTeam] = {}

    for level in ("light", "standard", "complex", "critical"):
        raw = data["models"][level]
        teams[level] = ModelTeam(
            level=level,  # type: ignore[arg-type]
            label=raw["label"],
            fork_extractor=_role(raw, "fork_extractor"),
            fork_auditor=_role(raw, "fork_auditor"),
            max_debate_rounds=int(raw["max_debate_rounds"]),
            primary_planner=_role(raw, "primary_planner"),
            secondary_planner=_role(raw, "secondary_planner"),
            plan_reviewer=_role(raw, "plan_reviewer"),
            final_decider=_role(raw, "final_decider"),
            requirements_final_checker=_role(raw, "requirements_final_checker"),
            recommended_implementer=_role(raw, "implementer"),
            recommended_code_reviewer=_role(raw, "code_reviewer"),
            recommended_final_gate=_role(raw, "final_gate"),
        )

    return AppSettings(
        codex_command=_safe_command(commands["codex"], "codex"),
        claude_command=_safe_command(commands["claude"], "claude"),
        timeout_seconds=int(commands["timeout_seconds"]),
        projects_directory=str(app.get("projects_directory", "05_プロジェクト")),
        default_workspace=str(app.get("default_workspace", "")),
        voice=VoiceSettings(
            backend=str(voice.get("backend", "auto")),
            whisper_model=str(voice.get("whisper_model", "small")),
            device=str(voice.get("device", "cpu")),
            compute_type=str(voice.get("compute_type", "int8")),
            max_recording_seconds=int(voice.get("max_recording_seconds", 60)),
            start_timeout_seconds=int(voice.get("start_timeout_seconds", 10)),
            silence_seconds=float(voice.get("silence_seconds", 1.2)),
            silence_threshold=float(voice.get("silence_threshold", 0.012)),
            initial_prompt=str(voice.get("initial_prompt", "")),
            corrections={str(key): str(value) for key, value in voice.get("corrections", {}).items()},
            input_device=str(voice.get("input_device", "")),
        ),
        teams=teams,
        critical_keywords=tuple(routing["critical_keywords"]),
        complex_keywords=tuple(routing["complex_keywords"]),
        light_keywords=tuple(routing["light_keywords"]),
    )


_COMMAND_NAME = re.compile(r"[A-Za-z0-9._-]+")


def _safe_command(value: object, key: str) -> str:
    """設定値は実行ファイル名としてそのまま使われるため、形式を制限する。

    パス区切り・空白・シェルメタ文字を含む値を許すと、config.tomlを書き換えるだけで
    別のコマンドを起動できてしまう。
    """
    text = str(value)
    if not _COMMAND_NAME.fullmatch(text):
        raise ValueError(
            f"config.tomlの[commands].{key}に使えない文字が含まれています: {text!r}。"
            "英数字、ドット、ハイフン、アンダースコアだけのコマンド名を指定してください。"
        )
    return text


def _role(raw: dict, prefix: str) -> Role:
    return Role(
        provider=raw[f"{prefix}_provider"],
        model=str(raw[f"{prefix}_model"]),
    )
