from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audio_editor
import audio_preview
import sound_studio
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

    def test_pal_document_exposes_the_full_six_bit_duration_table(self) -> None:
        profile, reference = audio_case("europe")
        document = audio_editor.export_document(
            parse_ines(reference.read_bytes())["prg"], profile
        )
        referenced = [
            command["value"] & 0x3F
            for command in document["commands"]
            if command["kind"] == "duration"
        ]
        self.assertEqual(len(document["durations"]), 64)
        self.assertEqual(len(document["timing_tail"]), 2)
        self.assertGreater(max(referenced), 25)
        self.assertLess(max(referenced), len(document["durations"]))

    def test_migrates_schema_one_pal_duration_storage_without_loss(self) -> None:
        profile, reference = audio_case("europe")
        current = audio_editor.export_document(
            parse_ines(reference.read_bytes())["prg"], profile
        )
        legacy = copy.deepcopy(current)
        legacy["schema_version"] = 1
        legacy["timing_tail"] = legacy["durations"][26:] + legacy["timing_tail"]
        legacy["durations"] = legacy["durations"][:26]
        self.assertEqual(audio_editor.upgrade_document(legacy), current)

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


class SoundStudioTests(unittest.TestCase):
    def model(self, profile_id: str = "usa") -> sound_studio.SoundStudioDocument:
        profile, reference = audio_case(profile_id)
        image = reference.read_bytes()
        document = audio_editor.export_document(parse_ines(image)["prg"], profile)
        return sound_studio.SoundStudioDocument(
            document,
            profile,
            image,
            ROOT / "content/workspace" / profile_id / "audio.json",
            ROOT / "build/content" / profile_id / "audio-test.nes",
        )

    def test_stream_projection_covers_all_symbolic_entries(self) -> None:
        model = self.model()
        spans = sound_studio.stream_spans(model.document["commands"])
        self.assertEqual(list(spans), [audio_editor.stream_id(i) for i in range(114)])
        self.assertTrue(all(start < end for start, end in spans.values()))

    def test_command_edit_is_validated_dirty_and_undoable(self) -> None:
        model = self.model()
        index = next(
            i
            for i, command in enumerate(model.document["commands"])
            if command["kind"] == "note" and "entry" not in command
        )
        original = model.document["commands"][index]["value"]
        replacement = 1 if original != 1 else 2
        self.assertTrue(model.edit_command(index, "note", f"${replacement:02X}"))
        self.assertTrue(model.dirty)
        self.assertNotEqual(model.rebuilt_image(), model.base_image)
        self.assertTrue(model.undo())
        self.assertFalse(model.dirty)
        self.assertEqual(model.rebuilt_image(), model.base_image)

    def test_rejects_command_kind_with_different_encoded_size(self) -> None:
        model = self.model()
        index = next(
            i
            for i, command in enumerate(model.document["commands"])
            if command["kind"] == "note"
        )
        with self.assertRaisesRegex(audio_editor.AudioEditorError, "byte size"):
            model.edit_command(index, "call", "stream_000")

    def test_effect_envelope_and_timing_edits_use_one_undo_stack(self) -> None:
        model = self.model("europe")
        channel = model.document["effects"][0]["channels"][0]
        virtual = (int(channel["selector"]) + 1) & 7
        self.assertTrue(model.edit_effect_channel(0, 0, virtual, channel["stream"]))
        self.assertEqual(
            model.document["effects"][0]["channels"][0]["selector"],
            virtual | 0x80,
        )
        step = model.document["envelopes"][0]["steps"][0]
        self.assertTrue(
            model.edit_envelope_step(0, 0, step["duration"], step["volume"] ^ 1)
        )
        self.assertTrue(model.edit_timing("durations", 0, 2))
        self.assertEqual(len(model.undo_stack), 3)
        model.validate()

    def test_integer_parser_accepts_editor_notation(self) -> None:
        self.assertEqual(sound_studio.parse_integer("$2A", "value"), 0x2A)
        self.assertEqual(sound_studio.parse_integer("0x2a", "value"), 0x2A)
        self.assertEqual(sound_studio.parse_integer("42", "value"), 42)


class AudioPreviewTests(unittest.TestCase):
    def test_traces_every_effect_for_both_console_timings(self) -> None:
        for profile_id in ("usa", "europe"):
            profile, reference = audio_case(profile_id)
            document = audio_editor.export_document(
                parse_ines(reference.read_bytes())["prg"], profile
            )
            for effect in range(1, 27):
                with self.subTest(profile=profile_id, effect=effect):
                    trace = audio_preview.trace_effect(document, effect, 180)
                    self.assertTrue(trace.frames)
                    self.assertGreater(trace.note_events, 0)
                    self.assertEqual(len(trace.frames[0]), 4)

    def test_writes_non_silent_mono_preview_at_requested_sample_rate(self) -> None:
        profile, reference = audio_case("usa")
        document = audio_editor.export_document(
            parse_ines(reference.read_bytes())["prg"], profile
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "effect.wav"
            trace = audio_preview.write_preview(
                document, profile, 5, path, 0.2, sample_rate=8_000
            )
            with wave.open(str(path), "rb") as source:
                self.assertEqual(source.getnchannels(), 1)
                self.assertEqual(source.getsampwidth(), 2)
                self.assertEqual(source.getframerate(), 8_000)
                payload = source.readframes(source.getnframes())
        self.assertTrue(payload)
        self.assertTrue(any(payload))
        self.assertGreater(trace.note_events, 0)

    def test_preview_mixer_can_isolate_or_mute_apu_voices(self) -> None:
        profile, reference = audio_case("usa")
        document = audio_editor.export_document(
            parse_ines(reference.read_bytes())["prg"], profile
        )
        trace = audio_preview.trace_effect(document, 5, 30)
        pulse = audio_preview.render_trace(
            trace, profile["timing"], sample_rate=8_000, enabled_voices={0}
        )
        muted = audio_preview.render_trace(
            trace, profile["timing"], sample_rate=8_000, enabled_voices=set()
        )
        self.assertTrue(any(pulse))
        self.assertFalse(any(muted))
        self.assertNotEqual(pulse, muted)

    def test_parses_named_preview_channels(self) -> None:
        self.assertEqual(audio_preview.parse_voices("all"), {0, 1, 2, 3})
        self.assertEqual(audio_preview.parse_voices("pulse1, noise"), {0, 3})
        self.assertEqual(audio_preview.parse_voices(""), set())
        with self.assertRaisesRegex(audio_preview.AudioPreviewError, "unknown APU"):
            audio_preview.parse_voices("pulse3")

    def test_piano_roll_segments_cover_each_voice_without_gaps(self) -> None:
        profile, reference = audio_case("usa")
        document = audio_editor.export_document(
            parse_ines(reference.read_bytes())["prg"], profile
        )
        trace = audio_preview.trace_effect(document, 1, 180)
        segments = audio_preview.trace_segments(trace)
        for voice in range(4):
            selected = [segment for segment in segments if segment.voice == voice]
            self.assertEqual(selected[0].start, 0)
            self.assertEqual(selected[-1].end, len(trace.frames))
            self.assertTrue(
                all(
                    left.end == right.start
                    for left, right in zip(selected, selected[1:])
                )
            )

    def test_effect_catalog_uses_confirmed_call_contexts(self) -> None:
        self.assertEqual(len(sound_studio.EFFECT_CONTEXTS), 26)
        self.assertEqual(sound_studio.EFFECT_CONTEXTS[6], "Create breakable block")
        self.assertEqual(sound_studio.EFFECT_CONTEXTS[20], "Enter door")
        self.assertEqual(sound_studio.EFFECT_CONTEXTS[21], "Collect key")
        self.assertIn("PAL resume", sound_studio.EFFECT_CONTEXTS[11])

    def test_program_library_categorizes_every_descriptor_once(self) -> None:
        categorized = [
            effect
            for _name, effects in sound_studio.PROGRAM_GROUPS[:-1]
            for effect in effects
        ]
        self.assertEqual(sorted(categorized), list(range(1, 27)))
        self.assertEqual(len(set(categorized)), 26)
        self.assertEqual(
            sound_studio.program_numbers("All programs"), tuple(range(1, 27))
        )
        self.assertEqual(
            sound_studio.program_label(1),
            "01 - Room audio A / warning return A",
        )
        self.assertIn(16, sound_studio.program_numbers("Music loops"))


if __name__ == "__main__":
    unittest.main()
