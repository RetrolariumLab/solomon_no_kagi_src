from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import graphics_editor
import graphics_studio
from project import digest, parse_ines
from revision_profiles import get_profile, load_profiles


def synthetic_image() -> tuple[bytes, dict[str, object]]:
    header = bytearray(b"NES\x1a")
    header.extend((2, 4, 0x30, 0))
    header.extend(b"\x00" * 8)
    prg = bytearray(32768)
    prg[0x100 : 0x100 + 36] = (
        graphics_editor.ROOM_PALETTE_HEADER
        + bytes(index % 0x40 for index in range(32))
        + bytes((0,))
    )
    prg[0x200 : 0x200 + 14] = bytes(range(12)) + bytes((0x80, 0x80))
    prg[0x300 : 0x300 + 3] = bytes((0x2C, 0x1C, 0x0C))
    chr_data = bytes(graphics_editor.CHR_SIZE)
    image = bytes(header) + bytes(prg) + chr_data
    profile: dict[str, object] = {
        "id": "test",
        "rom": {"sha256": digest(image, "sha256")},
        "chr": {"sha256": digest(chr_data, "sha256")},
        "graphics_authoring": {
            "room_palette_template_address": "0x8100",
            "room_group_colors_address": "0x8200",
            "ending_palette_values_address": "0x8300",
        },
    }
    return image, profile


def reference_case(profile_id: str) -> tuple[dict[str, object], bytes]:
    profiles = load_profiles(ROOT / "config" / "revision_profiles.json")
    profile = get_profile(profiles, profile_id)
    path = ROOT / profile["reference_rom"]
    if not path.is_file():
        raise unittest.SkipTest(f"{profile_id} reference ROM is unavailable")
    return profile, path.read_bytes()


class TileCodecTests(unittest.TestCase):
    def test_decodes_and_encodes_both_bitplanes(self) -> None:
        encoded = bytes((0xAA,) + (0,) * 7 + (0xCC,) + (0,) * 7)
        rows = graphics_editor.decode_tile(encoded)
        self.assertEqual(rows[0], "32103210")
        self.assertEqual(graphics_editor.encode_tile(rows), encoded)

    def test_rejects_wrong_row_shape_and_pixel_value(self) -> None:
        with self.assertRaisesRegex(graphics_editor.GraphicsEditorError, "8-pixel"):
            graphics_editor.encode_tile(["0"] * 8)
        with self.assertRaisesRegex(graphics_editor.GraphicsEditorError, "non-2-bit"):
            graphics_editor.encode_tile(["00000004"] + ["00000000"] * 7)


class GraphicsDocumentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image, self.profile = synthetic_image()
        self.document = graphics_editor.export_document(self.image, self.profile)

    def test_exports_complete_fixed_chr_layout(self) -> None:
        self.assertEqual(len(self.document["banks"]), 4)
        self.assertEqual(len(self.document["banks"][0]["tiles"]), 512)
        self.assertEqual(
            graphics_editor.document_summary(self.document),
            "4 CHR banks, 2048 tiles, 131072 pixels, 8 room palettes",
        )
        self.assertEqual(len(self.document["palette_data"]["room_palettes"]), 8)

    def test_zero_edit_build_reproduces_complete_image(self) -> None:
        rebuilt = graphics_editor.build_graphics_image(
            self.document, self.image, self.profile
        )
        graphics_editor.validate_rebuilt_document(
            self.document, rebuilt, self.profile
        )
        self.assertEqual(rebuilt, self.image)

    def test_pixel_edit_changes_only_the_selected_chr_plane_bit(self) -> None:
        modified = copy.deepcopy(self.document)
        modified["banks"][2]["tiles"][7]["rows"][3] = "00100000"
        rebuilt = graphics_editor.build_graphics_image(
            modified, self.image, self.profile
        )
        graphics_editor.validate_rebuilt_document(modified, rebuilt, self.profile)
        changed = [
            index
            for index, (before, after) in enumerate(zip(self.image, rebuilt))
            if before != after
        ]
        expected = 16 + 32768 + 2 * 8192 + 7 * 16 + 3
        self.assertEqual(changed, [expected])
        self.assertEqual(rebuilt[expected], 0x20)

    def test_palette_edit_changes_only_the_profile_owned_prg_byte(self) -> None:
        modified = copy.deepcopy(self.document)
        modified["palette_data"]["room_palettes"][3][2] = 0x3F
        rebuilt = graphics_editor.build_graphics_image(
            modified, self.image, self.profile
        )
        graphics_editor.validate_rebuilt_document(modified, rebuilt, self.profile)
        changed = [
            index
            for index, (before, after) in enumerate(zip(self.image, rebuilt))
            if before != after
        ]
        self.assertEqual(changed, [16 + 0x100 + 3 + 3 * 4 + 2])

    def test_rejects_invalid_room_group_palette_marker(self) -> None:
        modified = copy.deepcopy(self.document)
        modified["palette_data"]["room_group_colors"][0] = 0x81
        with self.assertRaisesRegex(
            graphics_editor.GraphicsEditorError, "special marker"
        ):
            graphics_editor.build_graphics_image(
                modified, self.image, self.profile
            )

    def test_schema_one_workspace_gains_verified_palette_data(self) -> None:
        legacy = copy.deepcopy(self.document)
        legacy["schema_version"] = 1
        del legacy["palette_data"]
        legacy["banks"][0]["tiles"][0]["rows"][0] = "10000000"
        upgraded = graphics_editor.upgrade_document(
            legacy, self.image, self.profile
        )
        self.assertEqual(upgraded["schema_version"], 2)
        self.assertEqual(upgraded["banks"][0]["tiles"][0]["rows"][0], "10000000")
        self.assertEqual(
            upgraded["palette_data"], self.document["palette_data"]
        )

    def test_rejects_non_contiguous_tile_index(self) -> None:
        modified = copy.deepcopy(self.document)
        modified["banks"][0]["tiles"][4]["index"] = 5
        with self.assertRaisesRegex(
            graphics_editor.GraphicsEditorError, "non-contiguous"
        ):
            graphics_editor.encode_document(modified, self.profile)

    def test_rejects_document_from_another_profile(self) -> None:
        modified = copy.deepcopy(self.document)
        modified["source_profile"] = "europe"
        with self.assertRaisesRegex(graphics_editor.GraphicsEditorError, "profile"):
            graphics_editor.encode_document(modified, self.profile)

    def test_rejects_changed_base_rom(self) -> None:
        changed = bytearray(self.image)
        changed[16] = 1
        with self.assertRaisesRegex(graphics_editor.GraphicsEditorError, "base ROM"):
            graphics_editor.build_graphics_image(
                self.document, bytes(changed), self.profile
            )


class RegionalGraphicsTests(unittest.TestCase):
    def test_round_trips_both_supported_profile_images(self) -> None:
        for profile_id in ("usa", "europe"):
            with self.subTest(profile=profile_id):
                profile, image = reference_case(profile_id)
                document = graphics_editor.export_document(image, profile)
                rebuilt = graphics_editor.build_graphics_image(
                    document, image, profile
                )
                graphics_editor.validate_rebuilt_document(
                    document, rebuilt, profile
                )
                self.assertEqual(rebuilt, image)

    def test_supported_profiles_share_chr_but_not_document_identity(self) -> None:
        usa, usa_image = reference_case("usa")
        europe, europe_image = reference_case("europe")
        self.assertEqual(
            parse_ines(usa_image)["chr"], parse_ines(europe_image)["chr"]
        )
        usa_document = graphics_editor.export_document(usa_image, usa)
        europe_document = graphics_editor.export_document(europe_image, europe)
        self.assertNotEqual(
            usa_document["source_rom_sha256"],
            europe_document["source_rom_sha256"],
        )
        self.assertEqual(
            usa_document["source_chr_sha256"],
            europe_document["source_chr_sha256"],
        )
        self.assertEqual(
            usa_document["palette_data"], europe_document["palette_data"]
        )


class GraphicsStudioTests(unittest.TestCase):
    def model(self) -> graphics_studio.GraphicsStudioDocument:
        image, profile = synthetic_image()
        document = graphics_editor.export_document(image, profile)
        return graphics_studio.GraphicsStudioDocument(
            document,
            profile,
            image,
            ROOT / "content/workspace/test/graphics.json",
            ROOT / "build/content/test/graphics.nes",
        )

    def test_atlas_projection_places_all_tiles_in_row_major_order(self) -> None:
        model = self.model()
        model.edit_pixel(0, 17, 2, 3, 3)
        projection = graphics_studio.atlas_pixels(model.document, 0)
        self.assertEqual(len(projection), 256)
        self.assertTrue(all(len(row) == 128 for row in projection))
        self.assertEqual(projection[8 + 3][8 + 2], "3")
        self.assertEqual(graphics_studio.tile_position(17), (1, 1))
        self.assertEqual(graphics_studio.tile_index(1, 1), 17)

    def test_pixel_edit_is_validated_dirty_and_undoable(self) -> None:
        model = self.model()
        self.assertTrue(model.edit_pixel(2, 7, 4, 5, 3))
        self.assertTrue(model.dirty)
        self.assertNotEqual(model.rebuilt_image(), model.base_image)
        self.assertEqual(model.undo(), (2, 7))
        self.assertFalse(model.dirty)
        self.assertEqual(model.rebuilt_image(), model.base_image)

    def test_transformations_share_one_bounded_undo_history(self) -> None:
        model = self.model()
        model.edit_pixel(1, 3, 0, 0, 1)
        model.transform(1, 3, "flip_horizontal")
        self.assertEqual(model.rows(1, 3)[0], "00000001")
        model.transform(1, 3, "flip_vertical")
        self.assertEqual(model.rows(1, 3)[7], "00000001")
        model.transform(1, 3, "rotate_clockwise")
        self.assertEqual(model.rows(1, 3)[7], "10000000")
        self.assertEqual(len(model.undo_stack), 4)

    def test_fill_and_cross_tile_paste_preserve_fixed_layout(self) -> None:
        model = self.model()
        model.transform(0, 0, "fill", 2)
        copied = model.rows(0, 0)
        self.assertTrue(model.replace_rows(3, 511, copied))
        self.assertEqual(model.rows(3, 511), ["22222222"] * 8)
        graphics_editor.encode_document(model.document, model.profile)

    def test_rejects_invalid_atlas_and_pixel_coordinates(self) -> None:
        model = self.model()
        with self.assertRaisesRegex(graphics_editor.GraphicsEditorError, "0..511"):
            graphics_studio.tile_position(512)
        with self.assertRaisesRegex(graphics_editor.GraphicsEditorError, "outside"):
            model.edit_pixel(0, 0, 8, 0, 1)


if __name__ == "__main__":
    unittest.main()
