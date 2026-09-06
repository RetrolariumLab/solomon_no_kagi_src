from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audio_editor
from audio_data import (
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
from project import parse_ines
from revision_profiles import get_profile, load_profiles


def audio_case(profile_id: str) -> tuple[dict, Path]:
    profiles = load_profiles(ROOT / "config/revision_profiles.json")
    profile = get_profile(profiles, profile_id)
    reference = ROOT / profile["reference_rom"]
    if not reference.is_file():
        raise unittest.SkipTest(f"{profile_id} reference ROM is not present")
    return profile, reference


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


class AudioEditorTests(unittest.TestCase):
    def test_exports_one_owner_for_each_physical_audio_command(self) -> None:
        profile, reference = audio_case("usa")
        document = audio_editor.export_document(
            parse_ines(reference.read_bytes())["prg"], profile
        )
        entries = [
            command["entry"] for command in document["commands"] if "entry" in command
        ]
        self.assertEqual(entries, [audio_editor.stream_id(index) for index in range(114)])
        self.assertEqual(len(document["effects"]), 26)
        self.assertEqual(len(document["envelopes"]), 8)

    def test_round_trips_both_profile_audio_banks_byte_for_byte(self) -> None:
        for profile_id in ("usa", "europe"):
            with self.subTest(profile=profile_id):
                profile, reference = audio_case(profile_id)
                original = reference.read_bytes()
                document = audio_editor.export_document(
                    parse_ines(original)["prg"], profile
                )
                rebuilt = audio_editor.build_audio_image(document, original, profile)
                self.assertEqual(rebuilt, original)
                audio_editor.validate_rebuilt_document(document, rebuilt, profile)

    def test_reflows_symbolic_stream_entries_when_command_sizes_change(self) -> None:
        profile, reference = audio_case("usa")
        original = reference.read_bytes()
        document = audio_editor.export_document(parse_ines(original)["prg"], profile)
        commands = document["commands"]
        entry_indices = [
            index for index, command in enumerate(commands) if "entry" in command
        ]
        note_index = value_index = entry_index = -1
        for candidate in entry_indices:
            notes = [
                index
                for index in range(candidate)
                if commands[index]["kind"] == "note" and "entry" not in commands[index]
            ]
            values = [
                index
                for index in range(candidate + 1, len(commands))
                if commands[index]["kind"] in audio_editor.VALUE_COMMANDS
                and "entry" not in commands[index]
            ]
            if notes and values:
                note_index, value_index, entry_index = notes[-1], values[0], candidate
                break
        self.assertGreaterEqual(entry_index, 0)
        target = commands[entry_index]["entry"]
        layout = audio_editor.profile_layout(profile)
        _, original_entries = audio_editor.encode_commands(commands, layout)

        modified = copy.deepcopy(document)
        modified["commands"][note_index] = {"kind": "set_control", "value": 0}
        modified["commands"][value_index] = {"kind": "note", "value": 0x10}
        _, modified_entries = audio_editor.encode_commands(
            modified["commands"], layout
        )
        self.assertEqual(modified_entries[target], original_entries[target] + 1)

        rebuilt = audio_editor.build_audio_image(modified, original, profile)
        self.assertNotEqual(rebuilt, original)
        audio_editor.validate_rebuilt_document(modified, rebuilt, profile)

    def test_rejects_stream_growth_and_invalid_effect_boundary(self) -> None:
        profile, reference = audio_case("usa")
        document = audio_editor.export_document(
            parse_ines(reference.read_bytes())["prg"], profile
        )
        grown = copy.deepcopy(document)
        grown["commands"].append({"kind": "note", "value": 0})
        with self.assertRaisesRegex(audio_editor.AudioEditorError, "encode to"):
            audio_editor.encode_document(grown, profile)

        boundary = copy.deepcopy(document)
        boundary["effects"][1]["channels"][0]["selector"] &= 0x7F
        with self.assertRaisesRegex(audio_editor.AudioEditorError, "first channel"):
            audio_editor.encode_document(boundary, profile)


if __name__ == "__main__":
    unittest.main()
