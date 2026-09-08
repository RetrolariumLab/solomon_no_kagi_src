from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.validation import source_2_minor_release as audit


ROOT = Path(__file__).resolve().parents[2]


class Source2MinorReleaseTests(unittest.TestCase):
    def test_release_header_is_project_owned(self) -> None:
        release = {"schema_version": 1, "release_line": "2.x"}
        self.assertEqual(audit.validate_release_header(release), [])
        release["contract"] = {"source": "external"}
        self.assertIn(
            "release manifest must contain only project-owned metadata",
            audit.validate_release_header(release),
        )

    def test_inherited_section_hash_rejects_baseline_drift(self) -> None:
        predecessor = {identifier: [] for identifier in audit.INHERITED_SECTION_IDS}
        release = {
            "inherited_sections": [
                {"id": identifier, "sha256": audit.section_digest([])}
                for identifier in sorted(audit.INHERITED_SECTION_IDS)
            ],
            "accepted_profiles": [],
        }
        self.assertEqual(audit.validate_inheritance(predecessor, release), [])
        release["inherited_sections"][0]["sha256"] = "0" * 64
        self.assertTrue(
            any(
                "inherited Source 2.0 section changed" in error
                for error in audit.validate_inheritance(predecessor, release)
            )
        )

    def test_development_history_accepts_an_unpinned_terminal(self) -> None:
        release = {
            "status": "development",
            "predecessor": {"commit": "base"},
            "delta_history": {
                "from_exclusive": "base",
                "through_inclusive": None,
                "commit_count": 0,
            },
        }
        with patch.object(audit.release_history, "validate_release_history", return_value=[]):
            self.assertEqual(audit.validate_delta_history(ROOT, release), [])

    def test_pinned_history_rejects_uncovered_substantive_commit(self) -> None:
        release = {
            "status": "development",
            "predecessor": {"commit": "base"},
            "delta_history": {
                "from_exclusive": "base",
                "through_inclusive": "1" * 40,
                "commit_count": 1,
            },
        }
        responses = [["1" * 40], ["2" * 40], ["scripts/tool.py"]]
        with patch.object(audit, "git_lines", side_effect=responses), patch.object(
            audit.release_history, "validate_release_history", return_value=[]
        ):
            errors = audit.validate_delta_history(ROOT, release)
        self.assertEqual(
            errors,
            ["delta_history does not cover substantive commit " + "2" * 12],
        )

    def test_project_release_boundary_and_predecessor_are_current(self) -> None:
        release = audit.load_json(ROOT / "config/source_reconstruction_2_1.json")
        self.assertEqual(audit.validate_release_header(release), [])
        predecessor, errors = audit.validate_predecessor(ROOT, release)
        self.assertEqual(errors, [])
        self.assertEqual(audit.validate_inheritance(predecessor, release), [])


if __name__ == "__main__":
    unittest.main()
