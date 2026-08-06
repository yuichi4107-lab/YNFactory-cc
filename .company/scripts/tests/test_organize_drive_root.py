from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
# organize_drive_root imports sync_drive_git as a sibling module.
sys.path.insert(0, str(SCRIPTS_DIR))

MODULE_PATH = SCRIPTS_DIR / "organize_drive_root.py"
SPEC = importlib.util.spec_from_file_location("organize_drive_root", MODULE_PATH)
assert SPEC and SPEC.loader
organize_drive_root = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = organize_drive_root
SPEC.loader.exec_module(organize_drive_root)


TODAY = "2026-08-05"


def touch(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_fake_drive(root: Path) -> None:
    """A tree covering every rule category plus the cases that must not move."""
    # 01_コード
    touch(root / "scripts" / "post_to_x.py")
    touch(root / "scripts" / "__pycache__" / "post_to_x.pyc")
    touch(root / "_scripts" / "generate_note_weekly_batch.py")
    # 02_設定 / 03_成果物
    touch(root / "docs" / "backup-zslim.md")
    touch(root / "ebooks" / "vol1.md")
    touch(root / "ebook-produce" / "plan.md")
    # 05_プロジェクト（Drive にしかない quant-bot を含む）
    touch(root / "shorts-factory" / "main.py")
    touch(root / "keiba-unified" / "jra" / "run.py")
    touch(root / "quant-bot" / "bot.py")
    touch(root / "tools" / "x-threads-auto-post" / "index.js")
    # .company: outputs/inputs/context は外へ、運営部分は残る
    touch(root / ".company" / "outputs" / "note-article-1" / "cover.png")
    touch(root / ".company" / "inputs" / "context-map.md")
    touch(root / ".company" / "context" / "references" / "chara.xlsx")
    touch(root / ".company" / "secretary" / "HANDOFF.md", "handoff")
    touch(root / ".company" / "DASHBOARD.md")
    touch(root / ".company" / "tmp_coverage.txt")
    touch(root / ".company" / "tmp" / "scratch.md")
    touch(root / ".company" / "codex" / "queue" / ".keep")
    touch(root / "codex" / "queue" / "job-a" / "prompt.md")
    # 99_その他 行きのゴミとキャッシュ
    touch(root / "mobile_full.png")
    touch(root / "skills-bundle-20260726.zip")
    touch(root / ".playwright-mcp" / "page-1.yml")
    touch(root / ".wrangler" / "state")
    touch(root / "_archive" / "2026-07-05-root-cleanup" / "old.png")
    # 動かしてはいけないもの
    touch(root / "CLAUDE.md", "rules")
    touch(root / "AGENTS.md", "rules")
    touch(root / ".gitignore", "ignore")
    touch(root / ".agents" / "skills" / "company" / "SKILL.md")
    touch(root / ".claude" / "settings.json")
    touch(root / ".codex" / "config.toml")
    touch(root / ".git_drivebackup" / "HEAD")
    touch(root / ".vscode" / "settings.json")


def organize(root: Path, apply: bool = True, purge_cache: bool = False):
    planner = organize_drive_root.build_planner(root, TODAY, purge_cache)
    if apply:
        for bucket in organize_drive_root.BUCKETS:
            (root / bucket).mkdir(exist_ok=True)
    planner.run(apply=apply)
    if apply:
        organize_drive_root.write_manifest(planner, TODAY)
    return planner


class OrganizeDriveRootTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "YNFactory-cc"
        self.root.mkdir()
        make_fake_drive(self.root)
        self.junk = self.root / "99_その他" / f"{TODAY}-cleanup"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_dry_run_changes_nothing(self) -> None:
        planner = organize(self.root, apply=False)
        self.assertTrue(planner.actions)
        self.assertTrue((self.root / "shorts-factory" / "main.py").exists())
        self.assertFalse((self.root / "05_プロジェクト").exists())

    def test_code_config_and_deliverables_land_in_buckets(self) -> None:
        organize(self.root)
        self.assertTrue((self.root / "01_コード" / "scripts" / "post_to_x.py").exists())
        self.assertTrue((self.root / "02_設定" / "docs" / "backup-zslim.md").exists())
        self.assertTrue((self.root / "03_成果物" / "ebooks" / "vol1.md").exists())
        self.assertTrue((self.root / "03_成果物" / "ebook-produce" / "plan.md").exists())
        self.assertFalse((self.root / "docs").exists())

    def test_projects_move_including_drive_only_ones(self) -> None:
        organize(self.root)
        base = self.root / "05_プロジェクト"
        self.assertTrue((base / "shorts-factory" / "main.py").exists())
        self.assertTrue((base / "keiba-unified" / "jra" / "run.py").exists())
        self.assertTrue((base / "quant-bot" / "bot.py").exists())
        # tools/ is a wrapper: its contents are promoted, the wrapper disappears.
        self.assertTrue((base / "x-threads-auto-post" / "index.js").exists())
        self.assertFalse((self.root / "tools").exists())

    def test_company_keeps_operations_but_loses_outputs_and_inputs(self) -> None:
        organize(self.root)
        self.assertTrue((self.root / "03_成果物" / "outputs" / "note-article-1" / "cover.png").exists())
        self.assertTrue((self.root / "04_インプット" / "inputs" / "context-map.md").exists())
        self.assertTrue((self.root / "04_インプット" / "context" / "references" / "chara.xlsx").exists())
        self.assertFalse((self.root / ".company" / "outputs").exists())
        self.assertFalse((self.root / ".company" / "inputs").exists())
        # 会社運営データはそのまま
        self.assertEqual(
            (self.root / ".company" / "secretary" / "HANDOFF.md").read_text(encoding="utf-8"),
            "handoff",
        )
        self.assertTrue((self.root / ".company" / "DASHBOARD.md").exists())

    def test_root_codex_queue_merges_into_company_and_wrapper_is_pruned(self) -> None:
        organize(self.root)
        self.assertTrue((self.root / ".company" / "codex" / "queue" / "job-a" / "prompt.md").exists())
        self.assertFalse((self.root / "codex").exists())

    def test_junk_and_caches_go_to_99(self) -> None:
        organize(self.root)
        self.assertTrue((self.junk / "mobile_full.png").exists())
        self.assertTrue((self.junk / "skills-bundle-20260726.zip").exists())
        self.assertTrue((self.junk / "company-tmp_coverage.txt").exists())
        self.assertTrue((self.junk / "company-tmp" / "scratch.md").exists())
        self.assertTrue((self.junk / "playwright-mcp" / "page-1.yml").exists())
        self.assertTrue((self.junk / "_archive" / "2026-07-05-root-cleanup" / "old.png").exists())
        self.assertFalse((self.root / "mobile_full.png").exists())

    def test_purge_cache_deletes_instead_of_moving(self) -> None:
        organize(self.root, purge_cache=True)
        self.assertFalse((self.root / ".playwright-mcp").exists())
        self.assertFalse((self.junk / "playwright-mcp").exists())
        # Purging a nested cache must not take its parent with it.
        self.assertTrue((self.root / "01_コード" / "scripts" / "post_to_x.py").exists())
        self.assertFalse((self.root / "01_コード" / "scripts" / "__pycache__").exists())

    def test_tool_discovered_config_stays_at_root(self) -> None:
        organize(self.root)
        for rel in ("CLAUDE.md", "AGENTS.md", ".gitignore", ".vscode/settings.json",
                    ".agents/skills/company/SKILL.md", ".claude/settings.json",
                    ".codex/config.toml", ".git_drivebackup/HEAD"):
            self.assertTrue((self.root / rel).exists(), rel)

    def test_protected_path_in_rules_is_rejected(self) -> None:
        planner = organize_drive_root.Planner(self.root, self.junk, purge_cache=False)
        for bad in (".agents", "CLAUDE.md", ".git_drivebackup", "../outside", "/etc/passwd"):
            with self.assertRaises(SystemExit, msg=bad):
                planner.move(bad, "99_その他")

    def test_merge_collision_gets_suffix_not_overwrite(self) -> None:
        keep = self.root / ".company" / "codex" / "queue" / "job-a"
        touch(keep / "keep.md", "original")

        organize(self.root)

        self.assertEqual((keep / "keep.md").read_text(encoding="utf-8"), "original")
        self.assertTrue((keep.with_name("job-a-2") / "prompt.md").exists())

    def test_rerun_is_idempotent(self) -> None:
        organize(self.root)
        before = sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*"))

        second = organize(self.root)
        self.assertEqual(second.actions, [])

        after = sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*"))
        self.assertEqual(before, after)

    def test_manifest_records_every_action(self) -> None:
        planner = organize(self.root)
        manifest = (self.junk / "MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn(f"# Drive root restructure {TODAY}", manifest)
        self.assertIn("shorts-factory", manifest)
        # Header row plus one row per action.
        self.assertEqual(manifest.count("\n| "), len(planner.actions) + 1)


if __name__ == "__main__":
    unittest.main()
