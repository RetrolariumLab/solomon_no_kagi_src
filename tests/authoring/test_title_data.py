from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from scripts.authoring.title_data import (
    TitleCursorCommand,
    TitleLiteralRun,
    collect_report,
    decode_buttons,
    decode_cursor_command,
    decode_demo_input,
    decode_stream,
    encode_buttons,
    encode_cursor_command,
    encode_demo_input,
    encode_stream,
    load_manifest,
    title_ppu_address,
    validate_manifest_profile,
    validate_report,
)


class TitleDataTests(unittest.TestCase):
    def test_committed_profiles_record_relocated_identical_title_and_demo_data(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[2]
        usa = load_manifest(root / "config" / "title_data.json")
        europe = load_manifest(root / "config" / "title_data_europe.json")
        validate_manifest_profile(usa, "usa")
        validate_manifest_profile(europe, "europe")
        self.assertNotEqual(usa["data_start"], europe["data_start"])
        self.assertEqual(usa["data_sha1"], europe["data_sha1"])
        self.assertEqual(
            usa["demo_input"]["data_sha1"], europe["demo_input"]["data_sha1"]
        )

    def test_cursor_commands_round_trip_semantically(self) -> None:
        expected = (
            (0x06, "set_column", 6),
            (0x53, "set_row", 0x53),
            (0x60, "add_row", 1),
            (0x7E, "add_row", 31),
            (0x7F, "terminate", None),
        )
        for opcode, kind, value in expected:
            command = decode_cursor_command(opcode)
            self.assertEqual((command.kind, command.value), (kind, value))
            self.assertEqual(encode_cursor_command(command), opcode)

    def test_ppu_address_preserves_decoder_carry_rotation(self) -> None:
        self.assertEqual(title_ppu_address(0x53, 0x06), 0x28C6)
        self.assertEqual(title_ppu_address(0x59, 0x26), 0x2A66)

    def test_demo_input_round_trip_uses_named_buttons(self) -> None:
        self.assertEqual(decode_buttons(0x89), ("A", "UP", "RIGHT"))
        self.assertEqual(encode_buttons(("A", "UP", "RIGHT")), 0x89)
        prg = bytearray(32_768)
        prg[0:2] = bytes((0x20, 0x03))
        prg[2:4] = bytes((0x89, 0x00))
        steps = decode_demo_input(bytes(prg), 0x8000, 0x8002, 2)
        self.assertEqual(encode_demo_input(steps), (prg[0:2], prg[2:4]))

    def test_stream_round_trip_groups_literal_tiles(self) -> None:
        prg = bytearray(32_768)
        encoded = bytes((0x53, 0x06, 0xE8, 0x8F, 0x60, 0xEA, 0x7F))
        prg[0 : len(encoded)] = encoded
        stream = decode_stream(bytes(prg), 0x8000)
        literals = [
            token for token in stream.tokens if isinstance(token, TitleLiteralRun)
        ]
        self.assertEqual([run.tiles for run in literals], [b"\xe8\x8f", b"\xea"])
        self.assertEqual([run.ppu_address for run in literals], [0x28C6, 0x2906])
        self.assertEqual(encode_stream(stream), encoded)

    def test_collects_a_minimal_complete_layout(self) -> None:
        prg = bytearray(32_768)
        encoded = bytes((0x40, 0x00, 0x80, 0x7F))
        prg[0 : len(encoded)] = encoded
        prg[0x10] = 2
        prg[0x11] = 0
        digest = hashlib.sha1(encoded).hexdigest()
        manifest = {
            "data_start": "0x8000",
            "data_end": "0x8003",
            "data_sha1": digest,
            "demo_input": {
                "duration_address": "0x8010",
                "input_address": "0x8011",
                "end_address": "0x8011",
                "input_count": 1,
                "encoded_size": 2,
                "terminal_duration_alias": 0,
                "duration_sha1": hashlib.sha1(b"\x02").hexdigest(),
                "input_sha1": hashlib.sha1(b"\x00").hexdigest(),
                "data_sha1": hashlib.sha1(b"\x02\x00").hexdigest(),
            },
            "streams": [
                {
                    "name": "test",
                    "address": "0x8000",
                    "end_address": "0x8003",
                    "encoded_size": 4,
                    "command_count": 3,
                    "literal_run_count": 1,
                    "literal_tile_count": 1,
                    "literal_ppu_addresses": ["0x2000"],
                    "sha1": digest,
                }
            ],
        }
        report = collect_report(bytes(prg), manifest)
        self.assertTrue(report["coverage_exact"])
        self.assertTrue(report["round_trip"])
        self.assertEqual(report["audited_size"], 6)
        self.assertEqual(validate_report(report, manifest), [])
        changed_report = {**report, "data_sha1": "changed"}
        self.assertEqual(
            validate_report(changed_report, manifest),
            ["packed title aggregate SHA-1 differs from manifest"],
        )

    def test_rejects_invalid_command_and_literal_encoding(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid packed title command"):
            encode_cursor_command(TitleCursorCommand("add_row", 32))
        invalid = decode_stream(bytes((0x80, 0x7F)) + bytes(32_766), 0x8000)
        bad_tokens = (
            TitleLiteralRun(invalid.tokens[0].ppu_address, b"\x40"),
            TitleCursorCommand("terminate"),
        )
        with self.assertRaisesRegex(ValueError, "contains a command byte"):
            encode_stream(type(invalid)(0x8000, bad_tokens, 2))


if __name__ == "__main__":
    unittest.main()
