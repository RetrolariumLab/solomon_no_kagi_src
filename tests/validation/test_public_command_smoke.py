from __future__ import annotations

import json
from pathlib import Path
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
        def invalidate_release(clone: Path) -> None:
            path = clone / "config" / "source_reconstruction_2_1.json"
            release = json.loads(path.read_text(encoding="utf-8"))
            release["release_line"] = "invalid"
            path.write_text(
                json.dumps(release, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        with self.assertRaises(
            public_command_smoke.PublicCommandSmokeError
        ) as raised:
            public_command_smoke.run_disposable_make(
                ROOT,
                "source-2-minor-audit",
                prepare_clone=invalidate_release,
            )

        message = str(raised.exception)
        self.assertIn("public command 'make source-2-minor-audit' failed", message)
        self.assertIn("release_line must be 2.x", message)


if __name__ == "__main__":
    unittest.main()
