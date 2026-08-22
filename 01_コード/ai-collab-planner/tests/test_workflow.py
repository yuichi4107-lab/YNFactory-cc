import tempfile
import unittest
from pathlib import Path

from ai_planner.clients import DEMO_FORKS, DEMO_MEDIATION, DemoModelRunner
from ai_planner.config import load_settings
from ai_planner.domain import RunResult
from ai_planner.project import initialize_project_files
from ai_planner.workflow import CollaborationWorkflow

SETTINGS = load_settings(Path(__file__).parents[1] / "config.toml")
UNTOUCHED_REQUIREMENTS = "# 要件定義書・実装プラン\n\n未作成\n"


class RecordingRunner(DemoModelRunner):
    """呼び出し回数と書き込み可否を記録する。"""

    def __init__(self):
        super().__init__()
        self.writable_values: list[bool] = []
        self.calls = 0

    def run(self, role, prompt, cwd, writable=False):
        self.calls += 1
        self.writable_values.append(writable)
        return super().run(role, prompt, cwd, writable)


class MediationRunner(RecordingRunner):
    """調停役の応答だけを差し替え、収束条件を検証する。"""

    def __init__(self, unsorted_counts: list[int], continuation: str):
        super().__init__()
        self.unsorted_counts = unsorted_counts
        self.continuation = continuation
        self.mediation_calls = 0

    def run(self, role, prompt, cwd, writable=False):
        if "【工程】調停" in prompt:
            self.calls += 1
            self.writable_values.append(writable)
            index = min(self.mediation_calls, len(self.unsorted_counts) - 1)
            count = self.unsorted_counts[index]
            self.mediation_calls += 1
            # 申告件数と表の中身は必ず一致させる（一致しない応答はSEC-3で停止するため）
            rows = [
                f"| A-{number} | 未整理 | まだ詰まっていない | - | - | - |"
                for number in range(1, count + 1)
            ]
            rows.append(f"| A-{count + 1} | 統合済み | 集約する | 速さ | 構造 | - |")
            rows.append(f"| A-{count + 2} | 要判断 | 決めきれない | 小さく始める | 拡張性 | 利用人数の見込み |")
            table = "\n".join(rows)
            body = (
                "# 調停\n\n"
                "## ここまでの経緯\n\nデモ用の経緯です。\n\n"
                "## 争点ごとの統合案\n\n"
                "| 争点ID | 状態 | 統合案 | 立場Aから採った要素 | 立場Bから採った要素 | 要判断の場合に人間が決めること |\n"
                "|---|---|---|---|---|---|\n"
                f"{table}\n\n"
                f"## 未整理件数\n\n未整理: {count}件\n\n"
                f"## 継続判定\n\n{self.continuation}\n"
            )
            return RunResult(role.provider, role.model, body, 0, "demo")
        return super().run(role, prompt, cwd, writable)


def _run(runner, level: str, approve=lambda _document: True, goal: str = "テスト目的"):
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name)
    initialize_project_files(root)
    workflow = CollaborationWorkflow(runner, progress=lambda _message: None, approve=approve)
    outcome = workflow.execute(root=root, goal=goal, team=SETTINGS.teams[level])
    return directory, root, outcome


class TeamConfigTest(unittest.TestCase):
    def test_every_level_has_an_independent_requirements_final_checker(self):
        for team in SETTINGS.teams.values():
            self.assertTrue(team.requirements_final_checker.enabled)
            self.assertNotEqual(
                team.final_decider.provider,
                team.requirements_final_checker.provider,
            )

    def test_debate_round_limits_are_configured_per_level(self):
        self.assertEqual(SETTINGS.teams["light"].max_debate_rounds, 0)
        self.assertEqual(SETTINGS.teams["standard"].max_debate_rounds, 2)
        self.assertEqual(SETTINGS.teams["complex"].max_debate_rounds, 3)
        self.assertEqual(SETTINGS.teams["critical"].max_debate_rounds, 3)

    def test_only_light_skips_the_debate(self):
        self.assertFalse(SETTINGS.teams["light"].debate_enabled)
        for level in ("standard", "complex", "critical"):
            self.assertTrue(SETTINGS.teams[level].debate_enabled)

    def test_fork_auditor_is_a_different_company_than_the_extractor(self):
        team = SETTINGS.teams["critical"]
        self.assertTrue(team.fork_auditor.enabled)
        self.assertNotEqual(team.fork_extractor.provider, team.fork_auditor.provider)


class DebateWorkflowTest(unittest.TestCase):
    def test_standard_run_produces_every_debate_artifact(self):
        runner = RecordingRunner()
        directory, root, outcome = _run(runner, "standard")
        with directory:
            self.assertTrue(outcome.completed)
            self.assertTrue(outcome.requirements_created)
            for name in (
                "01_forks_and_stances.md",
                "02_plan_stance_a.md",
                "03_plan_stance_b.md",
                "04_issues.md",
                "round1/response_a.md",
                "round1/response_b.md",
                "round1/mediation.md",
                "90_requirements_draft.md",
                "91_final_checked_requirements.md",
            ):
                self.assertTrue((outcome.run_dir / name).exists(), name)

            content = (root / "01_計画" / "REQUIREMENTS.md").read_text(encoding="utf-8")
            self.assertIn("## 14. 争点と統合結果", content)
            self.assertIn("### 13.3 AIモデルの役割分担", content)
            self.assertIn("実装は未実施", (root / ".ai-workflow" / "STATUS.md").read_text(encoding="utf-8"))
            self.assertFalse((root / "03_成果物" / "IMPLEMENTATION_REPORT.md").exists())
            self.assertFalse((root / "05_レビュー" / "CODE_REVIEW.md").exists())

    def test_all_calls_stay_read_only(self):
        runner = RecordingRunner()
        directory, _root, _outcome = _run(runner, "critical")
        with directory:
            self.assertTrue(runner.writable_values)
            self.assertTrue(all(value is False for value in runner.writable_values))

    def test_issue_ids_are_tracked_through_to_the_final_document(self):
        runner = RecordingRunner()
        directory, root, outcome = _run(runner, "standard")
        with directory:
            self.assertEqual(outcome.issue_ids, ("A-1", "A-2"))
            section = (root / "01_計画" / "REQUIREMENTS.md").read_text(encoding="utf-8")
            for issue_id in outcome.issue_ids:
                self.assertIn(issue_id, section)


class ConvergenceTest(unittest.TestCase):
    """多ラウンド化の危険はすべて収束条件に集中しているため、ここを厚く検証する。"""

    def test_single_round_when_everything_is_integrated(self):
        runner = MediationRunner([0], "終了：統合完了")
        directory, _root, outcome = _run(runner, "standard")
        with directory:
            self.assertEqual(outcome.rounds_used, 1)
            self.assertEqual(outcome.stop_reason, "統合完了")
            # 1(分岐点) + 2(2案) + 1(争点表) + 3(1ラウンド) + 1(統合) + 1(最終チェック)
            self.assertEqual(runner.calls, 9)

    def test_unresolved_tradeoffs_do_not_prevent_completion(self):
        """要判断が残っていても、未整理が0なら正常終了する。"""
        runner = MediationRunner([0], "終了：統合完了")
        directory, root, outcome = _run(runner, "standard")
        with directory:
            self.assertTrue(outcome.completed)
            self.assertIn("要判断", (outcome.run_dir / "round1" / "mediation.md").read_text(encoding="utf-8"))

    def test_round_cap_stops_a_mediator_that_never_finishes(self):
        runner = MediationRunner([5, 4, 3, 2, 1], "続行")
        directory, _root, outcome = _run(runner, "standard")
        with directory:
            self.assertEqual(outcome.rounds_used, 2)
            self.assertEqual(outcome.stop_reason, "上限")
            # 1 + 2 + 1 + 3*2 + 1 + 1
            self.assertEqual(runner.calls, 12)

    def test_no_progress_stops_even_when_the_mediator_says_continue(self):
        """未整理件数が減らなければ、上限より前に打ち切る。"""
        runner = MediationRunner([3, 3, 3], "続行")
        directory, _root, outcome = _run(runner, "complex")
        with directory:
            self.assertEqual(outcome.rounds_used, 2)
            self.assertEqual(outcome.stop_reason, "停滞（進展なし）")
            # 上限3ラウンドだが2ラウンドで止まる: 1 + 2 + 1 + 3*2 + 1 + 1
            self.assertEqual(runner.calls, 12)

    def test_mediator_can_declare_a_stall(self):
        runner = MediationRunner([4], "終了：停滞")
        directory, _root, outcome = _run(runner, "complex")
        with directory:
            self.assertEqual(outcome.rounds_used, 1)
            self.assertEqual(outcome.stop_reason, "停滞")

    def test_unparsable_continuation_stops_instead_of_continuing_silently(self):
        runner = MediationRunner([2], "たぶん続けたほうがよいと思います")
        directory, root, _ = None, None, None
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            initialize_project_files(root)
            workflow = CollaborationWorkflow(runner, progress=lambda _m: None)
            with self.assertRaisesRegex(RuntimeError, "継続判定"):
                workflow.execute(root=root, goal="目的", team=SETTINGS.teams["standard"])
            self.assertEqual(
                (root / "01_計画" / "REQUIREMENTS.md").read_text(encoding="utf-8"),
                UNTOUCHED_REQUIREMENTS,
            )

    def test_unparsable_unsorted_count_stops(self):
        class BadCountRunner(RecordingRunner):
            def run(self, role, prompt, cwd, writable=False):
                if "【工程】調停" in prompt:
                    body = DEMO_MEDIATION.replace("未整理: 0件", "だいたい片付きました")
                    return RunResult(role.provider, role.model, body, 0, "demo")
                return super().run(role, prompt, cwd, writable)

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            initialize_project_files(root)
            workflow = CollaborationWorkflow(BadCountRunner(), progress=lambda _m: None)
            with self.assertRaisesRegex(RuntimeError, "未整理件数"):
                workflow.execute(root=root, goal="目的", team=SETTINGS.teams["standard"])


class ApprovalTest(unittest.TestCase):
    def test_rejection_stops_before_spending_further_calls(self):
        runner = RecordingRunner()
        directory, root, outcome = _run(runner, "standard", approve=lambda _document: False)
        with directory:
            self.assertFalse(outcome.completed)
            self.assertFalse(outcome.requirements_created)
            self.assertEqual(outcome.stop_reason, "承認されませんでした")
            # 分岐点抽出の1回だけで止まる
            self.assertEqual(runner.calls, 1)
            self.assertEqual(
                (root / "01_計画" / "REQUIREMENTS.md").read_text(encoding="utf-8"),
                UNTOUCHED_REQUIREMENTS,
            )

    def test_approval_document_shown_to_the_human_is_the_forks_and_stances(self):
        shown: list[str] = []

        def approve(document: str) -> bool:
            shown.append(document)
            return True

        runner = RecordingRunner()
        directory, _root, _outcome = _run(runner, "standard", approve=approve)
        with directory:
            self.assertEqual(len(shown), 1)
            self.assertIn("# 分岐点と立場", shown[0])
            self.assertIn("### 捨てるもの", shown[0])


class SkipDebateTest(unittest.TestCase):
    def test_light_level_keeps_the_three_step_behaviour(self):
        runner = RecordingRunner()
        directory, root, outcome = _run(runner, "light")
        with directory:
            self.assertTrue(outcome.completed)
            self.assertEqual(outcome.rounds_used, 0)
            self.assertEqual(outcome.stop_reason, "議論なし")
            self.assertEqual(runner.calls, 3)
            self.assertIn("## 14. 争点と統合結果", (root / "01_計画" / "REQUIREMENTS.md").read_text(encoding="utf-8"))

    def test_no_forks_skips_the_debate_without_asking_for_approval(self):
        class NoForksRunner(RecordingRunner):
            def run(self, role, prompt, cwd, writable=False):
                if "【工程】分岐点抽出と立場設定" in prompt:
                    self.calls += 1
                    self.writable_values.append(writable)
                    body = (
                        "# 分岐点と立場\n\n"
                        "## 確認した事実\n\n依頼文だけで方針が決まります。\n\n"
                        "## 分岐点\n\nなし。決めないと進めない点はありません。\n\n"
                        "## 立場A\n\n分岐点がないため設定しません。\n\n"
                        "## 立場B\n\n分岐点がないため設定しません。\n"
                    )
                    return RunResult(role.provider, role.model, body, 0, "demo")
                return super().run(role, prompt, cwd, writable)

        asked: list[str] = []

        def approve(document: str) -> bool:
            asked.append(document)
            return False

        runner = NoForksRunner()
        directory, _root, outcome = _run(runner, "standard", approve=approve)
        with directory:
            self.assertEqual(asked, [])
            self.assertTrue(outcome.completed)
            self.assertEqual(outcome.rounds_used, 0)
            # 分岐点抽出1 + 案1 + 統合1 + 最終チェック1
            self.assertEqual(runner.calls, 4)


class SafetyTest(unittest.TestCase):
    def test_missing_discard_section_stops_the_run(self):
        class NoDiscardRunner(RecordingRunner):
            def run(self, role, prompt, cwd, writable=False):
                if "【工程】分岐点抽出と立場設定" in prompt:
                    body = DEMO_FORKS.replace("### 捨てるもの", "### あとまわしにするもの")
                    return RunResult(role.provider, role.model, body, 0, "demo")
                return super().run(role, prompt, cwd, writable)

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            initialize_project_files(root)
            workflow = CollaborationWorkflow(NoDiscardRunner(), progress=lambda _m: None)
            with self.assertRaisesRegex(RuntimeError, "捨てるもの"):
                workflow.execute(root=root, goal="目的", team=SETTINGS.teams["standard"])

    def test_missing_issue_in_final_document_stops_the_run(self):
        class DroppedIssueRunner(RecordingRunner):
            def run(self, role, prompt, cwd, writable=False):
                result = super().run(role, prompt, cwd, writable)
                if "【工程】要件定義書の最終チェック" in prompt:
                    return RunResult(
                        role.provider,
                        role.model,
                        result.output.replace("| A-2 | 統合済み", "| B-9 | 統合済み"),
                        0,
                        "demo",
                    )
                return result

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            initialize_project_files(root)
            workflow = CollaborationWorkflow(DroppedIssueRunner(), progress=lambda _m: None)
            with self.assertRaisesRegex(RuntimeError, "A-2"):
                workflow.execute(root=root, goal="目的", team=SETTINGS.teams["standard"])
            self.assertEqual(
                (root / "01_計画" / "REQUIREMENTS.md").read_text(encoding="utf-8"),
                UNTOUCHED_REQUIREMENTS,
            )

    def test_error_text_cannot_be_approved_as_requirements(self):
        class BrokenFinalRunner(RecordingRunner):
            def run(self, role, prompt, cwd, writable=False):
                if "【工程】要件定義書・実装プランの統合" in prompt:
                    return RunResult(
                        role.provider,
                        role.model,
                        "資料の内容を取得できませんでした。要件定義は確定できません。",
                        0,
                        "demo",
                    )
                return super().run(role, prompt, cwd, writable)

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            initialize_project_files(root)
            workflow = CollaborationWorkflow(BrokenFinalRunner(), progress=lambda _m: None)
            with self.assertRaisesRegex(RuntimeError, "エラー内容"):
                workflow.execute(root=root, goal="テスト目的", team=SETTINGS.teams["standard"])
            self.assertEqual(
                (root / "01_計画" / "REQUIREMENTS.md").read_text(encoding="utf-8"),
                UNTOUCHED_REQUIREMENTS,
            )


if __name__ == "__main__":
    unittest.main()
