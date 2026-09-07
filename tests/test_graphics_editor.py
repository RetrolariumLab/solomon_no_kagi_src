from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import graphics_editor
from project import digest, parse_ines
from revision_profiles import get_profile, load_profiles


def synthetic_image() -> tuple[bytes, dict[str, object]]:
    header = bytearray(b"NES\x1a")
    header.extend((2, 4, 0x30, 0))
    header.extend(b"\x00" * 8)
    prg = bytes(32768)
    chr_data = bytes(graphics_editor.CHR_SIZE)
    image = bytes(header) + prg + chr_data
    profile: dict[str, object] = {
        "id": "test",
        "rom": {"sha256": digest(image, "sha256")},
        "chr": {"sha256": digest(chr_data, "sha256")},
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
        self.document = graphics_editor.export_document(
            bytes(parse_ines(self.image)["chr"]), self.profile
        )

    def test_exports_complete_fixed_chr_layout(self) -> None:
        self.assertEqual(len(self.document["banks"]), 4)
        self.assertEqual(len(self.document["banks"][0]["tiles"]), 512)
        self.assertEqual(
            graphics_editor.document_summary(self.document),
            "4 CHR banks, 2048 tiles, 131072 pixels",
        )

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
                parsed = parse_ines(image)
                document = graphics_editor.export_document(
                    bytes(parsed["chr"]), profile
                )
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
        usa_document = graphics_editor.export_document(
            bytes(parse_ines(usa_image)["chr"]), usa
        )
        europe_document = graphics_editor.export_document(
            bytes(parse_ines(europe_image)["chr"]), europe
        )
        self.assertNotEqual(
            usa_document["source_rom_sha256"],
            europe_document["source_rom_sha256"],
        )
        self.assertEqual(
            usa_document["source_chr_sha256"],
            europe_document["source_chr_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
