import tempfile
import unittest
import subprocess
from pathlib import Path

from ai_planner.project import (
    archive_legacy_source,
    copy_legacy_workflow,
    initialize_project_files,
    inspect_project,
    project_lock,
    sanitize_project_name,
    suggest_project_name,
)


class ProjectTest(unittest.TestCase):
    def test_initialization_does_not_overwrite_existing_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents = root / "AGENTS.md"
            agents.write_text("user rules", encoding="utf-8")

            initialize_project_files(root)

            self.assertEqual(agents.read_text(encoding="utf-8"), "user rules")
            self.assertTrue((root / "CLAUDE.md").exists())
            self.assertTrue((root / ".ai-workflow" / "AI_WORKFLOW.md").exists())
            self.assertTrue((root / "00_依頼" / "GOAL.md").exists())
            self.assertTrue((root / "01_計画" / "PLAN.md").exists())
            self.assertTrue((root / "90_実行履歴").is_dir())

    def test_lock_is_removed_after_use(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_project_files(root)
            lock = root / ".ai-workflow" / "active.lock"
            with project_lock(root):
                self.assertTrue(lock.exists())
            self.assertFalse(lock.exists())

    def test_project_name_is_windows_safe(self):
        self.assertEqual(sanitize_project_name('売上:管理/改善?'), "売上-管理-改善")
        self.assertEqual(sanitize_project_name("CON"), "CON-プロジェクト")

    def test_project_name_is_suggested_from_goal(self):
        result = suggest_project_name("note×AI×XでLINEスタンプで収益化したい")
        self.assertEqual(result, "note-AI-X-LINEスタンプ収益化")

    def test_long_goal_is_compacted_for_project_folder(self):
        goal = (
            "AIを使ったことがない人に、AIを使って業務効率するための提案をしたいと思っています。\n"
            "簡単なアンケートに答えると実現方法をイメージできる資料を作成するwebアプリを作りたい。\n"
            "思い込みで勝手にできないと決めつけていることも質問する。"
        )
        self.assertEqual(
            suggest_project_name(goal),
            "AI初心者向け業務効率化提案アンケートWebアプリ",
        )

    def test_legacy_workflow_is_copied_then_archived_without_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            legacy = workspace / ".ai-workflow"
            legacy.mkdir()
            (legacy / "PLAN.md").write_text("old plan", encoding="utf-8")
            project = workspace / "05_プロジェクト" / "テスト"
            initialize_project_files(project)

            migration = copy_legacy_workflow(workspace, project)
            self.assertIsNotNone(migration)
            source, destination = migration  # type: ignore[misc]
            self.assertEqual((destination / "PLAN.md").read_text(encoding="utf-8"), "old plan")
            archived = archive_legacy_source(source)
            self.assertFalse(legacy.exists())
            self.assertTrue(archived.exists())
            self.assertEqual((archived / "PLAN.md").read_text(encoding="utf-8"), "old plan")

    def test_legacy_migration_ignores_windows_system_files(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            legacy = workspace / ".ai-workflow"
            runs = legacy / "runs"
            runs.mkdir(parents=True)
            (runs / "PLAN.md").write_text("old plan", encoding="utf-8")
            (runs / "desktop.ini").write_text("system metadata", encoding="utf-8")
            project = workspace / "05_プロジェクト" / "テスト"
            initialize_project_files(project)

            migration = copy_legacy_workflow(workspace, project)

            self.assertIsNotNone(migration)
            _, destination = migration  # type: ignore[misc]
            self.assertEqual((destination / "runs" / "PLAN.md").read_text(encoding="utf-8"), "old plan")
            self.assertFalse((destination / "runs" / "desktop.ini").exists())

    def test_nested_named_project_detects_parent_git_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            subprocess.run(["git", "init", "-q", workspace], check=True)
            project = workspace / "05_プロジェクト" / "テスト"
            project.mkdir(parents=True)

            state = inspect_project(project)

            self.assertTrue(state.is_git)
            self.assertEqual(state.git_root, workspace.resolve())


if __name__ == "__main__":
    unittest.main()
