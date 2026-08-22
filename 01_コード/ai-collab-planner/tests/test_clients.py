import subprocess
import unittest
from unittest.mock import patch
from pathlib import Path

from ai_planner.clients import CliModelRunner
from ai_planner.config import load_settings
from ai_planner.domain import Role


class ClientCommandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings = load_settings(Path(__file__).parents[1] / "config.toml")
        cls.runner = CliModelRunner(settings)

    def test_codex_review_is_read_only(self):
        command = self.runner._codex_command(Role("codex", "gpt-5.6-sol"), "review", False)
        self.assertIn("read-only", command)
        self.assertNotIn("workspace-write", command)
        self.assertNotIn("--ask-for-approval", command)
        self.assertNotIn("--yolo", command)
        self.assertIn("--skip-git-repo-check", command)
        self.assertNotIn("review", command)
        self.assertEqual(command[-1], "-")

    def test_codex_can_run_in_a_new_non_git_project(self):
        command = self.runner._codex_command(Role("codex", "gpt-5.6-sol"), "requirements", False)
        self.assertEqual(command[1], "exec")
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("read-only", command)

    def test_codex_implementation_is_workspace_write(self):
        command = self.runner._codex_command(Role("codex", "gpt-5.6-sol"), "implement", True)
        self.assertIn("workspace-write", command)
        self.assertNotIn("danger-full-access", command)

    def test_claude_review_has_only_read_tools(self):
        command = self.runner._claude_command(Role("claude", "claude-opus-5"), "review", False)
        self.assertIn("plan", command)
        self.assertIn("Read,Glob,Grep", command)
        self.assertIn("--strict-mcp-config", command)
        self.assertNotIn("review", command)

    @patch("ai_planner.clients.subprocess.run")
    @patch("ai_planner.clients.shutil.which")
    def test_run_uses_resolved_windows_command_path(self, mock_which, mock_run):
        resolved = r"C:\Users\test\AppData\Roaming\npm\codex.cmd"
        mock_which.return_value = resolved
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")

        self.runner.run(Role("codex", "gpt-5.6-sol"), "review", Path.cwd(), False)

        executed_command = mock_run.call_args.args[0]
        self.assertEqual(executed_command[0], resolved)
        self.assertEqual(mock_run.call_args.kwargs["input"], "review")

    @patch("ai_planner.clients.subprocess.run")
    @patch("ai_planner.clients.shutil.which")
    def test_claude_prompt_is_passed_through_stdin(self, mock_which, mock_run):
        resolved = r"C:\Users\test\AppData\Roaming\npm\claude.cmd"
        mock_which.return_value = resolved
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")

        long_prompt = "計画本文" * 5000
        self.runner.run(Role("claude", "claude-opus-5"), long_prompt, Path.cwd(), False)

        executed_command = mock_run.call_args.args[0]
        self.assertNotIn(long_prompt, executed_command)
        self.assertEqual(mock_run.call_args.kwargs["input"], long_prompt)

    @patch("ai_planner.clients.subprocess.run")
    @patch("ai_planner.clients.shutil.which")
    def test_claude_auth_status_does_not_run_inference(self, mock_which, mock_run):
        mock_which.return_value = r"C:\Tools\claude.cmd"
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="Logged in", stderr="")

        ok, detail = self.runner.auth_status("claude")

        self.assertTrue(ok)
        self.assertEqual(detail, "Logged in")
        self.assertEqual(mock_run.call_args.args[0][1:], ["auth", "status", "--text"])
        self.assertNotIn("-p", mock_run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
