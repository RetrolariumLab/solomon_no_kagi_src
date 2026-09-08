from __future__ import annotations

from pathlib import Path
import unittest

from scripts.validation import public_command_smoke


ROOT = Path(__file__).resolve().parents[2]


class PublicCommandSmokeTests(unittest.TestCase):
    def test_real_lint_target_passes_in_disposable_clone(self) -> None:
        output = public_command_smoke.run_disposable_make(ROOT, "lint")
        self.assertIn("project structure, manifests, source contract", output)


if __name__ == "__main__":
    unittest.main()
