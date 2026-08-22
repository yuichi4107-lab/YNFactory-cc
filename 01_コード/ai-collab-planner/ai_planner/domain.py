from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


Provider = Literal["codex", "claude", "none"]
Level = Literal["light", "standard", "complex", "critical"]


@dataclass(frozen=True)
class Role:
    provider: Provider
    model: str

    @property
    def enabled(self) -> bool:
        return self.provider != "none" and self.model != "none"


@dataclass(frozen=True)
class ModelTeam:
    level: Level
    label: str
    fork_extractor: Role
    fork_auditor: Role
    primary_planner: Role
    secondary_planner: Role
    plan_reviewer: Role
    final_decider: Role
    requirements_final_checker: Role
    recommended_implementer: Role
    recommended_code_reviewer: Role
    recommended_final_gate: Role
    max_debate_rounds: int = 0

    @property
    def debate_enabled(self) -> bool:
        """議論工程を実行できる構成かどうか。"""
        return (
            self.max_debate_rounds > 0
            and self.fork_extractor.enabled
            and self.secondary_planner.enabled
            and self.plan_reviewer.enabled
        )


@dataclass(frozen=True)
class RoutingDecision:
    level: Level
    reasons: tuple[str, ...]
    matched_keywords: tuple[str, ...]


@dataclass(frozen=True)
class RunResult:
    provider: Provider
    model: str
    output: str
    return_code: int
    command_summary: str


@dataclass(frozen=True)
class ProjectState:
    root: Path
    is_git: bool
    git_root: Path | None
    branch: str
    dirty_files: tuple[str, ...]
