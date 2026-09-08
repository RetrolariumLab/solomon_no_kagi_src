from __future__ import annotations

from pathlib import Path
import unittest

from scripts.validation.ppu_update_data import (
    PpuUpdateCommand,
    PpuUpdateStream,
    decode_split_pointers,
    decode_stream,
    encode_command,
    encode_stream,
    load_manifest,
    validate_manifest_profile,
    validate_report,
)


class PpuUpdateDataTests(unittest.TestCase):
    def test_committed_profiles_record_distinct_localized_stream_layouts(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[2]
        usa = load_manifest(root / "config" / "validation" / "ppu_update_streams.json")
        europe = load_manifest(root / "config" / "validation" / "ppu_update_streams_europe.json")
        validate_manifest_profile(usa, "usa")
        validate_manifest_profile(europe, "europe")
        self.assertNotEqual(usa["pointer_sha1"], europe["pointer_sha1"])
        self.assertNotEqual(usa["data_sha1"], europe["data_sha1"])
        self.assertEqual(
            len(usa["stream_addresses"]), len(europe["stream_addresses"])
        )
        self.assertEqual(
            int(usa["data_end"], 0) - int(usa["data_start"], 0) + 1,
            367,
        )
        self.assertEqual(
            int(europe["data_end"], 0) - int(europe["data_start"], 0) + 1,
            349,
        )

    def test_decodes_repeat_and_literal_commands(self) -> None:
        prg = bytes((0x20, 0x40, 0x02, 0x24, 0x21, 0x00, 0xC1, 0xAA, 0xBB, 0x00))
        stream = decode_stream(prg + bytes(32_768 - len(prg)), 0x8000)
        self.assertEqual(stream.encoded_size, 10)
        self.assertEqual(
            stream.commands,
            (
                PpuUpdateCommand(0x2040, 1, False, 3, b"\x24"),
                PpuUpdateCommand(0x2100, 32, True, 2, b"\xAA\xBB"),
            ),
        )

    def test_stream_round_trip_preserves_encoding(self) -> None:
        stream = PpuUpdateStream(
            0x9000,
            (
                PpuUpdateCommand(0x23C0, 1, True, 2, b"\x55\xAA"),
                PpuUpdateCommand(0x2000, 32, False, 64, b"\x24"),
            ),
            0,
        )
        encoded = encode_stream(stream)
        prg = bytearray(32_768)
        prg[0x1000 : 0x1000 + len(encoded)] = encoded
        self.assertEqual(encode_stream(decode_stream(bytes(prg), 0x9000)), encoded)

    def test_rejects_invalid_payload_size(self) -> None:
        command = PpuUpdateCommand(0x2000, 1, True, 2, b"\x24")
        with self.assertRaisesRegex(ValueError, "payload"):
            encode_command(command)

    def test_decodes_parallel_pointer_tables(self) -> None:
        prg = bytearray(32_768)
        prg[0x100:0x102] = bytes((0x34, 0x78))
        prg[0x110:0x112] = bytes((0x92, 0x96))
        self.assertEqual(
            decode_split_pointers(bytes(prg), 0x8100, 0x8110, 2),
            [0x9234, 0x9678],
        )

    def test_audit_detects_pointer_and_hash_changes(self) -> None:
        report = {
            "pointers": [0x9000],
            "pointer_sha1": "wrong",
            "data_sha1": "data",
            "coverage_exact": True,
            "round_trip": True,
        }
        manifest = {
            "stream_addresses": ["0x9001"],
            "pointer_sha1": "pointer",
            "data_sha1": "data",
        }
        errors = validate_report(report, manifest)
        self.assertEqual(len(errors), 2)
        self.assertIn("pointer table", errors[0])


if __name__ == "__main__":
    unittest.main()
