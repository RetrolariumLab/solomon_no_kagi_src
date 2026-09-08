from __future__ import annotations

from pathlib import Path
import unittest

from scripts.authoring import editor_workstation_smoke


ROOT = Path(__file__).resolve().parents[2]


class EditorWorkstationSmokeContractTests(unittest.TestCase):
    def test_required_actions_cover_every_public_editor(self) -> None:
        self.assertEqual(
            editor_workstation_smoke.REQUIRED_ACTIONS,
            {
                "level": {"save", "build", "play", "preview", "dirty-close"},
                "sound": {"save", "build", "play", "preview", "dirty-close"},
                "graphics": {"save", "build", "preview", "dirty-close"},
                "presentation": {"save", "build", "preview", "dirty-close"},
            },
        )

    def test_make_routes_profile_smoke_through_the_workstation_driver(self) -> None:
        make = (ROOT / "mk" / "authoring.mk").read_text(encoding="utf-8")
        recipe = make.split("editor-ui-smoke-profile:", 1)[1]
        self.assertIn("authoring.editor_workstation_smoke", recipe)


if __name__ == "__main__":
    unittest.main()
