from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "git_drive_guard.py"
SPEC = importlib.util.spec_from_file_location("git_drive_guard", MODULE_PATH)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=path, check=True)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def age_file(path: Path, seconds: int) -> None:
    past = time.time() - seconds
    os.utime(path, (past, past))


class PathHeuristicsTest(unittest.TestCase):
    def test_drive_paths_are_detected(self) -> None:
        cases = [
            "/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc",
            "G:/マイドライブ/YNFactory-cc",
            "G:\\My Drive\\YNFactory-cc",
            "/Users/yuichi/Dropbox/YNFactory-cc",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertIsNotNone(guard.matched_drive_marker(Path(case)))

    def test_local_paths_are_not_flagged(self) -> None:
        for case in ["/Users/yuichi/YNFactory-cc", "C:/YNFactory-cc", "/home/user/YNFactory-cc"]:
            with self.subTest(case=case):
                self.assertIsNone(guard.matched_drive_marker(Path(case)))

    def test_conflict_names(self) -> None:
        positives = [
            "HANDOFF の競合コピー 2026-08-06.md",
            "notes競合コピー.md",
            "plan (yuichi's conflicted copy 2026-08-06).md",
            "chunk.tmp.drivedownload",
            "chunk.tmp.driveupload",
        ]
        for name in positives:
            with self.subTest(name=name):
                self.assertTrue(guard.is_conflict_name(name))

        for name in ["HANDOFF.md", "config", "pack-abc.pack"]:
            with self.subTest(name=name):
                self.assertFalse(guard.is_conflict_name(name))

    def test_drive_noise_names(self) -> None:
        for name in ["desktop.ini", ".DS_Store", "Icon\r", "spec.gdoc", "sheet.gsheet"]:
            with self.subTest(name=name):
                self.assertTrue(guard.is_drive_noise_name(name))
        self.assertFalse(guard.is_drive_noise_name("README.md"))


class RepoCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve() / "repo"
        self.root.mkdir()
        init_repo(self.root)
        self.ctx = guard.detect_context(self.root, lock_age=600, deep=False)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_clean_repo_has_no_critical_findings(self) -> None:
        findings = guard.collect(self.ctx, guard.BLOCKING_CHECKS)
        self.assertEqual([], [f for f in findings if f.severity == guard.CRITICAL])

    def test_stale_lock_is_critical_and_fixable(self) -> None:
        lock = self.ctx.git_dir / "index.lock"
        lock.write_text("", encoding="utf-8")
        age_file(lock, 3600)

        findings = guard.check_stale_locks(self.ctx)
        stale = [f for f in findings if f.check == "stale-locks"]
        self.assertEqual(1, len(stale))
        self.assertEqual(guard.CRITICAL, stale[0].severity)
        self.assertTrue(stale[0].fixable)
        self.assertIn(lock, stale[0].paths)

    def test_fresh_lock_is_only_a_warning(self) -> None:
        lock = self.ctx.git_dir / "index.lock"
        lock.write_text("", encoding="utf-8")

        findings = guard.check_stale_locks(self.ctx)
        self.assertEqual(["active-locks"], [f.check for f in findings])
        self.assertEqual(guard.WARN, findings[0].severity)

    def test_daily_sync_lock_is_ignored(self) -> None:
        lock = self.ctx.git_dir / "daily-git-sync.lock"
        lock.write_text("pid=1\n", encoding="utf-8")
        age_file(lock, 3600)

        self.assertEqual([], guard.check_stale_locks(self.ctx))

    def test_git_dir_conflict_copy_is_critical(self) -> None:
        stray = self.ctx.git_dir / "HEAD (1)"
        stray.write_text("ref: refs/heads/main\n", encoding="utf-8")

        findings = guard.check_git_dir_conflict_copies(self.ctx)
        self.assertEqual(1, len(findings))
        self.assertEqual(guard.CRITICAL, findings[0].severity)
        self.assertIn(stray, findings[0].paths)

    def test_worktree_conflict_copy_is_warning_only(self) -> None:
        stray = self.root / "05_プロジェクト" / "HANDOFF の競合コピー 2026-08-06.md"
        stray.parent.mkdir(parents=True)
        stray.write_text("draft\n", encoding="utf-8")

        findings = guard.check_worktree_conflict_copies(self.ctx)
        self.assertEqual(1, len(findings))
        self.assertEqual(guard.WARN, findings[0].severity)
        self.assertFalse(findings[0].fixable)

    def test_pruned_directories_are_skipped(self) -> None:
        stray = self.root / "node_modules" / "pkg" / "index の競合コピー.js"
        stray.parent.mkdir(parents=True)
        stray.write_text("//\n", encoding="utf-8")

        self.assertEqual([], guard.check_worktree_conflict_copies(self.ctx))

    def test_empty_object_is_critical(self) -> None:
        objects = self.ctx.git_dir / "objects" / "ab"
        objects.mkdir(parents=True, exist_ok=True)
        empty = objects / "cdef0123456789"
        empty.touch()

        findings = guard.check_empty_git_files(self.ctx)
        self.assertEqual(1, len(findings))
        self.assertEqual(guard.CRITICAL, findings[0].severity)
        self.assertIn(empty, findings[0].paths)

    def test_hooks_reported_missing_then_installed(self) -> None:
        self.assertEqual(["hooks"], [f.check for f in guard.check_hooks(self.ctx)])

        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, guard.command_install_hooks(self.ctx))

        self.assertEqual([], guard.check_hooks(self.ctx))
        for name in guard.HOOK_NAMES:
            hook = self.ctx.git_dir / "hooks" / name
            self.assertTrue(hook.is_file())
            self.assertTrue(os.access(hook, os.X_OK))

    def test_install_hooks_backs_up_foreign_hook(self) -> None:
        hooks_dir = self.ctx.git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        existing = hooks_dir / "pre-commit"
        existing.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")

        with redirect_stdout(io.StringIO()):
            guard.command_install_hooks(self.ctx)

        backup = hooks_dir / "pre-commit.bak"
        self.assertTrue(backup.is_file())
        self.assertIn("echo mine", backup.read_text(encoding="utf-8"))
        self.assertIn(guard.HOOK_MARKER, existing.read_text(encoding="utf-8"))

    def test_tracked_drive_noise_is_reported(self) -> None:
        noise = self.root / "desktop.ini"
        noise.write_text("[.ShellClassInfo]\n", encoding="utf-8")
        subprocess.run(["git", "add", "-f", "desktop.ini"], cwd=self.root, check=True)

        findings = guard.check_tracked_drive_noise(self.ctx)
        self.assertEqual(1, len(findings))
        self.assertEqual(guard.WARN, findings[0].severity)

    def test_gitignore_missing_patterns_are_reported(self) -> None:
        (self.root / ".gitignore").write_text("*.log\n", encoding="utf-8")

        findings = guard.check_gitignore(self.ctx)
        self.assertEqual(1, len(findings))
        self.assertEqual(sorted(guard.REQUIRED_IGNORE_PATTERNS), sorted(findings[0].details))

    def test_hook_mode_blocks_on_critical(self) -> None:
        stray = self.ctx.git_dir / "config (1)"
        stray.write_text("[core]\n", encoding="utf-8")

        with redirect_stdout(io.StringIO()):
            self.assertEqual(1, guard.command_check(self.ctx, hook_mode=True))

    def test_hook_mode_is_silent_and_passing_when_clean(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(0, guard.command_check(self.ctx, hook_mode=True))
        self.assertEqual("", buffer.getvalue())


class FixTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve() / "repo"
        self.root.mkdir()
        init_repo(self.root)
        self.ctx = guard.detect_context(self.root, lock_age=600, deep=False)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_fix_quarantines_stale_lock_and_conflict_copy(self) -> None:
        lock = self.ctx.git_dir / "index.lock"
        lock.write_text("", encoding="utf-8")
        age_file(lock, 3600)
        stray = self.ctx.git_dir / "HEAD (1)"
        stray.write_text("ref: refs/heads/main\n", encoding="utf-8")

        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, guard.command_fix(self.ctx, dry_run=False))

        self.assertFalse(lock.exists())
        self.assertFalse(stray.exists())

        quarantined = list((self.root / "_archive" / "git-drive-quarantine").rglob("*"))
        names = {path.name for path in quarantined}
        self.assertIn("index.lock", names)
        self.assertIn("HEAD (1)", names)

        # 隔離してもリポジトリは通常操作できる。
        result = subprocess.run(["git", "status", "--porcelain"], cwd=self.root, check=True)
        self.assertEqual(0, result.returncode)

    def test_dry_run_moves_nothing(self) -> None:
        lock = self.ctx.git_dir / "index.lock"
        lock.write_text("", encoding="utf-8")
        age_file(lock, 3600)

        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, guard.command_fix(self.ctx, dry_run=True))

        self.assertTrue(lock.exists())
        self.assertFalse((self.root / "_archive").exists())

    def test_fix_reports_when_nothing_is_fixable(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, guard.command_fix(self.ctx, dry_run=False))


if __name__ == "__main__":
    unittest.main()
