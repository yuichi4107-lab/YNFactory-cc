from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .clients import ModelRunner
from .domain import ModelTeam
from .project import (
    append_decision,
    create_run_directory,
    goal_path,
    plan_path,
    requirements_path,
    status_path,
    write_text,
)
from .prompts import (
    FINAL_HEADINGS,
    audit_forks,
    extract_forks_and_stances,
    final_check_requirements,
    finalize_plan,
    finalize_plan_without_debate,
    independent_plan,
    list_issues,
    mediate_round,
    respond_to_issues,
    solo_plan,
)
from .safety import (
    assert_no_injection,
    assert_no_secrets,
    injection_warning,
    scan_injection,
)


Progress = Callable[[str], None]
Approve = Callable[[str], bool]

CONTINUE = "続行"
STOP_INTEGRATED = "終了：統合完了"
STOP_STALLED = "終了：停滞"
CONTINUATION_TOKENS = (CONTINUE, STOP_INTEGRATED, STOP_STALLED)

FORK_DOCUMENT_HEADING = "# 分岐点と立場"
NO_FORKS_MARKER = "なし"


@dataclass
class WorkflowOutcome:
    run_dir: Path
    requirements_created: bool
    completed: bool
    rounds_used: int = 0
    stop_reason: str = ""
    issue_ids: tuple[str, ...] = field(default_factory=tuple)


def _always_approve(_document: str) -> bool:
    return True


class CollaborationWorkflow:
    """要件定義と実装プランだけを作る、読み取り専用のAIワークフロー。

    2案のどちらかを選ぶのではなく、両案の良いところを統合することを目的とする。
    """

    def __init__(
        self,
        runner: ModelRunner,
        progress: Progress,
        approve: Approve = _always_approve,
    ):
        self.runner = runner
        self.progress = progress
        self.approve = approve

    def execute(
        self,
        root: Path,
        goal: str,
        team: ModelTeam,
    ) -> WorkflowOutcome:
        run_dir = create_run_directory(root)
        final_requirements_path = requirements_path(root)

        # 依頼文はGOAL.mdへ保存され、すべての工程のプロンプトへ埋め込まれる。
        # 接続文字列などを貼り付けた場合に備え、書き込む前に検査する。
        assert_no_secrets("依頼文", goal)
        write_text(goal_path(root), f"# 目的\n\n{goal}")
        write_text(status_path(root), "# 現在の状態\n\n要件定義中（実装は行いません）")

        facts = "（事前の事実確認は行っていません。必要な範囲でフォルダを確認してください。）"
        forks = ""
        stance_a = ""
        stance_b = ""
        debate = False

        if team.debate_enabled:
            forks = self._build_forks_document(goal, team, root)
            write_text(run_dir / "01_forks_and_stances.md", forks)
            facts = _section(forks, "## 確認した事実") or facts

            # 対象フォルダのファイルに仕込まれた誘導文が、ここから全工程へ広がる。
            # 自動停止はせず、人間が止められるように警告して承認を求める。
            injection = scan_injection(forks)
            if injection:
                self.progress(
                    "AIへの指示に見える文を検出しました。承認画面の警告を確認してください。"
                )

            no_forks = _has_no_forks(forks)
            if no_forks and not injection:
                self.progress("分岐点がないため、議論を行わず要件定義へ進みます。")
            elif not self.approve(injection_warning(injection) + forks):
                write_text(
                    status_path(root),
                    "# 現在の状態\n\n分岐点と立場が承認されなかったため中止（実装は未実施）",
                )
                self.progress("承認されなかったため、AIを追加で呼ばずに中止しました。")
                return WorkflowOutcome(run_dir, False, False, 0, "承認されませんでした")
            elif not no_forks:
                debate = True
                stance_a = _section(forks, "## 立場A")
                stance_b = _section(forks, "## 立場B")

        if not debate:
            return self._run_without_debate(root, run_dir, goal, team, facts)

        return self._run_with_debate(
            root=root,
            run_dir=run_dir,
            goal=goal,
            team=team,
            facts=facts,
            forks=forks,
            stance_a=stance_a,
            stance_b=stance_b,
        )

    # ------------------------------------------------------------------
    # 分岐点と立場
    # ------------------------------------------------------------------

    def _build_forks_document(self, goal: str, team: ModelTeam, root: Path) -> str:
        self.progress(f"分岐点と立場を抽出: {team.fork_extractor.model}")
        extracted = self.runner.run(
            team.fork_extractor,
            extract_forks_and_stances(goal),
            root,
            writable=False,
        )
        forks = _validate_output("分岐点と立場", extracted.output)
        _validate_forks(forks)

        if team.fork_auditor.enabled:
            self.progress(f"分岐点の抜けを補完: {team.fork_auditor.model}")
            audited = self.runner.run(
                team.fork_auditor,
                audit_forks(goal, forks),
                root,
                writable=False,
            )
            forks = _validate_output("分岐点の補完", audited.output)
            _validate_forks(forks)
        return forks

    # ------------------------------------------------------------------
    # 議論なしの経路
    # ------------------------------------------------------------------

    def _run_without_debate(
        self,
        root: Path,
        run_dir: Path,
        goal: str,
        team: ModelTeam,
        facts: str,
    ) -> WorkflowOutcome:
        self.progress(f"要件定義案を作成: {team.primary_planner.model}")
        primary = self.runner.run(
            team.primary_planner,
            solo_plan(goal, facts),
            root,
            writable=False,
        )
        primary_output = _validate_output("要件定義案", primary.output)
        write_text(run_dir / "02_plan.md", primary_output)

        self.progress(f"要件定義書と実装プランを統合: {team.final_decider.model}")
        draft = self.runner.run(
            team.final_decider,
            finalize_plan_without_debate(goal, primary_output, team),
            root,
            writable=False,
        )
        draft_output = _validate_output(
            "要件定義書・実装プランの統合案",
            draft.output,
            required_headings=FINAL_HEADINGS,
        )
        write_text(run_dir / "90_requirements_draft.md", draft_output)

        checked_output = self._final_check(root, run_dir, goal, team, draft_output, "")
        self._save_final(root, run_dir, team, checked_output, rounds_used=0, stop_reason="議論なし")
        return WorkflowOutcome(run_dir, True, True, 0, "議論なし")

    # ------------------------------------------------------------------
    # 議論ありの経路
    # ------------------------------------------------------------------

    def _run_with_debate(
        self,
        root: Path,
        run_dir: Path,
        goal: str,
        team: ModelTeam,
        facts: str,
        forks: str,
        stance_a: str,
        stance_b: str,
    ) -> WorkflowOutcome:
        self.progress(f"立場Aの案を作成: {team.primary_planner.model}")
        plan_a = _validate_output(
            "立場Aの案",
            self.runner.run(
                team.primary_planner,
                independent_plan(goal, "立場A", stance_a, facts),
                root,
                writable=False,
            ).output,
        )
        write_text(run_dir / "02_plan_stance_a.md", plan_a)

        self.progress(f"立場Bの案を作成: {team.secondary_planner.model}")
        plan_b = _validate_output(
            "立場Bの案",
            self.runner.run(
                team.secondary_planner,
                independent_plan(goal, "立場B", stance_b, facts),
                root,
                writable=False,
            ).output,
        )
        write_text(run_dir / "03_plan_stance_b.md", plan_b)

        self.progress(f"2案の違いを争点として整理: {team.plan_reviewer.model}")
        issues = _validate_output(
            "争点表",
            self.runner.run(
                team.plan_reviewer,
                list_issues(goal, plan_a, plan_b, forks),
                root,
                writable=False,
            ).output,
            required_headings=("# 争点表",),
        )
        write_text(run_dir / "04_issues.md", issues)
        issue_ids = _extract_issue_ids(issues)
        if not issue_ids:
            raise RuntimeError("争点表から争点IDを読み取れませんでした。A-1形式のIDが必要です。")
        self.progress(f"争点を{len(issue_ids)}件抽出しました")

        mediation, rounds_used, stop_reason = self._run_debate_rounds(
            root=root,
            run_dir=run_dir,
            goal=goal,
            team=team,
            stance_a=stance_a,
            stance_b=stance_b,
            plan_a=plan_a,
            plan_b=plan_b,
            issues=issues,
        )

        stop_note = _stop_note(stop_reason, rounds_used, team.max_debate_rounds)
        self.progress(f"議論終了：{stop_note}")

        self.progress(f"要件定義書と実装プランを統合: {team.final_decider.model}")
        draft = self.runner.run(
            team.final_decider,
            finalize_plan(goal, plan_a, plan_b, issues, mediation, stop_note, team),
            root,
            writable=False,
        )
        draft_output = _validate_output(
            "要件定義書・実装プランの統合案",
            draft.output,
            required_headings=FINAL_HEADINGS,
        )
        write_text(run_dir / "90_requirements_draft.md", draft_output)

        checked_output = self._final_check(root, run_dir, goal, team, draft_output, issues)
        _validate_issue_coverage(checked_output, issue_ids)
        self._save_final(root, run_dir, team, checked_output, rounds_used, stop_reason)
        return WorkflowOutcome(run_dir, True, True, rounds_used, stop_reason, issue_ids)

    def _run_debate_rounds(
        self,
        root: Path,
        run_dir: Path,
        goal: str,
        team: ModelTeam,
        stance_a: str,
        stance_b: str,
        plan_a: str,
        plan_b: str,
        issues: str,
    ) -> tuple[str, int, str]:
        """上限までラウンドを回す。上限はfor文で保証し、AIの応答に依存させない。"""
        context = issues
        mediation = ""
        previous_unsorted: int | None = None
        rounds_used = 0
        stop_reason = "上限"

        for round_number in range(1, team.max_debate_rounds + 1):
            rounds_used = round_number
            round_dir = run_dir / f"round{round_number}"

            self.progress(f"ラウンド{round_number} 開始：立場Aの応答")
            response_a = _validate_output(
                f"ラウンド{round_number}の立場Aの応答",
                self.runner.run(
                    team.primary_planner,
                    respond_to_issues(goal, "立場A", stance_a, plan_a, context, round_number),
                    root,
                    writable=False,
                ).output,
                required_headings=("# 応答", "## 争点ごとの応答"),
            )
            write_text(round_dir / "response_a.md", response_a)

            self.progress(f"ラウンド{round_number}：立場Bの応答")
            response_b = _validate_output(
                f"ラウンド{round_number}の立場Bの応答",
                self.runner.run(
                    team.secondary_planner,
                    respond_to_issues(goal, "立場B", stance_b, plan_b, context, round_number),
                    root,
                    writable=False,
                ).output,
                required_headings=("# 応答", "## 争点ごとの応答"),
            )
            write_text(round_dir / "response_b.md", response_b)

            self.progress(f"ラウンド{round_number}：調停")
            mediation = _validate_output(
                f"ラウンド{round_number}の調停",
                self.runner.run(
                    team.plan_reviewer,
                    mediate_round(
                        goal,
                        issues,
                        context,
                        response_a,
                        response_b,
                        round_number,
                        team.max_debate_rounds,
                    ),
                    root,
                    writable=False,
                ).output,
                required_headings=(
                    "# 調停",
                    "## ここまでの経緯",
                    "## 争点ごとの統合案",
                    "## 未整理件数",
                    "## 継続判定",
                ),
            )
            write_text(round_dir / "mediation.md", mediation)

            unsorted = _parse_unsorted_count(mediation)
            continuation = _parse_continuation(mediation)
            self.progress(f"ラウンド{round_number} 終了（未整理{unsorted}件／判定{continuation}）")

            if unsorted == 0 or continuation == STOP_INTEGRATED:
                stop_reason = "統合完了"
                break
            if continuation == STOP_STALLED:
                stop_reason = "停滞"
                break
            if previous_unsorted is not None and unsorted >= previous_unsorted:
                stop_reason = "停滞（進展なし）"
                break

            previous_unsorted = unsorted
            context = mediation

        return mediation, rounds_used, stop_reason

    # ------------------------------------------------------------------
    # 共通の締め
    # ------------------------------------------------------------------

    def _final_check(
        self,
        root: Path,
        run_dir: Path,
        goal: str,
        team: ModelTeam,
        draft_output: str,
        issues: str,
    ) -> str:
        self.progress(f"要件定義書を最終チェック: {team.requirements_final_checker.model}")
        checked = self.runner.run(
            team.requirements_final_checker,
            final_check_requirements(goal, draft_output, issues),
            root,
            writable=False,
        )
        checked_output = _validate_output(
            "最終チェック済み要件定義書・実装プラン",
            checked.output,
            required_headings=FINAL_HEADINGS,
        )
        # AGENTS.md と CLAUDE.md が「作業前に REQUIREMENTS.md を読むこと」と定めているため、
        # この文書に指示文が残ると、以後のAIセッションが毎回それを読む。ここだけは停止する。
        assert_no_injection("最終チェック済み要件定義書", checked_output)
        write_text(run_dir / "91_final_checked_requirements.md", checked_output)
        return checked_output

    def _save_final(
        self,
        root: Path,
        run_dir: Path,
        team: ModelTeam,
        checked_output: str,
        rounds_used: int,
        stop_reason: str,
    ) -> None:
        final_requirements_path = requirements_path(root)
        write_text(final_requirements_path, checked_output)
        # 旧版や外部ツールとの互換性のため、PLAN.mdにも同じ内容を保存する。
        write_text(plan_path(root), checked_output)
        write_text(
            status_path(root),
            "# 現在の状態\n\n要件定義・実装プラン作成完了（実装は未実施）",
        )
        append_decision(
            root,
            "要件定義とモデル選定",
            f"レベル: {team.label}\n\n"
            f"議論ラウンド: {rounds_used}回（終了理由: {stop_reason}）\n\n"
            f"要件定義書: {final_requirements_path}\n\n実装は行っていません。",
        )
        self.progress(f"要件定義書を保存しました: {final_requirements_path}")
        self.progress("このツールによる実装、コード変更、デプロイは行っていません。")


# ----------------------------------------------------------------------
# 解析と検査
# ----------------------------------------------------------------------


def _section(document: str, heading: str) -> str:
    """指定した見出しの本文を取り出す。より浅い見出しが現れるまでを本文とする。"""
    level = len(heading) - len(heading.lstrip("#"))
    lines = document.splitlines()
    collected: list[str] = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            inside = True
            continue
        if inside:
            match = re.match(r"^(#{1,6})\s", stripped)
            if match and len(match.group(1)) <= level:
                break
            collected.append(line)
    return "\n".join(collected).strip()


def _has_no_forks(forks_document: str) -> bool:
    body = _section(forks_document, "## 分岐点")
    return body.startswith(NO_FORKS_MARKER)


def _validate_forks(forks_document: str) -> None:
    missing = [
        heading
        for heading in (FORK_DOCUMENT_HEADING, "## 確認した事実", "## 分岐点", "## 立場A", "## 立場B")
        if heading not in forks_document
    ]
    if missing:
        raise RuntimeError(f"分岐点と立場に必要な見出しがありません: {', '.join(missing)}")

    if _has_no_forks(forks_document):
        return

    for stance in ("## 立場A", "## 立場B"):
        body = _section(forks_document, stance)
        for required in ("### 優先するもの", "### 捨てるもの"):
            if required not in body:
                raise RuntimeError(
                    f"{stance}に「{required}」がありません。"
                    "捨てるものを書かないと立場の差が出ず、統合しても何も生まれないため停止しました。"
                )


def _extract_issue_ids(issues_document: str) -> tuple[str, ...]:
    found = re.findall(r"\bA-(\d+)\b", issues_document)
    unique = sorted({int(number) for number in found})
    return tuple(f"A-{number}" for number in unique)


def _parse_state_table(mediation_document: str) -> dict[str, str]:
    """「## 争点ごとの統合案」の表から、争点IDごとの状態を読み取る。"""
    body = _section(mediation_document, "## 争点ごとの統合案")
    states: dict[str, str] = {}
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if not re.fullmatch(r"A-\d+", cells[0]):
            continue
        for state in ("統合済み", "要判断", "未整理"):
            if state in cells[1]:
                states[cells[0]] = state
                break
    return states


def _parse_unsorted_count(mediation_document: str) -> int:
    """自己申告の件数を読み、表から数えた実数と突き合わせる。

    AIの出力がそのまま議論の継続判断に使われるため、自己申告だけを信じると、
    資料に仕込まれた誘導文で議論を早期終了させられる余地が残る。
    """
    body = _section(mediation_document, "## 未整理件数")
    match = re.search(r"未整理\s*[:：]\s*(\d+)", body)
    if match is None:
        raise RuntimeError(
            "調停の「## 未整理件数」を読み取れませんでした。"
            "『未整理: N件』の形式で1行だけ出力する必要があります。"
        )
    declared = int(match.group(1))

    states = _parse_state_table(mediation_document)
    if not states:
        raise RuntimeError(
            "調停の「## 争点ごとの統合案」から争点の状態を読み取れませんでした。"
            "争点IDと状態を含む表が必要です。"
        )
    counted = sum(1 for state in states.values() if state == "未整理")
    if declared != counted:
        raise RuntimeError(
            f"調停の未整理件数が一致しません（申告{declared}件、表から数えると{counted}件）。"
            "議論の継続判断に使う数字のため、数が合わない状態では次へ進めません。"
        )
    return declared


def _parse_continuation(mediation_document: str) -> str:
    body = _section(mediation_document, "## 継続判定").replace(":", "：")
    matched = [token for token in CONTINUATION_TOKENS if token in body]
    if len(matched) != 1:
        raise RuntimeError(
            "調停の「## 継続判定」を読み取れませんでした。"
            f"{'、'.join(CONTINUATION_TOKENS)} のいずれか1語だけを書く必要があります。"
        )
    return matched[0]


def _validate_issue_coverage(final_document: str, issue_ids: tuple[str, ...]) -> None:
    body = _section(final_document, "## 14. 争点と統合結果")
    missing = [issue_id for issue_id in issue_ids if issue_id not in body]
    if missing:
        raise RuntimeError(
            "「## 14. 争点と統合結果」に記載のない争点があります: " + "、".join(missing)
        )
    if "未整理" in body:
        raise RuntimeError(
            "「## 14. 争点と統合結果」に『未整理』の争点が残っています。"
            "統合済みか要判断のどちらかにする必要があります。"
        )


def _stop_note(stop_reason: str, rounds_used: int, max_rounds: int) -> str:
    details = {
        "統合完了": "未整理の争点がなくなったため終了しました。要判断として残った争点は人間が判断します。",
        "停滞": "調停役が、これ以上議論しても進展しないと判断したため打ち切りました。",
        "停滞（進展なし）": "未整理の争点が前のラウンドから減らなかったため打ち切りました。",
        "上限": "ラウンド上限に達したため打ち切りました。",
    }
    note = details.get(stop_reason, stop_reason)
    tail = ""
    if stop_reason != "統合完了":
        tail = "残っている未整理の争点は、要判断として未決事項へ回してください。"
    return f"{stop_reason}（{rounds_used}/{max_rounds}ラウンド）。{note}{tail}"


def _validate_output(
    stage: str,
    output: str,
    required_headings: tuple[str, ...] = (),
) -> str:
    cleaned = output.strip()
    if len(cleaned) < 20:
        raise RuntimeError(f"{stage}の出力が空または短すぎるため、安全のため停止しました。")

    failure_messages = (
        "要件定義は確定できません",
        "最終計画は確定できません",
        "failed to authenticate",
        "oauth session expired",
        "内容を取得できませんでした",
    )
    lowered = cleaned.casefold()
    if any(message.casefold() in lowered for message in failure_messages):
        raise RuntimeError(f"{stage}がエラー内容を返したため、次の工程へ進まず停止しました。")

    # すべてのAI出力がここを通る。秘密情報の検査はこの1か所に集約する。
    assert_no_secrets(stage, cleaned)

    missing = [heading for heading in required_headings if heading not in cleaned]
    if missing:
        raise RuntimeError(f"{stage}に必要な見出しがありません: {', '.join(missing)}")
    return cleaned
