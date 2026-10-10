from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.validation.tag_audit import TagAuditError, run_at_tag


def git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)


class TagAuditTests(unittest.TestCase):
    def test_the_tag_runs_its_own_tool_on_its_own_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            git(root, "init", "-q")
            git(root, "config", "user.name", "Test")
            git(root, "config", "user.email", "test@example.com")
            runner = root / "scripts" / "run.py"
            runner.parent.mkdir()
            runner.write_text(
                "import pathlib, sys\n"
                "sys.exit(0 if sys.argv[1:] == ['validation.audit'] and "
                "pathlib.Path('evidence.txt').is_file() else 1)\n",
                encoding="utf-8",
            )
            (root / "evidence.txt").write_text("released\n", encoding="utf-8")
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "Release")
            git(root, "tag", "-a", "release-1", "-m", "Release")
            # Later work removes the evidence and changes the runner.
            (root / "evidence.txt").unlink()
            runner.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
            git(root, "commit", "-q", "-am", "Move on")
            self.assertEqual(
                run_at_tag(root, "release-1", ["scripts/run.py", "validation.audit"]), 0
            )
            with self.assertRaisesRegex(TagAuditError, "cannot check out"):
                run_at_tag(root, "release-2", ["scripts/run.py", "validation.audit"])


if __name__ == "__main__":
    unittest.main()
