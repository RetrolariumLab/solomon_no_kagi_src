from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.validation import release_history


VALID_MESSAGE = """Add a concrete release change

Change one tracked file in the synthetic repository and expose the result as a
real Git object.

Preserve the release history contract while testing object-level validation.

Co-Authored-By: Codex <noreply@openai.com>
"""


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


class ReleaseHistoryTests(unittest.TestCase):
    def make_repository(self, root: Path) -> str:
        git(root, "init", "-q")
        git(root, "config", "user.name", "Daniel Oranguthang")
        git(root, "config", "user.email", "75395800+oranguthang@users.noreply.github.com")
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        git(root, "add", "tracked.txt")
        git(root, "commit", "-q", "-m", VALID_MESSAGE)
        return git(root, "rev-parse", "HEAD")

    def test_nonempty_commit_with_contract_message_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.make_repository(root)
            (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
            git(root, "commit", "-q", "-am", VALID_MESSAGE)
            self.assertEqual(release_history.validate_release_history(root, base), [])

    def test_allow_empty_commit_is_rejected_from_git_objects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.make_repository(root)
            git(root, "commit", "-q", "--allow-empty", "-m", VALID_MESSAGE)
            errors = release_history.validate_release_history(root, base)
            self.assertTrue(any("is empty relative" in error for error in errors))

    def test_invalid_message_and_author_report_each_failure(self) -> None:
        record = release_history.CommitRecord(
            object_id="1" * 40,
            parents=("0" * 40,),
            tree="tree",
            author="Unknown <unknown@example.invalid>",
            message="WIP.",
        )
        errors = release_history.validate_commit_messages([record])
        self.assertTrue(any("invalid English subject" in error for error in errors))
        self.assertTrue(any("unexpected author" in error for error in errors))
        self.assertTrue(any("co-author trailer" in error for error in errors))
        self.assertTrue(any("two or three body paragraphs" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
