from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

from scripts.validation import public_command_smoke


ROOT = Path(__file__).resolve().parents[2]


class PublicCommandSmokeTests(unittest.TestCase):
    def test_real_lint_target_passes_in_disposable_clone(self) -> None:
        output = public_command_smoke.run_disposable_make(ROOT, "lint")
        self.assertIn("project structure, manifests, source contract", output)

    def test_real_minor_release_audit_passes_in_disposable_clone(self) -> None:
        output = public_command_smoke.run_disposable_make(
            ROOT, "source-2-minor-audit"
        )
        self.assertIn("Source Reconstruction 2.1 contract", output)

    def test_real_minor_release_audit_propagates_failure(self) -> None:
        # The audit runs at the 2.1 tag; without the tag it cannot run.
        def drop_release_tag(clone: Path) -> None:
            subprocess.run(
                ["git", "-C", str(clone), "tag", "-d", "source-reconstruction-2.1"],
                check=True,
                capture_output=True,
            )

        with self.assertRaises(
            public_command_smoke.PublicCommandSmokeError
        ) as raised:
            public_command_smoke.run_disposable_make(
                ROOT,
                "source-2-minor-audit",
                prepare_clone=drop_release_tag,
            )

        message = str(raised.exception)
        self.assertIn("public command 'make source-2-minor-audit' failed", message)
        self.assertIn("cannot check out source-reconstruction-2.1", message)


if __name__ == "__main__":
    unittest.main()
