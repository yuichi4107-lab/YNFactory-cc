from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "planner_inbox.py"
SPEC = importlib.util.spec_from_file_location("planner_inbox", MODULE_PATH)
assert SPEC and SPEC.loader
planner_inbox = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = planner_inbox
SPEC.loader.exec_module(planner_inbox)


REQUIREMENTS_WITH_PENDING = """# 要件定義書

## 12. 未決事項・確認質問

- 認証方式が未定

## 14. 争点と統合結果

| 争点ID | 状態 | 統合後の結論 | 立場Aから採った要素 | 立場Bから採った要素 | 要判断の場合の人間への質問 |
|---|---|---|---|---|---|
| A-1 | 統合済み | 段階リリースにする | 早期公開 | 品質ゲート | - |
| A-3 | 要判断 | - | SSO | 個別ID | 認証をSSOに寄せるか個別IDにするか |
"""

REQUIREMENTS_ALL_RESOLVED = """# 要件定義書

## 14. 争点と統合結果

| 争点ID | 状態 | 統合後の結論 | 立場Aから採った要素 | 立場Bから採った要素 | 要判断の場合の人間への質問 |
|---|---|---|---|---|---|
| A-1 | 統合済み | 段階リリースにする | 早期公開 | 品質ゲート | - |
"""


def make_project(root: Path, name: str, *, final_checked: bool,
                 requirements: str, started: bool = False) -> Path:
    project = root / name
    (project / "01_計画").mkdir(parents=True)
    (project / "01_計画" / "REQUIREMENTS.md").write_text(requirements, encoding="utf-8")
    run_dir = project / "90_実行履歴" / "20260822-170500"
    run_dir.mkdir(parents=True)
    if final_checked:
        (run_dir / "91_final_checked_requirements.md").write_text("done", encoding="utf-8")
    if started:
        (project / "docs").mkdir()
        (project / "docs" / "SRS.md").write_text("srs", encoding="utf-8")
    return project


class ScanTest(unittest.TestCase):
    def test_completed_and_untouched_is_ready_for_nagame(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "05_プロジェクト"
            root.mkdir()
            make_project(root, "alpha", final_checked=True,
                         requirements=REQUIREMENTS_ALL_RESOLVED)
            items = planner_inbox.scan([root])
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["project_name"], "alpha")
            self.assertEqual(items[0]["status"], "ready_for_nagame")
            self.assertEqual(items[0]["decisions_pending"], [])

    def test_implementation_started_is_in_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "05_プロジェクト"
            root.mkdir()
            make_project(root, "beta", final_checked=True, started=True,
                         requirements=REQUIREMENTS_ALL_RESOLVED)
            items = planner_inbox.scan([root])
            self.assertEqual(items[0]["status"], "in_progress")

    def test_without_final_check_is_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "05_プロジェクト"
            root.mkdir()
            make_project(root, "gamma", final_checked=False,
                         requirements=REQUIREMENTS_ALL_RESOLVED)
            items = planner_inbox.scan([root])
            self.assertEqual(items[0]["status"], "draft")

    def test_pending_decisions_are_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "05_プロジェクト"
            root.mkdir()
            make_project(root, "delta", final_checked=True,
                         requirements=REQUIREMENTS_WITH_PENDING)
            items = planner_inbox.scan([root])
            self.assertEqual(len(items[0]["decisions_pending"]), 1)
            self.assertIn("A-3", items[0]["decisions_pending"][0])
            self.assertIn("認証をSSOに寄せるか個別IDにするか",
                          items[0]["decisions_pending"][0])

    def test_duplicate_project_name_across_roots_is_deduped(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "local" / "05_プロジェクト"
            second = Path(tmp) / "drive" / "05_プロジェクト"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            make_project(first, "same", final_checked=True,
                         requirements=REQUIREMENTS_ALL_RESOLVED)
            make_project(second, "same", final_checked=True,
                         requirements=REQUIREMENTS_ALL_RESOLVED)
            items = planner_inbox.scan([first, second])
            self.assertEqual(len(items), 1)
            self.assertTrue(str(items[0]["requirements_path"]).replace("\\", "/")
                            .find("/local/") >= 0)

    def test_project_without_requirements_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "05_プロジェクト"
            root.mkdir()
            (root / "empty" / "docs").mkdir(parents=True)
            items = planner_inbox.scan([root])
            self.assertEqual(items, [])

    def test_missing_root_is_skipped_without_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist"
            self.assertEqual(planner_inbox.scan([missing]), [])


class PendingDecisionTest(unittest.TestCase):
    def test_returns_empty_when_chapter_14_missing(self):
        self.assertEqual(planner_inbox.read_pending_decisions("# 何もない"), [])

    def test_ignores_resolved_rows(self):
        found = planner_inbox.read_pending_decisions(REQUIREMENTS_ALL_RESOLVED)
        self.assertEqual(found, [])

    def test_ignores_header_separator_row(self):
        found = planner_inbox.read_pending_decisions(REQUIREMENTS_WITH_PENDING)
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
