from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

from scripts.build import make_help
from scripts.reconstruction_status import parse_make_targets


ROOT = Path(__file__).resolve().parents[1]


class MakeHelpTests(unittest.TestCase):
    def test_build_helper_package_is_not_ignored(self) -> None:
        result = subprocess.run(
            ["git", "check-ignore", "scripts/build/make_help.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_documents_existing_public_targets(self) -> None:
        documented = make_help.documented_targets()
        entry_count = sum(len(entries) for _, entries in make_help.TARGET_GROUPS)
        self.assertEqual(len(documented), entry_count)
        self.assertLessEqual(documented, parse_make_targets(ROOT / "Makefile"))

    def test_rendering_exposes_each_category_and_selector(self) -> None:
        rendered = make_help.render_help()
        for heading, _entries in make_help.TARGET_GROUPS:
            self.assertIn(f"{heading}:", rendered)
        self.assertIn("PROFILE=usa|europe", rendered)
        self.assertIn("LEFT_PROFILE=", rendered)


if __name__ == "__main__":
    unittest.main()
