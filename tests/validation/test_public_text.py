from __future__ import annotations

from pathlib import Path
import os
import subprocess
import tempfile
import unittest

from scripts.validation import public_text


class PublicTextTests(unittest.TestCase):
    def make_repository(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.name", "Release Tester"], cwd=root, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "tester@example.com"],
            cwd=root,
            check=True,
        )
        return root

    def commit(self, root: Path, message: str) -> None:
        environment = os.environ.copy()
        environment["GIT_AUTHOR_DATE"] = "2026-01-01T00:00:00+00:00"
        environment["GIT_COMMITTER_DATE"] = "2026-01-01T00:00:00+00:00"
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", message],
            cwd=root,
            env=environment,
            check=True,
        )

    def test_accepts_latin_text_and_neutral_punctuation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "README.md").write_text("English text — verified.\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            self.assertEqual(public_text.validate_current_tree(root), [])

    def test_rejects_non_latin_letters_in_current_text_and_paths(self) -> None:
        root = self.make_repository()
        document = root / "README.md"
        document.write_text("\u041d\u0435\u0430\u043d\u0433\u043b\u0438\u0439\u0441\u043a\u0438\u0439\n", encoding="utf-8")
        named = root / "docs" / "\u0444\u0430\u0439\u043b.md"
        named.parent.mkdir()
        named.write_text("English\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        errors = public_text.validate_current_tree(root)
        self.assertTrue(any("README.md" in error for error in errors))
        self.assertTrue(any("historical" not in error and "path " in error for error in errors))

    def test_rejects_deleted_non_latin_history(self) -> None:
        root = self.make_repository()
        document = root / "notes.md"
        document.write_text("\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a\n", encoding="utf-8")
        self.commit(root, "Add draft")
        document.unlink()
        (root / "README.md").write_text("English replacement\n", encoding="utf-8")
        self.commit(root, "Replace draft")
        self.assertEqual(public_text.validate_current_tree(root), [])
        errors = public_text.validate_history(root, "HEAD")
        self.assertTrue(any("historical blob" in error for error in errors))

    def test_rejects_non_latin_commit_metadata(self) -> None:
        root = self.make_repository()
        (root / "README.md").write_text("English\n", encoding="utf-8")
        self.commit(root, "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a")
        errors = public_text.validate_history(root, "HEAD")
        self.assertTrue(any("history HEAD" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
