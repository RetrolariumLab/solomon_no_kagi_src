"""Tests for the stable categorized script runner."""

from __future__ import annotations

import unittest

from scripts import run


class ScriptRunnerTests(unittest.TestCase):
    def test_lists_tools_from_each_public_category(self) -> None:
        tools = run.available_tools()

        self.assertIn("authoring.level_editor", tools)
        self.assertIn("build.project", tools)
        self.assertIn("runtime.runtime_scenarios", tools)
        self.assertIn("validation.source_2_minor_release", tools)

    def test_rejects_flat_and_private_names(self) -> None:
        for name in ("project", "private.tool", "build._hidden"):
            with self.subTest(name=name), self.assertRaises(SystemExit):
                run.require_tool(name)


if __name__ == "__main__":
    unittest.main()
