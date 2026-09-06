from __future__ import annotations

import unittest

from scripts.audio_data import (
    AUDIO_STREAM_DATA,
    EUROPE_LAYOUT,
    AudioCommand,
    AudioStream,
    collect_report,
    decode_pointer_table,
    decode_stream,
    emit_source,
    encode_stream,
    validate_report,
)


class AudioDataTests(unittest.TestCase):
    def test_decodes_little_endian_pointer_table(self) -> None:
        prg = bytearray(32_768)
        offset = 0x100
        prg[offset : offset + 4] = bytes((0x34, 0x92, 0x78, 0x96))
        self.assertEqual(decode_pointer_table(bytes(prg), 0x8100, 2), [0x9234, 0x9678])

    def test_decodes_commands_and_arguments(self) -> None:
        prg = bytearray(32_768)
        offset = AUDIO_STREAM_DATA - 0x8000
        encoded = bytes((0x80, 0x24, 0xF1, 0x07, 0xF3, 0xA0, 0xF5, 0xF9))
        prg[offset : offset + len(encoded)] = encoded
        stream = decode_stream(bytes(prg), AUDIO_STREAM_DATA)
        self.assertEqual(stream.encoded_size, len(encoded))
        self.assertEqual(stream.commands[2], AudioCommand(AUDIO_STREAM_DATA + 2, 0xF1, b"\x07"))
        self.assertEqual(stream.commands[-1].opcode, 0xF9)
        self.assertEqual(encode_stream(stream), encoded)

    def test_encodes_stream_without_normalizing_tokens(self) -> None:
        stream = AudioStream(
            AUDIO_STREAM_DATA,
            (
                AudioCommand(AUDIO_STREAM_DATA, 0x8F, b""),
                AudioCommand(AUDIO_STREAM_DATA + 1, 0xF2, b"\x92\xF5"),
            ),
            4,
        )
        self.assertEqual(encode_stream(stream), bytes((0x8F, 0xF2, 0x92, 0xF5)))

    def test_rejects_unknown_command(self) -> None:
        prg = bytearray(32_768)
        prg[AUDIO_STREAM_DATA - 0x8000] = 0xFA
        with self.assertRaisesRegex(ValueError, "unknown audio opcode"):
            decode_stream(bytes(prg), AUDIO_STREAM_DATA)

    def test_decodes_stream_with_europe_layout_bounds(self) -> None:
        prg = bytearray(32_768)
        offset = EUROPE_LAYOUT.stream_data - 0x8000
        prg[offset : offset + 2] = bytes((0x80, 0xF9))
        stream = decode_stream(bytes(prg), EUROPE_LAYOUT.stream_data, EUROPE_LAYOUT)
        self.assertEqual(stream.encoded_size, 2)
        self.assertEqual(stream.commands[-1].opcode, 0xF9)

    def test_source_uses_symbolic_audio_pointers(self) -> None:
        # Reuse the reviewed image in the integration-style emitter test; the
        # smaller decoder tests above remain independent synthetic fixtures.
        from pathlib import Path

        from scripts.room_data import extract_prg

        root = Path(__file__).resolve().parent.parent
        candidates = list(root.glob("Solomon?s Key (U)*.nes"))
        if not candidates:
            self.skipTest("reference ROM is not present")
        source = emit_source(extract_prg(candidates[0].read_bytes()))
        self.assertIn("AudioPeriodTable:", source)
        self.assertIn("SoundEffectDescriptor26:", source)
        self.assertIn("AudioJump AudioStream", source)
        self.assertIn("CpuVectors:", source)

    def test_europe_reference_has_complete_reachable_stream_coverage(self) -> None:
        from pathlib import Path

        from scripts.room_data import extract_prg

        root = Path(__file__).resolve().parent.parent
        candidates = list(root.glob("Solomon?s Key (E)*.nes"))
        if not candidates:
            self.skipTest("European reference ROM is not present")
        report = collect_report(
            extract_prg(candidates[0].read_bytes()), EUROPE_LAYOUT
        )
        self.assertEqual(report["stream_entry_count"], 114)
        self.assertEqual(report["stream_command_count"], 2255)
        self.assertEqual(report["stream_coverage_size"], 2725)
        self.assertTrue(report["coverage_complete"])
        self.assertTrue(report["round_trip"])

    def test_audit_detects_changed_counts_hash_and_coverage(self) -> None:
        report = {
            "period_count": 12,
            "duration_count": 26,
            "envelope_count": 8,
            "envelope_step_count": 1,
            "sound_effect_count": 26,
            "sound_effect_channel_count": 1,
            "stream_entry_count": 1,
            "stream_command_count": 1,
            "stream_data_size": 1,
            "stream_coverage_size": 1,
            "table_sha1": "wrong",
            "stream_sha1": "stream",
            "envelope_pointers": [0xF3AA],
            "sound_effect_pointers": [0xF4B0],
            "stream_addresses": [0xF592],
            "coverage_complete": False,
            "round_trip": True,
        }
        manifest = dict(report)
        manifest["period_count"] = 13
        manifest["table_sha1"] = "table"
        manifest["coverage_complete"] = True
        errors = validate_report(report, manifest)
        self.assertEqual(len(errors), 3)


if __name__ == "__main__":
    unittest.main()
