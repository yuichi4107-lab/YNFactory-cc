from __future__ import annotations

from .config import AppSettings
from .domain import RoutingDecision


def decide_level(goal: str, settings: AppSettings) -> RoutingDecision:
    """自然言語の目的を、説明可能な固定ルールで分類する。"""
    normalized = goal.casefold()

    critical = _matches(normalized, settings.critical_keywords)
    if critical:
        return RoutingDecision(
            level="critical",
            reasons=("失敗時の影響が大きい高リスク要素を含みます。",),
            matched_keywords=critical,
        )

    complex_hits = _matches(normalized, settings.complex_keywords)
    if len(complex_hits) >= 1 or len(goal) >= 500:
        reason = "複数段階の技術判断が必要です。"
        if len(goal) >= 500:
            reason = "依頼内容が長く、複数の要件を含みます。"
        return RoutingDecision(
            level="complex",
            reasons=(reason,),
            matched_keywords=complex_hits,
        )

    light_hits = _matches(normalized, settings.light_keywords)
    if light_hits and len(goal) < 200:
        return RoutingDecision(
            level="light",
            reasons=("変更範囲が明確な軽作業と判断しました。",),
            matched_keywords=light_hits,
        )

    return RoutingDecision(
        level="standard",
        reasons=("一般的な機能追加または改善作業と判断しました。",),
        matched_keywords=(),
    )


def _matches(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(keyword for keyword in keywords if keyword.casefold() in text)

