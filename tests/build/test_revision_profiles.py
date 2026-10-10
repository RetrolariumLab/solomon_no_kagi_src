from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]

from scripts.build import project
from scripts.build import revision_profiles
from scripts.validation import room_data


def sample_image(seed: int = 0x20) -> bytes:
    header = b"NES\x1a" + bytes((2, 4, 0x30, 0)) + bytes(8)
    prg = bytes((seed + index) & 0xFF for index in range(32_768))
    chr_data = bytes((seed ^ index) & 0xFF for index in range(32_768))
    return header + prg + chr_data


def region_descriptor(payload: bytes) -> dict[str, object]:
    return {
        "size": len(payload),
        "sha1": project.digest(payload),
        "sha256": project.digest(payload, "sha256"),
    }


def sample_profile(
    profile_id: str,
    image: bytes,
    source_status: str = "complete",
    asset_path: str | None = None,
) -> dict[str, object]:
    parsed = project.parse_ines(image)
    path = asset_path or f"revisions/{profile_id}/chr/game.chr"
    return {
        "id": profile_id,
        "name": f"Sample {profile_id}",
        "region": "Test",
        "timing": "ntsc",
        "room_layout": "usa",
        "source_status": source_status,
        "assembly_define": None if source_status == "planned" else 0,
        "level_preview": None if source_status == "planned" else {
            "object_animation_pointer_address": "0xd000",
            "enemy_type_configuration_address": "0xa400",
        },
        "graphics_authoring": None if source_status == "planned" else {
            "room_palette_template_address": "0x8100",
            "room_group_colors_address": "0x8200",
            "ending_palette_values_address": "0x8300",
        },
        "playtest": None if source_status == "planned" else {
            "room_load_address": "0x9000",
            "gameplay_address": "0xa000",
            "current_room_address": "0x0428",
            "start_frame": 300,
            "ready_frames": 1000,
        },
        "reference_rom": f"{profile_id}.nes",
        "reference_provenance": "Synthetic unit-test image.",
        "rom": region_descriptor(image),
        "header": region_descriptor(parsed["header"]),
        "prg": region_descriptor(parsed["prg"]),
        "chr": region_descriptor(parsed["chr"]),
        "room_fingerprints": {
            family: project.digest(family.encode("ascii"), "sha256")
            for family in revision_profiles.ROOM_FAMILIES
        },
        "verified_source_ranges": [],
        "extracted_assets": [
            {
                "id": f"{profile_id}_chr",
                "path": path,
                "region": "chr",
                "offset": 0,
                **region_descriptor(parsed["chr"]),
            }
        ],
    }


def sample_document() -> tuple[dict[str, object], dict[str, bytes]]:
    images = {"usa": sample_image(), "europe": sample_image(0x31)}
    document = {
        "schema_version": 1,
        "default_profile": "usa",
        "source_2_required_profiles": ["usa", "europe"],
        "profiles": [
            sample_profile("usa", images["usa"]),
            sample_profile(
                "europe",
                images["europe"],
                source_status="in-progress",
            ),
        ],
    }
    return document, images


class ManifestValidationTests(unittest.TestCase):
    def test_accepts_complete_manifest(self) -> None:
        document, _ = sample_document()
        self.assertEqual(revision_profiles.validate_profiles(document), [])

    def test_rejects_unknown_schema(self) -> None:
        document, _ = sample_document()
        document["schema_version"] = 2
        self.assertEqual(
            revision_profiles.validate_profiles(document),
            ["revision profile manifest is not schema 1"],
        )

    def test_rejects_duplicate_profile_ids(self) -> None:
        document, _ = sample_document()
        document["profiles"][1]["id"] = "usa"
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("revision profile ids are not unique", errors)

    def test_rejects_incomplete_default_profile(self) -> None:
        document, _ = sample_document()
        document["profiles"][0]["source_status"] = "in-progress"
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("default revision profile is not source-complete", errors)

    def test_rejects_missing_required_profile(self) -> None:
        document, _ = sample_document()
        document["source_2_required_profiles"].append("missing")
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("required profile does not exist: missing", errors)

    def test_rejects_invalid_room_layout(self) -> None:
        document, _ = sample_document()
        document["profiles"][1]["room_layout"] = "unknown"
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("europe has an unknown room layout", errors)

    def test_rejects_buildable_profile_without_graphics_authoring_contract(self) -> None:
        document, _ = sample_document()
        del document["profiles"][0]["graphics_authoring"]
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa has no graphics authoring contract", errors)

    def test_rejects_invalid_graphics_authoring_address(self) -> None:
        document, _ = sample_document()
        document["profiles"][0]["graphics_authoring"][
            "room_palette_template_address"
        ] = "0xfff0"
        errors = revision_profiles.validate_profiles(document)
        self.assertIn(
            "usa has invalid graphics authoring room_palette_template_address",
            errors,
        )

    def test_rejects_incomplete_room_fingerprint_inventory(self) -> None:
        document, _ = sample_document()
        del document["profiles"][0]["room_fingerprints"]["room_items"]
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa room fingerprint families differ", errors)

    def test_rejects_invalid_hash(self) -> None:
        document, _ = sample_document()
        document["profiles"][0]["prg"]["sha256"] = "not-a-hash"
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa has invalid prg sha256", errors)

    def test_rejects_region_sizes_that_do_not_compose_rom(self) -> None:
        document, _ = sample_document()
        document["profiles"][0]["chr"]["size"] -= 1
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa region sizes do not compose the ROM", errors)

    def test_rejects_escaping_asset_path(self) -> None:
        document, _ = sample_document()
        document["profiles"][0]["extracted_assets"][0]["path"] = "../private.chr"
        errors = revision_profiles.validate_profiles(document)
        self.assertTrue(any("unsafe asset path" in error for error in errors))

    def test_rejects_asset_outside_region(self) -> None:
        document, _ = sample_document()
        asset = document["profiles"][0]["extracted_assets"][0]
        asset["offset"] = 32_000
        asset["size"] = 1_000
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa/usa_chr exceeds chr", errors)

    def test_accepts_shared_asset_with_identical_identity(self) -> None:
        image = sample_image()
        shared = "chr/shared.chr"
        document = {
            "schema_version": 1,
            "default_profile": "usa",
            "source_2_required_profiles": ["usa", "europe"],
            "profiles": [
                sample_profile("usa", image, asset_path=shared),
                sample_profile(
                    "europe",
                    image,
                    source_status="in-progress",
                    asset_path=shared,
                ),
            ],
        }
        self.assertEqual(revision_profiles.validate_profiles(document), [])

    def test_rejects_shared_asset_with_conflicting_identity(self) -> None:
        document, _ = sample_document()
        shared = "chr/shared.chr"
        document["profiles"][0]["extracted_assets"][0]["path"] = shared
        document["profiles"][1]["extracted_assets"][0]["path"] = shared
        errors = revision_profiles.validate_profiles(document)
        self.assertIn(
            "asset path has conflicting profile data: chr/shared.chr",
            errors,
        )

    def test_rejects_planned_profile_with_assembly_define(self) -> None:
        document, images = sample_document()
        planned = sample_profile("japan", images["usa"], source_status="planned")
        planned["assembly_define"] = 2
        document["profiles"].append(planned)
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("japan planned source has an assembly define", errors)

    def test_rejects_buildable_profile_without_playtest_contract(self) -> None:
        document, _ = sample_document()
        del document["profiles"][0]["playtest"]
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa has no playtest contract", errors)

    def test_rejects_buildable_profile_without_level_preview_contract(self) -> None:
        document, _ = sample_document()
        del document["profiles"][0]["level_preview"]
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa has no level preview contract", errors)

    def test_rejects_invalid_level_preview_address(self) -> None:
        document, _ = sample_document()
        document["profiles"][0]["level_preview"][
            "object_animation_pointer_address"
        ] = "0x10000"
        errors = revision_profiles.validate_profiles(document)
        self.assertIn(
            "usa has invalid level preview object_animation_pointer_address",
            errors,
        )

    def test_rejects_invalid_playtest_address(self) -> None:
        document, _ = sample_document()
        document["profiles"][0]["playtest"]["room_load_address"] = "0x7000"
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa has invalid playtest room_load_address", errors)

    def test_rejects_overlapping_verified_source_ranges(self) -> None:
        document, images = sample_document()
        profile = document["profiles"][0]
        parsed = project.parse_ines(images["usa"])
        first = parsed["prg"][10:30]
        second = parsed["prg"][20:40]
        profile["verified_source_ranges"] = [
            {
                "id": "first",
                "region": "prg",
                "offset": 10,
                **region_descriptor(first),
            },
            {
                "id": "second",
                "region": "prg",
                "offset": 20,
                **region_descriptor(second),
            },
        ]
        errors = revision_profiles.validate_profiles(document)
        self.assertIn("usa has overlapping verified source ranges", errors)

    def test_loader_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "profiles.json"
            manifest.write_text(
                '{"schema_version":1,"schema_version":1}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(project.ProjectError, "duplicate JSON key"):
                revision_profiles.load_profiles(manifest)


class ProfileSelectionTests(unittest.TestCase):
    def test_get_profile_returns_unique_match(self) -> None:
        document, _ = sample_document()
        profile = revision_profiles.get_profile(document, "europe")
        self.assertEqual(profile["timing"], "ntsc")

    def test_get_profile_rejects_unknown_id(self) -> None:
        document, _ = sample_document()
        with self.assertRaisesRegex(project.ProjectError, "not found"):
            revision_profiles.get_profile(document, "missing")

    def test_default_selection_is_source_2_scope(self) -> None:
        document, _ = sample_document()
        selected = revision_profiles.selected_profiles(document, None, False)
        self.assertEqual([profile["id"] for profile in selected], ["usa", "europe"])

    def test_all_selection_includes_planned_profiles(self) -> None:
        document, images = sample_document()
        document["profiles"].append(
            sample_profile("japan", images["usa"], source_status="planned")
        )
        selected = revision_profiles.selected_profiles(document, None, True)
        self.assertEqual(
            [profile["id"] for profile in selected],
            ["usa", "europe", "japan"],
        )

    def test_requires_assembly_define_for_buildable_source(self) -> None:
        document, _ = sample_document()
        profile = revision_profiles.get_profile(document, "europe")
        self.assertEqual(revision_profiles.require_buildable_source(profile), 0)

    def test_rejects_planned_source_build(self) -> None:
        document, images = sample_document()
        profile = sample_profile("japan", images["usa"], source_status="planned")
        with self.assertRaisesRegex(project.ProjectError, "no buildable source"):
            revision_profiles.require_buildable_source(profile)


class ReferenceImageTests(unittest.TestCase):
    def test_verifies_every_image_region(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usa.nes"
            path.write_bytes(images["usa"])
            parsed = revision_profiles.verify_reference(path, profile)
        self.assertEqual(len(parsed["prg"]), 32_768)
        self.assertEqual(len(parsed["chr"]), 32_768)

    def test_rejects_wrong_reference_image(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usa.nes"
            path.write_bytes(images["europe"])
            with self.assertRaisesRegex(project.ProjectError, "ROM sha1 mismatch"):
                revision_profiles.verify_reference(path, profile)

    def test_identifies_profile_by_complete_sha256(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.identify_profile(document, images["europe"])
        self.assertEqual(profile["id"], "europe")

    def test_rejects_unknown_image_identity(self) -> None:
        document, _ = sample_document()
        with self.assertRaisesRegex(project.ProjectError, "no unique profile"):
            revision_profiles.identify_profile(document, sample_image(0x99))

    def test_verifies_declared_source_range(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        parsed = project.parse_ines(images["usa"])
        payload = parsed["prg"][100:180]
        profile["verified_source_ranges"] = [
            {
                "id": "sample",
                "region": "prg",
                "offset": 100,
                **region_descriptor(payload),
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.nes"
            built = Path(directory) / "built.nes"
            reference.write_bytes(images["usa"])
            built.write_bytes(images["usa"])
            revision_profiles.verify_source_ranges(built, reference, profile)

    def test_rejects_changed_source_range(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        parsed = project.parse_ines(images["usa"])
        payload = parsed["prg"][100:180]
        profile["verified_source_ranges"] = [
            {
                "id": "sample",
                "region": "prg",
                "offset": 100,
                **region_descriptor(payload),
            }
        ]
        changed = bytearray(images["usa"])
        changed[16 + 120] ^= 0xFF
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.nes"
            built = Path(directory) / "built.nes"
            reference.write_bytes(images["usa"])
            built.write_bytes(changed)
            with self.assertRaisesRegex(project.ProjectError, "source range differs"):
                revision_profiles.verify_source_ranges(built, reference, profile)

    def test_verifies_complete_built_revision(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.nes"
            built = Path(directory) / "built.nes"
            reference.write_bytes(images["usa"])
            built.write_bytes(images["usa"])
            revision_profiles.verify_built_revision(built, reference, profile)

    def test_rejects_changed_complete_built_revision(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        changed = bytearray(images["usa"])
        changed[16 + 120] ^= 0xFF
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.nes"
            built = Path(directory) / "built.nes"
            reference.write_bytes(images["usa"])
            built.write_bytes(changed)
            with self.assertRaisesRegex(project.ProjectError, "built ROM sha1 mismatch"):
                revision_profiles.verify_built_revision(built, reference, profile)


class SplitAssetTests(unittest.TestCase):
    def test_writes_only_manifest_owned_slice(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        parsed = project.parse_ines(images["usa"])
        asset = profile["extracted_assets"][0]
        asset["offset"] = 11
        asset["size"] = 37
        payload = parsed["chr"][11:48]
        asset.update(region_descriptor(payload))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            paths = revision_profiles.split_profile(profile, parsed, output)
            self.assertEqual(paths, [output / asset["path"]])
            self.assertEqual(paths[0].read_bytes(), payload)
            self.assertFalse((output / "prg").exists())

    def test_reuses_identical_generated_asset(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        parsed = project.parse_ines(images["usa"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated"
            first = revision_profiles.split_profile(profile, parsed, output)
            second = revision_profiles.split_profile(profile, parsed, output)
            self.assertEqual(first, second)
            self.assertEqual(first[0].read_bytes(), parsed["chr"])

    def test_rejects_manifest_hash_that_does_not_match_slice(self) -> None:
        document, images = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        parsed = project.parse_ines(images["usa"])
        profile["extracted_assets"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(project.ProjectError, "sha256 mismatch"):
                revision_profiles.split_profile(profile, parsed, Path(directory))


class RoomEvidenceTests(unittest.TestCase):
    def test_removes_only_layout_dependent_offsets(self) -> None:
        value = {
            "prg_offset": 0x1234,
            "encoded_size": 5,
            "nested": [{"prg_offset": 0x5678, "value": 9}],
        }
        self.assertEqual(
            revision_profiles.without_locations(value),
            {"encoded_size": 5, "nested": [{"value": 9}]},
        )

    def test_structural_difference_reports_precise_path(self) -> None:
        left = {"rooms": [{"items": [1, 2]}]}
        right = {"rooms": [{"items": [1, 3]}]}
        self.assertEqual(
            revision_profiles.first_structural_difference(left, right),
            ("room_data.rooms[0].items[1]", 2, 3),
        )

    def test_equal_structures_have_no_difference(self) -> None:
        value = {"rooms": [{"items": [1, 2]}]}
        self.assertIsNone(
            revision_profiles.first_structural_difference(value, copy.deepcopy(value))
        )

    def test_room_audit_accepts_recorded_fingerprints(self) -> None:
        document, _ = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        fake_document = {
            family: {"family": family} for family in revision_profiles.ROOM_FAMILIES
        }
        profile["room_fingerprints"] = {
            family: revision_profiles.content_fingerprint(value)
            for family, value in fake_document.items()
        }
        with patch.object(revision_profiles, "room_document", return_value=fake_document):
            actual = revision_profiles.audit_room_fingerprints({}, profile)
        self.assertEqual(actual, profile["room_fingerprints"])

    def test_room_audit_rejects_changed_semantics(self) -> None:
        document, _ = sample_document()
        profile = revision_profiles.get_profile(document, "usa")
        fake_document = {
            family: {"family": family} for family in revision_profiles.ROOM_FAMILIES
        }
        with patch.object(revision_profiles, "room_document", return_value=fake_document):
            with self.assertRaisesRegex(project.ProjectError, "fingerprint mismatch"):
                revision_profiles.audit_room_fingerprints({}, profile)


if __name__ == "__main__":
    unittest.main()
