from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import project
import level_editor
import revision_profiles


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


def empty_level_fixture() -> tuple[dict[str, object], bytes, dict[str, object]]:
    image = sample_image(0x44)
    profile = sample_profile("usa", image)
    document = {
        "schema_version": level_editor.DOCUMENT_SCHEMA,
        "game": level_editor.DOCUMENT_GAME,
        "source_profile": "usa",
        "source_rom_sha256": profile["rom"]["sha256"],
        "dimensions": {"width": 16, "height": 12},
        "tile_patterns": [
            {
                "index": index,
                "palette": 0,
                "top_left": 0,
                "top_right": 0,
                "bottom_left": 0,
                "bottom_right": 0,
            }
            for index in range(58)
        ],
        "mirror_schedules": [
            {"index": index, "initial_phase": [0] * 4, "loop_phase": [0] * 4}
            for index in range(16)
        ],
        "mirror_enemy_sets": [
            {"index": index, "enemy_types": [0x50], "loop_offset": 0}
            for index in range(17)
        ],
        "rooms": [
            {
                "number": index + 1,
                "blocks": {"brown": [], "white": []},
                "enemies": {"spawn_lifetime": 0, "placements": []},
                "items": {
                    "metadata": {
                        "mirror_2_schedule": 0,
                        "mirror_1_schedule": 0,
                        "mirror_2_enemy_set": 0,
                        "mirror_1_enemy_set": 0,
                        "key_status": "normal",
                        "time_decrease_rate": 0,
                        "door": {"x": 0, "y": -1},
                        "key": {"x": 0, "y": -1},
                        "player_start": {"x": 0, "y": -1},
                        "mirror_1": {"x": 0, "y": -1},
                        "mirror_2": {"x": 0, "y": -1},
                    },
                    "commands": [{"kind": "end", "opcode": 0}],
                },
            }
            for index in range(53)
        ],
    }
    return document, image, profile


class LevelDocumentValueTests(unittest.TestCase):
    def test_clean_position_discards_encoded_raw_value(self) -> None:
        self.assertEqual(
            level_editor.clean_position({"x": 7, "y": 5, "raw": 0x67}),
            {"x": 7, "y": 5},
        )

    def test_hidden_position_is_encodable(self) -> None:
        self.assertEqual(
            level_editor.clean_position({"x": 0, "y": -1}),
            {"x": 0, "y": -1},
        )

    def test_rejects_position_outside_packed_nibbles(self) -> None:
        for value in ({"x": 16, "y": 0}, {"x": 0, "y": -2}, {"x": 0, "y": 14}):
            with self.subTest(value=value):
                with self.assertRaisesRegex(level_editor.LevelEditorError, "outside"):
                    level_editor.clean_position(value)

    def test_spawn_lifetime_conversion_is_bijective(self) -> None:
        for decoded in range(256):
            encoded = level_editor.encoded_lifetime(decoded)
            self.assertEqual(level_editor.decoded_lifetime(encoded), decoded)

    def test_status_rate_encodes_editor_fields(self) -> None:
        self.assertEqual(
            level_editor.status_rate_byte(
                {"key_status": "normal", "time_decrease_rate": 2}
            ),
            0x02,
        )
        self.assertEqual(
            level_editor.status_rate_byte(
                {"key_status": "in_block", "time_decrease_rate": 1}
            ),
            0x41,
        )
        self.assertEqual(
            level_editor.status_rate_byte(
                {"key_status": "hidden", "time_decrease_rate": 2}
            ),
            0x82,
        )

    def test_rejects_unknown_key_status(self) -> None:
        with self.assertRaisesRegex(level_editor.LevelEditorError, "key status"):
            level_editor.status_rate_byte(
                {"key_status": "surprise", "time_decrease_rate": 1}
            )

    def test_repeat_opcode_is_derived_from_position_count(self) -> None:
        command = level_editor.encode_item_command(
            {
                "kind": "repeat",
                "type": 0x18,
                "positions": [{"x": 1, "y": 2}, {"x": 3, "y": 4}],
            }
        )
        self.assertEqual(command["opcode"], 0xC1)

    def test_rejects_empty_repeat(self) -> None:
        with self.assertRaisesRegex(level_editor.LevelEditorError, "1..32"):
            level_editor.encode_item_command(
                {"kind": "repeat", "type": 0x18, "positions": []}
            )

    def test_exports_only_editable_metadata_fields(self) -> None:
        metadata = {
            "mirror_2_schedule": 0,
            "mirror_1_schedule": 1,
            "mirror_2_enemy_set": 2,
            "mirror_1_enemy_set": 3,
            "key_status": "hidden",
            "time_decrease_rate": 2,
            "status_rate_raw": 0x82,
            **{
                name: {"x": index, "y": index, "raw": 0x10 + index}
                for index, name in enumerate(level_editor.POSITION_FIELDS)
            },
        }
        exported = level_editor.export_metadata(metadata)
        self.assertNotIn("status_rate_raw", exported)
        self.assertEqual(exported["door"], {"x": 0, "y": 0})


class LevelDocumentStructureTests(unittest.TestCase):
    def test_accepts_document_header(self) -> None:
        document, _, _ = empty_level_fixture()
        self.assertIs(level_editor.validate_document_header(document), document)

    def test_rejects_wrong_dimensions(self) -> None:
        document, _, _ = empty_level_fixture()
        document["dimensions"] = {"width": 20, "height": 12}
        with self.assertRaisesRegex(level_editor.LevelEditorError, "dimensions"):
            level_editor.validate_document_header(document)

    def test_rejects_wrong_game(self) -> None:
        document, _, _ = empty_level_fixture()
        document["game"] = "another-game"
        with self.assertRaisesRegex(level_editor.LevelEditorError, "another game"):
            level_editor.validate_document_header(document)

    def test_requires_contiguous_room_numbers(self) -> None:
        document, _, _ = empty_level_fixture()
        document["rooms"][4]["number"] = 99
        with self.assertRaisesRegex(level_editor.LevelEditorError, "not contiguous"):
            level_editor.require_indexed_records(document["rooms"], "rooms", 53)

    def test_requires_exact_record_count(self) -> None:
        with self.assertRaisesRegex(level_editor.LevelEditorError, "exactly 16"):
            level_editor.require_indexed_records([], "mirror_schedules", 16)

    def test_save_is_deterministic_and_loads(self) -> None:
        document, _, _ = empty_level_fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "levels.json"
            self.assertEqual(level_editor.save_document(path, document), "WRITE")
            first = path.read_bytes()
            self.assertEqual(level_editor.save_document(path, document), "OK")
            self.assertEqual(path.read_bytes(), first)
            self.assertEqual(level_editor.load_document(path), document)


class LevelPackingTests(unittest.TestCase):
    def test_pack_records_updates_split_pointer_planes(self) -> None:
        prg = bytearray(256)
        used, capacity = level_editor.pack_records(
            prg,
            pointer_table=10,
            data_start=40,
            data_end=50,
            records=(b"abc", b"de"),
            name="sample",
        )
        self.assertEqual((used, capacity), (5, 10))
        self.assertEqual(prg[40:45], b"abcde")
        self.assertEqual(prg[10:14], bytes((0x28, 0x2B, 0x80, 0x80)))

    def test_pack_records_rejects_capacity_overflow(self) -> None:
        with self.assertRaisesRegex(level_editor.LevelEditorError, "budget"):
            level_editor.pack_records(
                bytearray(64),
                pointer_table=0,
                data_start=10,
                data_end=12,
                records=(b"too long",),
                name="sample",
            )

    def test_build_and_decode_document(self) -> None:
        document, image, profile = empty_level_fixture()
        rebuilt, usage = level_editor.build_level_image(document, image, profile)
        self.assertEqual(len(rebuilt), len(image))
        self.assertEqual(usage["room_blocks"], (2544, 2544))
        level_editor.validate_rebuilt_document(document, rebuilt, profile)

    def test_modified_combined_block_survives_build_and_decode(self) -> None:
        document, image, profile = empty_level_fixture()
        document["rooms"][0]["blocks"]["brown"].append({"x": 4, "y": 5})
        document["rooms"][0]["blocks"]["white"].append({"x": 4, "y": 5})
        rebuilt, _ = level_editor.build_level_image(document, image, profile)
        decoded = level_editor.export_document(project.parse_ines(rebuilt), profile)
        self.assertEqual(
            decoded["rooms"][0]["blocks"]["brown"],
            [{"x": 4, "y": 5}],
        )
        self.assertEqual(
            decoded["rooms"][0]["blocks"]["white"],
            [{"x": 4, "y": 5}],
        )

    def test_modified_enemy_survives_build_and_decode(self) -> None:
        document, image, profile = empty_level_fixture()
        document["rooms"][0]["enemies"] = {
            "spawn_lifetime": 17,
            "placements": [{"type": 0x71, "position": {"x": 7, "y": 5}}],
        }
        rebuilt, _ = level_editor.build_level_image(document, image, profile)
        decoded = level_editor.export_document(project.parse_ines(rebuilt), profile)
        self.assertEqual(decoded["rooms"][0]["enemies"], document["rooms"][0]["enemies"])

    def test_modified_item_survives_build_and_decode(self) -> None:
        document, image, profile = empty_level_fixture()
        document["rooms"][0]["items"]["commands"] = [
            {"kind": "item", "type": 0x18, "position": {"x": 3, "y": 4}},
            {"kind": "end", "opcode": 0},
        ]
        rebuilt, _ = level_editor.build_level_image(document, image, profile)
        decoded = level_editor.export_document(project.parse_ines(rebuilt), profile)
        self.assertEqual(
            decoded["rooms"][0]["items"]["commands"],
            document["rooms"][0]["items"]["commands"],
        )

    def test_repeated_item_group_survives_build_and_decode(self) -> None:
        document, image, profile = empty_level_fixture()
        document["rooms"][0]["items"]["commands"] = [
            {
                "kind": "repeat",
                "type": 0x98,
                "positions": [
                    {"x": 3, "y": 4},
                    {"x": 7, "y": 8},
                    {"x": 12, "y": 2},
                ],
            },
            {"kind": "end", "opcode": 0},
        ]
        rebuilt, _ = level_editor.build_level_image(document, image, profile)
        decoded = level_editor.export_document(project.parse_ines(rebuilt), profile)
        self.assertEqual(
            decoded["rooms"][0]["items"]["commands"],
            document["rooms"][0]["items"]["commands"],
        )

    def test_constellation_terminator_survives_build_and_decode(self) -> None:
        document, image, profile = empty_level_fixture()
        document["rooms"][0]["items"]["commands"][-1] = {
            "kind": "constellation",
            "opcode": 0xF7,
            "position": {"x": 4, "y": 5},
        }
        rebuilt, _ = level_editor.build_level_image(document, image, profile)
        decoded = level_editor.export_document(project.parse_ines(rebuilt), profile)
        self.assertEqual(
            decoded["rooms"][0]["items"]["commands"][-1],
            document["rooms"][0]["items"]["commands"][-1],
        )

    def test_enemy_budget_overflow_is_rejected(self) -> None:
        document, image, profile = empty_level_fixture()
        document["rooms"][0]["enemies"]["placements"] = [
            {"type": 0x18, "position": {"x": index % 16, "y": index % 12}}
            for index in range(400)
        ]
        with self.assertRaisesRegex(level_editor.LevelEditorError, "budget"):
            level_editor.build_level_image(document, image, profile)


if __name__ == "__main__":
    unittest.main()
