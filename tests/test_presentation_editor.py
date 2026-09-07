from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import presentation_editor
from project import digest
from revision_profiles import get_profile, load_profiles


def synthetic_case() -> tuple[bytes, dict[str, object], dict[str, object]]:
    header = b"NES\x1a" + bytes((2, 4, 0x30, 0)) + bytes(8)
    prg = bytearray(32768)
    record = bytes((0x40, 0x00, 0x80, 0x7F))
    logo = bytes((0x40, 0x01, 0x81, 0x7F))
    prg[0x100 : 0x104] = record
    prg[0x110 : 0x114] = logo
    prg[0x120 : 0x122] = bytes((2, 4))
    prg[0x122 : 0x124] = bytes((0x01, 0x80))
    image = header + bytes(prg) + bytes(32768)
    profile: dict[str, object] = {
        "id": "test",
        "rom": {"sha256": digest(image, "sha256")},
    }
    manifest: dict[str, object] = {
        "streams": [
            {"name": "record", "address": "0x8100", "encoded_size": 4},
            {"name": "logo", "address": "0x8110", "encoded_size": 4},
        ],
        "demo_input": {
            "duration_address": "0x8120",
            "input_address": "0x8122",
            "input_count": 2,
        },
    }
    return image, profile, manifest


def reference_case(profile_id: str) -> tuple[dict[str, object], bytes]:
    profiles = load_profiles(ROOT / "config" / "revision_profiles.json")
    profile = get_profile(profiles, profile_id)
    path = ROOT / profile["reference_rom"]
    if not path.is_file():
        raise unittest.SkipTest(f"{profile_id} reference ROM is unavailable")
    return profile, path.read_bytes()


class PresentationDocumentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image, self.profile, self.manifest = synthetic_case()
        self.manifest_patch = patch(
            "presentation_editor.profile_manifest", return_value=self.manifest
        )
        self.manifest_patch.start()
        self.addCleanup(self.manifest_patch.stop)
        self.document = presentation_editor.export_document(
            self.image, self.profile
        )

    def test_exports_both_streams_and_every_demo_step(self) -> None:
        self.assertEqual([item["name"] for item in self.document["streams"]], ["record", "logo"])
        self.assertEqual(len(self.document["demo_steps"]), 2)
        self.assertEqual(
            presentation_editor.document_summary(self.document),
            "2 title streams, 2 literal tiles, 2 demo steps",
        )

    def test_zero_edit_build_reproduces_complete_image(self) -> None:
        rebuilt = presentation_editor.build_presentation_image(
            self.document, self.image, self.profile
        )
        presentation_editor.validate_rebuilt_document(
            self.document, rebuilt, self.profile
        )
        self.assertEqual(rebuilt, self.image)

    def test_literal_tile_edit_changes_only_its_fixed_prg_byte(self) -> None:
        modified = copy.deepcopy(self.document)
        modified["streams"][0]["tokens"][2]["tiles"][0] = 0x82
        rebuilt = presentation_editor.build_presentation_image(
            modified, self.image, self.profile
        )
        presentation_editor.validate_rebuilt_document(modified, rebuilt, self.profile)
        changed = [
            index
            for index, (before, after) in enumerate(zip(self.image, rebuilt))
            if before != after
        ]
        self.assertEqual(changed, [16 + 0x102])

    def test_demo_edit_changes_duration_and_named_button_mask(self) -> None:
        modified = copy.deepcopy(self.document)
        modified["demo_steps"][1]["duration"] = 9
        modified["demo_steps"][1]["buttons"] = ["A", "LEFT"]
        rebuilt = presentation_editor.build_presentation_image(
            modified, self.image, self.profile
        )
        presentation_editor.validate_rebuilt_document(modified, rebuilt, self.profile)
        changed = [
            index
            for index, (before, after) in enumerate(zip(self.image, rebuilt))
            if before != after
        ]
        self.assertEqual(changed, [16 + 0x121, 16 + 0x123])
        self.assertEqual(rebuilt[16 + 0x123], 0x82)

    def test_rejects_stream_growth_and_unknown_demo_button(self) -> None:
        grown = copy.deepcopy(self.document)
        grown["streams"][0]["tokens"][2]["tiles"].append(0x83)
        with self.assertRaisesRegex(
            presentation_editor.PresentationEditorError, "exactly 4 bytes"
        ):
            presentation_editor.build_presentation_image(
                grown, self.image, self.profile
            )
        invalid = copy.deepcopy(self.document)
        invalid["demo_steps"][0]["buttons"] = ["FIRE"]
        with self.assertRaisesRegex(
            presentation_editor.PresentationEditorError, "unknown demo input button"
        ):
            presentation_editor.build_presentation_image(
                invalid, self.image, self.profile
            )


class RegionalPresentationTests(unittest.TestCase):
    def test_round_trips_both_supported_profiles(self) -> None:
        for profile_id in ("usa", "europe"):
            with self.subTest(profile=profile_id):
                profile, image = reference_case(profile_id)
                document = presentation_editor.export_document(image, profile)
                rebuilt = presentation_editor.build_presentation_image(
                    document, image, profile
                )
                presentation_editor.validate_rebuilt_document(
                    document, rebuilt, profile
                )
                self.assertEqual(rebuilt, image)

    def test_relocated_profiles_share_content_but_keep_identity(self) -> None:
        usa, usa_image = reference_case("usa")
        europe, europe_image = reference_case("europe")
        usa_document = presentation_editor.export_document(usa_image, usa)
        europe_document = presentation_editor.export_document(europe_image, europe)
        self.assertEqual(usa_document["streams"], europe_document["streams"])
        self.assertEqual(usa_document["demo_steps"], europe_document["demo_steps"])
        self.assertNotEqual(usa_document["layout"], europe_document["layout"])
        self.assertNotEqual(
            usa_document["source_rom_sha256"],
            europe_document["source_rom_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
