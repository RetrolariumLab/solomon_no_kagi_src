from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]

from scripts.build import project
from scripts.build import verify_rom


def sample_ines() -> bytes:
    header = b"NES\x1a" + bytes((1, 1, 0x30, 0)) + bytes(8)
    return header + bytes(range(256)) * 64 + bytes([0xA5]) * 8_192


def sample_manifest(image: bytes) -> dict[str, object]:
    parsed = project.parse_ines(image)
    return {
        "schema_version": 1,
        "reference_rom": {
            "file_size": len(image),
            "file_sha1": project.digest(image),
            "file_sha256": project.digest(image, "sha256"),
            "file_md5": project.digest(image, "md5"),
            "file_crc32": project.crc32(image),
            "payload_sha1": project.digest(parsed["payload"]),
            "payload_sha256": project.digest(parsed["payload"], "sha256"),
            "payload_crc32": project.crc32(parsed["payload"]),
            "header_sha1": project.digest(parsed["header"]),
            "header_sha256": project.digest(parsed["header"], "sha256"),
            "prg_sha1": project.digest(parsed["prg"]),
            "prg_sha256": project.digest(parsed["prg"], "sha256"),
            "prg_crc32": project.crc32(parsed["prg"]),
            "chr_sha1": project.digest(parsed["chr"]),
            "chr_sha256": project.digest(parsed["chr"], "sha256"),
            "chr_crc32": project.crc32(parsed["chr"]),
            "trainer_size": 0,
            "prg_size": 16_384,
            "chr_size": 8_192,
            "mapper": 3,
            "mirroring": "horizontal",
        },
    }


class DifferenceTests(unittest.TestCase):
    def test_equal_data_has_no_difference(self) -> None:
        self.assertIsNone(verify_rom.first_difference(b"abc", b"abc"))

    def test_finds_changed_byte(self) -> None:
        self.assertEqual(verify_rom.first_difference(b"axc", b"abc"), (1, 0x78, 0x62))

    def test_finds_truncation(self) -> None:
        self.assertEqual(verify_rom.first_difference(b"ab", b"abc"), (2, None, 0x63))

    def test_prg_mismatch_reports_cpu_address(self) -> None:
        parsed = project.parse_ines(sample_ines())
        changed = b"\x01" + parsed["prg"][1:]
        with self.assertRaisesRegex(project.ProjectError, r"CPU \$8000"):
            verify_rom.compare_bytes("prg", changed, parsed["prg"], parsed)


class VerificationTests(unittest.TestCase):
    def test_complete_comparison(self) -> None:
        image = sample_ines()
        output = io.StringIO()
        with redirect_stdout(output):
            verify_rom.compare_images(image, image, sample_manifest(image), "all")
        self.assertIn("built image matches the manifest", output.getvalue())

    def test_region_comparison_is_focused(self) -> None:
        original = sample_ines()
        changed = original[:-1] + bytes([original[-1] ^ 0xFF])
        output = io.StringIO()
        with redirect_stdout(output):
            verify_rom.compare_images(changed, original, sample_manifest(original), "prg")
        self.assertIn("prg:", output.getvalue())

    def test_asset_comparison(self) -> None:
        image = sample_ines()
        parsed = project.parse_ines(image)
        output = io.StringIO()
        with redirect_stdout(output):
            verify_rom.verify_asset(
                parsed["chr"], image, sample_manifest(image), "chr"
            )
        self.assertIn("chr:", output.getvalue())

    def test_report_validates_manifest(self) -> None:
        image = sample_ines()
        output = io.StringIO()
        with redirect_stdout(output):
            verify_rom.report_image(image, sample_manifest(image))
        self.assertIn("image matches the manifest", output.getvalue())


if __name__ == "__main__":
    unittest.main()
