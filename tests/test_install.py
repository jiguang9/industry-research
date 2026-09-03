"""Tests for tools/install.py.

Runs the installer as a subprocess (the way a user actually invokes it) so
these tests exercise the real CLI, not just importable internals. All
filesystem side effects are confined to temp directories; INDUSTRY_RESEARCH_BACKUP_ROOT
is overridden so --replace never touches the real $HOME.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALL_PY = ROOT / "tools" / "install.py"


def run_install(args: list[str], cwd: Path, backup_root: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["INDUSTRY_RESEARCH_BACKUP_ROOT"] = str(backup_root)
    return subprocess.run(
        [sys.executable, str(INSTALL_PY), *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )


class InstallTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.backup_root = self.tmp / "backups"
        # A cwd that is deliberately NOT the repo root, to prove the
        # installer locates the source from its own file location.
        self.cwd = self.tmp / "somewhere_else"
        self.cwd.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_fresh_install_with_space_and_unicode_path(self):
        dest = self.tmp / "测试 目录" / "industry-research"
        result = run_install(["--platform", "codex", "--dest", str(dest)], self.cwd, self.backup_root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((dest / "SKILL.md").exists())
        self.assertTrue((dest / "MANIFEST.sha256").exists())
        self.assertTrue((dest / "VERSION").exists())
        self.assertTrue((dest / "LICENSE").exists())

    def test_install_does_not_copy_dev_only_directories(self):
        dest = self.tmp / "no-dev-files"
        run_install(["--platform", "codex", "--dest", str(dest)], self.cwd, self.backup_root)
        for dev_dir in ("tests", "tools", "evals", "docs", "examples", ".github", ".git"):
            self.assertFalse((dest / dev_dir).exists(), f"{dev_dir} should not be installed")

    def test_idempotent_reinstall_is_a_no_op_success(self):
        dest = self.tmp / "idempotent"
        first = run_install(["--platform", "codex", "--dest", str(dest)], self.cwd, self.backup_root)
        self.assertEqual(first.returncode, 0)
        second = run_install(["--platform", "codex", "--dest", str(dest)], self.cwd, self.backup_root)
        self.assertEqual(second.returncode, 0)
        self.assertIn("up to date", second.stdout)

    def test_conflicting_content_without_replace_fails_and_leaves_target_untouched(self):
        dest = self.tmp / "conflict"
        run_install(["--platform", "codex", "--dest", str(dest)], self.cwd, self.backup_root)
        (dest / "SKILL.md").write_text("local edit that must survive", encoding="utf-8")

        result = run_install(["--platform", "codex", "--dest", str(dest)], self.cwd, self.backup_root)
        self.assertEqual(result.returncode, 1)
        self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "local edit that must survive")

    def test_replace_overwrites_and_backs_up_outside_dest_tree(self):
        dest = self.tmp / "replace-me"
        run_install(["--platform", "codex", "--dest", str(dest)], self.cwd, self.backup_root)
        (dest / "SKILL.md").write_text("local edit that should be backed up", encoding="utf-8")

        result = run_install(["--platform", "codex", "--dest", str(dest), "--replace"], self.cwd, self.backup_root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        real_skill_md = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), real_skill_md)

        backups = list(self.backup_root.iterdir())
        self.assertEqual(len(backups), 1)
        backed_up_skill_md = (backups[0] / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(backed_up_skill_md, "local edit that should be backed up")

        # The backup must not itself look like an installable skill sitting
        # inside dest's parent (i.e. not discoverable by a skills scanner
        # rooted at dest.parent).
        self.assertNotEqual(backups[0].parent, dest.parent)

    def test_refuses_when_target_equals_source(self):
        result = run_install(["--platform", "codex", "--dest", str(ROOT)], self.cwd, self.backup_root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("same as the source", result.stdout + result.stderr)

    def test_refuses_when_target_is_inside_source(self):
        result = run_install(
            ["--platform", "codex", "--dest", str(ROOT / "some_nested_target")], self.cwd, self.backup_root
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside the source repository", result.stdout + result.stderr)

    def test_default_platform_targets_are_under_home_and_named_industry_research(self):
        for platform in ("claude", "codex", "openclaw", "hermes"):
            help_text = subprocess.run(
                [sys.executable, str(INSTALL_PY), "--help"], capture_output=True, text=True
            ).stdout
            self.assertIn(platform, help_text)

    def test_all_four_platforms_installable_side_by_side_via_dest(self):
        for platform in ("claude", "codex", "openclaw", "hermes"):
            dest = self.tmp / "multi" / platform / "industry-research"
            result = run_install(["--platform", platform, "--dest", str(dest)], self.cwd, self.backup_root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((dest / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
